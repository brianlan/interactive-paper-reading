#!/usr/bin/env python3
"""
End-to-end academic paper processing pipeline.

This script provides a complete workflow for processing academic papers:
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

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from grobid_processor import GrobidProcessor
from tei_processor import TEIProcessor


class AcademicPaperProcessor:
    """Complete academic paper processing pipeline."""
    
    def __init__(self, grobid_server_url="http://localhost:8070"):
        """Initialize the processor.
        
        Args:
            grobid_server_url: URL of the GROBID server
        """
        self.grobid_processor = GrobidProcessor(server_url=grobid_server_url)
        self.tei_processor = TEIProcessor()
    
    def process_pdf_to_tei(self, pdf_path, output_dir):
        """Process PDF to TEI XML using GROBID.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save TEI output
            
        Returns:
            Path to the generated TEI file, or None if failed
        """
        print(f"📄 Processing PDF: {pdf_path.name}")
        
        # Check server status
        if not self.grobid_processor.check_server_status():
            print("❌ Cannot connect to GROBID server")
            return None
        
        try:
            result_dir = self.grobid_processor.process_pdf(
                pdf_path=pdf_path,
                output_dir=output_dir,
                add_coordinates=True,  # Essential for figure cropping
                consolidate_header=True,  # Better metadata
                consolidate_citations=True,  # Better references
                generate_ids=True,  # Add XML IDs
                segment_sentences=True,  # Sentence boundaries
                n_workers=5  # Conservative number of workers
            )
            
            # Find the generated TEI file
            tei_files = list(result_dir.glob("*.tei.xml"))
            if tei_files:
                tei_file = tei_files[0]
                print(f"✅ TEI generated: {tei_file.name} ({tei_file.stat().st_size / 1024:.1f} KB)")
                return tei_file
            else:
                print("❌ No TEI file generated")
                return None
                
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            return None
    
    def process_tei_to_content(self, tei_file, pdf_file, output_dir):
        """Process TEI XML to extract structured content.
        
        Args:
            tei_file: Path to the TEI XML file
            pdf_file: Path to the original PDF file (for cropping)
            output_dir: Directory to save extracted content
        """
        print(f"🔍 Processing TEI: {tei_file.name}")
        
        # Create output subdirectories
        figures_dir = output_dir / "figures"
        graphics_dir = output_dir / "graphics"
        
        # Extract sections
        print("\n📝 Extracting sections...")
        try:
            sections = self.tei_processor.extract_sections(tei_file)
            print(f"Found {len(sections)} sections")
            
            # Save as markdown
            markdown_file = output_dir / f"{tei_file.stem.replace('.grobid', '')}_sections.md"
            self.tei_processor.save_sections_as_markdown(sections, markdown_file)
            print(f"✅ Sections saved: {markdown_file.name}")
            
        except Exception as e:
            print(f"❌ Error extracting sections: {e}")
        
        # Extract figures and tables
        print("\n🖼️  Extracting figures and tables...")
        try:
            figures_tables = self.tei_processor.extract_figures_tables(tei_file)
            print(f"Found {len(figures_tables)} figures/tables")
            
            if figures_tables and pdf_file and pdf_file.exists():
                figures_dir.mkdir(exist_ok=True)
                print("✂️  Cropping figures from PDF...")
                
                for i, fig_table in enumerate(figures_tables):
                    # Generate safe filename
                    safe_caption = "".join(c for c in fig_table.caption[:30] 
                                         if c.isalnum() or c in (' ', '-')).strip()
                    safe_caption = safe_caption.replace(' ', '_')
                    if not safe_caption:
                        safe_caption = f"{fig_table.element_type}_{i+1}"
                    
                    output_file = figures_dir / f"{fig_table.element_type}_{i+1}_{safe_caption}.png"
                    
                    try:
                        self.tei_processor.crop_figure_from_pdf(fig_table, pdf_file, output_file)
                        print(f"  ✅ {output_file.name}")
                    except Exception as e:
                        print(f"  ❌ Failed to crop {fig_table.element_type} {i+1}: {e}")
            
        except Exception as e:
            print(f"❌ Error extracting figures/tables: {e}")
        
        # Extract graphics
        print("\n🎨 Extracting graphics...")
        try:
            graphics = self.tei_processor.extract_graphics(tei_file)
            print(f"Found {len(graphics)} graphics")
            
            if graphics and pdf_file and pdf_file.exists():
                graphics_dir.mkdir(exist_ok=True)
                print("✂️  Cropping graphics from PDF...")
                
                for i, graphic in enumerate(graphics):
                    # Generate safe filename
                    safe_caption = "".join(c for c in graphic.parent_figure_caption[:30] 
                                         if c.isalnum() or c in (' ', '-')).strip()
                    safe_caption = safe_caption.replace(' ', '_')
                    if not safe_caption:
                        safe_caption = f"graphic_{i+1}"
                    
                    output_file = graphics_dir / f"graphic_{i+1}_{safe_caption}.png"
                    
                    try:
                        self.tei_processor.crop_graphic_from_pdf(graphic, pdf_file, output_file)
                        print(f"  ✅ {output_file.name}")
                    except Exception as e:
                        print(f"  ❌ Failed to crop graphic {i+1}: {e}")
            
        except Exception as e:
            print(f"❌ Error extracting graphics: {e}")
    
    def process_complete_pipeline(self, pdf_path, output_dir):
        """Run the complete PDF → TEI → Content pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save all outputs
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 Starting complete academic paper processing pipeline")
        print(f"📄 Input PDF: {pdf_path}")
        print(f"📁 Output directory: {output_dir}")
        print("=" * 60)
        
        # Step 1: PDF → TEI
        tei_file = self.process_pdf_to_tei(pdf_path, output_dir)
        if not tei_file:
            print("❌ Pipeline failed at PDF → TEI step")
            return
        
        # Step 2: TEI → Content
        self.process_tei_to_content(tei_file, pdf_path, output_dir)
        
        print("\n🎉 Pipeline complete!")
        print(f"📁 All outputs saved to: {output_dir}")
    
    def process_tei_only(self, tei_path, pdf_path=None, output_dir=None):
        """Process existing TEI file to extract content.
        
        Args:
            tei_path: Path to the TEI XML file
            pdf_path: Optional path to PDF file for cropping
            output_dir: Directory to save outputs (defaults to TEI file's directory)
        """
        tei_path = Path(tei_path)
        if output_dir is None:
            output_dir = tei_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_file = Path(pdf_path) if pdf_path else None
        
        print("🔍 Processing existing TEI file")
        print(f"📄 TEI file: {tei_path}")
        if pdf_file:
            print(f"📖 PDF file: {pdf_file}")
        print(f"📁 Output directory: {output_dir}")
        print("=" * 60)
        
        self.process_tei_to_content(tei_path, pdf_file, output_dir)
        
        print("\n🎉 TEI processing complete!")
        print(f"📁 All outputs saved to: {output_dir}")


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
