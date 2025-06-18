#!/usr/bin/env python3
"""
Example: Process academic paper with GROBID

This script demonstrates how to use the GROBID processor programmatically
to process academic papers with TEI output and coordinates.
"""

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from grobid_processor import GrobidProcessor


def main():
    # Initialize GROBID processor with your server
    processor = GrobidProcessor(server_url="http://10.243.123.49:8070")
    
    # Check server status
    if not processor.check_server_status():
        print("Cannot connect to GROBID server at http://10.243.123.49:8070")
        return
    
    # Use the specific PDF file you provided
    pdf_path = Path("/Users/rlan/work/papers/ObjectDetection/DN-DETR-2203.01305v3.pdf")
    
    if not pdf_path.exists():
        print(f"PDF file not found: {pdf_path}")
        return
    
    print(f"Processing PDF: {pdf_path.name}")
    
    # Set output directory in papers folder
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "papers" / "processed_output"
    
    try:
        # Process PDF with all your specified options:
        # - TEI format (default output)
        # - Process fulltext document 
        # - Add coordinates
        result_dir = processor.process_pdf(
            pdf_path=pdf_path,
            output_dir=output_dir,
            add_coordinates=True,  # Your requirement: "add coordinates"
            consolidate_header=True,  # Enhanced metadata
            consolidate_citations=True,  # Enhanced references
            generate_ids=True,  # Add XML IDs
            segment_sentences=True,  # Sentence boundaries
            n_workers=5  # Conservative number of workers
        )
        
        print(f"\n🎉 Successfully processed {pdf_path.name}")
        print(f"TEI output saved to: {result_dir}")
        
        # Show what was generated
        tei_files = list(result_dir.glob("*.tei.xml"))
        if tei_files:
            tei_file = tei_files[0]
            print(f"\nGenerated TEI file: {tei_file.name}")
            print(f"File size: {tei_file.stat().st_size / 1024:.1f} KB")
            
            # Show first few lines of the TEI file
            print("\nFirst few lines of TEI output:")
            print("=" * 50)
            with open(tei_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 10:
                        print("...")
                        break
                    print(line.rstrip())
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
