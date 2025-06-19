# Academic Paper Processing CLI Scripts

This directory contains **command-line interface (CLI) scripts** for processing academic papers. All core logic has been moved to the `interactive_paper_reading` package, making these scripts lightweight CLI wrappers.

## 🏗️ Architecture

### Package Structure
- **`interactive_paper_reading/`** - Core reusable library with all business logic
- **`scripts/`** - CLI scripts using argparse for user interaction

### Core Components (in `interactive_paper_reading` package)
1. **`GrobidProcessor`** - PDF to TEI XML conversion
2. **`TEIProcessor`** - Extract sections, figures, graphics from TEI
3. **`PaperAnalyzer`** - LLM-based paper analysis
4. **`PaperProcessingPipeline`** - Comprehensive end-to-end pipeline
5. **`AcademicPaperProcessor`** - Simplified pipeline wrapper

## 🧰 CLI Scripts

### 1. Comprehensive Pipeline (`comprehensive_pipeline.py`)
Complete end-to-end processing with batch support
```bash
python comprehensive_pipeline.py paper.pdf --output ./output --analyze
```

### 2. Academic Paper Processor (`process_academic_paper.py`)  
Simplified pipeline for basic processing
```bash
python process_academic_paper.py paper.pdf --output-dir ./output
```

### 3. GROBID Processor (`grobid_processor.py`)
PDF to TEI conversion only
```bash
python grobid_processor.py paper.pdf --output output.tei.xml
```

### 4. TEI Processor (`tei_processor.py`)
Extract content from existing TEI files
```bash
python tei_processor.py paper.tei.xml --all --pdf paper.pdf --output-dir ./output
```

### 5. Paper Analyzer (`paper_analyzer.py`)
LLM-based analysis of processed papers
```bash
python paper_analyzer.py sections.md --tei paper.tei.xml --output analysis.json
```

### 6. Example Scripts
- **`process_paper.py`** - Simple GROBID processing example
- **`process_tei_output.py`** - TEI extraction example

## 🚀 Usage Examples

### Quick Start
```bash
# Process a single paper with full analysis
python comprehensive_pipeline.py paper.pdf --output ./output --analyze

# Batch process multiple papers
python comprehensive_pipeline.py ./papers/*.pdf --output ./batch_output --batch

# Extract only sections (skip figures/graphics)
python comprehensive_pipeline.py paper.pdf --output ./output --no-figures --no-graphics
```

### Individual Components

#### GROBID Processing
```bash
python grobid_processor.py input.pdf output.tei.xml --url http://localhost:8070
```

#### TEI Content Extraction
```bash
python tei_processor.py input.tei.xml --output-dir ./output --pdf input.pdf
```

#### Paper Analysis
```bash
python paper_analyzer.py sections.md --tei paper.tei.xml --output analysis.json
```

## 📋 Prerequisites

### Required Dependencies
```bash
pip install requests lxml PyMuPDF pathlib
```

### GROBID Service
Start GROBID service locally:
```bash
docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
```

### LLM Analysis (Optional)
Set environment variables for LLM analysis:
```bash
export OPENAI_ACCESS_TOKEN="your-api-token"
export OPENAI_ENDPOINT="https://api.openai.com/v1"  # optional
export OPENAI_MODEL="gpt-4"  # optional
```

## 🔧 Configuration Options

### GROBID Processing
- `--url`: GROBID service URL (default: http://localhost:8070)
- `--timeout`: Request timeout in seconds
- `--consolidate-citations`: Enable citation consolidation

### TEI Processing  
- `--output-dir`: Directory for extracted content
- `--pdf`: Original PDF file for figure/graphic extraction
- `--extract-figures`: Extract figures and tables (default: true)
- `--extract-graphics`: Extract graphics (default: true)

### Paper Analysis
- `--tei`: TEI XML file for reference extraction
- `--output`: Save analysis results to JSON file
- `--endpoint`: Custom LLM API endpoint
- `--model`: LLM model name
- `--verbose`: Enable detailed logging

### Comprehensive Pipeline
- `--analyze`: Enable LLM analysis
- `--batch`: Batch processing mode
- `--no-figures`: Skip figure extraction
- `--no-graphics`: Skip graphics extraction
- `--quiet`: Suppress non-error output

## 📊 Output Structure

For each processed paper, the pipeline creates:
```
output/
├── paper-name.grobid.tei.xml          # TEI XML from GROBID
├── paper-name-sections.md             # Extracted sections in markdown
├── paper-name-figure-1.png           # Cropped figures/tables
├── paper-name-graphic-1.png          # Cropped graphics  
└── paper-name-analysis.json          # LLM analysis (if enabled)
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=scripts --cov-report=term-missing

# Specific component tests
python -m pytest tests/test_tei_processor.py -v
python -m pytest tests/test_paper_analyzer.py -v
```

Current test coverage:
- `tei_processor.py`: 96% (31 tests)
- `paper_analyzer.py`: 71% (22 tests)  
- Total: 53 tests passing

## 🔍 Advanced Features

### Multi-segment Coordinate Handling
The TEI processor automatically combines multi-segment coordinates (semicolon-separated) into a single bounding box for accurate figure cropping.

### Robust LLM Response Parsing  
The paper analyzer handles various LLM response formats:
- JSON wrapped in markdown code blocks
- Plain JSON responses
- Malformed responses with fallback parsing

### Enhanced Error Handling
- Detailed logging with configurable levels
- Graceful degradation when components fail
- Comprehensive error reporting in batch mode

### Reference Extraction
- Primary: Structured references from TEI XML
- Fallback: Citation patterns from markdown content
- Supports multiple reference formats and venues

## 🐛 Troubleshooting

### Common Issues

1. **GROBID Connection Error**
   ```
   Ensure GROBID service is running on specified port
   Check firewall/network connectivity
   ```

2. **Figure Extraction Fails**
   ```
   Verify PyMuPDF is installed: pip install PyMuPDF
   Check PDF file permissions and corruption
   ```

3. **LLM Analysis Fails**
   ```
   Verify API token is set correctly
   Check API endpoint and model availability
   Monitor rate limits and quota
   ```

4. **Out of Memory**
   ```
   Process papers individually instead of batch
   Reduce LLM max_tokens parameter
   Use lower resolution for figure extraction
   ```

## 📈 Performance Tips

- Use batch processing for multiple papers
- Enable parallel processing with `--batch` flag
- Skip unnecessary extractions with `--no-figures` or `--no-graphics`
- Use local GROBID instance for better performance
- Cache TEI files to avoid reprocessing

## 🔄 Pipeline Integration

The scripts are designed to work together in a modular pipeline:

1. **PDF → TEI**: `grobid_processor.py`
2. **TEI → Content**: `tei_processor.py` 
3. **Content → Analysis**: `paper_analyzer.py`
4. **All-in-One**: `comprehensive_pipeline.py`

Each component can be used independently or as part of the complete workflow.
