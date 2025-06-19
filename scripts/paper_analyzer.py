#!/usr/bin/env python3
"""
Academic Paper Analyzer using LLM.

This module analyzes processed academic papers to extract insights including:
1. Top 3 relevant papers from references with similarity reasoning
2. Heritage analysis - how this paper builds on previous work
3. Content analysis of the paper sections

The module can work with:
- Markdown files only (extracts from content)
- Markdown + TEI XML files (extract                print("\\n🏛️ HERITAGE ANALYSIS:")
        print(analysis.heritage_analysis)
        
        print("\\n💡 KEY CONTRIBUTIONS:")
        for i, contribution in enumerate(analysis.key_contributions, 1):
            print(f"{i}. {contribution}")
        
        print("\\n🔍 RESEARCH GAPS ADDRESSED:")
        for i, gap in enumerate(analysis.research_gaps, 1):
            print(f"{i}. {gap}")
        
        print("\\n🔬 METHODOLOGY INSIGHTS:")rint("\n🔬 METHODOLOGY INSIGHTS:")   print("\n🔍 RESEARCH GAPS ADDRESSED:")   print("\n💡 KEY CONTRIBUTIONS:")    print("\n🏛️ HERITAGE ANALYSIS:") structured references)
"""

import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import requests
from xml.etree import ElementTree as ET

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from tei_processor import TEIProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """Represents a bibliographic reference."""
    id: str
    title: str
    authors: List[str]
    year: Optional[str] = None
    venue: Optional[str] = None
    full_text: Optional[str] = None


@dataclass
class PaperAnalysis:
    """Results of paper analysis."""
    paper_title: str
    relevant_papers: List[Dict[str, str]]  # top 3 relevant papers with reasoning
    heritage_analysis: str
    key_contributions: List[str]
    research_gaps: List[str]
    methodology_insights: str


class PaperAnalyzer:
    """Analyzes academic papers using LLM for insights."""
    
    def __init__(self, 
                 openai_endpoint: Optional[str] = None,
                 openai_model: Optional[str] = None,
                 openai_token: Optional[str] = None):
        """Initialize the analyzer.
        
        Args:
            openai_endpoint: OpenAI API endpoint (defaults to env OPENAI_ENDPOINT)
            openai_model: Model name (defaults to env OPENAI_MODEL)
            openai_token: API token (defaults to env OPENAI_ACCESS_TOKEN)
        """
        self.endpoint = openai_endpoint or os.getenv('OPENAI_ENDPOINT', 'https://api.openai.com/v1')
        self.model = openai_model or os.getenv('OPENAI_MODEL', 'gpt-4')
        self.token = openai_token or os.getenv('OPENAI_ACCESS_TOKEN')
        
        if not self.token:
            raise ValueError("OpenAI API token must be provided or set in OPENAI_ACCESS_TOKEN environment variable")
        
        self.tei_processor = TEIProcessor()
    
    def extract_references_from_tei(self, tei_file: Path) -> List[Reference]:
        """Extract bibliographic references from TEI XML.
        
        Args:
            tei_file: Path to TEI XML file
            
        Returns:
            List of Reference objects
        """
        references = []
        
        try:
            tree = ET.parse(tei_file)
            root = tree.getroot()
            
            # TEI namespace
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            
            # Find all bibliographic structures
            bibl_structs = root.findall('.//tei:listBibl/tei:biblStruct', ns)
            
            for i, bibl_struct in enumerate(bibl_structs):
                ref_id = bibl_struct.get('{http://www.w3.org/XML/1998/namespace}id', f'ref_{i}')
                
                # Extract title
                title_elem = bibl_struct.find('.//tei:title[@level="a"]', ns)
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Unknown Title"
                
                # Extract authors
                authors = []
                author_elems = bibl_struct.findall('.//tei:author/tei:persName', ns)
                for author_elem in author_elems:
                    # Extract forename and surname
                    forename_elem = author_elem.find('tei:forename', ns)
                    surname_elem = author_elem.find('tei:surname', ns)
                    
                    forename = forename_elem.text.strip() if forename_elem is not None and forename_elem.text else ""
                    surname = surname_elem.text.strip() if surname_elem is not None and surname_elem.text else ""
                    
                    if forename and surname:
                        authors.append(f"{forename} {surname}")
                    elif surname:
                        authors.append(surname)
                
                # Extract publication year
                year = None
                date_elem = bibl_struct.find('.//tei:imprint/tei:date[@type="published"]', ns)
                if date_elem is not None:
                    when_attr = date_elem.get('when')
                    if when_attr:
                        year = when_attr[:4]  # Extract year part
                
                # Extract venue (journal/conference)
                venue = None
                journal_elem = bibl_struct.find('.//tei:title[@level="j"]', ns)
                if journal_elem is not None and journal_elem.text:
                    venue = journal_elem.text.strip()
                else:
                    # Try conference/proceedings
                    conf_elem = bibl_struct.find('.//tei:title[@level="m"]', ns)
                    if conf_elem is not None and conf_elem.text:
                        venue = conf_elem.text.strip()
                
                # Create full text representation
                author_str = ", ".join(authors) if authors else "Unknown Authors"
                year_str = f" ({year})" if year else ""
                venue_str = f" In {venue}." if venue else ""
                full_text = f"{author_str}{year_str}. {title}.{venue_str}"
                
                references.append(Reference(
                    id=ref_id,
                    title=title,
                    authors=authors,
                    year=year,
                    venue=venue,
                    full_text=full_text
                ))
        
        except Exception as e:
            print(f"Warning: Could not extract references from TEI: {e}")
        
        return references
    
    def extract_references_from_markdown(self, content: str) -> List[Reference]:
        """Extract references from markdown content using pattern matching.
        
        Args:
            content: Markdown content
            
        Returns:
            List of Reference objects extracted from text
        """
        references = []
        
        # Pattern to find reference citations like [1], [18], etc.
        citation_pattern = r'\[(\d+)\]'
        citations = set(re.findall(citation_pattern, content))
        
        # Look for author-year patterns like "Carion et al. [1]"
        author_year_pattern = r'([A-Z][a-z]+(?:\s+et\s+al\.?)?)\s*\[(\d+)\]'
        author_matches = re.findall(author_year_pattern, content)
        
        # Create reference objects from found patterns
        for i, citation in enumerate(sorted(citations, key=int)):
            # Find corresponding author if available
            authors = []
            for author, cite_id in author_matches:
                if cite_id == citation:
                    authors.append(author)
                    break
            
            if not authors:
                authors = ["Unknown Author"]
            
            references.append(Reference(
                id=f"ref_{citation}",
                title=f"Reference {citation}",
                authors=authors,
                full_text=f"{', '.join(authors)}. Reference {citation}."
            ))
        
        return references
    
    def call_llm(self, prompt: str) -> str:
        """Call the LLM API with the given prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM response
        """
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.7,
            'max_tokens': 4000,
        }
        
        try:
            logger.info("Making LLM API call...")
            response = requests.post(
                f'{self.endpoint}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("LLM API call successful")
            return result['choices'][0]['message']['content']
        
        except requests.RequestException as e:
            logger.error(f"LLM API call failed: {e}")
            raise RuntimeError(f"LLM API call failed: {e}")
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise RuntimeError(f"Unexpected API response format: {e}")
    
    def create_analysis_prompt(self, 
                              paper_content: str, 
                              references: List[Reference],
                              paper_title: str = "Unknown Paper") -> str:
        """Create a comprehensive analysis prompt for the LLM.
        
        Args:
            paper_content: The main content of the paper
            references: List of extracted references
            paper_title: Title of the paper
            
        Returns:
            Formatted prompt for LLM analysis
        """
        # Format references for the prompt
        references_text = ""
        if references:
            references_text = "\\n\\nAVAILABLE REFERENCES:\\n"
            for ref in references[:50]:  # Limit to first 50 references to avoid token limits
                references_text += f"- [{ref.id}] {ref.full_text}\\n"
        else:
            references_text = "\\n\\nNote: No structured references were available. Please infer relevant papers from the content."
        
        prompt = f"""
You are an expert academic researcher analyzing a research paper. Please provide a comprehensive analysis of the following paper.

PAPER TITLE: {paper_title}

PAPER CONTENT:
{paper_content[:8000]}  # Limit content to avoid token limits

{references_text}

Please provide a detailed analysis in the following JSON format:

{{
    "paper_title": "{paper_title}",
    "relevant_papers": [
        {{
            "reference": "Full citation or reference identifier",
            "similarity_reasoning": "Detailed explanation of why this paper is relevant, what specific aspects connect to the current work, and how it relates to the research problem",
            "relevance_score": "High/Medium/Low"
        }}
        // Include exactly 3 most relevant papers
    ],
    "heritage_analysis": "Comprehensive analysis of how this paper builds upon previous work. Discuss the lineage of ideas, what foundational concepts it inherits, how it extends or challenges existing approaches, and its position in the research evolution. Be specific about methodological heritage and conceptual foundations.",
    "key_contributions": [
        "List of 3-5 main contributions of this paper",
        "Focus on novel aspects and advances"
    ],
    "research_gaps": [
        "List of 2-4 research gaps this paper addresses",
        "What problems existed before this work"
    ],
    "methodology_insights": "Analysis of the methodology used, its novelty, strengths, and how it compares to previous approaches. Discuss technical innovations and experimental design."
}}

ANALYSIS GUIDELINES:
1. For RELEVANT PAPERS: Focus on the 3 most impactful and closely related works. Explain WHY each is relevant, not just WHAT it is about.
2. For HERITAGE ANALYSIS: Trace the intellectual lineage - how ideas evolved, what foundations this work builds on, and how it fits into the broader research narrative.
3. Be specific and detailed in your reasoning. Avoid generic statements.
4. If references are limited, use your knowledge of the field to identify the most likely relevant papers based on the content and methodology described.

Please ensure the response is valid JSON format.
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM response with robust error handling.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed JSON data or raises ValueError
        """
        response_clean = response.strip()
        
        # Handle different response formats
        if response_clean.startswith('```json') and response_clean.endswith('```'):
            # Extract JSON from markdown code block
            response_clean = response_clean[7:-3].strip()
        elif response_clean.startswith('```') and response_clean.endswith('```'):
            # Extract from generic code block
            response_clean = response_clean[3:-3].strip()
        elif response_clean.startswith('{') and response_clean.endswith('}'):
            # Already clean JSON
            pass
        else:
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(0)
            else:
                raise ValueError(f"No JSON object found in response: {response_clean[:200]}...")
        
        try:
            return json.loads(response_clean)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response content: {response_clean[:500]}...")
            raise ValueError(f"Failed to parse JSON response: {e}")

    def analyze_paper(self, 
                     markdown_file: Path, 
                     tei_file: Optional[Path] = None) -> PaperAnalysis:
        """Analyze a paper from markdown content and optional TEI file.
        
        Args:
            markdown_file: Path to the markdown file with paper content
            tei_file: Optional path to TEI XML file for structured references
            
        Returns:
            PaperAnalysis object with results
        """
        logger.info(f"Analyzing paper: {markdown_file.name}")
        
        # Read markdown content
        if not markdown_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_file}")
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract paper title from markdown
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        paper_title = title_match.group(1) if title_match else markdown_file.stem
        logger.info(f"Paper title: {paper_title}")
        
        # Extract references
        references = []
        
        # Try TEI first if available
        if tei_file and tei_file.exists():
            logger.info(f"Extracting references from TEI: {tei_file.name}")
            try:
                references = self.extract_references_from_tei(tei_file)
                logger.info(f"Found {len(references)} references from TEI")
            except Exception as e:
                logger.warning(f"Failed to extract references from TEI: {e}")
        
        # Fallback to markdown extraction if no TEI references found
        if not references:
            logger.info("Extracting references from markdown content")
            try:
                references = self.extract_references_from_markdown(content)
                logger.info(f"Found {len(references)} reference patterns from markdown")
            except Exception as e:
                logger.warning(f"Failed to extract references from markdown: {e}")
        
        # Create analysis prompt
        prompt = self.create_analysis_prompt(content, references, paper_title)
        
        # Call LLM for analysis
        logger.info("Analyzing paper with LLM...")
        try:
            response = self.call_llm(prompt)
            
            # Parse JSON response with enhanced error handling
            analysis_data = self._parse_llm_response(response)
            
            logger.info("Successfully parsed LLM response")
            return PaperAnalysis(
                paper_title=analysis_data.get('paper_title', paper_title),
                relevant_papers=analysis_data.get('relevant_papers', []),
                heritage_analysis=analysis_data.get('heritage_analysis', ''),
                key_contributions=analysis_data.get('key_contributions', []),
                research_gaps=analysis_data.get('research_gaps', []),
                methodology_insights=analysis_data.get('methodology_insights', '')
            )
        
        except ValueError as e:
            # If JSON parsing fails, return a basic analysis with the raw response
            logger.error(f"Could not parse JSON response: {e}")
            
            return PaperAnalysis(
                paper_title=paper_title,
                relevant_papers=[],
                heritage_analysis=f"LLM Response (failed to parse JSON): {response[:1000]}...",
                key_contributions=[],
                research_gaps=[],
                methodology_insights=""
            )
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise RuntimeError(f"Analysis failed: {e}")
    
    def save_analysis(self, analysis: PaperAnalysis, output_file: Path):
        """Save analysis results to a file.
        
        Args:
            analysis: PaperAnalysis object
            output_file: Path to save the results
        """
        output_data = {
            'paper_title': analysis.paper_title,
            'analysis_timestamp': str(Path().cwd()),  # Simple timestamp placeholder
            'relevant_papers': analysis.relevant_papers,
            'heritage_analysis': analysis.heritage_analysis,
            'key_contributions': analysis.key_contributions,
            'research_gaps': analysis.research_gaps,
            'methodology_insights': analysis.methodology_insights
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Analysis saved to: {output_file}")
    
    def print_analysis_summary(self, analysis: PaperAnalysis):
        """Print a formatted summary of the analysis.
        
        Args:
            analysis: PaperAnalysis object
        """
        print("\n" + "="*80)
        print(f"📄 PAPER ANALYSIS: {analysis.paper_title}")
        print("="*80)
        
        print("\n🔗 TOP 3 RELEVANT PAPERS:")
        for i, paper in enumerate(analysis.relevant_papers, 1):
            print(f"\n{i}. {paper.get('reference', 'N/A')}")
            print(f"   Relevance: {paper.get('relevance_score', 'N/A')}")
            print(f"   Reasoning: {paper.get('similarity_reasoning', 'N/A')}")
        
        print("\n🏛️ HERITAGE ANALYSIS:")
        print(analysis.heritage_analysis)
        
        print("\n💡 KEY CONTRIBUTIONS:")
        for i, contribution in enumerate(analysis.key_contributions, 1):
            print(f"{i}. {contribution}")
        
        print("\n🔍 RESEARCH GAPS ADDRESSED:")
        for i, gap in enumerate(analysis.research_gaps, 1):
            print(f"{i}. {gap}")
        
        print("\n🔬 METHODOLOGY INSIGHTS:")
        print(analysis.methodology_insights)
        
        print("\n" + "="*80)


def main():
    """Main function for command-line usage."""
    import argparse
    
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
