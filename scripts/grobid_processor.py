#!/usr/bin/env python3
"""
GROBID PDF Processor CLI

This script processes PDF files using GROBID to extract structured text in TEI format
with PDF coordinates included.

Requirements:
- TEI output format
- Process fulltext document
- Add coordinates
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to Python path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_paper_reading.grobid import GrobidProcessor


def main():
    parser = argparse.ArgumentParser(description="Process PDF files with GROBID")
    parser.add_argument("pdf_path", help="Path to PDF file or directory containing PDFs")
    parser.add_argument("-o", "--output", help="Output directory for TEI files")
    parser.add_argument("-s", "--server", default="http://10.243.123.49:8070", 
                       help="GROBID server URL (default: http://10.243.123.49:8070)")
    parser.add_argument("-n", "--workers", type=int, default=10,
                       help="Number of concurrent workers (default: 10)")
    parser.add_argument("--no-coordinates", action="store_true",
                       help="Don't add PDF coordinates to TEI output")
    parser.add_argument("--consolidate-header", action="store_true",
                       help="Consolidate header metadata")
    parser.add_argument("--consolidate-citations", action="store_true", 
                       help="Consolidate bibliographical references")
    parser.add_argument("--generate-ids", action="store_true",
                       help="Generate random xml:id for textual elements")
    parser.add_argument("--segment-sentences", action="store_true",
                       help="Segment sentences with <s> elements")
    parser.add_argument("--check-server", action="store_true",
                       help="Only check if GROBID server is running")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = GrobidProcessor(server_url=args.server)
    
    # Check server status
    if args.check_server:
        processor.check_server_status()
        return
    
    if not processor.check_server_status():
        print("\n💡 To start GROBID server with Docker:")
        print("docker run --rm -it -p 8070:8070 lfoppiano/grobid:0.8.0")
        return
    
    # Process PDF
    try:
        processor.process_pdf(
            pdf_path=args.pdf_path,
            output_path=args.output,
            add_coordinates=not args.no_coordinates,
            consolidate_header=args.consolidate_header,
            consolidate_citations=args.consolidate_citations,
            generate_ids=args.generate_ids,
            segment_sentences=args.segment_sentences,
            n_workers=args.workers
        )
    except Exception as e:
        print(f"❌ Failed to process PDF: {e}")
        exit(1)


if __name__ == "__main__":
    main()
