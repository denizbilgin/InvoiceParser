from PIL import Image
from readers.pdf_type import PDFType
from readers.text_based_pdf_reader import TextBasedPDFReader
from readers.scanned_pdf_reader import ScannedPDFReader
from readers.reader import Reader
from utils import detect_pdf_type


class ReaderFactory:
    @staticmethod
    def _check_tesseract() -> bool:
        try:
            import pytesseract
            pytesseract.image_to_string(Image.new('RGB', (100, 30), color = 'white'))
            return True
        except Exception:
            return False

    @staticmethod
    def create_reader(file_path: str) -> Reader:
        text_reader = TextBasedPDFReader(file_path)
        detected_file_type = detect_pdf_type(file_path)

        if detected_file_type == PDFType.TEXT_BASED:
            return text_reader
        else:
            if ReaderFactory._check_tesseract():
                return ScannedPDFReader(file_path)
            else:
                print(f"Tesseract not found. Using text-based reader: {file_path}")
                print("Tesseract installation is required for OCR feature.")
                return text_reader
