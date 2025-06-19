#!/usr/bin/env python3
"""
Comprehensive Academic Paper Processing Pipeline.

This script provides an end-to-end workflow for processing academic papers:
1. Convert PDF to TEI XML using GROBID
2. Extract structured content (sections, figures, tables, graphics)
3. Save sections as markdown and figures/tables as cropped images
4. Analyze the paper using LLM for insights and relevant references

Features:
- Batch processing support
- Robust error handling with logging
- Configurable output formats
- Integration with paper analyzer for insights
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from grobid_processor import GrobidProcessor
from tei_processor import TEIProcessor
from paper_analyzer import PaperAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaperProcessingPipeline:
    """Comprehensive pipeline for processing academic papers."""
    
    def __init__(self, 
                 grobid_url: str = "http://localhost:8070",
                 analyze_with_llm: bool = False,
                 llm_endpoint: Optional[str] = None,
                 llm_model: Optional[str] = None,
                 llm_token: Optional[str] = None):
        """Initialize the processing pipeline.
        
        Args:
            grobid_url: URL of the GROBID service
            analyze_with_llm: Whether to analyze papers with LLM
            llm_endpoint: LLM API endpoint
            llm_model: LLM model name
            llm_token: LLM API token
        """
        self.grobid_processor = GrobidProcessor(grobid_url)
        self.tei_processor = TEIProcessor()
        
        self.analyze_with_llm = analyze_with_llm
        if analyze_with_llm:
            try:
                self.paper_analyzer = PaperAnalyzer(
                    openai_endpoint=llm_endpoint,
                    openai_model=llm_model,
                    openai_token=llm_token
                )
                logger.info("LLM analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM analyzer: {e}")
                self.analyze_with_llm = False
    
    def process_single_paper(self, 
                           pdf_path: Path, 
                           output_dir: Path,
                           extract_figures: bool = True,
                           extract_graphics: bool = True) -> dict:
        """Process a single PDF paper through the complete pipeline.
        
        Args:
            pdf_path: Path to the input PDF file
            output_dir: Directory for output files
            extract_figures: Whether to extract and crop figures/tables
            extract_graphics: Whether to extract and crop graphics
            
        Returns:
            Dictionary with processing results and file paths
        """
        logger.info(f"Processing paper: {pdf_path.name}")
        
        results = {
            'pdf_path': pdf_path,
            'success': False,
            'tei_file': None,
            'markdown_file': None,
            'figures_extracted': 0,
            'graphics_extracted': 0,
            'analysis_file': None,
            'errors': []
        }
        
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Convert PDF to TEI XML using GROBID
            logger.info("Step 1: Converting PDF to TEI XML...")
            base_name = pdf_path.stem
            tei_file = output_dir / f"{base_name}.grobid.tei.xml"
            
            try:
                self.grobid_processor.process_pdf(pdf_path, tei_file)
                results['tei_file'] = tei_file
                logger.info(f"TEI XML saved to: {tei_file}")
            except Exception as e:
                error_msg = f"GROBID processing failed: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Step 2: Extract sections and save as markdown
            logger.info("Step 2: Extracting sections...")
            try:
                sections = self.tei_processor.extract_sections(tei_file)
                markdown_file = output_dir / f"{base_name}-sections.md"
                self.tei_processor.save_sections_as_markdown(sections, markdown_file)
                results['markdown_file'] = markdown_file
                logger.info(f"Markdown saved to: {markdown_file}")
                logger.info(f"Extracted {len(sections)} sections")
            except Exception as e:
                error_msg = f"Section extraction failed: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Step 3: Extract and crop figures/tables
            if extract_figures:
                logger.info("Step 3: Extracting figures and tables...")
                try:
                    figures = self.tei_processor.extract_figures_tables(tei_file)
                    
                    for i, figure in enumerate(figures):
                        try:
                            figure_name = f"{base_name}-{figure.element_type}-{i+1}.png"
                            figure_path = output_dir / figure_name
                            
                            self.tei_processor.crop_figure_from_pdf(
                                figure, pdf_path, figure_path
                            )
                            results['figures_extracted'] += 1
                            logger.debug(f"Extracted {figure.element_type}: {figure_path}")
                        except Exception as e:
                            logger.warning(f"Failed to extract {figure.element_type} {i+1}: {e}")
                    
                    logger.info(f"Extracted {results['figures_extracted']} figures/tables")
                except Exception as e:
                    error_msg = f"Figure extraction failed: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Step 4: Extract and crop graphics
            if extract_graphics:
                logger.info("Step 4: Extracting graphics...")
                try:
                    graphics = self.tei_processor.extract_graphics(tei_file)
                    
                    for i, graphic in enumerate(graphics):
                        try:
                            graphic_name = f"{base_name}-graphic-{i+1}.png"
                            graphic_path = output_dir / graphic_name
                            
                            self.tei_processor.crop_graphic_from_pdf(
                                graphic, pdf_path, graphic_path
                            )
                            results['graphics_extracted'] += 1
                            logger.debug(f"Extracted graphic: {graphic_path}")
                        except Exception as e:
                            logger.warning(f"Failed to extract graphic {i+1}: {e}")
                    
                    logger.info(f"Extracted {results['graphics_extracted']} graphics")
                except Exception as e:
                    error_msg = f"Graphics extraction failed: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Step 5: Analyze with LLM if enabled
            if self.analyze_with_llm and results['markdown_file']:
                logger.info("Step 5: Analyzing with LLM...")
                try:
                    analysis = self.paper_analyzer.analyze_paper(
                        results['markdown_file'], 
                        results['tei_file']
                    )
                    
                    analysis_file = output_dir / f"{base_name}-analysis.json"
                    self.paper_analyzer.save_analysis(analysis, analysis_file)
                    results['analysis_file'] = analysis_file
                    
                    # Print summary
                    self.paper_analyzer.print_analysis_summary(analysis)
                    logger.info(f"Analysis saved to: {analysis_file}")
                except Exception as e:
                    error_msg = f"LLM analysis failed: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            results['success'] = True
            logger.info(f"Successfully processed: {pdf_path.name}")
            
        except Exception as e:
            error_msg = f"Unexpected error processing {pdf_path.name}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def process_batch(self, 
                     pdf_files: List[Path], 
                     output_base_dir: Path,
                     extract_figures: bool = True,
                     extract_graphics: bool = True) -> List[dict]:
        """Process multiple PDF files in batch.
        
        Args:
            pdf_files: List of PDF file paths
            output_base_dir: Base directory for all outputs
            extract_figures: Whether to extract figures/tables
            extract_graphics: Whether to extract graphics
            
        Returns:
            List of processing results for each file
        """
        logger.info(f"Starting batch processing of {len(pdf_files)} files")
        
        all_results = []
        
        for pdf_file in pdf_files:
            try:
                # Create separate output directory for each paper
                paper_output_dir = output_base_dir / pdf_file.stem
                
                results = self.process_single_paper(
                    pdf_file, 
                    paper_output_dir,
                    extract_figures=extract_figures,
                    extract_graphics=extract_graphics
                )
                all_results.append(results)
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                all_results.append({
                    'pdf_path': pdf_file,
                    'success': False,
                    'errors': [str(e)]
                })
        
        # Print batch summary
        successful = sum(1 for r in all_results if r['success'])
        logger.info(f"Batch processing completed: {successful}/{len(pdf_files)} successful")
        
        return all_results


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Academic Paper Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single paper
  python comprehensive_pipeline.py paper.pdf --output ./output
  
  # Process with LLM analysis
  python comprehensive_pipeline.py paper.pdf --output ./output --analyze
  
  # Batch process directory
  python comprehensive_pipeline.py ./papers/*.pdf --output ./output --batch
  
  # Skip figure extraction
  python comprehensive_pipeline.py paper.pdf --output ./output --no-figures
  
  # Verbose logging
  python comprehensive_pipeline.py paper.pdf --output ./output --verbose
        """
    )
    
    parser.add_argument("pdf_files", nargs="+", help="PDF file(s) to process")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--grobid-url", default="http://localhost:8070", 
                        help="GROBID service URL")
    parser.add_argument("--analyze", action="store_true", 
                        help="Analyze papers with LLM")
    parser.add_argument("--llm-endpoint", help="LLM API endpoint")
    parser.add_argument("--llm-model", help="LLM model name")
    parser.add_argument("--llm-token", help="LLM API token")
    parser.add_argument("--no-figures", action="store_true", 
                        help="Skip figure/table extraction")
    parser.add_argument("--no-graphics", action="store_true", 
                        help="Skip graphics extraction")
    parser.add_argument("--batch", action="store_true", 
                        help="Process files in batch mode")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose logging")
    parser.add_argument("--quiet", "-q", action="store_true", 
                        help="Suppress output except errors")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    try:
        # Initialize pipeline
        pipeline = PaperProcessingPipeline(
            grobid_url=args.grobid_url,
            analyze_with_llm=args.analyze,
            llm_endpoint=args.llm_endpoint,
            llm_model=args.llm_model,
            llm_token=args.llm_token
        )
        
        # Validate input files
        pdf_files = []
        for pdf_pattern in args.pdf_files:
            pdf_path = Path(pdf_pattern)
            if pdf_path.is_file() and pdf_path.suffix.lower() == '.pdf':
                pdf_files.append(pdf_path)
            elif '*' in pdf_pattern:
                # Handle glob patterns
                from glob import glob
                matching_files = [Path(f) for f in glob(pdf_pattern) 
                                 if Path(f).suffix.lower() == '.pdf']
                pdf_files.extend(matching_files)
            else:
                logger.warning(f"Skipping non-PDF file: {pdf_pattern}")
        
        if not pdf_files:
            logger.error("No valid PDF files found")
            return 1
        
        output_dir = Path(args.output)
        
        # Process files
        if args.batch or len(pdf_files) > 1:
            results = pipeline.process_batch(
                pdf_files,
                output_dir,
                extract_figures=not args.no_figures,
                extract_graphics=not args.no_graphics
            )
        else:
            # Single file processing
            result = pipeline.process_single_paper(
                pdf_files[0],
                output_dir,
                extract_figures=not args.no_figures,
                extract_graphics=not args.no_graphics
            )
            results = [result]
        
        # Print final summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print("\n" + "="*80)
        print("📊 PROCESSING SUMMARY")
        print("="*80)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        
        if failed > 0:
            print("\n❌ FAILED FILES:")
            for result in results:
                if not result['success']:
                    print(f"  - {result['pdf_path'].name}: {'; '.join(result['errors'])}")
        
        print(f"\n📁 Output directory: {output_dir}")
        print(f"{'='*80}")
        
        return 0 if failed == 0 else 1
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
