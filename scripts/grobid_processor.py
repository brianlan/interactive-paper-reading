#!/usr/bin/env python3
"""
GROBID PDF Processor

This script processes PDF files using GROBID to extract structured text in TEI format
with PDF coordinates included.

Requirements:
- TEI output format
- Process fulltext document
- Add coordinates
"""

import argparse
import json
from pathlib import Path
from grobid_client.grobid_client import GrobidClient


class GrobidProcessor:
    def __init__(self, config_path=None, server_url="http://localhost:8070"):
        """
        Initialize GROBID processor
        
        Args:
            config_path: Path to GROBID config file
            server_url: GROBID server URL
        """
        if config_path is None:
            # Create default config
            self.config = {
                "grobid_server": server_url,
                "batch_size": 1000,
                "sleep_time": 10,  # Increased wait time
                "timeout": 120,   # Increased timeout to 2 minutes
                "coordinates": ["persName", "figure", "ref", "biblStruct", "formula", "s"]
            }
            config_path = self._create_temp_config()
        
        self.client = GrobidClient(config_path=config_path)
        self.config_path = config_path
    
    def _create_temp_config(self):
        """Create temporary config file"""
        config_path = "/tmp/grobid_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        return config_path
    
    def process_pdf(self, pdf_path, output_dir=None, add_coordinates=True, 
                   consolidate_header=False, consolidate_citations=False,
                   generate_ids=False, segment_sentences=False, n_workers=10):
        """
        Process a single PDF or directory of PDFs with GROBID
        
        Args:
            pdf_path: Path to PDF file or directory containing PDFs
            output_dir: Output directory for TEI files (optional)
            add_coordinates: Add PDF coordinates to TEI output
            consolidate_header: Consolidate header metadata
            consolidate_citations: Consolidate bibliographical references
            generate_ids: Generate random xml:id for textual elements
            segment_sentences: Segment sentences with <s> elements
            n_workers: Number of concurrent workers
        """
        
        # Validate inputs
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF path does not exist: {pdf_path}")
        
        # Set output directory
        if output_dir is None:
            if pdf_path.is_file():
                output_dir = pdf_path.parent / "grobid_output"
            else:
                output_dir = pdf_path / "grobid_output"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        print(f"Processing PDF(s): {pdf_path}")
        print(f"Output directory: {output_dir}")
        print(f"GROBID server: {self.config['grobid_server']}")
        print(f"Add coordinates: {add_coordinates}")
        print(f"Workers: {n_workers}")
        
        try:
            # Process with GROBID client
            # The client's process method handles the service type and parameters
            self.client.process(
                service="processFulltextDocument",
                input_path=str(pdf_path),
                output=str(output_dir),
                n=n_workers,
                tei_coordinates=add_coordinates,
                consolidate_header=consolidate_header,
                consolidate_citations=consolidate_citations,
                generateIDs=generate_ids,
                segment_sentences=segment_sentences,
                verbose=True
            )
            
            print("✅ Processing completed successfully!")
            print(f"TEI files saved to: {output_dir}")
            
            # List generated files
            tei_files = list(output_dir.glob("*.tei.xml"))
            if tei_files:
                print(f"\nGenerated {len(tei_files)} TEI file(s):")
                for tei_file in tei_files[:5]:  # Show first 5
                    print(f"  - {tei_file.name}")
                if len(tei_files) > 5:
                    print(f"  ... and {len(tei_files) - 5} more")
            
            return output_dir
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            raise
    
    def check_server_status(self):
        """Check if GROBID server is running"""
        try:
            import requests
            response = requests.get(f"{self.config['grobid_server']}/api/isalive")
            if response.status_code == 200:
                print(f"✅ GROBID server is running at {self.config['grobid_server']}")
                return True
            else:
                print(f"❌ GROBID server responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to GROBID server: {e}")
            print(f"Please ensure GROBID is running at {self.config['grobid_server']}")
            print("You can start GROBID with Docker: docker run --rm -it -p 8070:8070 lfoppiano/grobid:0.8.0")
            return False


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
            output_dir=args.output,
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
