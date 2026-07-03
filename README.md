# Olympics Historical Analyst

A simple, single-table portfolio project demonstrating **Text-to-SQL over structured data** using Snowflake Cortex Analyst and Cortex Search — built on 120 years of real Olympic athlete and medal history.

---

## What it does

Ask questions about Olympic history in plain English and get correct, transparent SQL back — no dashboard, no pre-built charts, no anticipating every question in advance. A semantic model teaches Cortex Analyst what the data means (what counts as an "athlete" vs. an "entry", what a "medal" is, which fields people might phrase differently), and Cortex Search handles fuzzy/approximate country and sport names so a question like *"How many athletes competed for Great Britain?"* still resolves correctly even though the real data stores that as `"UK"`.

This project is intentionally simple: one table, no data pipeline, no external data blend — a deliberate contrast to a larger multi-table Cortex Analyst project, built to demonstrate the core concepts cleanly without the added complexity of a full data engineering pipeline.

---

## Dataset

**[120 Years of Olympic History: Athletes and Results](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results)** (Kaggle) — 271,116 rows covering every Olympic Games from Athens 1896 to Rio 2016.

One row = one athlete competing in one event at one Games. Columns: `ID, Name, Sex, Age, Height, Weight, Team, NOC, Games, Year, Season, City, Sport, Event, Medal`.

Loaded as-is, with no transformation — the only setup step is teaching Snowflake to treat the literal `"NA"` values as true NULLs (used for non-medal entries and missing physical stats on early 20th-century athletes).

---

## Architecture

```
athlete_events.csv (Kaggle)
        │
        ▼
Snowflake Internal Stage (olympics_stage)
        │  COPY INTO (match-by-column-name)
        ▼
CORE.ATHLETE_EVENTS  ── single table, 271,116 rows
        │
        ├──► 2x Cortex Search Services
        │      (fuzzy match: sport, team)
        │
        ▼
Semantic View (OLYMPICS_SEMANTIC_MODEL)
        │  1 logical table, dimensions, facts,
        │  metrics, Cortex Search links
        │  (no relationships needed — single table)
        ▼
Cortex Analyst  ◄── Streamlit in Snowflake (chat UI)
```

---

## Repository Structure

```
├── README.md
├── Setup.sql              # Database, schema, warehouse, stage, table load
├── olympics_semantic_model.yaml   # Semantic model definition
├── create_olympics_semantic_model_view.sql    # Semantic view creation (with Cortex Search linked)
├── olympics_cs.sql              # Cortex Search service definitions
└── streamlit_app.py      # Streamlit chat application
```

---

## Setup / Reproduction

1. Download `athlete_events.csv` from [Kaggle](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results)
2. Run `Setup.sql` — creates database/schema/warehouse, loads the CSV into one table
3. Run `create_olympics_semantic_model_view.sql` — builds the semantic view (this file already includes the full YAML, with Cortex Search services linked in)
4. Run `olympics_cs.sql` first if creating the search services fresh — required before step 3
5. Deploy `streamlit_app.py` as a Streamlit in Snowflake app
