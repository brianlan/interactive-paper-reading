"""
TEI XML processor for extracting sections and figures from GROBID output.

This module provides functionality to:
1. Extract document sections with hierarchical numbering
2. Extract figures and tables with PDF coordinates
3. Save sections as markdown
4. Crop figures/tables from PDF using coordinates
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import xml.etree.ElementTree as ET


@dataclass
class Section:
    """Represents a document section with number, title, and content."""
    
    number: str
    title: str
    content: str
    
    def to_markdown(self) -> str:
        """Convert section to markdown format."""
        level = self.number.count('.') + 2  # Start with ## for top-level sections
        header_prefix = '#' * level
        
        return f"{header_prefix} {self.number} {self.title}\n\n{self.content}\n\n"


@dataclass
class FigureTable:
    """Represents a figure or table with coordinates."""
    
    element_type: str  # 'figure' or 'table'
    caption: str
    page: int
    x: float
    y: float
    width: float
    height: float
    
    @property
    def coordinates(self) -> Tuple[float, float, float, float]:
        """Return coordinates as (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class Graphic:
    """Represents a graphic element with coordinates."""
    
    graphic_type: str  # 'bitmap', 'vector', etc.
    page: int
    x: float
    y: float
    width: float
    height: float
    parent_figure_caption: str = ""  # Caption from parent figure if available
    
    @property
    def coordinates(self) -> Tuple[float, float, float, float]:
        """Return coordinates as (x, y, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)


class TEIProcessor:
    """Processes TEI XML files from GROBID to extract structured content."""
    
    def __init__(self):
        """Initialize the TEI processor."""
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    def extract_sections(self, tei_file_path: Path) -> List[Section]:
        """
        Extract all document sections from TEI XML file.
        
        Args:
            tei_file_path: Path to the TEI XML file
            
        Returns:
            List of Section objects ordered by document structure
            
        Raises:
            FileNotFoundError: If the TEI file doesn't exist
        """
        try:
            with open(tei_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"TEI file not found: {tei_file_path}")
        
        root = ET.fromstring(content)
        sections = []
        
        # Find all div elements that contain sections
        for div in root.findall('.//tei:div', self.namespaces):
            section = self._extract_section_from_div(div)
            if section:
                sections.append(section)
        
        return sections
    
    def extract_figures_tables(self, tei_file_path: Path) -> List[FigureTable]:
        """
        Extract all figures and tables with coordinates from TEI XML file.
        
        Args:
            tei_file_path: Path to the TEI XML file
            
        Returns:
            List of FigureTable objects with coordinate information
            
        Raises:
            FileNotFoundError: If the TEI file doesn't exist
        """
        try:
            with open(tei_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"TEI file not found: {tei_file_path}")
        
        root = ET.fromstring(content)
        figures_tables = []
        
        # Find all figure elements
        for figure in root.findall('.//tei:figure', self.namespaces):
            fig_table = self._extract_figure_table_from_element(figure, 'figure')
            if fig_table:
                figures_tables.append(fig_table)
        
        # Find all table elements  
        for table in root.findall('.//tei:table', self.namespaces):
            fig_table = self._extract_figure_table_from_element(table, 'table')
            if fig_table:
                figures_tables.append(fig_table)
        
        return figures_tables
    
    def save_sections_as_markdown(self, sections: List[Section], output_path: Path) -> None:
        """
        Save extracted sections as a markdown file.
        
        Args:
            sections: List of Section objects to save
            output_path: Path where to save the markdown file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for section in sections:
                f.write(section.to_markdown())
    
    def crop_figure_from_pdf(
        self, 
        figure: FigureTable, 
        pdf_path: Path, 
        output_path: Path
    ) -> None:
        """
        Crop a figure or table from PDF using coordinates.
        
        Args:
            figure: FigureTable object with coordinates
            pdf_path: Path to the source PDF file
            output_path: Path where to save the cropped image
        """
        self._crop_pdf_region(
            pdf_path=pdf_path,
            page=figure.page,
            coordinates=figure.coordinates,
            output_path=output_path
        )
    
    def extract_graphics(self, tei_file_path: Path) -> List[Graphic]:
        """
        Extract all graphic elements with coordinates from TEI XML file.
        
        Args:
            tei_file_path: Path to the TEI XML file
            
        Returns:
            List of Graphic objects with coordinate information
            
        Raises:
            FileNotFoundError: If the TEI file doesn't exist
        """
        try:
            with open(tei_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"TEI file not found: {tei_file_path}")
        
        root = ET.fromstring(content)
        graphics = []
        
        # Find all figure elements and extract graphics from them
        for figure in root.findall('.//tei:figure', self.namespaces):
            # Get figure caption first
            head = figure.find('./tei:head', self.namespaces)
            figdesc = figure.find('./tei:figDesc', self.namespaces)
            
            caption_parts = []
            if head is not None:
                caption_parts.append(self._get_element_text(head))
            if figdesc is not None:
                caption_parts.append(self._get_element_text(figdesc))
            
            figure_caption = ' '.join(caption_parts).strip()
            
            # Find graphics within this figure
            for graphic in figure.findall('./tei:graphic', self.namespaces):
                graphic_obj = self._extract_graphic_from_element(graphic, figure_caption)
                if graphic_obj:
                    graphics.append(graphic_obj)
        
        return graphics

    def crop_graphic_from_pdf(
        self, 
        graphic: Graphic, 
        pdf_path: Path, 
        output_path: Path
    ) -> None:
        """
        Crop a graphic from PDF using coordinates.
        
        Args:
            graphic: Graphic object with coordinates
            pdf_path: Path to the source PDF file
            output_path: Path where to save the cropped image
        """
        self._crop_pdf_region(
            pdf_path=pdf_path,
            page=graphic.page,
            coordinates=graphic.coordinates,
            output_path=output_path
        )

    def _extract_section_from_div(self, div_element: ET.Element) -> Optional[Section]:
        """Extract section information from a div element."""
        # Find the head element for section title and number
        head = div_element.find('./tei:head', self.namespaces)
        if head is None:
            return None
        
        # Extract section number and title
        section_number = head.get('n', '')
        section_title = self._get_element_text(head).replace(section_number, '').strip()
        
        # Extract all paragraph content
        paragraphs = div_element.findall('.//tei:p', self.namespaces)
        content_parts = []
        
        for p in paragraphs:
            paragraph_text = self._get_element_text(p)
            if paragraph_text.strip():
                content_parts.append(paragraph_text.strip())
        
        content = '\n\n'.join(content_parts)
        
        if section_number and section_title:
            return Section(section_number, section_title, content)
        
        return None
    
    def _extract_figure_table_from_element(
        self, 
        element: ET.Element, 
        element_type: str
    ) -> Optional[FigureTable]:
        """Extract figure/table information from an element."""
        coords_attr = element.get('coords')
        if not coords_attr:
            return None
        
        # Parse coordinates: "page,x,y,width,height"
        try:
            coords = self._parse_coordinates(coords_attr)
            if not coords:
                return None
            
            page, x, y, width, height = coords
        except (ValueError, TypeError):
            return None
        
        # Extract caption
        head = element.find('./tei:head', self.namespaces)
        figdesc = element.find('./tei:figDesc', self.namespaces)
        
        caption_parts = []
        if head is not None:
            caption_parts.append(self._get_element_text(head))
        if figdesc is not None:
            caption_parts.append(self._get_element_text(figdesc))
        
        caption = ' '.join(caption_parts).strip()
        
        return FigureTable(
            element_type=element_type,
            caption=caption,
            page=page,
            x=x,
            y=y,
            width=width,
            height=height
        )
    
    def _parse_coordinates(self, coords_str: str) -> Optional[Tuple[int, float, float, float, float]]:
        """
        Parse coordinate string from GROBID TEI format.
        
        Format: "page,x,y,width,height" or multiple boxes separated by semicolons.
        Returns the first bounding box.
        """
        if not coords_str:
            return None
        
        # Take first bounding box if multiple exist (separated by semicolons)
        first_box = coords_str.split(';')[0]
        
        try:
            parts = first_box.split(',')
            if len(parts) >= 5:
                page = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                return (page, x, y, width, height)
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _get_element_text(self, element: ET.Element) -> str:
        """Extract all text content from an element, including nested elements."""
        if element.text:
            text = element.text
        else:
            text = ''
        
        for child in element:
            text += self._get_element_text(child)
            if child.tail:
                text += child.tail
        
        return text.strip()
    
    def _crop_pdf_region(
        self,
        pdf_path: Path,
        page: int,
        coordinates: Tuple[float, float, float, float],
        output_path: Path
    ) -> None:
        """
        Crop a region from PDF page and save as image.
        
        This method uses PyMuPDF (fitz) to extract the region.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF cropping. Install with: pip install PyMuPDF"
            )
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        x, y, width, height = coordinates
        
        # Open PDF
        doc = fitz.open(str(pdf_path))
        
        try:
            # Get the page (GROBID uses 1-based page numbers)
            page_obj = doc[page - 1]
            
            # Create rectangle for cropping
            # Note: fitz uses (x0, y0, x1, y1) format
            rect = fitz.Rect(x, y, x + width, y + height)
            
            # Get the pixmap (image) of the cropped region
            mat = fitz.Matrix(2.0, 2.0)  # 2x scaling for better quality
            pix = page_obj.get_pixmap(matrix=mat, clip=rect)
            
            # Save as PNG
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pix.save(str(output_path))
            
        finally:
            doc.close()
    
    def _extract_graphic_from_element(self, element: ET.Element, figure_caption: str = "") -> Optional[Graphic]:
        """Extract graphic information from a graphic element."""
        coords_attr = element.get('coords')
        graphic_type = element.get('type', 'unknown')
        
        if not coords_attr:
            return None
        
        # Parse coordinates: "page,x,y,width,height"
        try:
            coords = self._parse_coordinates(coords_attr)
            if not coords:
                return None
            
            page, x, y, width, height = coords
        except (ValueError, TypeError):
            return None
        
        # Try to get caption from parent figure if available
        # Note: We'll search for the figure that contains this graphic later
        parent_caption = figure_caption
        
        return Graphic(
            graphic_type=graphic_type,
            page=page,
            x=x,
            y=y,
            width=width,
            height=height,
            parent_figure_caption=parent_caption
        )
