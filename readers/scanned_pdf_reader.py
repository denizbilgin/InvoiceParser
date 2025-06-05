import io
from typing import Dict, Any
from typing import List
import PyPDF2
import cv2
import fitz
import numpy as np
import pytesseract
from readers.pdf_type import PDFType
from readers.reader import Reader
from PIL import Image


class ScannedPDFReader(Reader):
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.pdf_type = PDFType.SCANNED_IMAGE
        self.ocr_config = '--oem 3 --psm 6'

    def read_content(self) -> Dict[str, Any]:
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
                processed_image = self._preprocess_image(image)
                page_text = pytesseract.image_to_string(processed_image, config=self.ocr_config, lang='eng+tur')

                pages_content.append({
                    "page_number": page_number + 1,
                    "text": page_text,
                    "method": "ocr_tesseract"
                })

                full_text += page_text + "\n"

            return {
                "success": True,
                'filename': self.file_path.split('\\')[1],
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

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        try:
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            denoised = cv2.fastNlMeansDenoising(gray)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(thresh)

        except Exception as e:
            print(f"Image preprocessing error: {e}")
            return image

    def _pdf_to_images(self) -> List[Image.Image]:
        images: List[Image.Image] = []
        try:
            document = fitz.open(self.file_path)

            for page_number in range(len(document)):
                page = document.load_page(page_number)

                mat = fitz.Matrix(2.0, 2.0)
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
