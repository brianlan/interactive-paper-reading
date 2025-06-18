#!/usr/bin/env python3
"""
Test script to process DN-DETR PDF with GROBID
"""

import sys
from pathlib import Path
from grobid_processor import GrobidProcessor

def main():
    # Configuration
    pdf_path = "/Users/rlan/work/papers/ObjectDetection/DN-DETR-2203.01305v3.pdf"
    output_dir = "/Users/rlan/projects/interactive-paper-reading/papers/dn-detr"
    server_url = "http://10.243.123.49:8070"
    
    print("🔍 Testing GROBID PDF Processing")
    print(f"PDF: {pdf_path}")
    print(f"Output: {output_dir}")
    print(f"Server: {server_url}")
    print("-" * 50)
    
    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return 1
    
    # Initialize processor
    processor = GrobidProcessor(server_url=server_url)
    
    # Check server status first
    print("🏥 Checking GROBID server status...")
    if not processor.check_server_status():
        print("❌ Cannot connect to GROBID server")
        return 1
    
    # Process the PDF
    print("\n📄 Processing PDF with GROBID...")
    try:
        result_dir = processor.process_pdf(
            pdf_path=pdf_path,
            output_dir=output_dir,
            add_coordinates=True,  # Include PDF coordinates
            consolidate_header=True,  # Better metadata
            consolidate_citations=True,  # Better references
            n_workers=1  # Conservative for testing
        )
        
        print("\n✅ Processing completed!")
        print(f"📁 Results saved to: {result_dir}")
        
        # Show what was created
        tei_files = list(Path(result_dir).glob("*.tei.xml"))
        if tei_files:
            tei_file = tei_files[0]
            print(f"\n📋 Generated TEI file: {tei_file.name}")
            print(f"📏 File size: {tei_file.stat().st_size / 1024:.1f} KB")
            
            # Show first few lines
            with open(tei_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                print("\n📖 First few lines of TEI output:")
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2d}: {line.rstrip()}")
                if len(lines) == 10:
                    print("   ...")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error processing PDF: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
