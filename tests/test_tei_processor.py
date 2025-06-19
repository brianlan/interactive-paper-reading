"""
Tests for TEI XML processing functionality.

This module contains tests for extracting sections and figures from GROBID TEI XML files.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import xml.etree.ElementTree as ET

from interactive_paper_reading.tei import TEIProcessor, Section, FigureTable, Graphic


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
    def empty_sections_xml(self) -> str:
        """XML with empty sections to test edge cases."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text xml:lang="en">
        <body>
            <div xmlns="http://www.tei-c.org/ns/1.0">
                <head>No Number</head>
                <p></p>
            </div>
            <div xmlns="http://www.tei-c.org/ns/1.0">
                <p>Content without head</p>
            </div>
        </body>
    </text>
</TEI>'''

    @pytest.fixture
    def multi_segment_coords_xml(self) -> str:
        """XML with multi-segment coordinates to test coordinate combining."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text xml:lang="en">
        <body>
            <div xmlns="http://www.tei-c.org/ns/1.0">
                <head n="1">Test Section</head>
                <p>Content</p>
                <figure coords="1,100.0,200.0,50.0,25.0;1,120.0,230.0,30.0,15.0">
                    <head>Multi-segment Figure</head>
                </figure>
                <table coords="2,50.0,100.0,200.0,50.0">
                    <head>Test Table</head>
                </table>
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

    # NEW TESTS TO IMPROVE COVERAGE
    
    def test_empty_sections_handling(self, processor, empty_sections_xml):
        """Test handling of empty or malformed sections."""
        with patch('builtins.open', mock_open(read_data=empty_sections_xml)):
            sections = processor.extract_sections(Path('test.xml'))
            
        # Should handle empty sections gracefully
        assert isinstance(sections, list)
        # May have fewer sections due to filtering out invalid ones

    def test_extract_section_from_div_edge_cases(self, processor):
        """Test _extract_section_from_div with various edge cases."""
        # Test div without head element
        div_no_head = ET.Element('div')
        result = processor._extract_section_from_div(div_no_head)
        assert result is None

        # Test div with head but no number
        div_with_head = ET.Element('div')
        head = ET.SubElement(div_with_head, 'head')
        head.text = "Title Only"
        result = processor._extract_section_from_div(div_with_head)
        assert result is None

        # Test section with only number, no title
        div_number_only = ET.Element('div')
        head = ET.SubElement(div_number_only, 'head')
        head.set('n', '1')
        head.text = '1'  # Only number, no title
        result = processor._extract_section_from_div(div_number_only)
        assert result is None

    def test_multi_segment_coordinate_parsing(self, processor, multi_segment_coords_xml):
        """Test parsing of multi-segment coordinates."""
        with patch('builtins.open', mock_open(read_data=multi_segment_coords_xml)):
            figures = processor.extract_figures_tables(Path('test.xml'))
            
        # Should have at least one figure with combined coordinates
        assert len(figures) >= 1
        
        # The multi-segment figure should have combined bounding box
        multi_segment_figure = figures[0]
        assert multi_segment_figure.page == 1
        # Should encompass all segments: (100,200,50,25) and (120,230,30,15)
        # Expected combined: x=100, y=200, width=50, height=45
        assert multi_segment_figure.x == 100.0
        assert multi_segment_figure.y == 200.0

    def test_parse_coordinates_edge_cases(self, processor):
        """Test _parse_coordinates with various edge cases."""
        # Test empty string
        assert processor._parse_coordinates("") is None
        
        # Test invalid format
        assert processor._parse_coordinates("invalid") is None
        
        # Test insufficient parts
        assert processor._parse_coordinates("1,2,3") is None
        
        # Test non-numeric values
        assert processor._parse_coordinates("abc,def,ghi,jkl,mno") is None
        
        # Test mixed valid/invalid segments
        result = processor._parse_coordinates("1,100,200,50,25;invalid;2,150,250,30,15")
        assert result is not None
        assert result[0] == 1  # Should use first valid page
        
        # Test segments on different pages (should skip different page)
        result = processor._parse_coordinates("1,100,200,50,25;2,150,250,30,15")
        assert result is not None
        assert result[0] == 1  # Should only use page 1

    def test_extract_figure_table_no_coordinates(self, processor):
        """Test figure/table extraction when coordinates are missing."""
        element = ET.Element('figure')
        head = ET.SubElement(element, 'head')
        head.text = "Figure without coords"
        
        result = processor._extract_figure_table_from_element(element, 'figure')
        assert result is None

    def test_extract_figure_table_invalid_coordinates(self, processor):
        """Test figure/table extraction with invalid coordinates."""
        element = ET.Element('figure')
        element.set('coords', 'invalid,coords')
        head = ET.SubElement(element, 'head')
        head.text = "Figure with invalid coords"
        
        result = processor._extract_figure_table_from_element(element, 'figure')
        assert result is None

    def test_extract_graphic_no_coordinates(self, processor):
        """Test graphic extraction when coordinates are missing."""
        element = ET.Element('graphic')
        element.set('type', 'bitmap')
        
        result = processor._extract_graphic_from_element(element, "Test caption")
        assert result is None

    def test_crop_pdf_region_import_error(self, processor):
        """Test _crop_pdf_region when PyMuPDF is not available."""
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(ImportError, match="PyMuPDF is required"):
                processor._crop_pdf_region(
                    Path("test.pdf"), 
                    1, 
                    (100, 200, 300, 150), 
                    Path("output.png")
                )

    def test_crop_pdf_region_file_not_found(self, processor):
        """Test _crop_pdf_region when PDF file doesn't exist."""
        with patch('fitz.open', side_effect=Exception("File not found")):
            # Mock Path.exists to return False
            with patch.object(Path, 'exists', return_value=False):
                with pytest.raises(FileNotFoundError, match="PDF file not found"):
                    processor._crop_pdf_region(
                        Path("nonexistent.pdf"), 
                        1, 
                        (100, 200, 300, 150), 
                        Path("output.png")
                    )

    def test_crop_pdf_region_success(self, processor):
        """Test successful PDF region cropping."""
        # Mock fitz components
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pix = MagicMock()
        
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_page.get_pixmap.return_value = mock_pix
        
        with patch('fitz.open', return_value=mock_doc):
            with patch('fitz.Rect'):
                with patch('fitz.Matrix'):
                    with patch.object(Path, 'exists', return_value=True):
                        with patch.object(Path, 'mkdir'):
                            processor._crop_pdf_region(
                                Path("test.pdf"), 
                                1, 
                                (100, 200, 300, 150), 
                                Path("output.png")
                            )
        
        # Verify the mocks were called correctly
        mock_doc.close.assert_called_once()
        mock_page.get_pixmap.assert_called_once()
        mock_pix.save.assert_called_once()

    def test_get_element_text_nested_elements(self, processor):
        """Test _get_element_text with nested elements and tail text."""
        # Create complex nested structure
        root = ET.Element('root')
        root.text = "Root text "
        
        child1 = ET.SubElement(root, 'child1')
        child1.text = "Child1 text "
        child1.tail = " child1 tail "
        
        child2 = ET.SubElement(child1, 'child2')
        child2.text = "Child2 text"
        child2.tail = " child2 tail"
        
        result = processor._get_element_text(root)
        assert "Root text" in result
        assert "Child1 text" in result
        assert "Child2 text" in result
        assert "child1 tail" in result
        assert "child2 tail" in result

    def test_get_element_text_empty_element(self, processor):
        """Test _get_element_text with empty elements."""
        empty_element = ET.Element('empty')
        result = processor._get_element_text(empty_element)
        assert result == ""

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

    def test_section_to_markdown_nested_levels(self):
        """Test markdown generation for different nesting levels."""
        # Top level section
        section1 = Section("1", "Introduction", "Content")
        markdown1 = section1.to_markdown()
        assert markdown1.startswith("## 1 Introduction")
        
        # Nested section
        section2 = Section("1.1", "Subsection", "Content")  
        markdown2 = section2.to_markdown()
        assert markdown2.startswith("### 1.1 Subsection")
        
        # Deep nested section
        section3 = Section("1.1.1", "Subsubsection", "Content")
        markdown3 = section3.to_markdown()
        assert markdown3.startswith("#### 1.1.1 Subsubsection")


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


class TestGraphic:
    """Test cases for Graphic data class."""

    def test_graphic_creation(self):
        """Test that Graphic objects can be created correctly."""
        graphic = Graphic(
            graphic_type="bitmap",
            page=1,
            x=10.0,
            y=20.0,
            width=100.0,
            height=80.0,
            parent_figure_caption="Test Figure"
        )
        
        assert graphic.graphic_type == "bitmap"
        assert graphic.page == 1
        assert graphic.x == 10.0
        assert graphic.parent_figure_caption == "Test Figure"

    def test_graphic_coordinates_property(self):
        """Test that Graphic coordinates property works correctly."""
        graphic = Graphic(
            graphic_type="vector",
            page=2,
            x=50.0,
            y=75.0,
            width=200.0,
            height=125.0
        )
        
        coords = graphic.coordinates
        assert coords == (50.0, 75.0, 200.0, 125.0)

    def test_graphic_default_caption(self):
        """Test that Graphic uses default empty caption when not provided."""
        graphic = Graphic(
            graphic_type="bitmap",
            page=1,
            x=0.0,
            y=0.0,
            width=100.0,
            height=100.0
        )
        
        assert graphic.parent_figure_caption == ""
