"""
Academic Paper Processor - A simplified wrapper around the pipeline for basic processing.

This module provides the AcademicPaperProcessor class which is a simpler interface
for the comprehensive pipeline, focused on PDF-to-content extraction.
"""

from pathlib import Path
from typing import Optional

from .grobid import GrobidProcessor
from .tei import TEIProcessor


class AcademicPaperProcessor:
    """Complete academic paper processing pipeline."""
    
    def __init__(self, grobid_server_url="http://localhost:8070"):
        """Initialize the processor.
        
        Args:
            grobid_server_url: URL of the GROBID server
        """
        self.grobid_processor = GrobidProcessor(server_url=grobid_server_url)
        self.tei_processor = TEIProcessor()
    
    def process_pdf_to_tei(self, pdf_path: Path, output_dir: Path) -> Optional[Path]:
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
            tei_output = self.grobid_processor.process_pdf(
                pdf_path=pdf_path,
                output_path=output_dir,
                add_coordinates=True,  # Essential for figure cropping
                consolidate_header=True,  # Better metadata
                consolidate_citations=True,  # Better references
                generate_ids=True,  # Add XML IDs
                segment_sentences=True,  # Sentence boundaries
                n_workers=5  # Conservative number of workers
            )
            
            # Find the generated TEI file
            if tei_output.is_file():
                tei_file = tei_output
            else:
                tei_files = list(tei_output.glob("*.tei.xml"))
                if tei_files:
                    tei_file = tei_files[0]
                else:
                    print("❌ No TEI file generated")
                    return None
            
            print(f"✅ TEI generated: {tei_file.name} ({tei_file.stat().st_size / 1024:.1f} KB)")
            return tei_file
                
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            return None
    
    def process_tei_to_content(self, tei_file: Path, pdf_file: Optional[Path], output_dir: Path):
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
    
    def process_complete_pipeline(self, pdf_path: Path, output_dir: Path):
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
    
    def process_tei_only(self, tei_path: Path, pdf_path: Optional[Path] = None, output_dir: Optional[Path] = None):
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
