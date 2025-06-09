from abc import ABC, abstractmethod
from typing import Dict, Optional, List


class Validator(ABC):
    def __init__(self, invoice_data: Dict, ground_truth_po_numbers: Optional[List[str]] = None):
        self.invoice_data = invoice_data
        self.line_items = invoice_data.get("line_items", [])
        self.total_details = invoice_data.get("total_details", {})
        self.ground_truth_po_numbers = ground_truth_po_numbers or []

    @abstractmethod
    def check_line_item_consistency(self) -> List[Dict]:
        """
        This function calculates the total price by multiplying the quantity of the relevant product with the unit price.
        The function compares the total values in the invoice with its own calculations and converts the result into a
        dictionary by reporting it in detail.
        :return: Analyzed line items consistency report list
        """
        pass

    @abstractmethod
    def check_total_consistency(self) -> Dict:
        """
        This function adds up the total value of all line items, then compares it with the value in the file.
        :return: Total consistency report dictionary
        """
        pass

    @abstractmethod
    def report_missing_po_numbers(self) -> Dict:
        """
        This function reports missing PO numbers from the line items.
        :return: Missing PO numbers report dictionary
        """
        pass

    @abstractmethod
    def generate_report(self, filename: str) -> Dict:
        """
        This function combines other validator and report generator functions to get the complete report of the file.
        :param filename: Filename to generate report
        :return: General report of the file
        """
        pass
