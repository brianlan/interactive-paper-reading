#!/usr/bin/env python3
"""
Process TEI output from GROBID to extract sections and figures.

This script demonstrates how to use the TEIProcessor to:
1. Extract document sections and save as markdown
2. Extract figures/tables and crop them from the original PDF
"""

from pathlib import Path
import sys

# Add parent directory to Python path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_paper_reading.tei import TEIProcessor


def main():
    """Process the DN-DETR TEI file and extract content."""
    
    # Paths
    project_root = Path(__file__).parent.parent
    tei_file = project_root / "papers" / "processed_output" / "DN-DETR-2203.01305v3.grobid.tei.xml"
    pdf_file = project_root / "papers" / "input_pdfs" / "DN-DETR-2203.01305v3.pdf"
    
    # Output directories
    output_dir = project_root / "papers" / "processed_output"
    markdown_file = output_dir / "DN-DETR-sections.md"
    figures_dir = output_dir / "figures"
    
    # Check if files exist
    if not tei_file.exists():
        print(f"❌ TEI file not found: {tei_file}")
        return
    
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_file}")
        return
    
    print(f"📄 Processing TEI file: {tei_file.name}")
    print(f"📖 Source PDF: {pdf_file.name}")
    
    # Initialize processor
    processor = TEIProcessor()
    
    # Extract sections
    print("\n🔍 Extracting sections...")
    try:
        sections = processor.extract_sections(tei_file)
        print(f"Found {len(sections)} sections:")
        
        for section in sections:
            content_preview = section.content[:100] + "..." if len(section.content) > 100 else section.content
            print(f"  - {section.number} {section.title}")
            print(f"    Content: {content_preview}")
        
        # Save as markdown
        processor.save_sections_as_markdown(sections, markdown_file)
        print(f"✅ Sections saved to: {markdown_file}")
        
    except Exception as e:
        print(f"❌ Error extracting sections: {e}")
        return
    
    # Extract figures and tables
    print("\n🖼️  Extracting figures and tables...")
    try:
        figures_tables = processor.extract_figures_tables(tei_file)
        print(f"Found {len(figures_tables)} figures/tables:")
        
        for i, fig_table in enumerate(figures_tables):
            print(f"  - {fig_table.element_type.title()} {i+1}: {fig_table.caption[:50]}...")
            print(f"    Page {fig_table.page}, coords: ({fig_table.x:.1f}, {fig_table.y:.1f}, {fig_table.width:.1f}, {fig_table.height:.1f})")
        
        # Crop figures from PDF
        if figures_tables:
            figures_dir.mkdir(exist_ok=True)
            print("\n✂️  Cropping figures from PDF...")
            
            for i, fig_table in enumerate(figures_tables):
                # Generate output filename
                safe_caption = "".join(c for c in fig_table.caption[:30] if c.isalnum() or c in (' ', '-')).strip()
                safe_caption = safe_caption.replace(' ', '_')
                if not safe_caption:
                    safe_caption = f"{fig_table.element_type}_{i+1}"
                
                output_file = figures_dir / f"{fig_table.element_type}_{i+1}_{safe_caption}.png"
                
                try:
                    processor.crop_figure_from_pdf(fig_table, pdf_file, output_file)
                    print(f"  ✅ Saved: {output_file.name}")
                except Exception as e:
                    print(f"  ❌ Failed to crop {fig_table.element_type} {i+1}: {e}")
        
    except Exception as e:
        print(f"❌ Error extracting figures/tables: {e}")
        return
    
    # Extract graphics
    print("\n🎨 Extracting graphics...")
    try:
        graphics = processor.extract_graphics(tei_file)
        print(f"Found {len(graphics)} graphics:")
        
        for i, graphic in enumerate(graphics):
            caption_preview = graphic.parent_figure_caption[:50] + "..." if len(graphic.parent_figure_caption) > 50 else graphic.parent_figure_caption
            print(f"  - Graphic {i+1} ({graphic.graphic_type}): {caption_preview}")
            print(f"    Page {graphic.page}, coords: ({graphic.x:.1f}, {graphic.y:.1f}, {graphic.width:.1f}, {graphic.height:.1f})")
        
        # Crop graphics from PDF
        if graphics:
            graphics_dir = output_dir / "graphics"
            graphics_dir.mkdir(exist_ok=True)
            print("\n✂️  Cropping graphics from PDF...")
            
            for i, graphic in enumerate(graphics):
                # Generate output filename
                safe_caption = "".join(c for c in graphic.parent_figure_caption[:30] if c.isalnum() or c in (' ', '-')).strip()
                safe_caption = safe_caption.replace(' ', '_')
                if not safe_caption:
                    safe_caption = f"graphic_{i+1}"
                
                output_file = graphics_dir / f"graphic_{i+1}_{safe_caption}.png"
                
                try:
                    processor.crop_graphic_from_pdf(graphic, pdf_file, output_file)
                    print(f"  ✅ Saved: {output_file.name}")
                except Exception as e:
                    print(f"  ❌ Failed to crop graphic {i+1}: {e}")
        
    except Exception as e:
        print(f"❌ Error extracting graphics: {e}")
        return

    print("\n🎉 Processing complete!")
    print(f"📝 Markdown: {markdown_file}")
    if figures_tables:
        print(f"🖼️  Figures: {figures_dir}")
    if graphics:
        print(f"🎨 Graphics: {graphics_dir}")


if __name__ == "__main__":
    main()
