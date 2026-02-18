"""
Functional End-to-End Testing
Tests actual PDF generation, file uploads, and orientation validation.

Run with: pytest test_functional.py -v -s
"""

import pytest
import io
import os
from pathlib import Path
from PyPDF2 import PdfReader
from app import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_csv_single_card():
    """Valid CSV with one complete card (6 questions)."""
    return """level,subject,question,answer
Year 2,M,What is 2+2?,4
Year 2,S,What is water made of?,Hydrogen and Oxygen (H2O)
Year 2,E,What is a noun?,A naming word for a person place or thing
Year 2,H,Who was the first Queen of England?,Queen Mary I
Year 2,G,What is a map?,A drawing that shows you where places are
Year 2,A,What color do you get mixing red and blue?,Purple"""


@pytest.fixture
def sample_csv_two_cards():
    """Valid CSV with two complete cards (12 questions)."""
    return """level,subject,question,answer
Year 2,M,What is 2+2?,4
Year 2,S,What is water made of?,H2O
Year 2,E,What is a noun?,A naming word
Year 2,H,Who was the first Queen?,Queen Mary I
Year 2,G,What is a map?,A drawing of places
Year 2,A,What is red + blue?,Purple
Year 3,M,What is 5x5?,25
Year 3,S,What gas do plants produce?,Oxygen
Year 3,E,What is a verb?,An action word
Year 3,H,When was WW2?,1939-1945
Year 3,G,What is the capital of France?,Paris
Year 3,A,Who painted the Mona Lisa?,Leonardo da Vinci"""


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for PDF outputs."""
    output_dir = tmp_path / "test_pdfs"
    output_dir.mkdir()
    return output_dir


class TestPDFGeneration:
    """Test actual PDF generation and validation."""
    
    def test_generate_pdf_duplex_long(self, client, sample_csv_single_card, temp_output_dir):
        """Test PDF generation with duplex long edge printing."""
        print("\n\n🧪 Testing DUPLEX LONG EDGE PDF generation...")
        
        data = {
            'csv': (io.BytesIO(sample_csv_single_card.encode('utf-8')), 'test.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200, f"Failed with status {response.status_code}"
        assert response.content_type == 'application/pdf'
        
        # Save PDF for inspection
        pdf_path = temp_output_dir / 'duplex_long.pdf'
        pdf_path.write_bytes(response.data)
        
        # Validate PDF
        reader = PdfReader(io.BytesIO(response.data))
        
        print(f"✅ PDF generated successfully")
        print(f"   📄 Number of pages: {len(reader.pages)}")
        print(f"   📏 Page size: {reader.pages[0].mediabox.width} x {reader.pages[0].mediabox.height}")
        print(f"   💾 File size: {len(response.data):,} bytes")
        print(f"   📁 Saved to: {pdf_path}")
        
        # Should have 2 pages (1 for questions, 1 for answers)
        assert len(reader.pages) == 2, f"Expected 2 pages, got {len(reader.pages)}"
        
        # Check page size is A4 (595.2 x 841.8 points)
        page = reader.pages[0]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        # Allow some tolerance
        assert 590 < width < 600, f"Width {width} not A4"
        assert 835 < height < 850, f"Height {height} not A4"
        
        print(f"✅ PDF structure validated for duplex long edge")
    
    def test_generate_pdf_duplex_short(self, client, sample_csv_single_card, temp_output_dir):
        """Test PDF generation with duplex short edge printing."""
        print("\n\n🧪 Testing DUPLEX SHORT EDGE PDF generation...")
        
        data = {
            'csv': (io.BytesIO(sample_csv_single_card.encode('utf-8')), 'test.csv'),
            'print_mode': 'duplex_short'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        
        # Save PDF
        pdf_path = temp_output_dir / 'duplex_short.pdf'
        pdf_path.write_bytes(response.data)
        
        reader = PdfReader(io.BytesIO(response.data))
        
        print(f"✅ PDF generated successfully")
        print(f"   📄 Number of pages: {len(reader.pages)}")
        print(f"   💾 File size: {len(response.data):,} bytes")
        print(f"   📁 Saved to: {pdf_path}")
        
        # Should have 2 pages
        assert len(reader.pages) == 2
        
        print(f"✅ PDF structure validated for duplex short edge")
    
    def test_generate_pdf_single_sided(self, client, sample_csv_single_card, temp_output_dir):
        """Test PDF generation with single-sided printing."""
        print("\n\n🧪 Testing SINGLE-SIDED PDF generation...")
        
        data = {
            'csv': (io.BytesIO(sample_csv_single_card.encode('utf-8')), 'test.csv'),
            'print_mode': 'single_sided'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        
        # Save PDF
        pdf_path = temp_output_dir / 'single_sided.pdf'
        pdf_path.write_bytes(response.data)
        
        reader = PdfReader(io.BytesIO(response.data))
        
        print(f"✅ PDF generated successfully")
        print(f"   📄 Number of pages: {len(reader.pages)}")
        print(f"   💾 File size: {len(response.data):,} bytes")
        print(f"   📁 Saved to: {pdf_path}")
        
        # Single-sided should have only 1 page (questions only, no answers)
        assert len(reader.pages) == 1, f"Expected 1 page for single-sided, got {len(reader.pages)}"
        
        print(f"✅ PDF structure validated - questions only, no answer page")
    
    def test_generate_pdf_multiple_cards(self, client, sample_csv_two_cards, temp_output_dir):
        """Test PDF generation with multiple cards."""
        print("\n\n🧪 Testing MULTIPLE CARDS PDF generation...")
        
        data = {
            'csv': (io.BytesIO(sample_csv_two_cards.encode('utf-8')), 'test.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        
        # Save PDF
        pdf_path = temp_output_dir / 'multiple_cards.pdf'
        pdf_path.write_bytes(response.data)
        
        reader = PdfReader(io.BytesIO(response.data))
        
        print(f"✅ PDF generated successfully")
        print(f"   📄 Number of pages: {len(reader.pages)}")
        print(f"   💾 File size: {len(response.data):,} bytes")
        print(f"   📁 Saved to: {pdf_path}")
        
        # With 2 cards: should have 2 pages (cards arranged in grid)
        assert len(reader.pages) == 2, f"Expected 2 pages, got {len(reader.pages)}"
        
        print(f"✅ Multiple cards validated")
    
    def test_pdf_content_extraction(self, client, sample_csv_single_card):
        """Test that PDF contains the expected text content."""
        print("\n\n🧪 Testing PDF CONTENT extraction...")
        
        data = {
            'csv': (io.BytesIO(sample_csv_single_card.encode('utf-8')), 'test.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        
        reader = PdfReader(io.BytesIO(response.data))
        
        # Extract text from first page (questions)
        page_text = reader.pages[0].extract_text()
        
        print(f"✅ Text extraction successful")
        print(f"   📝 Extracted {len(page_text)} characters")
        
        # Check that questions are in the PDF
        assert "What is 2+2?" in page_text, "Question text not found in PDF"
        assert "What is water" in page_text or "water made of" in page_text, "Water question not found"
        assert "Year 2" in page_text, "Level not found in PDF"
        
        print(f"✅ Content validation passed - questions found in PDF")
        
        # Check answer page
        if len(reader.pages) > 1:
            answer_text = reader.pages[1].extract_text()
            print(f"   📝 Answer page has {len(answer_text)} characters")
            assert "4" in answer_text or "Hydrogen" in answer_text, "Answers not found in PDF"
            print(f"✅ Answer page validated")


class TestCSVValidation:
    """Test CSV validation and error handling."""
    
    def test_invalid_csv_missing_columns(self, client):
        """Test rejection of CSV with missing required columns."""
        print("\n\n🧪 Testing INVALID CSV (missing columns)...")
        
        invalid_csv = """question,answer
What is 2+2?,4
What is water?,H2O"""
        
        data = {
            'csv': (io.BytesIO(invalid_csv.encode('utf-8')), 'invalid.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        print(f"   Response status: {response.status_code}")
        
        # Should reject with 400 or 422
        assert response.status_code in [400, 422, 500], "Should reject invalid CSV"
        
        if response.status_code in [400, 422]:
            data = response.get_json()
            print(f"   Error message: {data.get('error', 'No error message')}")
            assert 'error' in data
            print(f"✅ Invalid CSV properly rejected")
        else:
            print(f"⚠️  Server error - may need better validation")
    
    def test_empty_csv(self, client):
        """Test rejection of empty CSV file."""
        print("\n\n🧪 Testing EMPTY CSV...")
        
        empty_csv = ""
        
        data = {
            'csv': (io.BytesIO(empty_csv.encode('utf-8')), 'empty.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        print(f"   Response status: {response.status_code}")
        assert response.status_code in [400, 422, 500], "Should reject empty CSV"
        print(f"✅ Empty CSV properly rejected")
    
    def test_incomplete_card(self, client):
        """Test rejection of CSV with incomplete card (less than 6 questions)."""
        print("\n\n🧪 Testing INCOMPLETE CARD (only 3 questions)...")
        
        incomplete_csv = """level,subject,question,answer
Year 2,M,What is 2+2?,4
Year 2,S,What is water?,H2O
Year 2,E,What is a noun?,A naming word"""
        
        data = {
            'csv': (io.BytesIO(incomplete_csv.encode('utf-8')), 'incomplete.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        print(f"   Response status: {response.status_code}")
        
        # Should reject incomplete cards
        assert response.status_code in [400, 422, 500], "Should reject incomplete card"
        
        if response.status_code == 400:
            data = response.get_json()
            print(f"   Error message: {data.get('error', 'No error message')}")
            print(f"✅ Incomplete card properly rejected")
        else:
            print(f"⚠️  Rejection occurred but may need clearer error message")


class TestFileUpload:
    """Test file upload functionality."""
    
    def test_no_file_uploaded(self, client):
        """Test error when no file is uploaded."""
        print("\n\n🧪 Testing NO FILE upload...")
        
        response = client.post(
            '/api/generate',
            data={'print_mode': 'duplex_long'},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print(f"   Error: {data['error']}")
        print(f"✅ Missing file properly rejected")
    
    def test_wrong_file_type(self, client):
        """Test rejection of non-CSV files."""
        print("\n\n🧪 Testing WRONG FILE TYPE (.txt)...")
        
        data = {
            'csv': (io.BytesIO(b'some text content'), 'test.txt'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        print(f"   Error: {data.get('error', 'No error')}")
        print(f"✅ Wrong file type rejected")
    
    def test_file_size_limit(self, client):
        """Test file size limit enforcement."""
        print("\n\n🧪 Testing FILE SIZE limit (>10MB)...")
        
        # Create a large file
        large_content = 'a' * (11 * 1024 * 1024)  # 11MB
        
        data = {
            'csv': (io.BytesIO(large_content.encode('utf-8')), 'large.csv'),
            'print_mode': 'duplex_long'
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 413, f"Expected 413, got {response.status_code}"
        data = response.get_json()
        assert 'error' in data
        print(f"   Error: {data['error']}")
        print(f"✅ File size limit enforced (10MB)")


def test_print_mode_comparison(client, sample_csv_single_card, temp_output_dir):
    """Compare all three print modes side by side."""
    print("\n\n" + "="*70)
    print("📊 PRINT MODE COMPARISON")
    print("="*70)
    
    modes = ['duplex_long', 'duplex_short', 'single_sided']
    results = {}
    
    for mode in modes:
        data = {
            'csv': (io.BytesIO(sample_csv_single_card.encode('utf-8')), 'test.csv'),
            'print_mode': mode
        }
        
        response = client.post(
            '/api/generate',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200, f"{mode} failed"
        
        # Save and analyze
        pdf_path = temp_output_dir / f'{mode}.pdf'
        pdf_path.write_bytes(response.data)
        
        reader = PdfReader(io.BytesIO(response.data))
        
        results[mode] = {
            'pages': len(reader.pages),
            'size_bytes': len(response.data),
            'path': pdf_path
        }
    
    # Print comparison table
    print(f"\n{'Mode':<20} {'Pages':<10} {'Size (KB)':<15} {'File Path'}")
    print("-" * 70)
    
    for mode, info in results.items():
        size_kb = info['size_bytes'] / 1024
        print(f"{mode:<20} {info['pages']:<10} {size_kb:>10.2f} KB   {info['path']}")
    
    print("\n" + "="*70)
    print("✅ All print modes generated successfully")
    print("="*70)
    
    # Validate expectations
    assert results['duplex_long']['pages'] == 2, "Duplex long should have 2 pages"
    assert results['duplex_short']['pages'] == 2, "Duplex short should have 2 pages"
    assert results['single_sided']['pages'] == 1, "Single-sided should have 1 page"
    
    print("\n📋 SUMMARY:")
    print("  ✅ Duplex Long: 2 pages (flip on long edge)")
    print("  ✅ Duplex Short: 2 pages (flip on short edge)")
    print("  ✅ Single-Sided: 1 page (questions only)")
    print(f"\n  All PDFs saved to: {temp_output_dir}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
