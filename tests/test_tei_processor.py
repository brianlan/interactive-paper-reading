"""
Tests for TEI XML processing functionality.

This module contains tests for extracting sections and figures from GROBID TEI XML files.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import xml.etree.ElementTree as ET

from scripts.tei_processor import TEIProcessor, Section, FigureTable, Graphic


class TestTEIProcessor:
    """Test cases for TEI XML processing."""

    @pytest.fixture
    def sample_tei_xml(self) -> str:
        """Sample TEI XML content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title level="a" type="main">Test Paper Title</title>
            </titleStmt>
        </fileDesc>
    </teiHeader>
    <facsimile>
        <surface n="1" ulx="0.0" uly="0.0" lrx="612.0" lry="792.0"/>
        <surface n="2" ulx="0.0" uly="0.0" lrx="612.0" lry="792.0"/>
    </facsimile>
    <text xml:lang="en">
        <body>
            <div xmlns="http://www.tei-c.org/ns/1.0">
                <head n="1">Introduction</head>
                <p>This is the introduction section.</p>
                <figure coords="1,100.0,200.0,300.0,150.0">
                    <head>Figure 1. Test figure</head>
                    <figDesc>Description of test figure</figDesc>
                    <graphic coords="1,120.0,220.0,260.0,110.0" type="bitmap" />
                </figure>
            </div>
            <div xmlns="http://www.tei-c.org/ns/1.0">
                <head n="2">Related Work</head>
                <p>This section discusses related work.</p>
                <div>
                    <head n="2.1">Subsection</head>
                    <p>This is a subsection.</p>
                </div>
            </div>
        </body>
    </text>
</TEI>'''

    @pytest.fixture
    def processor(self) -> TEIProcessor:
        """Create a TEI processor instance for testing."""
        return TEIProcessor()

    def test_processor_initialization(self, processor):
        """Test that TEIProcessor initializes correctly."""
        assert processor is not None
        assert hasattr(processor, 'extract_sections')
        assert hasattr(processor, 'extract_figures_tables')

    def test_extract_sections_returns_list(self, processor, sample_tei_xml):
        """Test that extract_sections returns a list of Section objects."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            sections = processor.extract_sections(Path('test.xml'))
            
        assert isinstance(sections, list)
        assert len(sections) >= 2  # At least Introduction and Related Work

    def test_section_structure(self, processor, sample_tei_xml):
        """Test that sections have correct structure."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            sections = processor.extract_sections(Path('test.xml'))
            
        # Check first section
        intro_section = sections[0]
        assert intro_section.number == "1"
        assert intro_section.title == "Introduction"
        assert "introduction section" in intro_section.content.lower()

    def test_extract_figures_tables_returns_list(self, processor, sample_tei_xml):
        """Test that extract_figures_tables returns a list of FigureTable objects."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            figures = processor.extract_figures_tables(Path('test.xml'))
            
        assert isinstance(figures, list)
        assert len(figures) >= 1

    def test_figure_coordinates_parsing(self, processor, sample_tei_xml):
        """Test that figure coordinates are parsed correctly."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            figures = processor.extract_figures_tables(Path('test.xml'))
            
        figure = figures[0]
        assert figure.page == 1
        assert figure.x == 100.0
        assert figure.y == 200.0
        assert figure.width == 300.0
        assert figure.height == 150.0

    def test_save_sections_as_markdown_creates_file(self, processor):
        """Test that save_sections_as_markdown creates a markdown file."""
        sections = [
            Section("1", "Introduction", "This is the introduction."),
            Section("2", "Methods", "This describes the methods.")
        ]
        
        with patch('builtins.open', mock_open()) as mock_file:
            processor.save_sections_as_markdown(sections, Path('output.md'))
            
        mock_file.assert_called_once_with(Path('output.md'), 'w', encoding='utf-8')

    def test_crop_figure_from_pdf_calls_correct_method(self, processor):
        """Test that crop_figure_from_pdf calls the correct cropping method."""
        figure = FigureTable(
            element_type="figure",
            caption="Test figure",
            page=1,
            x=100.0,
            y=200.0,
            width=300.0,
            height=150.0
        )
        
        with patch.object(processor, '_crop_pdf_region') as mock_crop:
            processor.crop_figure_from_pdf(
                figure, 
                Path('input.pdf'), 
                Path('output.png')
            )
            
        mock_crop.assert_called_once()

    def test_file_not_found_raises_exception(self, processor):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            processor.extract_sections(Path('non_existent.xml'))

    def test_extract_graphics_returns_list(self, processor, sample_tei_xml):
        """Test that extract_graphics returns a list of Graphic objects."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            graphics = processor.extract_graphics(Path('test.xml'))
            
        assert isinstance(graphics, list)
        if graphics:
            assert isinstance(graphics[0], Graphic)

    def test_graphic_structure(self, processor, sample_tei_xml):
        """Test the structure and properties of extracted graphics."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            graphics = processor.extract_graphics(Path('test.xml'))
            
        if graphics:
            graphic = graphics[0]
            assert isinstance(graphic.graphic_type, str)
            assert isinstance(graphic.page, int)
            assert isinstance(graphic.x, float)
            assert isinstance(graphic.y, float)
            assert isinstance(graphic.width, float)
            assert isinstance(graphic.height, float)
            assert isinstance(graphic.parent_figure_caption, str)
            
            # Test coordinates property
            coords = graphic.coordinates
            assert len(coords) == 4
            assert coords == (graphic.x, graphic.y, graphic.width, graphic.height)

    def test_crop_graphic_from_pdf_calls_correct_method(self, processor):
        """Test that crop_graphic_from_pdf calls the internal cropping method."""
        # Mock the internal cropping method
        with patch.object(processor, '_crop_pdf_region') as mock_crop:
            # Create a test graphic
            graphic = Graphic(
                graphic_type='bitmap',
                page=1,
                x=100.0,
                y=200.0,
                width=300.0,
                height=150.0,
                parent_figure_caption="Test caption"
            )
            
            pdf_path = Path("test.pdf")
            output_path = Path("output.png")
            
            # Call the method
            processor.crop_graphic_from_pdf(graphic, pdf_path, output_path)
            
            # Verify the internal method was called with correct parameters
            mock_crop.assert_called_once_with(
                pdf_path=pdf_path,
                page=1,
                coordinates=(100.0, 200.0, 300.0, 150.0),
                output_path=output_path
            )

class TestSection:
    """Test cases for Section data class."""

    def test_section_creation(self):
        """Test that Section objects can be created correctly."""
        section = Section("1.1", "Subsection Title", "Content here")
        
        assert section.number == "1.1"
        assert section.title == "Subsection Title"
        assert section.content == "Content here"

    def test_section_to_markdown(self):
        """Test that Section can be converted to markdown format."""
        section = Section("2", "Methods", "This describes the methodology.")
        markdown = section.to_markdown()
        
        assert markdown.startswith("## 2 Methods")
        assert "This describes the methodology." in markdown


class TestFigureTable:
    """Test cases for FigureTable data class."""

    def test_figure_creation(self):
        """Test that FigureTable objects can be created correctly."""
        figure = FigureTable(
            element_type="figure",
            caption="Figure 1. Test",
            page=2,
            x=50.0,
            y=100.0,
            width=200.0,
            height=150.0
        )
        
        assert figure.element_type == "figure"
        assert figure.caption == "Figure 1. Test"
        assert figure.page == 2
        assert figure.x == 50.0

    def test_coordinates_property(self):
        """Test that coordinates property returns correct bounding box."""
        figure = FigureTable(
            element_type="table",
            caption="Table 1",
            page=1,
            x=100.0,
            y=200.0,
            width=300.0,
            height=150.0
        )
        
        coords = figure.coordinates
        assert coords == (100.0, 200.0, 300.0, 150.0)
