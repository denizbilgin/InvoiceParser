import json
import requests
from typing import Tuple, Dict
from analyzers.abstracts.analyzer import Analyzer


class InvoiceAnalyzer(Analyzer):
    def __init__(
        self,
        model="mistral:7b-instruct",    # Local LLM to analyze invoice
        api_url="http://localhost:11434/api/generate",
        max_retries=3,
        prompt_path="analyzers/prompts/mvp_prompt.txt",
        seed=12     # Seed to get deterministic results
    ):
        self.model = model
        self.api_url = api_url
        self.max_retries = max_retries
        self.prompt_path = prompt_path
        self.seed = seed

    def build_prompt(self, invoice_text: str) -> str:
        """
        This function builds prompt with given invoice text and prompt template. The prompt template comes from analyzers/prompts/mvp_prompt.txt
        :param invoice_text: invoice text to be prompted
        :return: Prompt ready to be given to the local LLM and analyzed
        """
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as file:
                template = file.read()
        except FileNotFoundError:
            raise Exception(f"Prompt file not found: {self.prompt_path}")

        return template.replace("{invoice_text}", invoice_text)

    def extract_json_from_response(self, response_text: str) -> Dict:
        """
        This function extracts JSON data from response of the LLM. Sometimes LLM outputs may have unnecessary text next to the JSON data.
        :param response_text: Response that comes from an LLM
        :return: analyzed JSON data
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Find the first '{' sign and the last '}' sign
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')

            # The lines between these two signs are the json data we are looking for
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                json_text = response_text[first_brace:last_brace + 1]
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    pass

            self.seed *= 42
            print(response_text)
            raise ValueError("JSON could not be extracted.")

    def analyze_invoice(self, invoice_text: str):
        """
        This function analyzes the text given to it and divides it into meaningful groups. The function analyzes raw output with a local LLM.
        :param invoice_text: text to analyze
        :return: None
        """
        # Creating prompt for invoice
        prompt = self.build_prompt(invoice_text)

        for attempt in range(self.max_retries):
            try:
                # Determining LLM parameters
                data = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                        "seed": self.seed
                    }
                }

                response = requests.post(self.api_url, json=data, timeout=1200)
                response.raise_for_status()
                result = response.json()

                if 'response' in result:
                    parsed_json = self.extract_json_from_response(result['response'])
                    return parsed_json
                else:
                    print(f"Unexpected response format: {result}")

            # Error handling
            except requests.exceptions.RequestException as e:
                print(f"API error (trial {attempt + 1}): {e}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error (trial {attempt + 1}): {e}")
                print(f"Raw response: {result.get('response', '')[:500]}...")
            except ValueError as e:
                print(f"JSON extraction error (trial {attempt + 1}): {e}")
            except Exception as e:
                print(f"Unexpected error (trial {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                print(f"Trying again... ({attempt + 2}/{self.max_retries})")

        raise Exception(f"{self.max_retries} failed after trial")

    def validate_invoice_json(self, data) -> Tuple[bool, str]:
        """
        This function checks the existence and correctness of groups in the data given to it.
        :param data: data to validate
        :return: validation result (bool), description
        """
        required_keys = ['supplier_details', 'invoice_details', 'bill_to_details',
                         'line_items', 'total_details', 'payment_terms']

        for key in required_keys:
            if key not in data:
                return False, f"Missing key: {key}"

        if not isinstance(data['line_items'], list):
            return False, "line_items must be an array"

        try:
            float(data['total_details']['total'])
            float(data['total_details']['subtotal'])
            float(data['total_details']['vat (20%)'])
        except (ValueError, TypeError, KeyError):
            return False, "Total values must be numeric"
        return True, "Valid"
