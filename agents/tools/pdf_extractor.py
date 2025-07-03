import pdfplumber
from pypdf import PdfReader
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

def extract_script_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text content from PDF file using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extracted text and metadata
    """
    try:
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_file.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        extracted_text = ""
        page_count = 0
        word_count = 0
        
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract text from page
                    page_text = page.extract_text()
                    
                    if page_text:
                        # Clean up the text
                        page_text = page_text.strip()
                        extracted_text += f"\n--- PAGE {page_num} ---\n{page_text}\n"
                        
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
        
        # Calculate word count
        if extracted_text:
            word_count = len(extracted_text.split())
        
        # Clean up the final text
        extracted_text = extracted_text.strip()
        
        return {
            "success": True,
            "extracted_text": extracted_text,
            "page_count": page_count,
            "word_count": word_count,
            "file_path": str(pdf_file.absolute()),
            "file_size_mb": round(pdf_file.stat().st_size / (1024 * 1024), 2)
        }
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return {
            "success": False,
            "error": str(e),
            "extracted_text": "",
            "page_count": 0,
            "word_count": 0
        }
        
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        return {
            "success": False,
            "error": str(e),
            "extracted_text": "",
            "page_count": 0,
            "word_count": 0
        }

def extract_script_with_formatting(pdf_path: str) -> Dict[str, Any]:
    """Enhanced extraction for script analysis."""
    try:
        extracted_data = {
            "success": True,
            "extracted_text": "",
            "scenes": [],
            "page_count": 0,
            "word_count": 0,
            "formatting_preserved": True
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            extracted_data["page_count"] = len(pdf.pages)
            full_text = ""
            
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract with better layout preservation
                    page_text = page.extract_text(
                        layout=True, 
                        x_tolerance=2, 
                        y_tolerance=2,
                        keep_blank_chars=True
                    )
                    
                    if page_text:
                        # Clean up common PDF artifacts
                        page_text = re.sub(r'\n\s*\n\s*\n', '\n\n', page_text)  # Multiple newlines
                        page_text = re.sub(r'^\s*\d+\s*$', '', page_text, flags=re.MULTILINE)  # Page numbers
                        
                        full_text += f"{page_text}\n"
                        
                except Exception as e:
                    logger.warning(f"Error processing page {page_num}: {e}")
                    continue
            
            extracted_data["extracted_text"] = full_text.strip()
            extracted_data["word_count"] = len(full_text.split()) if full_text else 0
            
        return extracted_data
        
    except Exception as e:
        logger.error(f"Enhanced extraction failed: {e}")
        return extract_script_from_pdf(pdf_path)

# Alternative using pypdf for comparison
def extract_with_pypdf(pdf_path: str) -> Dict[str, Any]:
    """
    Alternative extraction using pypdf (formerly PyPDF2).
    Use this if pdfplumber has issues with specific PDFs.
    """
    try:
        reader = PdfReader(pdf_path)
        extracted_text = ""
        page_count = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"\n--- PAGE {page_num} ---\n{page_text}\n"
            except Exception as e:
                logger.warning(f"pypdf: Error extracting page {page_num}: {e}")
                continue
        
        return {
            "success": True,
            "extracted_text": extracted_text.strip(),
            "page_count": page_count,
            "word_count": len(extracted_text.split()) if extracted_text else 0,
            "extraction_method": "pypdf"
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "pypdf not installed. Use: pip install pypdf",
            "extracted_text": "",
            "page_count": 0,
            "word_count": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "extracted_text": "",
            "page_count": 0,
            "word_count": 0
        }