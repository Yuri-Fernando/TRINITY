"""
LLM-based uncertainty classification module.

Uses language models to classify and quantify regulatory uncertainty
in document chunks with contextual understanding.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from loguru import logger


class UncertaintyLevel(Enum):
    """Uncertainty severity levels."""
    NONE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class UncertaintyScore:
    """Classification result for a text chunk."""
    chunk_id: str
    text: str
    uncertainty_level: UncertaintyLevel
    confidence: float  # 0-1
    score: float  # 0-1 (normalized numerical score)
    signals: List[str]  # List of identified uncertainty signals
    reasoning: str
    keywords: List[str]
    regulatory_domain: Optional[str]  # e.g., "credit", "market", "operational"


class UncertaintyClassifier:
    """
    Classifies regulatory uncertainty in text chunks using LLMs.

    Uncertainty indicators:
    - Ambiguous language ("may", "could", "potentially")
    - Conditional statements ("if", "provided that")
    - Future-oriented language ("forthcoming", "expected to")
    - Conflicting directives (e.g., different parts of guidance)
    - Policy reversals or amendments
    - Emergent/novel regulations
    """

    UNCERTAINTY_PROMPT = PromptTemplate(
        input_variables=["text"],
        template="""Analyze the following regulatory or financial text for signals of regulatory uncertainty.

Text:
---
{text}
---

Provide analysis in JSON format with:
1. uncertainty_level: one of [NONE, LOW, MODERATE, HIGH, CRITICAL]
2. confidence: 0-1 confidence in the classification
3. signals: list of specific uncertainty indicators found
4. keywords: key phrases indicating uncertainty
5. regulatory_domain: the domain of regulation (credit, market, operational, etc.)
6. reasoning: brief explanation of the classification

Focus on:
- Ambiguous, vague, or conditional language
- Conflicting or contradictory statements
- Emerging/novel regulatory areas
- Policy changes or reversals
- Incomplete guidance or pending clarifications
- Multiple interpretations possible

JSON output only, no other text."""
    )

    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.3):
        """
        Initialize uncertainty classifier.

        Args:
            model_name: OpenAI model name
            temperature: LLM temperature for consistency
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )
        self.model_name = model_name

        logger.info(f"Initialized UncertaintyClassifier with {model_name}")

    def classify(self, chunk_id: str, text: str) -> UncertaintyScore:
        """
        Classify uncertainty in a single text chunk.

        Args:
            chunk_id: Unique chunk identifier
            text: Text to classify

        Returns:
            UncertaintyScore object
        """
        # Truncate text if too long (to stay within token limits)
        max_chars = 2000
        text_truncated = text[:max_chars]

        try:
            # Generate prompt and get LLM response
            prompt = self.UNCERTAINTY_PROMPT.format(text=text_truncated)
            response = self.llm.predict(prompt)

            # Parse JSON response
            result = json.loads(response)

            # Map string level to enum
            level_map = {
                "NONE": UncertaintyLevel.NONE,
                "LOW": UncertaintyLevel.LOW,
                "MODERATE": UncertaintyLevel.MODERATE,
                "HIGH": UncertaintyLevel.HIGH,
                "CRITICAL": UncertaintyLevel.CRITICAL
            }

            uncertainty_level = level_map.get(
                result.get("uncertainty_level", "LOW"),
                UncertaintyLevel.LOW
            )

            # Convert level to normalized score
            score = uncertainty_level.value / len(UncertaintyLevel)

            score_obj = UncertaintyScore(
                chunk_id=chunk_id,
                text=text_truncated,
                uncertainty_level=uncertainty_level,
                confidence=float(result.get("confidence", 0.5)),
                score=score,
                signals=result.get("signals", []),
                reasoning=result.get("reasoning", ""),
                keywords=result.get("keywords", []),
                regulatory_domain=result.get("regulatory_domain")
            )

            logger.debug(f"Classified {chunk_id}: {uncertainty_level.name} (score={score:.2f})")
            return score_obj

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {chunk_id}: {e}")
            # Return default score on error
            return UncertaintyScore(
                chunk_id=chunk_id,
                text=text_truncated,
                uncertainty_level=UncertaintyLevel.LOW,
                confidence=0.0,
                score=0.0,
                signals=["classification_error"],
                reasoning="Classification failed",
                keywords=[],
                regulatory_domain=None
            )
        except Exception as e:
            logger.error(f"Error classifying {chunk_id}: {e}")
            return UncertaintyScore(
                chunk_id=chunk_id,
                text=text_truncated,
                uncertainty_level=UncertaintyLevel.LOW,
                confidence=0.0,
                score=0.0,
                signals=["classification_error"],
                reasoning=f"Error: {str(e)}",
                keywords=[],
                regulatory_domain=None
            )

    def classify_batch(self, chunks: List[Dict[str, str]]) -> List[UncertaintyScore]:
        """
        Classify multiple chunks.

        Args:
            chunks: List of dicts with 'id' and 'text' keys

        Returns:
            List of UncertaintyScore objects
        """
        scores = []
        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.get("id", f"chunk_{idx}")
            text = chunk.get("text", "")

            if not text:
                logger.warning(f"Skipping empty chunk {chunk_id}")
                continue

            score = self.classify(chunk_id, text)
            scores.append(score)

        logger.info(f"Classified {len(scores)} chunks")
        return scores

    def extract_signals(self, text: str) -> List[str]:
        """Extract uncertainty signals from text using pattern matching."""
        signals = []

        # Ambiguous language
        ambiguous_patterns = [
            r'\b(may|might|could|potentially|possibly|potentially)\b',
            r'\b(somewhat|relatively|fairly)\b',
            r'\b(to be determined|TBD|pending|forthcoming)\b'
        ]

        # Conditional language
        conditional_patterns = [
            r'\bif\b',
            r'\bprovided that\b',
            r'\bsubject to\b'
        ]

        # Policy change indicators
        change_patterns = [
            r'\b(new|amended|revised|updated)\b',
            r'\breversed\b',
            r'\bphased in\b'
        ]

        import re

        for pattern in ambiguous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                signals.append("ambiguous_language")
                break

        for pattern in conditional_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                signals.append("conditional_language")
                break

        for pattern in change_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                signals.append("policy_change")
                break

        return signals


class ClassificationPipeline:
    """End-to-end classification pipeline."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.classifier = UncertaintyClassifier(model_name=model_name)

    def process_chunks(self, chunks: List[Dict[str, str]]) -> List[UncertaintyScore]:
        """Process multiple chunks and return scores."""
        return self.classifier.classify_batch(chunks)

    def export_scores(self, scores: List[UncertaintyScore], output_path: str) -> None:
        """Export scores to JSON."""
        data = {
            "classifications": [
                {
                    "chunk_id": score.chunk_id,
                    "uncertainty_level": score.uncertainty_level.name,
                    "score": score.score,
                    "confidence": score.confidence,
                    "signals": score.signals,
                    "keywords": score.keywords,
                    "regulatory_domain": score.regulatory_domain
                }
                for score in scores
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(scores)} scores to {output_path}")


if __name__ == "__main__":
    classifier = UncertaintyClassifier()

    sample_text = """
    The Federal Reserve issued updated guidance regarding credit risk policies.
    Banks may be required to implement new framework components, pending
    final rulemaking. The specific implementation timeline remains to be determined.
    """

    score = classifier.classify("test_001", sample_text)
    print(f"Classification: {score.uncertainty_level.name} (score={score.score:.2f})")
    print(f"Signals: {score.signals}")
