# Academic Paper Processing Pipeline

This directory contains a complete workflow for processing academic paper PDFs using GROBID and extracting structured content (sections, figures, tables, graphics) from TEI XML.

## Features

- **Complete Pipeline**: PDF → TEI XML → Structured Content
- **Section Extraction**: Export document sections as markdown
- **Figure/Table Extraction**: Crop and save figures/tables as images
- **Graphics Extraction**: Precise extraction of graphic elements within figures
- **Multi-segment Coordinate Support**: Handles complex coordinate parsing
- **Concurrent Processing**: Multiple PDFs processed in parallel

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start GROBID Server

You need a running GROBID server. The easiest way is with Docker:

```bash
# Start GROBID server (this may take a few minutes on first run)
docker run --rm -it -p 8070:8070 lfoppiano/grobid:0.8.0
```

Keep this terminal running. The server will be available at `http://localhost:8070`.

### 3. Process Academic Papers

**Complete Pipeline (Recommended):**
```bash
# Process PDF to TEI, then extract all content
python scripts/process_academic_paper.py path/to/your/paper.pdf

# Custom output directory
python scripts/process_academic_paper.py paper.pdf --output-dir custom/output
```

**Individual Steps:**
```bash
# Step 1: PDF → TEI XML only
python scripts/grobid_processor.py path/to/your/paper.pdf

# Step 2: TEI → Content extraction only
python scripts/process_academic_paper.py --tei-only existing.tei.xml --pdf paper.pdf
```

## Usage Examples

### Complete Pipeline Examples
```bash
# Basic processing: PDF → TEI → Markdown + Images
python scripts/process_academic_paper.py papers/bev/paper.pdf

# Custom GROBID server and output directory
python scripts/process_academic_paper.py paper.pdf \
  --grobid-server http://10.243.123.49:8070 \
  --output-dir processed_papers/

# Process existing TEI file only
python scripts/process_academic_paper.py --tei-only existing.tei.xml

# Process TEI with specific PDF for image cropping
python scripts/process_academic_paper.py --tei-only paper.tei.xml --pdf original.pdf
```

### Advanced GROBID Processing
```bash
# Direct GROBID processing with custom options
python scripts/grobid_processor.py papers/bev/paper.pdf \
  --consolidate-header \
  --consolidate-citations \
  --segment-sentences \
  -n 5

# Batch processing of multiple PDFs
python scripts/grobid_processor.py papers/ -o tei_output/
```

## Output

### Complete Pipeline Output
The complete pipeline generates:
- **TEI XML**: Structured document in TEI format (`.grobid.tei.xml`)
- **Markdown**: Document sections as markdown (`.md`)
- **Figures**: Cropped figure/table images (`.png`)
- **Graphics**: Precise graphic element images (`.png`)

Example output structure:
```
processed_output/
├── paper.grobid.tei.xml          # TEI XML from GROBID
├── paper_sections.md             # Extracted sections
├── figures/                      # Cropped figures and tables
│   ├── figure_1_network_arch.png
│   ├── table_1_results.png
│   └── ...
└── graphics/                     # Precise graphic elements
    ├── graphic_1_diagram.png
    ├── graphic_2_flowchart.png
    └── ...
```

### TEI XML Content
TEI files contain:
- Document structure (title, abstract, sections, etc.)
- Bibliographical references
- Figures and tables metadata
- PDF coordinates for all elements
- Graphics and visual element locations

## Scripts Overview

- **`process_academic_paper.py`** - 🚀 **Main script**: Complete pipeline from PDF to structured content
- **`grobid_processor.py`** - GROBID integration for PDF → TEI XML conversion
- **`tei_processor.py`** - TEI XML parsing and content extraction library
- **`process_paper.py`** - Example script for PDF → TEI processing
- **`process_tei_output.py`** - Example script for TEI → content extraction

## Configuration Options

### GROBID Processing Options
- `--server`: GROBID server URL (default: `http://localhost:8070`)
- `--workers`: Number of concurrent workers (default: 10)
- `--no-coordinates`: Disable PDF coordinate extraction
- `--consolidate-header`: Enhance header metadata with external sources
- `--consolidate-citations`: Enhance bibliographical references
- `--generate-ids`: Add XML IDs to elements
- `--segment-sentences`: Add sentence boundaries

### Pipeline Options
- `--output-dir`: Custom output directory
- `--tei-only`: Process existing TEI file only (skip GROBID)
- `--pdf`: Specify PDF file for image cropping (with `--tei-only`)
- `--grobid-server`: Custom GROBID server URL

## Troubleshooting

### GROBID Server Issues
- Ensure Docker is running
- Check if port 8070 is available
- Wait a few minutes for the server to fully start

### Memory Issues
- Reduce number of workers with `-n` parameter
- Process PDFs in smaller batches

### Large Files
- GROBID works best with academic papers (typically under 50 pages)
- Very large PDFs may timeout - adjust timeout in config if needed

## Next Steps

After processing, you can:
1. **Analyze extracted content**: Use the markdown files and cropped images
2. **Build search indices**: Index the structured document content
3. **Create visualizations**: Use coordinate data for interactive document viewers
4. **Develop annotations**: Build annotation tools using document structure
5. **Compare papers**: Analyze multiple papers using standardized outputs

## Testing

The processing pipeline includes comprehensive unit tests:

```bash
# Run all tests
pytest tests/

# Run tests with coverage
pytest --cov=scripts tests/

# View HTML coverage report
pytest --cov=scripts --cov-report=html tests/
open htmlcov/index.html
```
