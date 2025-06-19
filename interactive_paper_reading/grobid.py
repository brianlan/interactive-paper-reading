"""
GROBID PDF Processor

This module provides functionality to process PDF files using GROBID 
to extract structured text in TEI format with PDF coordinates.
"""

import json
import logging
import requests
from pathlib import Path
from grobid_client.grobid_client import GrobidClient

logger = logging.getLogger(__name__)


class GrobidProcessor:
    """GROBID processor for converting PDF files to TEI XML."""
    
    def __init__(self, config_path=None, server_url="http://localhost:8070"):
        """
        Initialize GROBID processor
        
        Args:
            config_path: Path to GROBID config file
            server_url: GROBID server URL
        """
        if config_path is None:
            # Create default config
            self.config = {
                "grobid_server": server_url,
                "batch_size": 1000,
                "sleep_time": 10,  # Increased wait time
                "timeout": 120,   # Increased timeout to 2 minutes
                "coordinates": ["persName", "figure", "ref", "biblStruct", "formula", "s"]
            }
            config_path = self._create_temp_config()
        
        self.client = GrobidClient(config_path=config_path)
        self.config_path = config_path
    
    def _create_temp_config(self):
        """Create temporary config file"""
        config_path = "/tmp/grobid_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        return config_path
    
    def process_pdf(self, pdf_path, output_path=None, add_coordinates=True, 
                   consolidate_header=False, consolidate_citations=False,
                   generate_ids=False, segment_sentences=False, n_workers=10):
        """
        Process a single PDF or directory of PDFs with GROBID
        
        Args:
            pdf_path: Path to PDF file or directory containing PDFs
            output_path: Output path for TEI files (file or directory)
            add_coordinates: Add PDF coordinates to TEI output
            consolidate_header: Consolidate header metadata
            consolidate_citations: Consolidate bibliographical references
            generate_ids: Generate random xml:id for textual elements
            segment_sentences: Segment sentences with <s> elements
            n_workers: Number of concurrent workers
            
        Returns:
            Path to output file or directory
        """
        
        # Validate inputs
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF path does not exist: {pdf_path}")
        
        # Set output path
        if output_path is None:
            if pdf_path.is_file():
                output_path = pdf_path.parent / f"{pdf_path.stem}.grobid.tei.xml"
            else:
                output_path = pdf_path / "grobid_output"
        else:
            output_path = Path(output_path)
        
        # Create output directory if needed
        if pdf_path.is_dir() or not output_path.suffix:
            output_path.mkdir(exist_ok=True, parents=True)
        else:
            output_path.parent.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Processing PDF(s): {pdf_path}")
        logger.info(f"Output: {output_path}")
        logger.info(f"GROBID server: {self.config['grobid_server']}")
        
        try:
            # Use direct HTTP request instead of grobid_client since it's not working properly
            if pdf_path.is_file():
                return self._process_single_pdf_direct(pdf_path, output_path, add_coordinates,
                                                     consolidate_header, consolidate_citations,
                                                     generate_ids, segment_sentences)
            else:
                # Handle directory processing
                raise NotImplementedError("Directory processing not yet implemented with direct HTTP method")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
    
    def _process_single_pdf_direct(self, pdf_path, output_path, add_coordinates=True,
                                  consolidate_header=False, consolidate_citations=False,
                                  generate_ids=False, segment_sentences=False):
        """Process a single PDF using direct HTTP requests to GROBID"""
        
        # Prepare coordinates parameter
        coordinates = ','.join(self.config['coordinates']) if add_coordinates else ''
        
        # Prepare request data
        data = {}
        if coordinates:
            data['teiCoordinates'] = coordinates
        if consolidate_header:
            data['consolidateHeader'] = '1'
        if consolidate_citations:
            data['consolidateCitations'] = '1'
        if generate_ids:
            data['generateIDs'] = '1'
        if segment_sentences:
            data['segmentSentences'] = '1'
        
        # Make request to GROBID server
        url = f"{self.config['grobid_server']}/api/processFulltextDocument"
        
        with open(pdf_path, 'rb') as f:
            files = {'input': f}
            response = requests.post(url, files=files, data=data, timeout=self.config['timeout'])
        
        if response.status_code != 200:
            raise RuntimeError(f"GROBID server error: {response.status_code} - {response.text}")
        
        # Determine output file path
        if output_path.is_dir():
            # Save to directory with generated filename
            output_file = output_path / f"{pdf_path.stem}.grobid.tei.xml"
        else:
            # Use specified output path
            output_file = output_path
        
        # Save response content
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"TEI file saved to: {output_file}")
        logger.info("Processing completed successfully!")
        
        return output_file
    
    def check_server_status(self):
        """Check if GROBID server is running"""
        try:
            response = requests.get(f"{self.config['grobid_server']}/api/isalive")
            if response.status_code == 200:
                logger.info(f"GROBID server is running at {self.config['grobid_server']}")
                return True
            else:
                logger.error(f"GROBID server responded with status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot connect to GROBID server: {e}")
            return False
