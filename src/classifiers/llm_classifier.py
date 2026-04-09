"""
LLM-based content classifier using Claude API.

Classifies pharmaceutical misinformation by theme, severity,
and source type using structured prompting.
"""

import json
import logging
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LLMClassifier:
    """Classify content using Claude API."""

    SYSTEM_PROMPT = """You are a medical misinformation research analyst classifying pharmaceutical content.

For each item, determine:
1. theme: One of {themes}
2. source_type: One of [news, blog, social, forum, commercial, video, scientific]
3. severity: 1-5 (1=mildly misleading, 5=dangerous — could cause patient harm)
4. time_period: One of [pre_2020, early_2020, late_2020, 2021, 2022, 2023_plus]
5. summary: 2-3 sentence explanation
6. quote_fragment: Key claim in under 10 words
7. is_misinfo: true/false — is this genuinely misinformation?

Respond ONLY with a JSON array. No markdown, no backticks.
Each object: {{"title","theme","source_type","severity","time_period","summary","quote_fragment","is_misinfo"}}"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        themes: Optional[List[str]] = None,
    ):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.themes = themes or [
            "ndma_cancer", "recall_confusion", "safety_fear",
            "patient_cessation", "anti_pharma", "predatory_alt",
        ]

    def classify_batch(
        self,
        items: List[Dict],
        batch_size: int = 10,
    ) -> List[Dict]:
        """
        Classify a batch of content items.

        Args:
            items: List of dicts with at least 'title' and 'text' keys
            batch_size: Number of items per API call

        Returns:
            List of classification dicts
        """
        all_results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_text = "\n\n".join(
                f"ITEM {j+1}:\nTitle: {item.get('title', '')}\n"
                f"Source: {item.get('source_name', '')}\n"
                f"Date: {item.get('published_date', 'unknown')}\n"
                f"Text: {(item.get('text', '') or '')[:500]}"
                for j, item in enumerate(batch)
            )

            system = self.SYSTEM_PROMPT.format(themes=", ".join(self.themes))

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system,
                    messages=[{
                        "role": "user",
                        "content": f"Classify these {len(batch)} items:\n\n{batch_text}",
                    }],
                )

                text = "".join(
                    block.text for block in response.content
                    if hasattr(block, "text")
                )

                parsed = self._parse_json(text)
                if parsed:
                    # Attach original content IDs
                    for j, result in enumerate(parsed):
                        if j < len(batch):
                            result["_content_id"] = batch[j].get("id")
                    all_results.extend(parsed)

                logger.info(
                    f"Classified batch {i // batch_size + 1}: "
                    f"{len(parsed or [])} items"
                )

                time.sleep(1.0)  # Rate limiting

            except Exception as e:
                logger.error(f"Classification failed for batch: {e}")

        return all_results

    def _parse_json(self, text: str) -> Optional[List[Dict]]:
        """Extract JSON array from LLM response."""
        cleaned = text.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        # Try to find array in text
        import re
        match = re.search(r'\[[\s\S]*\]', cleaned)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

        logger.warning("Failed to parse JSON from LLM response")
        return None


class RuleBasedClassifier:
    """
    Simple keyword-based classifier as fallback when LLM is unavailable.
    Lower accuracy but zero API cost.
    """

    def __init__(self, themes=None):
        from .themes import DEFAULT_THEMES
        self.themes = themes or DEFAULT_THEMES

    def classify(self, title: str, text: str = "") -> Dict:
        """Classify a single item by keyword matching."""
        combined = f"{title} {text}".lower()

        best_theme = "recall_confusion"
        best_score = 0

        for key, theme in self.themes.items():
            score = sum(1 for kw in theme.keywords if kw.lower() in combined)
            if score > best_score:
                best_score = score
                best_theme = key

        # Estimate severity from language intensity
        severity = 3
        danger_words = ["stop", "immediately", "poison", "deadly", "kill", "death"]
        if any(w in combined for w in danger_words):
            severity = 5
        elif any(w in combined for w in ["toxic", "dangerous", "harmful", "cancer"]):
            severity = 4
        elif any(w in combined for w in ["misleading", "confusing", "unclear"]):
            severity = 2

        return {
            "theme": best_theme,
            "severity": severity,
            "source_type": "unknown",
            "summary": f"Rule-based classification: matched theme '{best_theme}'",
            "is_misinfo": best_score > 0,
            "confidence": min(best_score / 3.0, 1.0),
        }
