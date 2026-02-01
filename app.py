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
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response


@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')


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
            # Generate cards
            cards = load_cards_from_csv(csv_path)
            render_pdf(cards, pdf_path, LayoutConfig())
            
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
    
    except Exception as e:
        # Unexpected errors - don't expose internal details in production
        app.logger.error(f"Error generating cards: {str(e)}", exc_info=True)
        # Security: Don't leak internal error details in production
        if app.config['DEBUG']:
            return jsonify({'error': f'Error: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Failed to generate cards. Please check your CSV format.'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    # Development server only - use gunicorn in production
    # Never run with debug=True in production!
    import sys
    if '--debug' in sys.argv:
        app.config['DEBUG'] = True
        print("⚠️  WARNING: Running in DEBUG mode. Do not use in production!")
    app.run(host='127.0.0.1', port=5000)  # Only bind to localhost by default
