from typing import Dict, Any
import PyPDF2
import pdfplumber
from readers.pdf_type import PDFType
from readers.abstracts.reader import Reader
from utils import extract_tables_from_page_text


class TextBasedPDFReader(Reader):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.pdf_type = PDFType.TEXT_BASED

    def read_content(self) -> Dict[str, Any]:
        """
        This function reads content from native PDFs. Tries 2 PDF reader library, and uses the best one.
        :return: A dictionary containing data read from a file
        """
        if not self.validate_file():
            return {
                'success': False,
                'error': 'Invalid file'
            }

        try:
            # Reading with PyPDF2
            content_pypdf2 = self._read_with_pypdf2()

            # Reading with PDFPlumber
            content_pdfplumber = self._read_with_pdfplumber()

            # Selecting the better one
            final_content = content_pdfplumber if len(content_pdfplumber.get('text', '')) > len(content_pypdf2.get('text', '')) else content_pypdf2

            return {
                "success": True,
                'filename': self.file_path,
                "pdf_type": self.pdf_type.value,
                "content": final_content,
            }
        except Exception as e:
            print(f"PDF reading error: {e}")

    def _read_with_pypdf2(self) -> Dict[str, Any]:
        """
        This function reads content from native PDFs. Uses PyPDF2 for reading PDFs,
        :return: A dictionary containing data read from a file
        """
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages_content = []
                full_text = ""

                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()

                    # Grouping the data
                    tables = extract_tables_from_page_text(page_text)

                    pages_content.append({
                        "page_number": page_num + 1,
                        "text": page_text,
                        "tables": tables,
                        "method": "pypdf2"
                    })
                    full_text += page_text + "\n"

                return {
                    "text": full_text,
                    "pages": pages_content,
                    "pages_count": len(pdf_reader.pages),
                    "method": "pypdf2"
                }

        except Exception as e:
            print(f"PyPDF2 reading error: {e}")
            return {"text": "", "pages": [], "pages_count": 0, "error": str(e)}

    def _read_with_pdfplumber(self) -> Dict[str, Any]:
        """
        This function reads content from native PDFs. Uses PDFPlumber for reading PDFs,
        :return: A dictionary containing data read from a file
        """
        try:
            with pdfplumber.open(self.file_path) as pdf:
                pages_content = []
                full_text = ""

                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""

                    # Grouping the data with built-in function of PDFPlumber
                    tables = page.extract_tables()

                    page_info = {
                        "page_number": page_num + 1,
                        "text": page_text,
                        "tables": tables,
                        "method": "pdfplumber"
                    }

                    pages_content.append(page_info)
                    full_text += page_text + "\n"

                return {
                    "text": full_text,
                    "pages": pages_content,
                    "pages_count": len(pdf.pages),
                    "method": "pdfplumber"
                }

        except Exception as e:
            print(f"pdfplumber reading error: {e}")
            return {"text": "", "pages": [], "pages_count": 0, "error": str(e)}