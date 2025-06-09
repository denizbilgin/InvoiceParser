from abc import ABC, abstractmethod
from typing import Tuple


class Analyzer(ABC):
    @abstractmethod
    def analyze_invoice(self, invoice_text: str):
        """
        This function analyzes the text given to it and divides it into meaningful groups.
        :param invoice_text: text to analyze
        :return: None
        """
        pass

    @abstractmethod
    def validate_invoice_json(self, data) -> Tuple[bool, str]:
        """
        This function checks the existence and correctness of groups in the data given to it.
        :param data: data to validate
        :return: validation result (bool), description
        """
        pass
