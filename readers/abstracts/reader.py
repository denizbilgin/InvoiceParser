import os
from abc import ABC, abstractmethod
from typing import Dict, Any
from readers.pdf_type import PDFType


class Reader(ABC):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pdf_type: PDFType | None = None
        self.raw_text = ''
        self.pages_content = []

    @abstractmethod
    def read_content(self) -> Dict[str, Any]:
        """
        This function reads content from native or scanned PDFs. If the file is scanned, this function performs OCR.
        :return: A dictionary containing data read from a file
        """
        pass

    def validate_file(self) -> bool:
        """
        This function checks if the file is PDF.
        :return: If it is PDF it returns True, otherwise it returns False.
        """
        if not os.path.exists(self.file_path) or not self.file_path.lower().endswith('.pdf'):
            return False
        return True
