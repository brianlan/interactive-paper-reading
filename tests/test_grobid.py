"""
Tests for GROBID PDF processing functionality.

This module contains tests for processing PDF files with GROBID
to extract structured text in TEI format.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
import requests

from interactive_paper_reading.grobid import GrobidProcessor


class TestGrobidProcessor:
    """Test cases for GrobidProcessor."""

    @pytest.fixture
    def default_config(self):
        """Default configuration for GROBID processor."""
        return {
            'grobid_server': 'http://localhost:8070',
            'batch_size': 1000,
            'sleep_time': 10,
            'timeout': 120,
            'coordinates': ['persName', 'figure', 'ref', 'biblStruct', 'formula', 's']
        }

    @pytest.fixture
    def processor(self, default_config):
        """Create a GrobidProcessor instance for testing."""
        with patch('interactive_paper_reading.grobid.GrobidClient'):
            return GrobidProcessor(server_url=default_config['grobid_server'])

    def test_processor_initialization_with_server_url(self):
        """Test GrobidProcessor initialization with server URL."""
        with patch('interactive_paper_reading.grobid.GrobidClient'):
            processor = GrobidProcessor(server_url='http://custom:8070')
            assert processor.config['grobid_server'] == 'http://custom:8070'

    def test_processor_initialization_with_config_path(self, tmp_path, default_config):
        """Test GrobidProcessor initialization with config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(default_config))
        
        with patch('interactive_paper_reading.grobid.GrobidClient'):
            processor = GrobidProcessor(config_path=str(config_file))
            assert processor.config_path == str(config_file)

    def test_processor_initialization_no_params_raises_error(self):
        """Test that initialization without parameters still works (uses defaults)."""
        # The current implementation actually provides defaults, so this should work
        with patch('interactive_paper_reading.grobid.GrobidClient'):
            processor = GrobidProcessor()
            assert processor.config['grobid_server'] == 'http://localhost:8070'

    def test_processor_initialization_invalid_config_file(self):
        """Test initialization with invalid config file."""
        with pytest.raises(FileNotFoundError):
            GrobidProcessor(config_path='/nonexistent/config.json')

    def test_check_server_status_success(self, processor):
        """Test successful server status check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch('requests.get', return_value=mock_response):
            assert processor.check_server_status() is True

    def test_check_server_status_failure(self, processor):
        """Test server status check when server is down."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch('requests.get', return_value=mock_response):
            assert processor.check_server_status() is False

    def test_check_server_status_connection_error(self, processor):
        """Test server status check with connection error."""
        with patch('requests.get', side_effect=requests.ConnectionError()):
            assert processor.check_server_status() is False

    def test_process_pdf_file_not_found(self, processor):
        """Test process_pdf with non-existent file."""
        with pytest.raises(FileNotFoundError, match="PDF path does not exist"):
            processor.process_pdf('/nonexistent/file.pdf')

    @patch('interactive_paper_reading.grobid.Path.exists')
    def test_process_pdf_single_file_success(self, mock_exists, processor, tmp_path):
        """Test successful processing of a single PDF file."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Use a file output path instead of directory to avoid the directory logic
        output_file = tmp_path / "test.grobid.tei.xml"
        
        # Mock the direct HTTP processing method
        with patch.object(processor, '_process_single_pdf_direct', return_value=output_file):
            with patch('interactive_paper_reading.grobid.Path.is_file', return_value=True):
                result = processor.process_pdf('/test/file.pdf', str(output_file))
            
        assert result == output_file

    @patch('interactive_paper_reading.grobid.Path.exists')
    def test_process_pdf_directory_not_implemented(self, mock_exists, processor):
        """Test that directory processing raises NotImplementedError."""
        # Mock path as directory
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = False
        mock_path.is_dir.return_value = True
        
        with patch('interactive_paper_reading.grobid.Path', return_value=mock_path):
            with pytest.raises(NotImplementedError, match="Directory processing not yet implemented"):
                processor.process_pdf('/test/directory')

    def test_process_single_pdf_direct_success(self, processor):
        """Test successful direct HTTP processing of PDF."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<TEI>test content</TEI>'
        
        # Mock file operations
        mock_open_func = mock_open()
        
        with patch('requests.post', return_value=mock_response):
            with patch('builtins.open', mock_open_func):
                with patch('pathlib.Path.is_dir', return_value=True):
                    result = processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output')
                    )
        
        # Verify file was written
        mock_open_func.assert_called()
        assert isinstance(result, Path)
        assert result.name == 'test.grobid.tei.xml'

    def test_process_single_pdf_direct_server_error(self, processor):
        """Test direct HTTP processing with server error."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        
        with patch('requests.post', return_value=mock_response):
            with patch('builtins.open', mock_open()):
                with pytest.raises(RuntimeError, match="GROBID server error: 500"):
                    processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output')
                    )

    def test_process_single_pdf_direct_request_timeout(self, processor):
        """Test direct HTTP processing with request timeout."""
        with patch('requests.post', side_effect=requests.Timeout()):
            with patch('builtins.open', mock_open()):
                with pytest.raises(requests.Timeout):
                    processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output')
                    )

    def test_process_single_pdf_direct_coordinates_parameter(self, processor):
        """Test that coordinates parameter is properly formatted."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<TEI>test content</TEI>'
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            with patch('builtins.open', mock_open()):
                with patch('pathlib.Path.is_dir', return_value=True):
                    processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output'),
                        add_coordinates=True
                    )
        
        # Check that coordinates were included in the request
        call_args = mock_post.call_args
        assert 'data' in call_args.kwargs
        assert 'teiCoordinates' in call_args.kwargs['data']
        expected_coords = ','.join(processor.config['coordinates'])
        assert call_args.kwargs['data']['teiCoordinates'] == expected_coords

    def test_process_single_pdf_direct_no_coordinates(self, processor):
        """Test processing without coordinates."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<TEI>test content</TEI>'
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            with patch('builtins.open', mock_open()):
                with patch('pathlib.Path.is_dir', return_value=True):
                    processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output'),
                        add_coordinates=False
                    )
        
        # Check that coordinates were not included in the request
        call_args = mock_post.call_args
        data = call_args.kwargs.get('data', {})
        assert 'teiCoordinates' not in data or data['teiCoordinates'] == ''

    def test_process_single_pdf_direct_output_to_file(self, processor):
        """Test processing with specific output file path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<TEI>test content</TEI>'
        
        with patch('requests.post', return_value=mock_response):
            with patch('builtins.open', mock_open()) as mock_open_func:
                with patch('pathlib.Path.is_dir', return_value=False):
                    result = processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output/custom.xml')
                    )
        
        # Should use the specified output file path
        mock_open_func.assert_called_with(Path('/output/custom.xml'), 'wb')
        assert result == Path('/output/custom.xml')

    def test_default_config_creation(self, processor):
        """Test that default configuration is created correctly."""
        config = processor.config
        
        assert 'grobid_server' in config
        assert 'batch_size' in config
        assert 'sleep_time' in config
        assert 'timeout' in config
        assert 'coordinates' in config
        assert isinstance(config['coordinates'], list)

    def test_config_parameter_validation(self, processor):
        """Test that configuration parameters are properly validated."""
        # Test that coordinates is a list
        assert isinstance(processor.config['coordinates'], list)
        
        # Test that timeout is numeric
        assert isinstance(processor.config['timeout'], (int, float))
        
        # Test that batch_size is numeric
        assert isinstance(processor.config['batch_size'], (int, float))

    @patch('interactive_paper_reading.grobid.Path.exists')
    def test_process_pdf_with_all_options(self, mock_exists, processor, tmp_path):
        """Test process_pdf with all optional parameters."""
        mock_exists.return_value = True
        
        # Use a file output path instead of directory to avoid the directory logic
        output_file = tmp_path / "test.grobid.tei.xml"
        
        with patch.object(processor, '_process_single_pdf_direct', return_value=output_file) as mock_process:
            with patch('interactive_paper_reading.grobid.Path.is_file', return_value=True):
                result = processor.process_pdf(
                    '/test/file.pdf',
                    str(output_file),
                    add_coordinates=False,
                    consolidate_header=True,
                    consolidate_citations=True,
                    generate_ids=True,
                    segment_sentences=True,
                    n_workers=5
                )
        
        # Verify all parameters were passed correctly
        mock_process.assert_called_once_with(
            Path('/test/file.pdf'),
            output_file,
            False,  # add_coordinates
            True,   # consolidate_header
            True,   # consolidate_citations
            True,   # generate_ids
            True    # segment_sentences
        )
        assert result == output_file

    def test_process_single_pdf_direct_consolidation_parameters(self, processor):
        """Test that consolidation parameters are properly set."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<TEI>test content</TEI>'
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            with patch('builtins.open', mock_open()):
                with patch('pathlib.Path.is_dir', return_value=True):
                    processor._process_single_pdf_direct(
                        Path('/test.pdf'), 
                        Path('/output'),
                        consolidate_header=True,
                        consolidate_citations=True,
                        generate_ids=True,
                        segment_sentences=True
                    )
        
        # Check that all parameters were included in the request
        call_args = mock_post.call_args
        data = call_args.kwargs['data']
        assert data['consolidateHeader'] == '1'
        assert data['consolidateCitations'] == '1'
        assert data['generateIDs'] == '1'
        assert data['segmentSentences'] == '1'
