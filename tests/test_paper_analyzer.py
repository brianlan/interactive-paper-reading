"""
Tests for paper analyzer functionality.

This module contains tests for analyzing academic papers using LLM.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import xml.etree.ElementTree as ET
import requests

from interactive_paper_reading.analyzer import PaperAnalyzer, Reference, PaperAnalysis


class TestPaperAnalyzer:
    """Test cases for PaperAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a PaperAnalyzer instance for testing."""
        with patch.dict('os.environ', {'OPENAI_ACCESS_TOKEN': 'test-token'}):
            return PaperAnalyzer()

    @pytest.fixture
    def sample_tei_xml(self) -> str:
        """Sample TEI XML with references."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <text>
        <back>
            <div type="references">
                <listBibl>
                    <biblStruct xml:id="ref1">
                        <analytic>
                            <title level="a">Deep Learning for Object Detection</title>
                            <author>
                                <persName>
                                    <forename>John</forename>
                                    <surname>Smith</surname>
                                </persName>
                            </author>
                        </analytic>
                        <monogr>
                            <title level="j">Computer Vision Journal</title>
                            <imprint>
                                <date type="published" when="2020"/>
                            </imprint>
                        </monogr>
                    </biblStruct>
                    <biblStruct xml:id="ref2">
                        <analytic>
                            <title level="a">Another Paper</title>
                            <author>
                                <persName>
                                    <forename>Jane</forename>
                                    <surname>Doe</surname>
                                </persName>
                            </author>
                        </analytic>
                        <monogr>
                            <title level="m">Conference Proceedings</title>
                            <imprint>
                                <date type="published" when="2021"/>
                            </imprint>
                        </monogr>
                    </biblStruct>
                </listBibl>
            </div>
        </back>
    </text>
</TEI>'''

    @pytest.fixture
    def sample_markdown(self) -> str:
        """Sample markdown content."""
        return '''# Test Paper Title

## Abstract
This paper presents a novel approach to object detection.

## Introduction
Recent advances in deep learning [1] have shown promising results.
The work by Smith et al. [2] demonstrates the effectiveness of this approach.

## References
[1] Smith, J. (2020). Deep Learning for Object Detection.
[2] Doe, J. (2021). Another Paper.
'''

    @pytest.fixture
    def mock_llm_response(self) -> str:
        """Mock LLM response in JSON format."""
        return '''```json
{
    "paper_title": "Test Paper Title",
    "relevant_papers": [
        {
            "reference": "Smith, J. (2020). Deep Learning for Object Detection",
            "similarity_reasoning": "This paper directly relates to the core methodology",
            "relevance_score": "High"
        }
    ],
    "heritage_analysis": "This paper builds on foundational work in deep learning",
    "key_contributions": ["Novel detection algorithm", "Improved accuracy"],
    "research_gaps": ["Limited real-time performance"],
    "methodology_insights": "Uses advanced neural networks"
}
```'''

    def test_analyzer_initialization_with_token(self):
        """Test PaperAnalyzer initialization with valid token."""
        with patch.dict('os.environ', {'OPENAI_ACCESS_TOKEN': 'test-token'}):
            analyzer = PaperAnalyzer()
            assert analyzer.token == 'test-token'
            # Don't assert specific model since it depends on environment
            assert analyzer.model is not None
            assert analyzer.endpoint is not None

    def test_analyzer_initialization_no_token_raises_error(self):
        """Test that missing token raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API token must be provided"):
                PaperAnalyzer()

    def test_analyzer_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        analyzer = PaperAnalyzer(
            openai_endpoint='https://custom.endpoint.com',
            openai_model='gpt-3.5-turbo',
            openai_token='custom-token'
        )
        assert analyzer.endpoint == 'https://custom.endpoint.com'
        assert analyzer.model == 'gpt-3.5-turbo'
        assert analyzer.token == 'custom-token'

    def test_extract_references_from_tei_success(self, analyzer, sample_tei_xml):
        """Test successful reference extraction from TEI XML."""
        with patch('builtins.open', mock_open(read_data=sample_tei_xml)):
            references = analyzer.extract_references_from_tei(Path('test.xml'))

        assert len(references) == 2
        
        # Check first reference
        ref1 = references[0]
        assert ref1.id == 'ref1'
        assert ref1.title == 'Deep Learning for Object Detection'
        assert ref1.authors == ['John Smith']
        assert ref1.year == '2020'
        assert ref1.venue == 'Computer Vision Journal'
        assert 'John Smith (2020)' in ref1.full_text

        # Check second reference
        ref2 = references[1]
        assert ref2.id == 'ref2'
        assert ref2.title == 'Another Paper'
        assert ref2.authors == ['Jane Doe']
        assert ref2.year == '2021'
        assert ref2.venue == 'Conference Proceedings'

    def test_extract_references_from_tei_malformed_xml(self, analyzer):
        """Test reference extraction with malformed XML."""
        malformed_xml = "<?xml version='1.0'?><invalid>"
        
        with patch('builtins.open', mock_open(read_data=malformed_xml)):
            with patch('xml.etree.ElementTree.parse', side_effect=ET.ParseError):
                references = analyzer.extract_references_from_tei(Path('test.xml'))

        assert references == []

    def test_extract_references_from_tei_file_not_found(self, analyzer):
        """Test reference extraction when TEI file doesn't exist."""
        with patch('xml.etree.ElementTree.parse', side_effect=FileNotFoundError):
            references = analyzer.extract_references_from_tei(Path('nonexistent.xml'))

        assert references == []

    def test_extract_references_from_markdown_success(self, analyzer, sample_markdown):
        """Test successful reference extraction from markdown."""
        references = analyzer.extract_references_from_markdown(sample_markdown)

        assert len(references) >= 2
        
        # Should find citation patterns [1] and [2]
        ref_ids = [ref.id for ref in references]
        assert 'ref_1' in ref_ids
        assert 'ref_2' in ref_ids

    def test_extract_references_from_markdown_no_citations(self, analyzer):
        """Test reference extraction from markdown without citations."""
        content = "# Paper\n\nThis paper has no citations."
        references = analyzer.extract_references_from_markdown(content)

        assert references == []

    def test_call_llm_success(self, analyzer, mock_llm_response):
        """Test successful LLM API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': mock_llm_response}}]
        }
        mock_response.raise_for_status.return_value = None

        with patch('requests.post', return_value=mock_response):
            result = analyzer.call_llm("Test prompt")

        assert mock_llm_response in result

    def test_call_llm_request_error(self, analyzer):
        """Test LLM API call with request error."""
        with patch('requests.post', side_effect=requests.RequestException("Network error")):
            with pytest.raises(RuntimeError, match="LLM API call failed"):
                analyzer.call_llm("Test prompt")

    def test_call_llm_invalid_response_format(self, analyzer):
        """Test LLM API call with invalid response format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'invalid': 'format'}
        mock_response.raise_for_status.return_value = None

        with patch('requests.post', return_value=mock_response):
            with pytest.raises(RuntimeError, match="Unexpected API response format"):
                analyzer.call_llm("Test prompt")

    def test_create_analysis_prompt_with_references(self, analyzer):
        """Test prompt creation with references."""
        references = [
            Reference("ref1", "Test Paper", ["Author One"], "2020", "Journal", "Author One (2020). Test Paper. In Journal."),
            Reference("ref2", "Another Paper", ["Author Two"], "2021", "Conference", "Author Two (2021). Another Paper. In Conference.")
        ]
        
        prompt = analyzer.create_analysis_prompt(
            "Paper content here", 
            references, 
            "Test Title"
        )

        assert "Test Title" in prompt
        assert "Paper content here" in prompt
        assert "AVAILABLE REFERENCES:" in prompt
        assert "Test Paper" in prompt
        assert "Another Paper" in prompt

    def test_create_analysis_prompt_no_references(self, analyzer):
        """Test prompt creation without references."""
        prompt = analyzer.create_analysis_prompt(
            "Paper content here", 
            [], 
            "Test Title"
        )

        assert "Test Title" in prompt
        assert "Paper content here" in prompt
        assert "No structured references were available" in prompt

    @patch('interactive_paper_reading.analyzer.PaperAnalyzer.call_llm')
    def test_analyze_paper_success(self, mock_call_llm, analyzer, sample_markdown, mock_llm_response):
        """Test successful paper analysis."""
        mock_call_llm.return_value = mock_llm_response

        with patch('builtins.open', mock_open(read_data=sample_markdown)):
            with patch.object(Path, 'exists', return_value=True):
                analysis = analyzer.analyze_paper(Path('test.md'))

        assert isinstance(analysis, PaperAnalysis)
        assert analysis.paper_title == "Test Paper Title"
        assert len(analysis.relevant_papers) >= 1
        assert analysis.heritage_analysis != ""

    @patch('interactive_paper_reading.analyzer.PaperAnalyzer.call_llm')
    def test_analyze_paper_with_tei(self, mock_call_llm, analyzer, sample_markdown, sample_tei_xml, mock_llm_response):
        """Test paper analysis with TEI file."""
        mock_call_llm.return_value = mock_llm_response

        with patch('builtins.open', mock_open(read_data=sample_markdown)):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(analyzer, 'extract_references_from_tei') as mock_extract:
                    mock_extract.return_value = [
                        Reference("ref1", "Test", ["Author"], "2020")
                    ]
                    
                    analysis = analyzer.analyze_paper(Path('test.md'), Path('test.xml'))

        assert isinstance(analysis, PaperAnalysis)
        mock_extract.assert_called_once()

    def test_analyze_paper_file_not_found(self, analyzer):
        """Test paper analysis with non-existent markdown file."""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Markdown file not found"):
                analyzer.analyze_paper(Path('nonexistent.md'))

    @patch('interactive_paper_reading.analyzer.PaperAnalyzer.call_llm')
    def test_analyze_paper_invalid_json_response(self, mock_call_llm, analyzer, sample_markdown):
        """Test paper analysis with invalid JSON response from LLM."""
        mock_call_llm.return_value = "Invalid JSON response"

        with patch('builtins.open', mock_open(read_data=sample_markdown)):
            with patch.object(Path, 'exists', return_value=True):
                analysis = analyzer.analyze_paper(Path('test.md'))

        # Should return basic analysis with raw response in heritage_analysis
        assert isinstance(analysis, PaperAnalysis)
        assert "Invalid JSON response" in analysis.heritage_analysis
        assert analysis.relevant_papers == []

    def test_save_analysis(self, analyzer):
        """Test saving analysis to file."""
        analysis = PaperAnalysis(
            paper_title="Test Paper",
            relevant_papers=[{"reference": "Test", "reasoning": "Test"}],
            heritage_analysis="Test heritage",
            key_contributions=["Contribution 1"],
            research_gaps=["Gap 1"],
            methodology_insights="Test insights"
        )

        with patch('builtins.open', mock_open()) as mock_file:
            analyzer.save_analysis(analysis, Path('output.json'))

        mock_file.assert_called_once_with(Path('output.json'), 'w', encoding='utf-8')

    def test_print_analysis_summary(self, analyzer, capsys):
        """Test printing analysis summary."""
        analysis = PaperAnalysis(
            paper_title="Test Paper",
            relevant_papers=[{
                "reference": "Test Reference",
                "similarity_reasoning": "Test reasoning",
                "relevance_score": "High"
            }],
            heritage_analysis="Test heritage analysis",
            key_contributions=["Contribution 1", "Contribution 2"],
            research_gaps=["Gap 1"],
            methodology_insights="Test methodology insights"
        )

        analyzer.print_analysis_summary(analysis)
        
        captured = capsys.readouterr()
        assert "PAPER ANALYSIS: Test Paper" in captured.out
        assert "TOP 3 RELEVANT PAPERS:" in captured.out
        assert "Test Reference" in captured.out
        assert "HERITAGE ANALYSIS:" in captured.out
        assert "KEY CONTRIBUTIONS:" in captured.out
        assert "RESEARCH GAPS ADDRESSED:" in captured.out
        assert "METHODOLOGY INSIGHTS:" in captured.out


class TestReference:
    """Test cases for Reference data class."""

    def test_reference_creation(self):
        """Test Reference object creation."""
        ref = Reference(
            id="ref1",
            title="Test Paper",
            authors=["Author One", "Author Two"],
            year="2020",
            venue="Test Journal",
            full_text="Full citation text"
        )
        
        assert ref.id == "ref1"
        assert ref.title == "Test Paper"
        assert ref.authors == ["Author One", "Author Two"]
        assert ref.year == "2020"
        assert ref.venue == "Test Journal"
        assert ref.full_text == "Full citation text"

    def test_reference_creation_minimal(self):
        """Test Reference creation with minimal required fields."""
        ref = Reference(
            id="ref1",
            title="Test Paper",
            authors=["Author One"]
        )
        
        assert ref.id == "ref1"
        assert ref.title == "Test Paper"
        assert ref.authors == ["Author One"]
        assert ref.year is None
        assert ref.venue is None
        assert ref.full_text is None


class TestPaperAnalysis:
    """Test cases for PaperAnalysis data class."""

    def test_paper_analysis_creation(self):
        """Test PaperAnalysis object creation."""
        analysis = PaperAnalysis(
            paper_title="Test Paper",
            relevant_papers=[{"ref": "test"}],
            heritage_analysis="Heritage text",
            key_contributions=["Contribution 1"],
            research_gaps=["Gap 1"],
            methodology_insights="Methodology text"
        )
        
        assert analysis.paper_title == "Test Paper"
        assert analysis.relevant_papers == [{"ref": "test"}]
        assert analysis.heritage_analysis == "Heritage text"
        assert analysis.key_contributions == ["Contribution 1"]
        assert analysis.research_gaps == ["Gap 1"]
        assert analysis.methodology_insights == "Methodology text"
