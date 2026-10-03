# Power BI build guide

## Load and reshape
1. In Power BI Desktop choose **Get data → Text/CSV** and select `germany_nuts2_ageing_powerbi.csv`; choose **Transform Data**.
2. Select `geo` and `region_name`, then choose **Transform → Unpivot Columns → Unpivot Other Columns**. Rename `Attribute` to `Year`, `Value` to `Share`.
3. Set `Year` to Whole number and `Share` to Decimal number. Close & Apply. Rename the table `Ageing`.
4. Choose **View → Themes → Browse for themes** and import `german_atlas_theme.json`.
5. Create each measure from `measures.dax` separately via **New measure**.

## Suggested one-page report
- Header: “Germany, getting older” · share of residents aged 65+ · NUTS 2 · 2014–2025.
- KPI cards: latest regional median, highest 2025 share, largest change since 2014.
- Left: line chart by year and region, with a region slicer.
- Right: horizontal bar chart of 2025 share, descending by region.
- Bottom: table with region, 2014 share, 2025 share, change (pp), and Eurostat flag.
- Add year and region slicers.

## Data notes
- Eurostat `demo_r_pjanind2`, indicator `PC_Y65_MAX`, unit `PC`.
- Published value is already a percentage; do not divide by population or multiply by 100.
- `b` marks a break in time series in 2023; preserve and disclose it. `2023` flag is discussed in project notes; add one in Power BI if using the 2023 series.
- A median/mean across regions is not Germany’s population-weighted national share.
- CSV covers 38 German NUTS 2 regions × 12 years, 2014–2025. It is a reshaped portfolio dataset; use repo scripts to refresh from the official API.
