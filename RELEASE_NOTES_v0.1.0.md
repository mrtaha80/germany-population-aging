# v0.1.0 — German regional population ageing (preview)

**Release status:** portfolio preview. The analysis pipeline, refreshed regional dataset, tests, Power BI starter files, and interactive dashboard preview are ready. A native Power BI `.pbix` has not yet been created, so this should be published as a **pre-release/preview**, not presented as a finished Power BI report.

## What’s included

- Reproducible Eurostat downloader for `demo_r_pjanind2`, with compressed-file validation, header checks, retrieval metadata, and SHA-256 checksum.
- Data inspection and cleaning scripts for Eurostat’s regional population-structure indicator `PC_Y65_MAX` in unit `PC`.
- Cleaned-data output workflow covering 38 German NUTS 2 regions from 2014–2025; raw and processed local data are excluded from Git.
- Automated tests for indicator/geography filtering, percentage-point change calculations, Eurostat observation flags, and missing observations.
- Power BI starter files: regional data CSV, theme, DAX measures, and a build guide.
- Interactive dashboard preview: [German regional ageing dashboard](https://app.clickup.com/90122145635/artifact/2kxv5kv3-572?version=1).

## Headline findings in the supplied 2014–2025 extract

- The median regional share aged 65+ increased from **20.3% (2014)** to **22.6% (2025)**, a rise of **2.3 percentage points**.
- **35 of 38** regions increased, **one** was unchanged, and **two** declined.
- The highest 2025 share was **Chemnitz: 30.4%**.
- The largest rise was **Mecklenburg-Vorpommern: +5.5 percentage points**.
- The largest decline was **Hamburg: −0.9 percentage points**.

These are descriptive regional comparisons. The median across regions is **not** a population-weighted estimate for Germany and does not explain why regional shares changed.

## Data-quality note

Eurostat marks the 2023 observations with `b` (break in time series). Preserve this flag and mention it when interpreting the time series, especially comparisons around 2023.

## Verification

The committed automated suite was run with `python -m unittest discover -s tests -v`: **5 tests passed**. Tests use synthetic fixtures; they verify pipeline behavior and are not an independent validation of every live Eurostat observation.

## Build the native Power BI report

Import `powerbi/germany_nuts2_ageing_powerbi.csv`, keep the region and `flag_2023` columns, unpivot the 2014–2025 columns in Power Query, apply the theme, and add the DAX measures as described in `powerbi/PowerBI_build_guide.md`. Save the finished report as a `.pbix` before calling the Power BI deliverable complete.

## Reproduce

```powershell
py -m pip install -r requirements.txt
py src/download_data.py
py src/inspect_data.py
py src/clean_data.py
py -m unittest discover -s tests -v
```

For an actual GitHub release, use tag **`v0.1.0`** and mark it as a **pre-release** until the `.pbix` is included and reviewed.