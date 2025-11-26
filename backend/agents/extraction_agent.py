from typing import Any, Dict, List
from .base_agent import BaseAgent
import re
import json
import google.generativeai as genai
import config

class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("Extraction Agent", layer=3)
        self.gemini_model = None
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')

    async def execute(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """
        Extract structured information and entities using Gemini AI

        Args:
            input_data: Text content to extract from
            parameters: Configuration including fields, confidence threshold, entity types

        Returns:
            Dictionary containing extracted fields and entities
        """
        params = parameters or {}
        extract_fields = params.get('extractFields', ['name', 'date', 'amount', 'description'])
        custom_fields = params.get('customFields', '')
        confidence_threshold = params.get('confidenceThreshold', config.EXTRACTION_CONFIDENCE_THRESHOLD)
        enable_ner = params.get('enableNER', True)
        entity_types = params.get('entityTypes', ['PERSON', 'DATE', 'MONEY', 'ORG'])

        try:
            # Extract text from input
            text = await self._extract_text(input_data)

            if not text or len(text.strip()) == 0:
                raise Exception("No text content to extract from")

            # Perform extraction using both Gemini and regex patterns
            extracted_fields = {}
            entities = {}

            if self.gemini_model:
                # Use Gemini for intelligent extraction
                gemini_result = await self._extract_with_gemini(
                    text, extract_fields, custom_fields, entity_types
                )
                extracted_fields = gemini_result['fields']
                entities = gemini_result['entities']

            # Fallback or supplement with regex-based extraction
            regex_entities = {
                "dates": self._extract_dates(text),
                "emails": self._extract_emails(text),
                "phones": self._extract_phones(text),
                "numbers": self._extract_numbers(text),
                "urls": self._extract_urls(text)
            }

            # Merge regex entities with NER entities if not present
            for entity_type, values in regex_entities.items():
                if entity_type not in entities or not entities[entity_type]:
                    entities[entity_type] = values

            # If no Gemini, try to extract fields with regex
            if not self.gemini_model:
                extracted_fields = self._extract_fields_regex(text, extract_fields)

            # Calculate confidence scores
            field_confidences = {}
            for field, value in extracted_fields.items():
                if value and value != "Not found":
                    field_confidences[field] = 0.95 if self.gemini_model else 0.7
                else:
                    field_confidences[field] = 0.0

            avg_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0

            # Build structured output
            structured_data = {
                "total_fields": len(extracted_fields),
                "filled_fields": sum(1 for v in extracted_fields.values() if v and v != "Not found"),
                "total_entities": sum(len(v) for v in entities.values() if isinstance(v, list)),
                "entity_types": list(entities.keys()),
                "field_confidences": field_confidences
            }

            return {
                "extracted_fields": extracted_fields,
                "entities": entities,
                "structured_data": structured_data,
                "average_confidence": round(avg_confidence, 3),
                "extraction_method": "gemini_ai" if self.gemini_model else "regex_patterns",
                "fields_requested": extract_fields,
                "custom_fields": custom_fields if custom_fields else None
            }

        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")

    async def _extract_text(self, input_data: Any) -> str:
        """Extract text from various input formats"""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            # Try multiple keys where text might be stored
            for key in ['extracted_text', 'full_text', 'text', 'content']:
                if key in input_data:
                    return str(input_data[key])
            # Check for nested output
            if 'output' in input_data and isinstance(input_data['output'], dict):
                for key in ['extracted_text', 'full_text', 'text']:
                    if key in input_data['output']:
                        return str(input_data['output'][key])
            # Serialize as JSON
            return json.dumps(input_data)
        else:
            return str(input_data)

    async def _extract_with_gemini(
        self,
        text: str,
        fields: List[str],
        custom_fields: str,
        entity_types: List[str]
    ) -> Dict[str, Any]:
        """Use Gemini AI to extract structured information"""

        # Build extraction prompt
        fields_str = ", ".join(fields)
        entities_str = ", ".join(entity_types)

        prompt = f"""Extract the following information from the text below:

Fields to extract: {fields_str}
{f"Additional custom fields: {custom_fields}" if custom_fields else ""}

Entity types to identify: {entities_str}

Text:
{text[:3000]}

Please provide the extracted information in JSON format with two sections:
1. "fields": a dictionary with keys for each requested field
2. "entities": a dictionary with keys for each entity type containing lists of found entities

If a field or entity is not found, use "Not found" as the value or an empty list.
Return only the JSON, no additional text.
"""

        try:
            response = self.gemini_model.generate_content(prompt)
            result_text = response.text.strip()

            # Try to extract JSON from response
            if '```json' in result_text:
                json_start = result_text.find('```json') + 7
                json_end = result_text.find('```', json_start)
                result_text = result_text[json_start:json_end].strip()
            elif '```' in result_text:
                json_start = result_text.find('```') + 3
                json_end = result_text.find('```', json_start)
                result_text = result_text[json_start:json_end].strip()

            result = json.loads(result_text)

            return {
                "fields": result.get("fields", {}),
                "entities": result.get("entities", {})
            }

        except Exception as e:
            print(f"⚠ Gemini extraction failed: {e}")
            return {"fields": {}, "entities": {}}

    def _extract_fields_regex(self, text: str, fields: List[str]) -> Dict[str, str]:
        """Fallback regex-based field extraction"""
        extracted = {}

        for field in fields:
            field_lower = field.lower()
            # Try to find field near the text
            pattern = rf'{field}[:\s]+([^\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted[field] = match.group(1).strip()
            else:
                extracted[field] = "Not found"

        return extracted

    def _extract_dates(self, text: str) -> List[str]:
        """Extract date patterns"""
        patterns = [
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # DD/MM/YYYY or MM/DD/YYYY
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        return list(set(dates))[:10]  # Return unique dates, max 10

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(pattern, text)))

    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers"""
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',  # International
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))[:10]

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numeric values including currency"""
        patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # USD currency
            r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',  # Regular numbers
        ]
        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, text))
        return list(set(numbers))[:15]

    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        return list(set(re.findall(pattern, text)))
