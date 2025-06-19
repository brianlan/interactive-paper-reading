"""
Interactive Paper Reading Library

A comprehensive library for processing academic papers using GROBID,
extracting structured content, and analyzing papers with LLM.
"""

__version__ = "1.0.0"
__author__ = "Interactive Paper Reading Team"

from .grobid import GrobidProcessor
from .tei import TEIProcessor, Section, FigureTable, Graphic
from .analyzer import PaperAnalyzer, Reference, PaperAnalysis
from .pipeline import PaperProcessingPipeline
from .processor import AcademicPaperProcessor

__all__ = [
    "GrobidProcessor",
    "TEIProcessor", 
    "Section",
    "FigureTable", 
    "Graphic",
    "PaperAnalyzer",
    "Reference",
    "PaperAnalysis", 
    "PaperProcessingPipeline",
    "AcademicPaperProcessor"
]
