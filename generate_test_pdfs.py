"""
Manual PDF Generation Test Script
Generates PDFs for manual inspection and verification.
"""

import requests
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:5000"
CSV_FILE = "test_real_cards.csv"
OUTPUT_DIR = Path("test_output_pdfs")

def test_pdf_generation():
    """Generate PDFs for all print modes."""
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("="*70)
    print("🧪 MANUAL PDF GENERATION TEST")
    print("="*70)
    print(f"\n📁 CSV File: {CSV_FILE}")
    print(f"📂 Output Directory: {OUTPUT_DIR}")
    print(f"🌐 Server: {BASE_URL}\n")
    
    # Check if CSV file exists
    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        print(f"❌ Error: {CSV_FILE} not found!")
        return
    
    print(f"✅ CSV file found ({csv_path.stat().st_size} bytes)\n")
    
    # Test each print mode
    print_modes = [
        ('duplex_long', 'Duplex - Long Edge (flip on long edge)'),
        ('duplex_short', 'Duplex - Short Edge (flip on short edge)'),
        ('single_sided', 'Single-Sided (questions only)')
    ]
    
    results = []
    
    for mode, description in print_modes:
        print(f"\n📄 Testing: {mode}")
        print(f"   Description: {description}")
        
        output_file = OUTPUT_DIR / f"cards_{mode}.pdf"
        
        try:
            # Upload CSV and get PDF
            with open(csv_path, 'rb') as f:
                files = {'csv': (CSV_FILE, f, 'text/csv')}
                data = {'print_mode': mode}
                
                response = requests.post(
                    f"{BASE_URL}/api/generate",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            if response.status_code == 200:
                # Save PDF
                output_file.write_bytes(response.content)
                
                size_kb = len(response.content) / 1024
                print(f"   ✅ SUCCESS")
                print(f"   💾 Size: {size_kb:.2f} KB")
                print(f"   📁 Saved: {output_file}")
                
                results.append({
                    'mode': mode,
                    'status': 'SUCCESS',
                    'size': size_kb,
                    'file': output_file
                })
            else:
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error.get('error', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text[:200]}")
                
                results.append({
                    'mode': mode,
                    'status': 'FAILED',
                    'error': response.status_code
                })
        
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                'mode': mode,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"\n{'Mode':<20} {'Status':<10} {'Size':<15} {'File'}")
    print("-"*70)
    
    for result in results:
        mode = result['mode']
        status = result['status']
        
        if status == 'SUCCESS':
            size = f"{result['size']:.2f} KB"
            file = str(result['file'])
            print(f"{mode:<20} {status:<10} {size:<15} {file}")
        else:
            error = result.get('error', 'Unknown')
            print(f"{mode:<20} {status:<10} {error!s:<15}")
    
    print("\n" + "="*70)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    print(f"✅ {successful}/{len(results)} tests passed")
    
    if successful > 0:
        print(f"\n📂 PDFs generated in: {OUTPUT_DIR.absolute()}")
        print("\n🔍 NEXT STEPS:")
        print("  1. Open the PDFs in Adobe Reader or your default PDF viewer")
        print("  2. Check page orientation (portrait)")
        print("  3. Verify duplex PDFs have 2 pages, single-sided has 1 page")
        print("  4. Check question alignment and readability")
        print("  5. Print test pages to verify duplex orientation works correctly")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    test_pdf_generation()
