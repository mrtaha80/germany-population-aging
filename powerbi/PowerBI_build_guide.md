# Power BI build guide

## Load and reshape
1. In Power BI Desktop choose **Get data → Text/CSV** and select `germany_nuts2_ageing_powerbi.csv`; choose **Transform Data**.
2. Keep `geo`, `region_name`, and `flag_2023`; select only the year columns (`2014`–`2025`) and choose **Transform → Unpivot Columns**. Rename `Attribute` to `Year`, `Value` to `Share`.
3. Set `Year` to Whole number and `Share` to Decimal number. Keep `flag_2023` as text; Close & Apply. Rename the table `Ageing`.
4. Import `german_atlas_theme.json` via **View → Themes → Browse for themes**.
5. Create each measure from `measures.dax` separately via **New measure**.

## Suggested one-page report
- Header: “Germany, getting older” · share of residents aged 65+ · NUTS 2 · 2014–2025.
- KPI cards: latest regional median, highest 2025 share, largest change since 2014.
- Left: line chart by year and region, with a region slicer.
- Right: horizontal bar chart of 2025 share, descending by region.
- Bottom: table with region, 2014 share, 2025 share, change (pp), and `flag_2023`.
- Add year and region slicers.

## Data notes
- Eurostat `demo_r_pjanind2`, indicator `PC_Y65_MAX`, unit `PC`.
- Published value is already a percentage; do not divide by population or multiply by 100.
- `flag_2023 = b` marks a break in time series; preserve and disclose it.
- A median/mean across regions is not Germany’s population-weighted national share.
- CSV covers 38 German NUTS 2 regions × 12 years, 2014–2025. It is a reshaped portfolio dataset; use repo scripts to refresh from the official API.
