import io
import re
from typing import Optional
from pypdf import PdfReader


class ParserService:
    """Service to parse resume and syllabus documents from PDF or plain text."""

    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
        """Extract all textual content from a PDF byte payload using pypdf."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            raw_text = "\n".join(text_parts)
            return ParserService.clean_text(raw_text)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document: {str(e)}")

    @staticmethod
    def clean_text(text: str) -> str:
        """Sanitizes text by collapsing extra whitespace, fixing line breaks, and stripping control chars."""
        if not text:
            return ""
        # Remove null bytes or non-printable chars
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Normalize newlines
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Replace multiple spaces with single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace 3 or more newlines with 2 newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def parse_input(file_bytes: Optional[bytes] = None, raw_text: Optional[str] = None, filename: Optional[str] = None) -> str:
        """Unified parser method accommodating PDF file upload or direct text input."""
        if file_bytes:
            if filename and filename.lower().endswith(".pdf"):
                return ParserService.extract_text_from_pdf_bytes(file_bytes)
            else:
                # Attempt to decode as UTF-8 or latin-1
                try:
                    return ParserService.clean_text(file_bytes.decode("utf-8"))
                except UnicodeDecodeError:
                    return ParserService.clean_text(file_bytes.decode("latin-1", errors="ignore"))
        elif raw_text:
            return ParserService.clean_text(raw_text)
        else:
            return ""
