#!/usr/bin/env python3
"""
Test script to verify the improved coordinate parsing that combines multiple bounding boxes.
"""

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from tei_processor import TEIProcessor


def test_coordinate_parsing():
    """Test the new coordinate parsing logic."""
    processor = TEIProcessor()
    
    # Test cases with multiple coordinate segments
    test_cases = [
        # Example from the user's observation
        "3,312.00,193.02,252.00,7.40;3,312.00,202.02,252.00,7.40;3,312.00,211.02,252.00,7.40;3,312.00,220.02,36.13,7.40",
        
        # Single coordinate (should work as before)
        "1,100.0,200.0,300.0,150.0",
        
        # Two segments
        "2,50.0,100.0,200.0,50.0;2,50.0,160.0,200.0,40.0",
        
        # Empty string
        "",
        
        # Invalid format
        "invalid,coords,string"
    ]
    
    print("Testing coordinate parsing with multiple segments...\n")
    
    for i, coords_str in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  Input: {coords_str}")
        
        result = processor._parse_coordinates(coords_str)
        
        if result:
            page, x, y, width, height = result
            print(f"  Output: page={page}, x={x:.2f}, y={y:.2f}, width={width:.2f}, height={height:.2f}")
            print(f"  Bounding box: ({x:.2f}, {y:.2f}) to ({x + width:.2f}, {y + height:.2f})")
        else:
            print("  Output: None (invalid coordinates)")
        
        print()
    
    # Specific test for the user's example
    print("=== DETAILED ANALYSIS OF USER'S EXAMPLE ===")
    user_coords = "3,312.00,193.02,252.00,7.40;3,312.00,202.02,252.00,7.40;3,312.00,211.02,252.00,7.40;3,312.00,220.02,36.13,7.40"
    result = processor._parse_coordinates(user_coords)
    
    if result:
        page, x, y, width, height = result
        print("Combined bounding box:")
        print(f"  Page: {page}")
        print(f"  Top-left: ({x:.2f}, {y:.2f})")
        print(f"  Bottom-right: ({x + width:.2f}, {y + height:.2f})")
        print(f"  Size: {width:.2f} x {height:.2f}")
        
        print("\nIndividual segments:")
        segments = user_coords.split(';')
        for i, segment in enumerate(segments, 1):
            parts = segment.split(',')
            if len(parts) >= 5:
                seg_x, seg_y, seg_w, seg_h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                print(f"  Segment {i}: ({seg_x:.2f}, {seg_y:.2f}) size {seg_w:.2f}x{seg_h:.2f}")
        
        print(f"\n→ The combined box now encompasses all {len(segments)} segments!")
    else:
        print("Failed to parse coordinates")


if __name__ == "__main__":
    test_coordinate_parsing()
