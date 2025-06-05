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
        pass

    def validate_file(self) -> bool:
        if not os.path.exists(self.file_path) or not self.file_path.lower().endswith('.pdf'):
            return False
        return True
