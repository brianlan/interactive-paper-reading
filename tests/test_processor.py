"""
Tests for the simplified processor functionality.

This module contains tests for the simplified processor interface
that provides a streamlined API for paper processing.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from interactive_paper_reading.processor import AcademicPaperProcessor


class TestAcademicPaperProcessor:
    """Test cases for AcademicPaperProcessor."""

    @pytest.fixture
    def processor(self):
        """Create an AcademicPaperProcessor instance for testing."""
        with patch('interactive_paper_reading.processor.GrobidProcessor'):
            with patch('interactive_paper_reading.processor.TEIProcessor'):
                return AcademicPaperProcessor(grobid_server_url='http://localhost:8070')

    def test_processor_initialization(self, processor):
        """Test AcademicPaperProcessor initialization."""
        assert processor.grobid_processor is not None
        assert processor.tei_processor is not None

    def test_processor_initialization_custom_url(self):
        """Test processor initialization with custom GROBID URL."""
        with patch('interactive_paper_reading.processor.GrobidProcessor') as mock_grobid:
            with patch('interactive_paper_reading.processor.TEIProcessor'):
                AcademicPaperProcessor(grobid_server_url='http://custom:8070')
                mock_grobid.assert_called_once_with(server_url='http://custom:8070')

    def test_process_pdf_to_tei_server_down(self, processor):
        """Test PDF to TEI processing when server is down."""
        processor.grobid_processor.check_server_status.return_value = False
        
        result = processor.process_pdf_to_tei(Path('/test.pdf'), Path('/output'))
        
        assert result is None

    def test_process_pdf_to_tei_success_file_output(self, processor):
        """Test successful PDF to TEI processing with file output."""
        processor.grobid_processor.check_server_status.return_value = True
        
        # Mock GROBID processor to return a file path
        tei_file = Path('/output/test.tei.xml')
        processor.grobid_processor.process_pdf.return_value = tei_file
        
        with patch('pathlib.Path.is_file', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                result = processor.process_pdf_to_tei(Path('/test.pdf'), Path('/output'))
        
        assert result == tei_file

    def test_process_pdf_to_tei_success_directory_output(self, processor):
        """Test successful PDF to TEI processing with directory output."""
        processor.grobid_processor.check_server_status.return_value = True
        
        # Mock GROBID processor to return a directory
        output_dir = Path('/output')
        processor.grobid_processor.process_pdf.return_value = output_dir
        
        # Mock directory with TEI files
        tei_file = Path('/output/test.tei.xml')
        with patch('pathlib.Path.is_file', return_value=False):
            with patch('pathlib.Path.glob', return_value=[tei_file]):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    
                    result = processor.process_pdf_to_tei(Path('/test.pdf'), Path('/output'))
        
        assert result == tei_file

    def test_process_pdf_to_tei_no_output_generated(self, processor):
        """Test PDF to TEI processing when no output is generated."""
        processor.grobid_processor.check_server_status.return_value = True
        
        # Mock GROBID processor to return a directory with no TEI files
        output_dir = Path('/output')
        processor.grobid_processor.process_pdf.return_value = output_dir
        
        with patch('pathlib.Path.is_file', return_value=False):
            with patch('pathlib.Path.glob', return_value=[]):
                result = processor.process_pdf_to_tei(Path('/test.pdf'), Path('/output'))
        
        assert result is None

    def test_process_pdf_to_tei_exception(self, processor):
        """Test PDF to TEI processing with exception."""
        processor.grobid_processor.check_server_status.return_value = True
        processor.grobid_processor.process_pdf.side_effect = Exception("Processing error")
        
        result = processor.process_pdf_to_tei(Path('/test.pdf'), Path('/output'))
        
        assert result is None

    def test_process_tei_to_content_sections_only(self, processor):
        """Test TEI to content processing with sections only."""
        tei_file = Path('/test.tei.xml')
        
        # Mock TEI processor
        mock_sections = ['section1', 'section2']
        processor.tei_processor.extract_sections.return_value = mock_sections
        processor.tei_processor.extract_figures_tables.return_value = []
        processor.tei_processor.extract_graphics.return_value = []
        
        with patch('pathlib.Path.mkdir'):
            processor.process_tei_to_content(tei_file, None, Path('/output'))
        
        # Verify sections were processed
        processor.tei_processor.extract_sections.assert_called_once_with(tei_file)
        processor.tei_processor.save_sections_as_markdown.assert_called_once()

    def test_process_tei_to_content_with_figures(self, processor):
        """Test TEI to content processing with figures."""
        tei_file = Path('/test.tei.xml')
        pdf_file = Path('/test.pdf')
        
        # Mock TEI processor
        processor.tei_processor.extract_sections.return_value = []
        processor.tei_processor.extract_figures_tables.return_value = [
            type('MockFigure', (), {
                'caption': 'Test figure',
                'element_type': 'figure'
            })()
        ]
        processor.tei_processor.extract_graphics.return_value = []
        
        with patch('pathlib.Path.mkdir'):
            with patch('pathlib.Path.exists', return_value=True):
                processor.process_tei_to_content(tei_file, pdf_file, Path('/output'))
        
        # Verify figures were processed
        processor.tei_processor.extract_figures_tables.assert_called_once_with(tei_file)
        processor.tei_processor.crop_figure_from_pdf.assert_called_once()

    def test_process_tei_to_content_sections_extraction_error(self, processor):
        """Test TEI to content processing with sections extraction error."""
        tei_file = Path('/test.tei.xml')
        
        # Mock TEI processor to raise exception
        processor.tei_processor.extract_sections.side_effect = Exception("Extraction error")
        processor.tei_processor.extract_figures_tables.return_value = []
        processor.tei_processor.extract_graphics.return_value = []
        
        with patch('pathlib.Path.mkdir'):
            # Should not raise exception, just handle gracefully
            processor.process_tei_to_content(tei_file, None, Path('/output'))

    def test_process_complete_pipeline_success(self, processor):
        """Test complete pipeline execution."""
        # Mock successful PDF to TEI processing
        tei_file = Path('/output/test.tei.xml')
        with patch.object(processor, 'process_pdf_to_tei', return_value=tei_file) as mock_pdf_to_tei:
            with patch.object(processor, 'process_tei_to_content') as mock_tei_to_content:
                with patch('pathlib.Path.mkdir'):
                    processor.process_complete_pipeline(Path('/test.pdf'), Path('/output'))
        
        # Verify both steps were called
        mock_pdf_to_tei.assert_called_once()
        mock_tei_to_content.assert_called_once()

    def test_process_complete_pipeline_pdf_failure(self, processor):
        """Test complete pipeline when PDF processing fails."""
        # Mock failed PDF to TEI processing
        with patch.object(processor, 'process_pdf_to_tei', return_value=None):
            with patch.object(processor, 'process_tei_to_content') as mock_tei_content:
                with patch('pathlib.Path.mkdir'):
                    processor.process_complete_pipeline(Path('/test.pdf'), Path('/output'))
        
        # TEI content processing should not be called
        mock_tei_content.assert_not_called()

    def test_process_tei_only_default_output_dir(self, processor):
        """Test processing TEI file only with default output directory."""
        tei_file = Path('/some/path/test.tei.xml')
        
        with patch.object(processor, 'process_tei_to_content') as mock_process:
            processor.process_tei_only(tei_file)
        
        # Should use TEI file's parent directory as output
        mock_process.assert_called_once_with(
            tei_file, None, tei_file.parent
        )

    def test_process_tei_only_custom_output_dir(self, processor):
        """Test processing TEI file only with custom output directory."""
        tei_file = Path('/test.tei.xml')
        output_dir = Path('/custom/output')
        
        with patch('pathlib.Path.mkdir'):
            with patch.object(processor, 'process_tei_to_content') as mock_process:
                processor.process_tei_only(tei_file, output_dir=output_dir)
        
        mock_process.assert_called_once_with(
            tei_file, None, output_dir
        )

    def test_process_tei_only_with_pdf(self, processor):
        """Test processing TEI file with accompanying PDF."""
        tei_file = Path('/test.tei.xml')
        pdf_file = Path('/test.pdf')
        
        with patch.object(processor, 'process_tei_to_content') as mock_process:
            processor.process_tei_only(tei_file, pdf_path=pdf_file)
        
        mock_process.assert_called_once_with(
            tei_file, pdf_file, tei_file.parent
        )
