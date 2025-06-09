import io
from typing import Dict, Any
from typing import List
import PyPDF2
from utils import preprocess_image, extract_tables_from_page_text, ocr_text_with_paragraphs
import fitz
from readers.pdf_type import PDFType
from readers.abstracts.reader import Reader
from PIL import Image


class ScannedPDFReader(Reader):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.pdf_type = PDFType.SCANNED_IMAGE
        self.ocr_config = '--oem 3 --psm 6'

    def read_content(self) -> Dict[str, Any]:
        """
            This function reads content from scanned PDFs. Because of the file is scanned, this function performs OCR.
            :return: A dictionary containing data read from a file
        """
        if not self.validate_file():
            return {
                'success': False,
                'error': 'Invalid file'
            }

        try:
            images = self._pdf_to_images()
            pages_content = []
            full_text = ""

            for page_number, image in enumerate(images):
                processed_image = preprocess_image(image)
                page_text = ocr_text_with_paragraphs(processed_image, ocr_config=self.ocr_config)

                # Grouping the page
                tables = extract_tables_from_page_text(page_text)

                pages_content.append({
                    "page_number": page_number + 1,
                    "text": page_text,
                    "tables": tables,
                    "method": "ocr_tesseract"
                })

                full_text += page_text + "\n"

            return {
                "success": True,
                'filename': self.file_path,
                "pdf_type": self.pdf_type.value,
                "content": {
                    "text": full_text,
                    "pages": pages_content,
                    "pages_count": len(images),
                    "method": "ocr_tesseract"
                }
            }
        except Exception as e:
            print(f"OCR reading error: {e}")
            return {"success": False, "error": str(e)}

    def _pdf_to_images(self) -> List[Image.Image]:
        """
        This function converts scanned PDFs to images. The function uses Fitz library for convertion.
        :return: Images of all pages
        """
        images: List[Image.Image] = []
        try:
            document = fitz.open(self.file_path)

            for page_number in range(len(document)):
                page = document.load_page(page_number)

                mat = fitz.Matrix(2, 2)     # x2 Zoom setting
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")

                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            document.close()
        except Exception as e:
            print(f"PDF to image conversion error: {e}")
            images = self._pdf_to_images_alternative()

        return images

    def _pdf_to_images_alternative(self) -> List[Image.Image]:
        """
        This function is an alternative for converting PDFs to image format. The function uses PDF2Image library for convertion.
        :return: Images of all pages
        """
        images = []

        try:
            from pdf2image import convert_from_path

            pil_images = convert_from_path(
                self.file_path,
                dpi=200,
                fmt='RGB'
            )

            images.extend(pil_images)
        except ImportError:
            try:
                with open(self.file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(pdf_reader.pages)):
                        white_page = Image.new('RGB', (2480, 3508), 'white')
                        images.append(white_page)
            except Exception as e:
                print(f"Alternative PDF conversion error: {e}")

        except Exception as e:
            print(f"pdf2image conversion error: {e}")
        return images
