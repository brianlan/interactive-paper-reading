# GROBID PDF Processing Setup

This directory contains scripts for processing PDF files with GROBID to extract structured text in TEI format.

## Features

The GROBID processor provides:
- **TEI format output**: Standard XML format for scholarly documents
- **Fulltext processing**: Complete document structure extraction  
- **PDF coordinates**: Bounding box coordinates for all extracted elements
- **Concurrent processing**: Multiple PDFs processed in parallel

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

### 3. Process PDF Files

```bash
# Check if GROBID server is running
python scripts/grobid_processor.py --check-server

# Process a single PDF
python scripts/grobid_processor.py path/to/your/paper.pdf

# Process with custom output directory
python scripts/grobid_processor.py path/to/your/paper.pdf -o output/directory

# Process directory of PDFs
python scripts/grobid_processor.py path/to/pdf/directory/
```

## Usage Examples

### Basic Processing (with coordinates)
```bash
python scripts/grobid_processor.py papers/bev/blos-bev/blos-bev.pdf
```

### Advanced Processing
```bash
python scripts/grobid_processor.py papers/bev/blos-bev/blos-bev.pdf \
  --consolidate-header \
  --consolidate-citations \
  --segment-sentences \
  -n 5
```

### Batch Processing
```bash
# Process all PDFs in a directory
python scripts/grobid_processor.py papers/ -o tei_output/
```

## Output

The processor generates TEI XML files with the `.grobid.tei.xml` extension. These files contain:

- Document structure (title, abstract, sections, etc.)
- Bibliographical references
- Figures and tables metadata
- PDF coordinates for all elements (when `--coordinates` is enabled)

## Configuration Options

- `--server`: GROBID server URL (default: `http://localhost:8070`)
- `--workers`: Number of concurrent workers (default: 10)
- `--no-coordinates`: Disable PDF coordinate extraction
- `--consolidate-header`: Enhance header metadata with external sources
- `--consolidate-citations`: Enhance bibliographical references
- `--generate-ids`: Add XML IDs to elements
- `--segment-sentences`: Add sentence boundaries

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
1. Parse the TEI XML files to extract specific information
2. Build search indices from the structured content
3. Create interactive visualizations using the coordinate data
4. Develop annotation tools leveraging the document structure
