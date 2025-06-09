from analyzers.invoice_analyzer import InvoiceAnalyzer
from readers.reader_factory import ReaderFactory
from utils import *
from validators.invoice_validator import InvoiceValidator

if __name__ == '__main__':
    invoices_folder_path = './invoices'
    raw_ocr_outputs_folder_path = 'outputs/raw_ocr_outputs'
    analyzed_outputs_folder_path = 'outputs/analyzed_outputs'
    final_outputs_path = 'outputs/final_outputs'

    # Ground truth POs for validating invoices. I wrote these by looking at myself
    ground_truth_pos = {
        "20250221092842541.json": [],
        "20250221125114588.json": ["PO-135298"],
        "Invaoice_2.json": ["PO-526365", "PO-360206", "PO-620087", "PO-756014", "PO-842742", "PO-362820"]
    }

    for filename in os.listdir(invoices_folder_path):
        print(f'{filename} is processing!')
        if filename.endswith('.pdf'):
            file_path = os.path.join(invoices_folder_path, filename)

            # Reader
            print('READING')
            reader = ReaderFactory.create_reader(file_path)
            result = reader.read_content()

            # Exporting result of the first step of the case
            export_outputs_as_json(result, filename, raw_ocr_outputs_folder_path)

            text = result['content']['text']

            # Analyzer
            print('ANALYZING')
            analyzer = InvoiceAnalyzer(seed=42)
            result = analyzer.analyze_invoice(text)

            is_valid, message = analyzer.validate_invoice_json(result)
            if is_valid:
                print("Success! JSON output:")
                print(json.dumps(result, indent=2, ensure_ascii=False))

                # Exporting result of the second step of the case
                export_outputs_as_json(result, filename, analyzed_outputs_folder_path)

                # Validator
                print('VALIDATING')
                filename = filename.replace('.pdf', '.json')
                validator = InvoiceValidator(result, ground_truth_pos[filename])
                analyzed_json = validator.generate_report(filename)
                print(analyzed_json)

                # Exporting result of the third step of the case
                export_outputs_as_json(analyzed_json, filename, final_outputs_path)
            else:
                print(f"Validation error: {message}")
                print("Raw output:", json.dumps(result, indent=2, ensure_ascii=False))

            print('=' * 50)