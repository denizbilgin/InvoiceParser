import os
from readers.reader_factory import ReaderFactory
from utils import *


if __name__ == '__main__':
    invoices_folder_path = './invoices'
    raw_ocr_outputs_folder_path = 'outputs/raw_ocr_outputs'

    for filename in os.listdir(invoices_folder_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(invoices_folder_path, filename)
            reader = ReaderFactory.create_reader(file_path)
            result = reader.read_content()

            export_raw_ocr_outputs_as_json(result, filename, raw_ocr_outputs_folder_path)

