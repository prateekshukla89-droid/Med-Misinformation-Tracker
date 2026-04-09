# PharmaMisinfo Tracker

**An open-source framework for monitoring pharmaceutical misinformation following drug recalls.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

PharmaMisinfo Tracker is a modular Python toolkit for systematically collecting, classifying, and analyzing pharmaceutical misinformation across news, social media, forums, and commercial health sites. It was developed to study the misinformation ecosystem surrounding the **2020 FDA metformin extended-release (ER) recall** but is designed to generalize to any pharmaceutical recall event (e.g., valsartan, ranitidine).

### What It Does

1. **Collects** content from multiple public sources (Google News, Reddit, Google Trends, Wayback Machine archives, news APIs)
2. **Classifies** each item by misinformation theme, source type, and severity using LLM-based and rule-based classifiers
3. **Stores** structured results in a local SQLite database with full provenance (URL, date, platform, raw text)
4. **Visualizes** temporal trends, theme distributions, and severity patterns with publication-ready figures

### Why It Exists

Drug recalls generate significant public confusion and misinformation that can lead to inappropriate medication cessation. Existing health misinformation tools focus on general fake news detection — none are purpose-built for tracking misinformation triggered by specific pharmaceutical safety events. This framework fills that gap.

## Case Study: Metformin ER Recall (2020)

The FDA initiated recalls of metformin ER products beginning in June 2020 due to NDMA (N-nitrosodimethylamine) contamination above acceptable intake limits. Despite the recall being limited to specific ER formulations from specific manufacturers, widespread confusion led to:

- Patients stopping **all** metformin (including unaffected IR formulations)
- News outlets publishing headlines that failed to distinguish ER from IR
- Supplement companies marketing "natural alternatives" by exploiting recall fears
- Anti-pharmaceutical conspiracy narratives linking the recall to broader distrust

This tool was built to systematically document and quantify these phenomena.

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/pharma-misinfo-tracker.git
cd pharma-misinfo-tracker
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your API keys
```

### API Keys Required

| Source | Key Required | How to Get |
|--------|-------------|------------|
| Google Trends | None | Free via `pytrends` |
| News API | Free tier | [newsapi.org](https://newsapi.org) (100 req/day) |
| Reddit (Pushshift) | Academic access | [Arctic Shift](https://arctic-shift.photon-reddit.com/) or institutional application |
| Wayback Machine | None | Free CDX API |
| Anthropic (Claude) | API key | [console.anthropic.com](https://console.anthropic.com) |

## Quick Start

```python
from pharma_misinfo import Pipeline

# Initialize with your recall event
pipeline = Pipeline(
    drug_name="metformin",
    recall_date="2020-06-01",
    search_terms=["metformin recall", "metformin NDMA", "metformin cancer"],
    date_range=("2019-01-01", "2025-12-31")
)

# Collect from all available sources
pipeline.collect()

# Classify misinformation themes and severity
pipeline.classify()

# Generate publication-ready figures
pipeline.visualize(output_dir="figures/")

# Export structured dataset
pipeline.export("metformin_misinfo_dataset.csv")
```

## Project Structure

```
pharma-misinfo-tracker/
├── src/
│   ├── collectors/          # Data collection modules
│   │   ├── google_trends.py # Google Trends time series
│   │   ├── news_api.py      # News article collection
│   │   ├── reddit.py        # Reddit post/comment collection
│   │   ├── wayback.py       # Wayback Machine archived pages
│   │   └── base.py          # Abstract collector interface
│   ├── classifiers/         # Content classification
│   │   ├── llm_classifier.py    # LLM-based (Claude/OpenAI) classifier
│   │   ├── rule_classifier.py   # Rule-based keyword classifier
│   │   └── themes.py            # Theme/severity definitions
│   ├── storage/             # Data persistence
│   │   ├── database.py      # SQLite storage layer
│   │   └── models.py        # Data models
│   └── visualization/       # Figure generation
│       ├── timeline.py      # Temporal trend charts
│       ├── heatmap.py       # Theme × period heatmaps
│       └── dashboard.py     # Summary dashboards
├── config/
│   ├── config.example.yaml  # Template configuration
│   └── metformin.yaml       # Metformin-specific search config
├── data/
│   ├── raw/                 # Raw collected data
│   └── processed/           # Classified/structured data
├── notebooks/
│   └── analysis.ipynb       # Example analysis notebook
├── tests/
├── docs/
│   └── METHODS.md           # Methodological documentation
├── requirements.txt
├── LICENSE
└── CITATION.cff
```

## Misinformation Taxonomy

The default classification schema includes six negative misinformation themes:

| Theme | Description | Example |
|-------|-------------|---------|
| `ndma_cancer` | Exaggerated NDMA/cancer risk claims | "Metformin causes cancer" |
| `recall_confusion` | Conflating ER recall with all metformin | "All metformin is recalled" |
| `safety_fear` | General safety fearmongering | "Metformin is toxic/poison" |
| `patient_cessation` | Encouraging inappropriate medication stopping | "Stop all metformin immediately" |
| `anti_pharma` | Conspiracy narratives about FDA/pharma | "FDA is hiding contamination" |
| `predatory_alt` | Exploiting fear to sell alternatives | "Switch to berberine — safer than recalled metformin" |

Severity is rated 1–5 (1 = mildly misleading, 5 = dangerous with potential for direct patient harm).

Custom themes can be defined in `config/` for other recall events.

## Extending to Other Recalls

```yaml
# config/valsartan.yaml
drug_name: valsartan
recall_date: "2018-07-05"
search_terms:
  - "valsartan recall"
  - "valsartan NDMA"
  - "valsartan cancer"
  - "losartan alternative valsartan"
date_range: ["2017-01-01", "2023-12-31"]
themes:
  - ndma_cancer
  - recall_confusion
  - safety_fear
  - patient_cessation
  - class_effect_fear    # custom: fear spreading to entire ARB class
```

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

Priority areas:
- Additional data collectors (TikTok, YouTube transcripts, Facebook public pages)
- Multilingual support (misinformation in non-English communities)
- Validation studies comparing LLM classification to manual expert coding
- Additional recall case studies (ranitidine, valsartan, losartan)

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{pharma_misinfo_tracker,
  author = {[Your Name]},
  title = {PharmaMisinfo Tracker: An Open-Source Framework for Monitoring Pharmaceutical Misinformation Following Drug Recalls},
  year = {2026},
  url = {https://github.com/YOUR_USERNAME/pharma-misinfo-tracker}
}
```

## Affiliation

Developed by Prateek Shukla, MD Assistant Professor of Medicine Division of Endocrinology, Department of Medicine, UMass Chan Medical School, Worcester, MA.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Disclaimer

This tool is for research purposes only. It does not provide medical advice. The classification of content as "misinformation" reflects the judgment of the classification system and should be validated by domain experts. Always consult healthcare providers for medical decisions.
