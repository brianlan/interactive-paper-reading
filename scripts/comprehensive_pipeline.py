#!/usr/bin/env python3
"""
Comprehensive Academic Paper Processing Pipeline CLI.

This script provides a command-line interface for end-to-end processing of academic papers:
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

# Add parent directory to Python path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_paper_reading.pipeline import PaperProcessingPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
