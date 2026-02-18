"""
PDF Analysis Script
Analyzes generated PDFs for structure, metadata, and content.
"""

from pathlib import Path
from PyPDF2 import PdfReader
import os

OUTPUT_DIR = Path("test_output_pdfs")

def analyze_pdf(pdf_path):
    """Analyze a PDF file and return detailed information."""
    
    if not pdf_path.exists():
        return {"error": "File not found"}
    
    try:
        reader = PdfReader(pdf_path)
        
        info = {
            'filename': pdf_path.name,
            'size_bytes': pdf_path.stat().st_size,
            'size_kb': pdf_path.stat().st_size / 1024,
            'num_pages': len(reader.pages),
            'pages': []
        }
        
        # Analyze each page
        for i, page in enumerate(reader.pages, 1):
            mediabox = page.mediabox
            width = float(mediabox.width)
            height = float(mediabox.height)
            
            # Extract text
            text = page.extract_text()
            
            # Detect rotation
            rotation = page.get('/Rotate', 0)
            
            page_info = {
                'number': i,
                'width': width,
                'height': height,
                'width_mm': width * 0.352778,  # Convert points to mm
                'height_mm': height * 0.352778,
                'orientation': 'Portrait' if height > width else 'Landscape',
                'rotation': rotation,
                'text_length': len(text),
                'text_preview': text[:200].replace('\n', ' ').strip()
            }
            
            info['pages'].append(page_info)
        
        return info
    
    except Exception as e:
        return {"error": str(e)}


def main():
    print("="*80)
    print("📊 PDF ANALYSIS REPORT")
    print("="*80)
    print()
    
    if not OUTPUT_DIR.exists():
        print(f"❌ Directory not found: {OUTPUT_DIR}")
        return
    
    # Find all PDFs
    pdf_files = list(OUTPUT_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {OUTPUT_DIR}")
        return
    
    print(f"📂 Directory: {OUTPUT_DIR.absolute()}")
    print(f"📄 Found {len(pdf_files)} PDF file(s)\n")
    
    # Analyze each PDF
    for pdf_path in sorted(pdf_files):
        print("\n" + "─"*80)
        print(f"📄 {pdf_path.name}")
        print("─"*80)
        
        info = analyze_pdf(pdf_path)
        
        if 'error' in info:
            print(f"❌ Error: {info['error']}")
            continue
        
        # Basic info
        print(f"\n📋 Basic Information:")
        print(f"   File Size: {info['size_kb']:.2f} KB ({info['size_bytes']:,} bytes)")
        print(f"   Pages: {info['num_pages']}")
        
        # Page details
        for page in info['pages']:
            print(f"\n   Page {page['number']}:")
            print(f"      Size: {page['width']:.1f} x {page['height']:.1f} points")
            print(f"      Size: {page['width_mm']:.1f} x {page['height_mm']:.1f} mm")
            print(f"      Orientation: {page['orientation']}")
            
            # Check if it's A4 size
            is_a4 = (200 < page['width_mm'] < 220 and 280 < page['height_mm'] < 300)
            print(f"      A4 Size: {'✅ Yes' if is_a4 else '❌ No'}")
            
            if page['rotation'] != 0:
                print(f"      Rotation: {page['rotation']}°")
            
            print(f"      Text Content: {page['text_length']} characters")
            
            if page['text_preview']:
                print(f"      Preview: {page['text_preview'][:100]}...")
    
    # Summary comparison
    print("\n\n" + "="*80)
    print("📊 COMPARISON SUMMARY")
    print("="*80)
    print(f"\n{'File':<30} {'Pages':<8} {'Size (KB)':<12} {'Orientation'}")
    print("─"*80)
    
    for pdf_path in sorted(pdf_files):
        info = analyze_pdf(pdf_path)
        if 'error' not in info:
            name = pdf_path.name
            pages = info['num_pages']
            size = f"{info['size_kb']:.2f}"
            orientation = info['pages'][0]['orientation'] if info['pages'] else 'Unknown'
            print(f"{name:<30} {pages:<8} {size:<12} {orientation}")
    
    print("\n" + "="*80)
    print("✅ VALIDATION CHECKS")
    print("="*80)
    
    # Validate each file
    for pdf_path in sorted(pdf_files):
        info = analyze_pdf(pdf_path)
        if 'error' in info:
            continue
        
        print(f"\n{pdf_path.name}:")
        
        checks = []
        
        # Check page count
        if 'duplex' in pdf_path.name:
            if info['num_pages'] == 2:
                checks.append("✅ Correct page count (2 pages for duplex)")
            else:
                checks.append(f"❌ Wrong page count ({info['num_pages']} instead of 2)")
        elif 'single' in pdf_path.name:
            if info['num_pages'] == 1:
                checks.append("✅ Correct page count (1 page for single-sided)")
            else:
                checks.append(f"❌ Wrong page count ({info['num_pages']} instead of 1)")
        
        # Check orientation
        for page in info['pages']:
            if page['orientation'] == 'Portrait':
                checks.append(f"✅ Page {page['number']}: Portrait orientation")
            else:
                checks.append(f"⚠️  Page {page['number']}: {page['orientation']} orientation")
        
        # Check A4 size
        all_a4 = all(200 < p['width_mm'] < 220 and 280 < p['height_mm'] < 300 for p in info['pages'])
        if all_a4:
            checks.append("✅ All pages are A4 size")
        else:
            checks.append("⚠️  Non-standard page size detected")
        
        # Check for content
        has_content = all(p['text_length'] > 0 for p in info['pages'])
        if has_content:
            checks.append("✅ All pages contain text content")
        else:
            checks.append("⚠️  Some pages may be empty")
        
        for check in checks:
            print(f"  {check}")
    
    print("\n" + "="*80)
    print("🎉 Analysis complete!")
    print("="*80)
    print("\n💡 TIP: Open the PDFs in your PDF viewer to visually inspect:")
    print("   • Card layout and alignment")
    print("   • Text readability and font sizes")
    print("   • Question/answer positioning")
    print("   • Print a test page to verify duplex orientation")
    print()


if __name__ == '__main__':
    main()
