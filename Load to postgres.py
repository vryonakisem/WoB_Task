"""
The Python script used to load and transform the data into PostgreSQL was generated with the assistance of AI tools (Claude), 
based on my precise specifications and analytical requirements. 
I directed the structure of the database, defined the transformation logic required 
(including the wide-to-long reshape, column standardisation, condition label normalisation and region enrichment), 
and validated every output against the underlying data to ensure accuracy.
The script was not written independently line by line, but the decisions behind it — what tables to create, 
how to join them, what to clean and what to preserve — were entirely my own. 

The code is fully reproducible and auditable, and I can explain every step of it.

This is consistent with the broader AI disclosure included in the presentation and covering email.
Helping Hands — Excel to PostgreSQL Loader
===========================================
SETUP:
  pip install pandas sqlalchemy psycopg2-binary openpyxl

USAGE:
  1. Update DB_CONFIG with your Postgres password
  2. Update FILE_PATHS with the location of your 3 Excel files
  3. Run: python load_to_postgres.py
"""

import pandas as pd
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# CONFIG — UPDATE THESE
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "127.0.0.1",
    "port":     5432,
    "database": "helping_hands",
    "user":     "postgres",
    "password": "YOUR_PASSWORD_HERE",   # ← change this
}

FILE_PATHS = {
    "customers": "001_Customer_Data.xlsx",   # ← update path if needed
    "carers":    "002_Carer_Data.xlsx",
    "postcodes": "003_PostCodeRegions.xlsx",
}

# ─────────────────────────────────────────────
# CONNECT
# ─────────────────────────────────────────────
url = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
engine = create_engine(url)
print("✅ Connected to PostgreSQL")


# ─────────────────────────────────────────────
# HELPER: melt wide (weekly columns) to long
# ─────────────────────────────────────────────
def melt_wide(df, id_cols, value_name):
    date_cols = [c for c in df.columns if c not in id_cols]
    melted = df.melt(
        id_vars=id_cols,
        value_vars=date_cols,
        var_name="week_date",
        value_name=value_name,
    )
    melted["week_date"] = pd.to_datetime(melted["week_date"])
    melted["year"] = melted["week_date"].dt.year
    melted = melted.dropna(subset=[value_name])
    return melted


# ─────────────────────────────────────────────
# LOAD CUSTOMER FILE
# ─────────────────────────────────────────────
print("\n📂 Reading customer file...")
cust_file = pd.read_excel(FILE_PATHS["customers"], sheet_name=None)

# --- customers table ---
cust_info = cust_file["Customer"].copy()
cust_info.columns = [c.strip() for c in cust_info.columns]
cust_info = cust_info[[
    "Customer External ID", "Postcode", "Gender",
    "Funded Type", "Start Date of Care in System",
    "End Date of Care", "Customer Age at Start of Care"
]]
cust_info.columns = [
    "customer_id", "postcode", "gender",
    "funded_type", "start_date", "end_date", "age_at_start"
]
cust_info["postcode_area"] = cust_info["postcode"].str.extract(r"^([A-Z]{1,2})")

# Load postcode regions so we can join region onto customers
postcodes = pd.read_excel(FILE_PATHS["postcodes"])
postcodes.columns = ["postcode_area", "postcode_area_name", "region"]
cust_info = cust_info.merge(
    postcodes[["postcode_area", "region"]], on="postcode_area", how="left"
)

cust_info.to_sql("customers", engine, if_exists="replace", index=False)
print(f"  ✅ customers: {len(cust_info):,} rows")

# --- shifts table ---
shifts_raw = cust_file["Customer Shifts "].copy()
shifts_raw.columns = [c.strip() for c in shifts_raw.columns]
# Fix column name typo in source file
shifts_raw.rename(
    columns={"Customer External ID`": "Customer External ID"}, inplace=True
)
shifts_long = melt_wide(
    shifts_raw,
    ["Customer External ID", "Funder External ID", "Carer External ID"],
    "shifts"
)
shifts_long.columns = [
    "customer_id", "funder_id", "carer_id", "week_date", "shifts", "year"
]
shifts_long.to_sql("shifts", engine, if_exists="replace", index=False)
print(f"  ✅ shifts:    {len(shifts_long):,} rows")

# --- prices table ---
prices_raw = cust_file["Customer Care Price"].copy()
prices_long = melt_wide(
    prices_raw,
    ["Customer External ID", "Funder External ID"],
    "price"
)
prices_long.columns = ["customer_id", "funder_id", "week_date", "price", "year"]
prices_long.to_sql("prices", engine, if_exists="replace", index=False)
print(f"  ✅ prices:    {len(prices_long):,} rows")

# --- conditions table ---
conditions = cust_file["Conditions"].copy()
conditions.columns = [
    c.strip().lower()
    .replace(" ", "_")
    .replace("'", "")
    .replace("chronic obstructive pulmonary disease", "copd")
    .replace("parkinsons_disease", "parkinsons")
    .replace("hearing_loss", "hearing_loss")
    .replace("heart_failure", "heart_failure")
    .replace("thyroid_concerns", "thyroid")
    for c in conditions.columns
]
conditions.rename(columns={"customer_external_id": "customer_id"}, inplace=True)

cond_cols = [c for c in conditions.columns if c != "customer_id"]
conditions["primary_condition"] = conditions[cond_cols].apply(
    lambda row: next((col for col in cond_cols if row[col] == 1), "None recorded"),
    axis=1,
)
conditions["num_conditions"] = conditions[cond_cols].sum(axis=1)
conditions.to_sql("conditions", engine, if_exists="replace", index=False)
print(f"  ✅ conditions:{len(conditions):,} rows")

# --- funders table ---
funders = cust_file["Funder"].copy()
funders.columns = ["customer_id", "funder_id", "funder_description", "postcode_sector"]
funders.to_sql("funders", engine, if_exists="replace", index=False)
print(f"  ✅ funders:   {len(funders):,} rows")


# ─────────────────────────────────────────────
# LOAD CARER FILE
# ─────────────────────────────────────────────
print("\n📂 Reading carer file...")
carer_file = pd.read_excel(FILE_PATHS["carers"], sheet_name=None)

# --- carer_costs table ---
costs_raw = carer_file["Carer Cost Per Week"].copy()
costs_long = melt_wide(costs_raw, ["Carer External ID"], "carer_cost")
costs_long.columns = ["carer_id", "week_date", "carer_cost", "year"]
costs_long.to_sql("carer_costs", engine, if_exists="replace", index=False)
print(f"  ✅ carer_costs:{len(costs_long):,} rows")


# ─────────────────────────────────────────────
# LOAD POSTCODE REGIONS
# ─────────────────────────────────────────────
print("\n📂 Reading postcode file...")
postcodes.to_sql("postcode_regions", engine, if_exists="replace", index=False)
print(f"  ✅ postcode_regions: {len(postcodes):,} rows")


# ─────────────────────────────────────────────
# ADD INDEXES FOR QUERY PERFORMANCE
# ─────────────────────────────────────────────
print("\n⚡ Adding indexes...")
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_shifts_customer   ON shifts(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_shifts_carer       ON shifts(carer_id);",
    "CREATE INDEX IF NOT EXISTS idx_shifts_week        ON shifts(week_date);",
    "CREATE INDEX IF NOT EXISTS idx_shifts_year        ON shifts(year);",
    "CREATE INDEX IF NOT EXISTS idx_prices_customer    ON prices(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_prices_week        ON prices(week_date);",
    "CREATE INDEX IF NOT EXISTS idx_costs_carer        ON carer_costs(carer_id);",
    "CREATE INDEX IF NOT EXISTS idx_costs_week         ON carer_costs(week_date);",
    "CREATE INDEX IF NOT EXISTS idx_customers_id       ON customers(customer_id);",
    "CREATE INDEX IF NOT EXISTS idx_conditions_id      ON conditions(customer_id);",
]
with engine.connect() as conn:
    for idx in indexes:
        conn.execute(text(idx))
    conn.commit()
print("  ✅ All indexes created")


# ─────────────────────────────────────────────
# QUICK VALIDATION
# ─────────────────────────────────────────────
print("\n📊 Row counts in database:")
tables = ["customers", "shifts", "prices", "carer_costs",
          "conditions", "funders", "postcode_regions"]
with engine.connect() as conn:
    for t in tables:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
        count = result.fetchone()[0]
        print(f"  {t:<20} {count:>8,} rows")

print("\n🎉 Database ready! Open TablePlus and connect to 'helping_hands'")
print("\nTry this query to test:\n")
print("""
  SELECT
      s.year,
      COUNT(DISTINCT s.customer_id)   AS customers,
      ROUND(SUM(p.price)::numeric, 0) AS total_revenue,
      ROUND(SUM(cc.carer_cost)::numeric, 0) AS total_cost,
      ROUND((SUM(p.price) - SUM(cc.carer_cost))::numeric, 0) AS total_profit
  FROM shifts s
  JOIN prices p
      ON s.customer_id = p.customer_id
     AND s.funder_id   = p.funder_id
     AND s.week_date   = p.week_date
  LEFT JOIN carer_costs cc
      ON s.carer_id  = cc.carer_id
     AND s.week_date = cc.week_date
  WHERE s.year IN (2021, 2022)
  GROUP BY s.year
  ORDER BY s.year;
""")
