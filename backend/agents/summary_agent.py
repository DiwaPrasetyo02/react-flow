from typing import Any, Dict, List
from .base_agent import BaseAgent
import re
import json
import google.generativeai as genai
import config

class SummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__("Summary Agent", layer=4)
        self.gemini_model = None
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')

    async def execute(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """
        Generate document summary using Gemini AI

        Args:
            input_data: Text content to summarize
            parameters: Configuration including length, type, custom prompt, temperature

        Returns:
            Dictionary containing summaries and key information
        """
        params = parameters or {}
        summary_length = params.get('summaryLength', 'medium')
        summary_type = params.get('summaryType', 'abstractive')
        custom_prompt = params.get('customPrompt', '')
        include_keywords = params.get('includeKeywords', True)
        temperature = params.get('temperature', 0.7)

        try:
            # Extract text from input
            text = await self._extract_text(input_data)

            if not text or len(text.strip()) == 0:
                raise Exception("No text content to summarize")

            # Calculate text statistics
            stats = self._calculate_statistics(text)

            # Generate summaries
            extractive_summary = ""
            abstractive_summary = ""
            key_phrases = []

            if self.gemini_model:
                # Use Gemini for intelligent summarization
                gemini_result = await self._summarize_with_gemini(
                    text, summary_length, summary_type, custom_prompt, temperature
                )
                abstractive_summary = gemini_result['abstractive']
                extractive_summary = gemini_result['extractive']
                key_phrases = gemini_result['key_phrases']
            else:
                # Fallback to basic summarization
                extractive_summary = self._basic_extractive_summary(text, summary_length)
                abstractive_summary = self._basic_abstractive_summary(text, stats)
                key_phrases = self._extract_key_phrases(text)

            # Calculate compression ratio
            summary_for_ratio = abstractive_summary if summary_type == 'abstractive' else extractive_summary
            compression_ratio = len(summary_for_ratio) / len(text) if text else 0

            return {
                "extractive_summary": extractive_summary,
                "abstractive_summary": abstractive_summary,
                "key_phrases": key_phrases if include_keywords else [],
                "statistics": {
                    **stats,
                    "summary_length": len(summary_for_ratio),
                    "compression_ratio": round(compression_ratio, 3)
                },
                "configuration": {
                    "summary_length": summary_length,
                    "summary_type": summary_type,
                    "temperature": temperature,
                    "used_custom_prompt": bool(custom_prompt)
                },
                "summarization_model": "gemini_pro" if self.gemini_model else "basic_extraction"
            }

        except Exception as e:
            raise Exception(f"Summarization failed: {str(e)}")

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

    def _calculate_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate text statistics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        avg_sentence_length = (
            sum(len(s.split()) for s in sentences) / len(sentences)
            if sentences else 0
        )

        return {
            "total_words": len(words),
            "total_sentences": len(sentences),
            "total_paragraphs": len(paragraphs),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "total_characters": len(text)
        }

    async def _summarize_with_gemini(
        self,
        text: str,
        length: str,
        summary_type: str,
        custom_prompt: str,
        temperature: float
    ) -> Dict[str, Any]:
        """Use Gemini AI to generate summaries"""

        # Determine target length
        length_guidelines = {
            'short': '1-2 sentences',
            'medium': '1 paragraph (3-5 sentences)',
            'long': '2-3 paragraphs'
        }
        target_length = length_guidelines.get(length, length_guidelines['medium'])

        # Build base prompt based on custom prompt or default
        if custom_prompt:
            base_instruction = custom_prompt
        else:
            base_instruction = "Summarize the following document, highlighting key points and main ideas."

        # Build complete prompt
        if summary_type == 'hybrid' or summary_type == 'both':
            prompt = f"""{base_instruction}

Provide both:
1. An EXTRACTIVE summary ({target_length}): Select and combine key sentences from the original text
2. An ABSTRACTIVE summary ({target_length}): Rewrite the main ideas in your own words
3. Key phrases: List 5-7 important keywords or phrases

Text:
{text[:4000]}

Respond in JSON format:
{{
  "extractive": "...",
  "abstractive": "...",
  "key_phrases": ["...", "..."]
}}
"""
        elif summary_type == 'extractive':
            prompt = f"""{base_instruction}

Create an EXTRACTIVE summary ({target_length}) by selecting and combining the most important sentences from the text.

Text:
{text[:4000]}

Also provide 5-7 key phrases.

Respond in JSON format:
{{
  "extractive": "...",
  "abstractive": "(same as extractive)",
  "key_phrases": ["...", "..."]
}}
"""
        else:  # abstractive
            prompt = f"""{base_instruction}

Create an ABSTRACTIVE summary ({target_length}) by rewriting the main ideas in your own words.

Text:
{text[:4000]}

Also provide 5-7 key phrases.

Respond in JSON format:
{{
  "extractive": "(basic extraction)",
  "abstractive": "...",
  "key_phrases": ["...", "..."]
}}
"""

        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                )
            )
            result_text = response.text.strip()

            # Extract JSON from response
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
                "extractive": result.get("extractive", ""),
                "abstractive": result.get("abstractive", ""),
                "key_phrases": result.get("key_phrases", [])
            }

        except Exception as e:
            print(f"⚠ Gemini summarization failed: {e}")
            # Fallback to basic summaries
            return {
                "extractive": self._basic_extractive_summary(text, length),
                "abstractive": f"Summary generation failed: {str(e)}",
                "key_phrases": self._extract_key_phrases(text)
            }

    def _basic_extractive_summary(self, text: str, length: str) -> str:
        """Generate basic extractive summary"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 3]

        # Determine number of sentences based on length
        num_sentences = {
            'short': 2,
            'medium': 5,
            'long': 10
        }.get(length, 5)

        # Take first N sentences (simple approach)
        summary_sentences = sentences[:min(num_sentences, len(sentences))]
        return ". ".join(summary_sentences) + "." if summary_sentences else text[:500]

    def _basic_abstractive_summary(self, text: str, stats: Dict) -> str:
        """Generate basic abstractive summary"""
        key_phrases = self._extract_key_phrases(text)
        key_phrases_str = ', '.join(key_phrases[:5])

        return (
            f"This document contains {stats['total_words']} words across "
            f"{stats['total_sentences']} sentences. "
            f"Key topics discussed include: {key_phrases_str}."
        )

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using simple frequency analysis"""
        # Remove common words
        common_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'it', 'its', 'they', 'their', 'them'
        ])

        # Extract words (longer than 4 characters)
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())

        # Filter out common words and count frequency
        filtered_words = [w for w in words if w not in common_words]

        # Get most frequent words
        from collections import Counter
        word_freq = Counter(filtered_words)
        most_common = word_freq.most_common(7)

        return [word for word, count in most_common]
