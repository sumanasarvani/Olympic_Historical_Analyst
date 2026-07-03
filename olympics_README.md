# Olympics Historical Analyst
### Natural Language Analytics with Snowflake Cortex Analyst

A simple, single-table portfolio project demonstrating **Text-to-SQL over structured data** using Snowflake Cortex Analyst and Cortex Search — built on 120 years of real Olympic athlete and medal history.

---

## What This Is

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

## Semantic Model

One logical table (`athlete_events`), no relationships section — the simplest possible semantic model shape. Defined in `olympics_semantic_model.yaml`, converted into a native Snowflake Semantic View via `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML`.

- **Dimensions**: Sex, Team, NOC, Season, City, Sport, Event, Medal, Year, Games — categorical fields to group/filter by
- **Facts**: Age, Height, Weight — raw numeric values aggregatable per row
- **Metrics**: pre-defined business logic to remove ambiguity, e.g.:
  - `athlete_count` = `COUNT(DISTINCT ID)` — distinct people
  - `event_entry_count` = `COUNT(*)` — total athlete-event rows (one athlete can have many)
  - `medal_count`, `gold_count`, `silver_count`, `bronze_count` — explicit medal-counting logic, since "how many medals" has more than one plausible (and wrong) interpretation without a defined metric

---

## Cortex Search Integration

Two fuzzy-match search services solve the same literal-retrieval problem as any Cortex Analyst project: real data uses specific literal strings, users type approximate ones.

| Search Service | Column | Solves |
|---|---|---|
| `team_search` | `team` | "USA" / "Holland" → resolves to the actual stored variants |
| `sport_search` | `sport` | approximate/misspelled sport names |

**Proof point:** asking *"How many athletes competed for Great Britain?"* correctly generated a `WHERE team IN ('Great Britain', 'Great Britain-1', 'Great Britain-2', 'Great Britain-3', 'Great Britain-4', 'Great Britain/Germany')` clause — finding every real variant of that team name in the data, not just a single obvious match.

---

## Streamlit Application

Single-page chat interface (`olympics_streamlit_app.py`), deployed as Streamlit in Snowflake:

- KPI cards (distinct athletes, total entries, medals awarded, countries represented)
- Natural language chat → Cortex Analyst interpretation → generated SQL → results table → auto-chart
- Generated SQL shown transparently for every answer
- Suggested starter questions, query history

---

## Tech Stack

Snowflake (Cortex Analyst, Cortex Search, Semantic Views, Streamlit in Snowflake), Python/Streamlit, Kaggle dataset.

---

## Repository Structure

```
├── README.md
├── initial_setup.sql              # Database, schema, warehouse, stage, table load
├── olympics_semantic_model.yaml   # Semantic model definition
├── create_semantic_view_v2.sql    # Semantic view creation (with Cortex Search linked)
├── cortex_search.sql              # Cortex Search service definitions
└── olympics_streamlit_app.py      # Streamlit chat application
```

---

## Setup / Reproduction

1. Download `athlete_events.csv` from [Kaggle](https://www.kaggle.com/datasets/heesoo37/120-years-of-olympic-history-athletes-and-results)
2. Run `initial_setup.sql` — creates database/schema/warehouse, loads the CSV into one table
3. Run `create_semantic_view_v2.sql` — builds the semantic view (this file already includes the full YAML, with Cortex Search services linked in)
4. Run `cortex_search.sql` first if creating the search services fresh — required before step 3
5. Deploy `olympics_streamlit_app.py` as a Streamlit in Snowflake app

---

## Demo Questions

- "How many athletes have competed?"
- "Which country has won the most gold medals?"
- "What's the average age of athletes by sport?"
- "How has the number of female athletes changed over time?"
- "How many athletes competed for Great Britain?" *(tests Cortex Search)*

---

## Limitations

- Single-table design — no join complexity, by design, to keep this project approachable
- Historical team-name inconsistencies in the raw data (e.g. "Holland" vs. "Netherlands" both appearing as separate literal values) reflect real quirks in the source dataset, not cleaning errors
- Data ends at Rio 2016; no more recent Games included in this dataset
