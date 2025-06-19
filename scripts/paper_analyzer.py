#!/usr/bin/env python3
"""
Academic Paper Analyzer using LLM CLI.

This script analyzes processed academic papers to extract insights including:
1. Top 3 relevant papers from references with similarity reasoning
2. Heritage analysis - how this paper builds on previous work
3. Content analysis of the paper sections

The script can work with:
- Markdown files only (extracts from content)
- Markdown + TEI XML files (structured references)
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to Python path for package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_paper_reading.analyzer import PaperAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Analyze academic papers using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze markdown only
  python paper_analyzer.py paper_sections.md
  
  # Analyze with TEI references
  python paper_analyzer.py paper_sections.md --tei paper.tei.xml
  
  # Save analysis to file
  python paper_analyzer.py paper_sections.md --output analysis.json
  
  # Use custom API settings
  python paper_analyzer.py paper_sections.md --model gpt-3.5-turbo --endpoint https://custom.api.com
  
  # Verbose logging
  python paper_analyzer.py paper_sections.md --verbose
        """
    )
    
    parser.add_argument("markdown_file", help="Path to markdown file with paper content")
    parser.add_argument("--tei", help="Path to TEI XML file for references")
    parser.add_argument("--output", "-o", help="Output file for analysis results (JSON)")
    parser.add_argument("--endpoint", help="OpenAI API endpoint")
    parser.add_argument("--model", help="Model name (default: gpt-4)")
    parser.add_argument("--token", help="API token (default: from OPENAI_ACCESS_TOKEN env var)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output except errors")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    try:
        # Initialize analyzer
        logger.info("Initializing paper analyzer...")
        analyzer = PaperAnalyzer(
            openai_endpoint=args.endpoint,
            openai_model=args.model,
            openai_token=args.token
        )
        
        # Validate input files
        markdown_path = Path(args.markdown_file)
        if not markdown_path.exists():
            logger.error(f"Markdown file not found: {markdown_path}")
            return 1
        
        tei_path = None
        if args.tei:
            tei_path = Path(args.tei)
            if not tei_path.exists():
                logger.warning(f"TEI file not found: {tei_path}")
                tei_path = None
        
        # Analyze paper
        logger.info("Starting paper analysis...")
        analysis = analyzer.analyze_paper(markdown_path, tei_path)
        
        # Print summary unless quiet mode
        if not args.quiet:
            analyzer.print_analysis_summary(analysis)
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            analyzer.save_analysis(analysis, output_path)
            logger.info(f"Analysis saved to: {output_path}")
        
        logger.info("Analysis completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 2
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 3
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return 4
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
