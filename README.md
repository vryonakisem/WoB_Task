# Helping Hands Home Care — Live-In Care Profitability Analysis

End-to-end data analysis of a UK home care provider's live-in care service.
Built a PostgreSQL database from raw Excel files, wrote SQL to answer 6 business
questions, and delivered insights in a 10-slide PowerPoint deck.

---

## The Brief

Helping Hands Home Care asked for analysis of their live-in care profitability
across FY2021–2023. Key questions:

1. How has profit grown year-on-year, and what are the main drivers?
2. What impact does a customer's age and condition have on profitability?
3. Are there any material mix changes (funding, geography, gender) over 3 years?
4. Does having more than one carer drive up customer churn?
5. What data limitations exist?
6. Any other interesting themes?

---

## Data Sources

| File | Contents |
|------|----------|
| `001_Customer_Data.xlsx` | 5 sheets — customer info, weekly shifts, weekly prices, funders, conditions |
| `002_Carer_Data.xlsx` | 2 sheets — carer profiles, weekly carer costs |
| `003_PostCodeRegions.xlsx` | Postcode → region mapping |

---

## What I Built

### Database (PostgreSQL 18)
Designed and built a local PostgreSQL database with 8 normalised tables:

| Table | Rows | Description |
|-------|------|-------------|
| `customers` | 2,700 | Customer demographics, region, funding type |
| `shifts` | 104,395 | Weekly shifts per customer-carer pair |
| `prices` | 83,754 | Weekly price charged per customer |
| `carer_costs` | 99,142 | Weekly cost per carer |
| `conditions` | 1,880 | Customer medical conditions |
| `carers` | 2,855 | Carer profiles and nationality |
| `funders` | 3,017 | Funder details |
| `postcode_regions` | 125 | Region mapping |

The key technical challenge was transforming **wide-format data** (125 weekly
columns per row) into **long-format** rows suitable for SQL analysis — reducing
~1.6M potential rows to 104,395 rows of actual shift data.

### Analysis (SQL)
All analysis performed in SQL. Key queries cover:
- Year-on-year profit growth with margin decomposition
- Profit bridge (waterfall) — price vs volume vs cost effects
- Profitability segmented by age band and medical condition
- Mix shift analysis by funding type and region
- Churn analysis by number of carers, with tenure context

### Presentation (PowerPoint)
10-slide deck covering all 6 questions with charts, waterfall diagrams,
and actionable recommendations.

---

## Key Findings

| Finding | Detail |
|---------|--------|
| **Profit grew 20.6%** | £28.6M → £34.4M (2021 → 2022) |
| **Price was the driver** | Revenue per shift +15% (£235 → £271). Volume was flat |
| **Cost discipline held** | Carer costs grew only 7.5% vs 15% price growth |
| **Split Funded growing** | Share rose 33% → 38% of revenue — the highest-margin segment |
| **Counter-intuitive churn** | 1-carer customers churn most (86%) but avg tenure is only 0.2 years — likely planned discharges not avoidable churn |
| **Depression patients most profitable** | £50.9k avg profit vs £29.7k for Cancer patients |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python (pandas, sqlalchemy) | Data cleaning, reshaping, loading |
| PostgreSQL 18 | Database |
| TablePlus | SQL query interface |
| PowerPoint | Presentation |

---

## Files in This Repo

```
├── README.md                          — this file
├── load_to_postgres.py                — builds the entire database from Excel files
├── analysis_queries.sql               — all SQL queries used in the analysis
└── HelpingHands_LiveIn_Analysis.pptx  — final presentation deck
```

---

## How to Reproduce

### 1. Requirements
```bash
pip install pandas sqlalchemy psycopg2-binary openpyxl
```

### 2. Set up PostgreSQL
```bash
psql -c "CREATE DATABASE helping_hands;"
```

### 3. Update the script
Open `load_to_postgres.py` and update:
```python
engine = create_engine("postgresql+psycopg2://YOUR_USER:@127.0.0.1:5433/helping_hands")
BASE = "/path/to/your/data/files/"
```

### 4. Run the loader
```bash
python3 load_to_postgres.py
```

### 5. Open TablePlus and connect
```
Host:     127.0.0.1
Port:     5433
Database: helping_hands
```

### 6. Run any query from analysis_queries.sql

---

## If I Had More Data

- **Discharge reason** — to distinguish avoidable churn from planned end-of-life discharge
- **NPS / satisfaction scores** — to predict churn earlier
- **Staff turnover by region** — to understand carer supply risk
- **Referral source** — to optimise customer acquisition spend
- **Spot vs contracted pricing** — to understand pricing flexibility

---

*Analysis by Emmanouil Vryonakis*
