"""
Misinformation theme and severity definitions.

These can be customized per recall event via config YAML files.
Default themes target negative pharmaceutical misinformation.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Dict


class Severity(IntEnum):
    """Misinformation severity scale (1-5)."""
    MILDLY_MISLEADING = 1   # Minor framing issues, mostly accurate
    SLIGHTLY_MISLEADING = 2  # Key omissions or slightly misleading framing
    MODERATE = 3             # Significant exaggerations or omissions
    MISLEADING = 4           # Clearly misleading, could affect patient behavior
    DANGEROUS = 5            # Could cause direct patient harm


@dataclass
class MisinfoTheme:
    """Definition of a misinformation theme."""
    key: str
    label: str
    description: str
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class SourceType:
    """Classification of content source."""
    key: str
    label: str


# ── Default Themes (Pharmaceutical Recall Misinformation) ──────────────

DEFAULT_THEMES: Dict[str, MisinfoTheme] = {
    "ndma_cancer": MisinfoTheme(
        key="ndma_cancer",
        label="NDMA / Cancer Scare",
        description="Exaggerated or false claims that metformin causes cancer, "
                    "beyond what NDMA contamination evidence supports",
        keywords=["cancer", "carcinogen", "NDMA", "tumor", "oncogenic"],
        examples=[
            "Metformin causes cancer — stop taking it immediately",
            "NDMA in all metformin batches at dangerous levels",
        ],
    ),
    "recall_confusion": MisinfoTheme(
        key="recall_confusion",
        label="Recall Confusion",
        description="Conflating the ER-specific recall with all metformin products, "
                    "failing to distinguish IR from ER formulations",
        keywords=["recall", "recalled", "all metformin", "pulled", "banned"],
        examples=[
            "All metformin has been recalled by the FDA",
            "Metformin recalled due to cancer-causing impurity",
        ],
    ),
    "safety_fear": MisinfoTheme(
        key="safety_fear",
        label="Safety Fearmongering",
        description="General claims that metformin is toxic, poisonous, or dangerous "
                    "beyond evidence-based risk assessment",
        keywords=["toxic", "poison", "dangerous", "deadly", "destroys", "harmful"],
        examples=[
            "Metformin is a toxic chemical destroying your body",
            "Metformin destroys your kidneys and liver",
        ],
    ),
    "patient_cessation": MisinfoTheme(
        key="patient_cessation",
        label="Patient Cessation",
        description="Content encouraging patients to stop metformin without "
                    "medical supervision, including unaffected formulations",
        keywords=["stop taking", "quit", "throw away", "don't take", "cessation"],
        examples=[
            "Stop taking metformin immediately — switch to cinnamon",
            "I stopped all my metformin after the recall news",
        ],
    ),
    "anti_pharma": MisinfoTheme(
        key="anti_pharma",
        label="Anti-Pharma Conspiracy",
        description="Conspiracy theories claiming FDA or pharmaceutical companies "
                    "deliberately contaminated or concealed contamination",
        keywords=["coverup", "cover-up", "hiding", "conspiracy", "big pharma",
                  "deliberately", "intentional", "corruption"],
        examples=[
            "FDA knew about contamination and covered it up",
            "Big pharma deliberately poisoning diabetics",
        ],
    ),
    "predatory_alt": MisinfoTheme(
        key="predatory_alt",
        label="Predatory Alternatives",
        description="Commercial exploitation of recall fears to sell supplements "
                    "or alternative treatments (berberine, cinnamon, etc.)",
        keywords=["berberine", "alternative", "natural", "supplement", "replace",
                  "instead of", "switch to"],
        examples=[
            "Recalled metformin? Try our safe natural berberine instead",
            "Metformin detox protocol — cleanse your body",
        ],
    ),
}

DEFAULT_SOURCE_TYPES: Dict[str, SourceType] = {
    "news": SourceType("news", "News Outlet"),
    "blog": SourceType("blog", "Health Blog"),
    "social": SourceType("social", "Social Media"),
    "forum": SourceType("forum", "Forum / Community"),
    "commercial": SourceType("commercial", "Commercial / Ad"),
    "video": SourceType("video", "Video"),
    "scientific": SourceType("scientific", "Scientific Literature"),
}
