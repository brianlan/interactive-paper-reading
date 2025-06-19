"""Test for formula extraction from TEI files."""

import tempfile
from pathlib import Path
import pytest

from interactive_paper_reading.tei import TEIProcessor


class TestFormulaExtraction:
    """Test formula extraction functionality."""
    
    def test_formulas_included_in_markdown_output(self):
        """Test that formulas from TEI XML are included in the markdown output."""
        # Use the existing TEI file with formulas
        tei_file = Path("/Users/rlan/projects/interactive-paper-reading/papers/sparse4d-v3/Sparse4Dv3-2311.11722.grobid.tei.xml")
        
        if not tei_file.exists():
            pytest.skip("TEI file not found")
        
        processor = TEIProcessor()
        sections = processor.extract_sections(tei_file)
        
        # Create a temporary output file for markdown
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            # Save sections as markdown
            processor.save_sections_as_markdown(sections, output_path)
            
            # Read the generated markdown
            with open(output_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Check that specific formulas from the TEI file are included
            # These are formulas I found in the TEI XML
            assert "A gt = {(x, y, z, w, l, h, yaw, v xyz ) i | i ∈ Z N }" in markdown_content
            assert "C = exp(-∥[x, y, z] pred -[x, y, z] gt ∥ 2 )" in markdown_content
            assert "L = λ 1 CE(Y pred , Y ) + λ 2 Focal(C pred , C)" in markdown_content
            
        finally:
            # Clean up temporary file
            if output_path.exists():
                output_path.unlink()
    
    def test_formula_extraction_with_simple_xml(self):
        """Test formula extraction with a simple TEI XML example."""
        # Create a simple TEI XML with a formula
        tei_content = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <body>
            <div>
                <head n="1">Test Section</head>
                <p>This is a test paragraph with a formula: 
                <formula xml:id="formula_0">E = mc²</formula>
                and some more text.</p>
            </div>
        </body>
    </text>
</TEI>'''
        
        # Create a temporary TEI file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(tei_content)
            tei_file = Path(tmp_file.name)
        
        try:
            processor = TEIProcessor()
            sections = processor.extract_sections(tei_file)
            
            # Should have one section
            assert len(sections) == 1
            section = sections[0]
            
            # Check that the formula is included in the content
            assert "E = mc²" in section.content
            
        finally:
            # Clean up temporary file
            if tei_file.exists():
                tei_file.unlink()

    def test_standalone_formula_extraction(self):
        """Test that standalone formulas (direct children of div) are extracted."""
        tei_content = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <body>
            <div>
                <head n="2">Mathematical Section</head>
                <p>This section contains a standalone formula:</p>
                <formula xml:id="formula_1">F = ma</formula>
                <p>And some concluding text.</p>
            </div>
        </body>
    </text>
</TEI>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(tei_content)
            tei_file = Path(tmp_file.name)
        
        try:
            processor = TEIProcessor()
            sections = processor.extract_sections(tei_file)
            
            assert len(sections) == 1
            section = sections[0]
            
            # Check that the standalone formula is included
            assert "F = ma" in section.content
            # Check that surrounding paragraphs are also included
            assert "This section contains a standalone formula:" in section.content
            assert "And some concluding text." in section.content
            
        finally:
            if tei_file.exists():
                tei_file.unlink()

    def test_multiple_formulas_in_section(self):
        """Test that multiple formulas in the same section are all extracted."""
        tei_content = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <body>
            <div>
                <head n="3">Physics Laws</head>
                <p>First law: <formula xml:id="formula_1">F = ma</formula></p>
                <formula xml:id="formula_2">E = mc²</formula>
                <p>Third law involves: <formula xml:id="formula_3">P = mv</formula></p>
            </div>
        </body>
    </text>
</TEI>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(tei_content)
            tei_file = Path(tmp_file.name)
        
        try:
            processor = TEIProcessor()
            sections = processor.extract_sections(tei_file)
            
            assert len(sections) == 1
            section = sections[0]
            
            # Check that all three formulas are included
            assert "F = ma" in section.content
            assert "E = mc²" in section.content
            assert "P = mv" in section.content
            
        finally:
            if tei_file.exists():
                tei_file.unlink()

    def test_empty_formula_handling(self):
        """Test that empty formulas don't break the extraction."""
        tei_content = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <body>
            <div>
                <head n="4">Test Section</head>
                <p>Some text before.</p>
                <formula xml:id="formula_empty"></formula>
                <p>Some text after.</p>
            </div>
        </body>
    </text>
</TEI>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(tei_content)
            tei_file = Path(tmp_file.name)
        
        try:
            processor = TEIProcessor()
            sections = processor.extract_sections(tei_file)
            
            assert len(sections) == 1
            section = sections[0]
            
            # Check that text around empty formula is still included
            assert "Some text before." in section.content
            assert "Some text after." in section.content
            
        finally:
            if tei_file.exists():
                tei_file.unlink()

    def test_section_without_formulas(self):
        """Test that sections without formulas still work correctly."""
        tei_content = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <body>
            <div>
                <head n="5">Regular Section</head>
                <p>This is just a regular paragraph.</p>
                <p>And another paragraph without any formulas.</p>
            </div>
        </body>
    </text>
</TEI>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(tei_content)
            tei_file = Path(tmp_file.name)
        
        try:
            processor = TEIProcessor()
            sections = processor.extract_sections(tei_file)
            
            assert len(sections) == 1
            section = sections[0]
            
            # Check that regular content is still extracted
            assert "This is just a regular paragraph." in section.content
            assert "And another paragraph without any formulas." in section.content
            
        finally:
            if tei_file.exists():
                tei_file.unlink()
