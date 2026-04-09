# Methodological Documentation

## Study Design

This framework implements a **systematic AI-assisted content analysis** of pharmaceutical misinformation. The methodology combines automated content collection from multiple web sources with LLM-based classification and human expert validation.

## Data Collection Protocol

### Sources and Access

| Source | Method | Historical Range | Authentication |
|--------|--------|-----------------|----------------|
| Google Trends | `pytrends` library | 2004–present | None required |
| Google News RSS | RSS feed parsing | ~30 days (live) | None required |
| NewsAPI.org | REST API | ~30 days (free tier) | API key (free) |
| Reddit (live) | PRAW library | Current posts | OAuth app credentials |
| Reddit (historical) | Arctic Shift API | 2005–2023 | None required |
| Wayback Machine | CDX API | Archived dates | None required |
| LexisNexis | Institutional access | Full archive | University credentials |

### Search Strategy

For each recall event, the following search term categories are used:

1. **Drug + recall terms**: `[drug] recall`, `[drug] recalled`, `[drug] FDA recall`
2. **Drug + contaminant**: `[drug] NDMA`, `[drug] contamination`, `[drug] impurity`
3. **Drug + fear terms**: `[drug] cancer`, `[drug] dangerous`, `[drug] toxic`
4. **Drug + cessation**: `stop taking [drug]`, `[drug] alternative`, `quit [drug]`
5. **Drug + conspiracy**: `[drug] coverup`, `FDA [drug] hiding`, `big pharma [drug]`

### Inclusion/Exclusion Criteria

**Included:**
- Publicly accessible web content
- Content in English
- Published within the defined study period
- Contains claims about the specified drug

**Excluded:**
- Content behind paywalls or login walls (unless accessible via institutional subscription)
- Private social media posts
- Content in languages other than English (unless multilingual module is enabled)
- Scientific literature presenting primary research findings (classified separately)

## Classification Protocol

### Automated Classification (LLM-based)

Each collected item is classified using a structured prompt sent to a large language model (Claude, Anthropic). The prompt requests:

1. **Theme assignment** from a predefined taxonomy
2. **Severity rating** on a 1–5 scale
3. **Source type** classification
4. **Time period** assignment
5. **Brief summary** of content and classification rationale

### Severity Scale

| Rating | Label | Definition |
|--------|-------|-----------|
| 1 | Mildly Misleading | Minor framing issues; content is mostly accurate |
| 2 | Slightly Misleading | Key omissions or slightly misleading framing |
| 3 | Moderate | Significant exaggerations or important omissions |
| 4 | Misleading | Clearly misleading claims that could affect patient behavior |
| 5 | Dangerous | Could cause direct patient harm through medication cessation or inappropriate substitution |

### Validation

LLM classifications should be validated by:
1. **Expert review**: A domain expert (e.g., physician, pharmacist) reviews a random sample (≥20%) of classified items
2. **Inter-rater reliability**: Cohen's kappa or Fleiss' kappa for theme agreement
3. **Rule-based cross-check**: Keyword-based classifier run in parallel to flag discrepancies

## Limitations

1. **LLM classification bias**: Large language models may have systematic biases in classifying health content
2. **Temporal coverage gaps**: Free API tiers have limited historical reach
3. **Platform access restrictions**: Many social media platforms restrict API access (Twitter/X, Facebook, TikTok)
4. **Language limitation**: English-only by default
5. **Sampling bias**: Search-based collection may miss content not indexed by search engines
6. **Ecological validity**: Automated collection cannot capture the full context of how misinformation is consumed

## Ethical Considerations

- No personally identifiable information is collected or stored
- Reddit usernames are anonymized in published datasets
- Content is analyzed for research purposes under fair use
- The tool does not provide medical advice
- Classifications represent algorithmic judgment and require expert validation
