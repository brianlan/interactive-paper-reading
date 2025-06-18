#!/usr/bin/env python3
"""
Test script for graphics extraction from TEI XML.
"""

from pathlib import Path
from tei_processor import TEIProcessor

def main():
    # Path to the TEI XML file
    tei_file = Path("../papers/processed_output/DN-DETR-2203.01305v3.grobid.tei.xml")
    pdf_file = Path("/Users/rlan/work/papers/ObjectDetection/DN-DETR-2203.01305v3.pdf")
    
    # Initialize processor
    processor = TEIProcessor()
    
    print("Extracting graphics from TEI XML...")
    
    try:
        # Extract graphics
        graphics = processor.extract_graphics(tei_file)
        
        print(f"Found {len(graphics)} graphics:")
        
        for i, graphic in enumerate(graphics, 1):
            print(f"\nGraphic {i}:")
            print(f"  Type: {graphic.graphic_type}")
            print(f"  Page: {graphic.page}")
            print(f"  Coordinates: {graphic.coordinates}")
            print(f"  Parent caption: {graphic.parent_figure_caption[:100]}...")
            
            # Create output filename
            output_dir = Path("../papers/processed_output/graphics")
            output_dir.mkdir(exist_ok=True)
            
            # Clean caption for filename
            clean_caption = "".join(c for c in graphic.parent_figure_caption[:50] if c.isalnum() or c in (' ', '_', '-')).strip()
            clean_caption = clean_caption.replace(' ', '_')
            
            if not clean_caption:
                clean_caption = f"graphic_{i}"
            
            output_file = output_dir / f"graphic_{i}_{clean_caption}.png"
            
            print(f"  Saving to: {output_file}")
            
            # Crop and save the graphic
            if pdf_file.exists():
                try:
                    processor.crop_graphic_from_pdf(graphic, pdf_file, output_file)
                    print(f"  ✓ Successfully saved graphic to {output_file}")
                except Exception as e:
                    print(f"  ✗ Failed to crop graphic: {e}")
            else:
                print(f"  ✗ PDF file not found: {pdf_file}")
        
    except Exception as e:
        print(f"Error extracting graphics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
