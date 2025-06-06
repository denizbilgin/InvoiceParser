from readers.reader_factory import ReaderFactory
from readers.text_based_pdf_reader import TextBasedPDFReader
from readers.scanned_pdf_reader import ScannedPDFReader
from utils import *


if __name__ == '__main__':
    invoices_folder_path = './invoices'
    raw_ocr_outputs_folder_path = 'outputs/raw_ocr_outputs'
    raw_ocr_outputs = []

    for filename in os.listdir(invoices_folder_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(invoices_folder_path, filename)
            reader = ReaderFactory.create_reader(file_path)
            result = reader.read_content()
            raw_ocr_outputs.append(result)
            export_raw_ocr_outputs_as_json(result, filename, raw_ocr_outputs_folder_path)



"""
ADIMLAR:

1. OCR Aşaması
    Amaç: PDF'ten metni ve tabloyu doğru şekilde al.
    - Hem serbest metin (adres, po vs.) hem de tablo ayıklanmalı.
    - İlk olarak OCR çıktısını bir .txt olarak kaydet. Doğru okunduğuna emin ol.

2. PO Numarası Tespiti
    Amaç: Serbest metin içinde PO’yu bul.
    - Regex ve/veya ML teknikleri kullanabilirsin.
    
3. Ürün Kalemleri ve Tablo İşleme
    Amaç: Fatura içindeki tabloyu doğru parse et.
    - Veya OCR sonrası satır satır tabloyu parse et.
    - Tablodaki her satır için miktar, birim fiyat, toplam ayıkla ve kontrol et.

4. Tedarikçi Bilgisi Çıkarımı
    - Fatura başındaki veya altındaki metinden
        Firma adı
        Vergi numarası (regex: \d{10})
        Adres (NER veya heuristik ile)

5. Veri Tutarlılık Kontrolü
    - assert abs(item["quantity"] * item["unit_price"] - item["total_price"]) < tolerance
    - PO numarası bulunmazsa rapora yaz.
    - Tüm satırların toplamı, varsa "fatura toplamı" ile karşılaştırılır.

6. JSON Oluşturma ve Raporlama
7. Test & Değerlendirme
"""