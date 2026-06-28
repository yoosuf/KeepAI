import json
from typing import Any, Dict


class InvoiceAgent:
    @staticmethod
    def get_extraction_prompt(text_content: str) -> str:
        schema_instruction = """
        You are an invoice extraction AI. Extract the following fields from the text into a JSON object:
        - invoice_number (string)
        - vendor_name (string)
        - date (string, YYYY-MM-DD)
        - items (list of objects with description, quantity, unit_price, total)
        - total_amount (float)
        - currency (string, e.g. USD, EUR)

        Respond ONLY with the JSON object. No preamble.
        """
        return f"{schema_instruction}\n\nINPUT TEXT:\n{text_content}"

    @staticmethod
    def parse_response(response_text: str) -> Dict[str, Any]:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response_text}
