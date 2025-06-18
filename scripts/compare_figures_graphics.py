#!/usr/bin/env python3
"""
Compare figures vs graphics extraction.

This script shows the difference between:
1. Figures - the entire figure elements with captions
2. Graphics - the specific graphic elements within figures
"""

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from tei_processor import TEIProcessor


def main():
    # Path to the TEI XML file
    project_root = Path(__file__).parent.parent
    tei_file = project_root / "papers" / "processed_output" / "DN-DETR-2203.01305v3.grobid.tei.xml"
    
    # Initialize processor
    processor = TEIProcessor()
    
    print("=== COMPARISON: FIGURES vs GRAPHICS ===\n")
    
    # Extract figures
    print("📊 FIGURES (complete figure elements):")
    figures = processor.extract_figures_tables(tei_file)
    
    for i, figure in enumerate(figures[:8], 1):  # Show first 8 for brevity
        if figure.element_type == 'figure':
            print(f"  Figure {i}:")
            print(f"    Caption: {figure.caption}")
            print(f"    Page: {figure.page}")
            print(f"    Coordinates: ({figure.x:.1f}, {figure.y:.1f}, {figure.width:.1f}, {figure.height:.1f})")
            print()
    
    print("🎨 GRAPHICS (specific graphic elements within figures):")
    graphics = processor.extract_graphics(tei_file)
    
    for i, graphic in enumerate(graphics, 1):
        print(f"  Graphic {i}:")
        print(f"    Type: {graphic.graphic_type}")
        print(f"    Parent Caption: {graphic.parent_figure_caption}")
        print(f"    Page: {graphic.page}")
        print(f"    Coordinates: ({graphic.x:.1f}, {graphic.y:.1f}, {graphic.width:.1f}, {graphic.height:.1f})")
        print()
    
    print("=== KEY DIFFERENCES ===")
    print("📊 Figures: Extract the entire figure element including all text and captions")
    print("🎨 Graphics: Extract only the precise graphic/image content within figures")
    print("              - Usually have more precise bounding boxes")
    print("              - Focus on the actual visual content")
    print("              - May have different coordinates than their parent figures")
    
    print(f"\nFound {len([f for f in figures if f.element_type == 'figure'])} figures total")
    print(f"Found {len(graphics)} graphics total")
    
    # Show coordinate comparison for first graphic
    if graphics and figures:
        print("\n=== COORDINATE COMPARISON EXAMPLE ===")
        graphic1 = graphics[0]
        
        # Find corresponding figure
        figure1 = None
        for fig in figures:
            if (fig.element_type == 'figure' and 
                fig.page == graphic1.page and 
                graphic1.parent_figure_caption in fig.caption):
                figure1 = fig
                break
        
        if figure1:
            print(f"Figure 1 coordinates: ({figure1.x:.1f}, {figure1.y:.1f}, {figure1.width:.1f}, {figure1.height:.1f})")
            print(f"Graphic 1 coordinates: ({graphic1.x:.1f}, {graphic1.y:.1f}, {graphic1.width:.1f}, {graphic1.height:.1f})")
            print("→ The graphic coordinates are typically more precise to the actual image content")


if __name__ == "__main__":
    main()
