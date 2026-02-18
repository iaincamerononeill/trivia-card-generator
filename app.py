"""
Flask web application for trivia card generator.
Provides a web interface for uploading CSV files and generating printable trivia cards.
"""

from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
from pathlib import Path
import tempfile
import os
import secrets
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from card_generator_v2 import load_cards_from_csv, render_pdf, LayoutConfig

app = Flask(__name__)

# Enable CORS for external sites to call the API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure upload limits (10MB max)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Security: Generate secret key for session management
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = secrets.token_hex(32)

# Security: Disable debug mode in production
app.config['DEBUG'] = False

# Security: Set secure headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Allow inline styles and scripts for the application while maintaining security for other resources
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; img-src 'self' data:"
    return response


# Error handler for file size limit
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size exceeding limit."""
    return jsonify({'error': 'File size exceeds 10MB limit'}), 413


@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')


@app.route('/privacy')
def privacy():
    """Serve the privacy policy page."""
    return render_template('privacy.html')


@app.route('/accessibility')
def accessibility():
    """Serve the accessibility statement page."""
    return render_template('accessibility.html')


@app.route('/api/generate', methods=['POST'])
def generate_cards():
    """
    Generate trivia cards from uploaded CSV file.
    
    Expects:
        - CSV file in request.files['csv']
    
    Returns:
        - PDF file for download
        - Or JSON error if generation fails
    """
    try:
        # Check if file was uploaded
        if 'csv' not in request.files:
            return jsonify({'error': 'No CSV file uploaded'}), 400
        
        file = request.files['csv']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Security: Sanitize filename
        filename = secure_filename(file.filename)
        
        if not filename or not filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Security: Check file content type
        if file.content_type and not file.content_type in ['text/csv', 'application/csv', 'text/plain', 'application/vnd.ms-excel']:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_csv:
            csv_path = Path(tmp_csv.name)
            # Read uploaded file and write to temp file
            file.seek(0)
            tmp_csv.write(file.read())
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            pdf_path = Path(tmp_pdf.name)
        
        try:
            # Get print mode from request (default to duplex_long)
            print_mode = request.form.get('print_mode', 'duplex_long')
            if print_mode not in ['duplex_long', 'duplex_short', 'single_sided']:
                return jsonify({'error': 'Invalid print_mode. Must be one of: duplex_long, duplex_short, single_sided'}), 400
            
            # Generate cards with selected print mode
            cards = load_cards_from_csv(csv_path)
            render_pdf(cards, pdf_path, LayoutConfig(), print_mode=print_mode)
            
            # Send the generated PDF
            # Note: We don't delete the PDF immediately as send_file needs it
            # The OS will clean up temp files automatically
            response = send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='trivia_cards.pdf'
            )
            
            # Clean up CSV immediately
            try:
                os.unlink(csv_path)
            except:
                pass
            
            return response
        
        except Exception as e:
            # Clean up on error
            try:
                os.unlink(csv_path)
            except:
                pass
            try:
                os.unlink(pdf_path)
            except:
                pass
            raise
    
    except ValueError as e:
        # Validation errors from card generator
        error_msg = str(e)
        app.logger.warning(f"Validation error: {error_msg}")
        return jsonify({'error': error_msg}), 400
    
    except RequestEntityTooLarge:
        # File size exceeds limit
        app.logger.warning("File size exceeds 10MB limit")
        return jsonify({'error': 'File size exceeds 10MB limit'}), 413
    
    except Exception as e:
        # Unexpected errors - don't expose internal details in production
        app.logger.error(f"Error generating cards: {str(e)}", exc_info=True)
        # Security: Don't leak internal error details in production
        if app.config['DEBUG']:
            return jsonify({'error': f'Error: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Failed to generate cards. Please check your CSV format.'}), 500


@app.route('/api/generate-ai', methods=['POST'])
def generate_with_ai():
    """Generate trivia cards using AI based on topic and parameters."""
    try:
        data = request.get_json()
        
        # Validate required fields
        topic = data.get('topic', '').strip()
        level = data.get('level', '').strip()
        num_cards = int(data.get('num_cards', 1))
        api_provider = data.get('api_provider', 'openai')
        api_key = data.get('api_key', '').strip()
        print_mode = data.get('print_mode', 'duplex_long')
        
        if not all([topic, level, api_key]):
            return jsonify({'error': 'Missing required fields: topic, level, api_key'}), 400
        
        if num_cards < 1 or num_cards > 10:
            return jsonify({'error': 'num_cards must be between 1 and 10'}), 400
        
        if print_mode not in ['duplex_long', 'duplex_short', 'single_sided']:
            return jsonify({'error': 'Invalid print_mode'}), 400
        
        # Import AI generator
        from ai_question_generator import generate_questions
        
        # Generate questions using AI
        csv_content = generate_questions(
            topic=topic,
            level=level,
            num_cards=num_cards,
            api_provider=api_provider,
            api_key=api_key
        )
        
        # Save CSV to temporary file
        csv_path = os.path.join(tempfile.gettempdir(), f"ai_cards_{secure_filename(topic)}.csv")
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        try:
            # Generate PDF
            cards = load_cards_from_csv(csv_path)
            pdf_path = os.path.join(tempfile.gettempdir(), f"ai_trivia_cards_{secure_filename(topic)}.pdf")
            render_pdf(cards, Path(pdf_path), LayoutConfig(), print_mode=print_mode)
            
            # Send PDF
            response = send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'ai_trivia_cards_{topic}.pdf'
            )
            
            # Clean up CSV
            try:
                os.unlink(csv_path)
            except:
                pass
            
            return response
            
        except Exception as e:
            # Clean up on error
            try:
                os.unlink(csv_path)
            except:
                pass
            try:
                os.unlink(pdf_path)
            except:
                pass
            raise
    
    except ValueError as e:
        app.logger.warning(f"AI generation validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        app.logger.error(f"Error in AI generation: {str(e)}", exc_info=True)
        if app.config['DEBUG']:
            return jsonify({'error': f'Error: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Failed to generate cards with AI. Please check your inputs and API key.'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # Development server only - use gunicorn in production
    # Never run with debug=True in production!
    import sys
    if '--debug' in sys.argv:
        app.config['DEBUG'] = True
        print("⚠️  WARNING: Running in DEBUG mode. Do not use in production!")
    app.run(host='127.0.0.1', port=5000)  # Only bind to localhost by default
