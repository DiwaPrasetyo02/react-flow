from typing import Any, Dict
from .base_agent import BaseAgent
import re

class SummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__("Summary Agent", layer=4)

    async def execute(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """
        Simulate text summarization
        In production, this would use transformer-based summarization models
        """
        text = str(input_data)

        # Basic text statistics
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Simulate extractive summarization (take first few sentences)
        summary_sentences = sentences[:3] if len(sentences) >= 3 else sentences
        extractive_summary = ". ".join(summary_sentences) + "."

        # Simulate abstractive summary
        abstractive_summary = f"This content discusses {len(words)} words across {len(sentences)} sentences. " + \
                            f"Key points include: {', '.join(words[:5])}."

        # Calculate key metrics
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        return {
            "extractive_summary": extractive_summary,
            "abstractive_summary": abstractive_summary,
            "statistics": {
                "total_words": len(words),
                "total_sentences": len(sentences),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "original_length": len(text),
                "summary_length": len(extractive_summary),
                "compression_ratio": round(len(extractive_summary) / len(text), 2) if text else 0
            },
            "key_phrases": self._extract_key_phrases(text),
            "summarization_model": "simulated-transformer"
        }

    def _extract_key_phrases(self, text: str) -> list:
        """Extract potential key phrases"""
        # Simple approach: find longer words
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        # Get most common words (simulated)
        unique_words = list(set(words))
        return unique_words[:5]  # Top 5 unique words
