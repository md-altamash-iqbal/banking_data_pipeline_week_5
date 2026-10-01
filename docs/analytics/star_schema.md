# Week 5 Data Lineage and Architecture

## End-to-End Data Flow

```text
┌──────────────────────────────┐
│        Raw Branch CSVs       │
│        data/raw/             │
│  BR001 / BR002 / BR003       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          Ingestion           │
│     src/ingestion/           │
│                              │
│ Read CSV → Parse Records     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Validation + Data Quality  │
│     validation.py            │
│     dq_metrics.py            │
│                              │
│ Valid → validated data       │
│ Invalid → DQ output          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       banking.db             │
│                              │
│ branches                     │
│ customers                    │
│ accounts                     │
│ transactions                 │
└──────────────┬───────────────┘
               │
               │ Daily transaction files
               │
               ▼
┌──────────────────────────────┐
│      Incremental Load        │
│ src/operational/             │
│ incremental_load.py          │
│                              │
│ INSERT new transaction IDs   │
│ UPDATE existing IDs          │
│ using UPSERT                 │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     Updated banking.db       │
│                              │
│ Final transactions: 20       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Analytical Transformation  │
│ src/analytics/               │
│ build_analytics.py           │
│                              │
│ Normalize dates              │
│ Build dimensions             │
│ Build transaction fact       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        analytics.db          │
│                              │
│ dim_branch                   │
│ dim_customer                 │
│ dim_account                  │
│ dim_date                     │
│ fact_transaction             │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Analytical SQL         │
│    sql/analytical_queries    │
│                              │
│ Aggregations                 │
│ CASE                         │
│ CTEs                         │
│ Window functions             │
│ Business questions           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Business Results       │
│                              │
│ Transaction totals           │
│ Branch analysis              │
│ Customer/account activity    │
│ Daily analysis               │
│ Transaction classification   │
└──────────────────────────────┘
