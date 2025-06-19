#!/usr/bin/env python3
"""
End-to-end academic paper processing pipeline CLI.

This script provides a command-line interface for processing academic papers:
1. PDF → TEI XML using GROBID
2. TEI XML → Structured content (sections, figures, graphics)
3. Export sections as markdown
4. Crop and save figures/graphics as images

Usage:
    python process_academic_paper.py path/to/paper.pdf
    python process_academic_paper.py path/to/paper.pdf --output-dir custom/output
    python process_academic_paper.py --tei-only path/to/existing.tei.xml
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to Python path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_paper_reading.processor import AcademicPaperProcessor


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="End-to-end academic paper processing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete pipeline: PDF → TEI → Content
  python process_academic_paper.py paper.pdf
  
  # Custom output directory
  python process_academic_paper.py paper.pdf --output-dir custom/output
  
  # Process existing TEI file only
  python process_academic_paper.py --tei-only existing.tei.xml
  
  # Process TEI with specific PDF for cropping
  python process_academic_paper.py --tei-only existing.tei.xml --pdf paper.pdf
  
  # Custom GROBID server
  python process_academic_paper.py paper.pdf --grobid-server http://10.243.123.49:8070
        """
    )
    
    parser.add_argument("input", help="PDF file path or TEI file path (with --tei-only)")
    parser.add_argument("--output-dir", "-o", help="Output directory (default: same as input)")
    parser.add_argument("--tei-only", action="store_true", 
                       help="Process existing TEI file only (skip GROBID)")
    parser.add_argument("--pdf", help="PDF file path (for cropping when using --tei-only)")
    parser.add_argument("--grobid-server", default="http://localhost:8070",
                       help="GROBID server URL (default: http://localhost:8070)")
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1
    
    # Set default output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent / "processed_output"
    
    # Initialize processor
    processor = AcademicPaperProcessor(grobid_server_url=args.grobid_server)
    
    try:
        if args.tei_only:
            # Process existing TEI file
            processor.process_tei_only(input_path, args.pdf, output_dir)
        else:
            # Complete pipeline
            processor.process_complete_pipeline(input_path, output_dir)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
