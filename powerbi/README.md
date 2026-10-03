# Power BI deliverables

## Dashboard
An interactive dashboard preview is available in ClickUp: [German regional ageing dashboard](https://app.clickup.com/90122145635/artifact/2kxv5kv3-572?version=1).

## Build in Power BI Desktop
Use `germany_nuts2_ageing_powerbi.csv` as the source. In Power Query, keep `geo` and `region_name`, then unpivot all year columns into `Year` and `Share`. Apply `german_atlas_theme.json`, then add measures from `measures.dax`. Follow `PowerBI_build_guide.md` for layout and settings. This repository does not yet contain a native `.pbix`; create and save it in Power BI Desktop after loading the files.

## Measure and caveat
Eurostat `demo_r_pjanind2`, indicator `PC_Y65_MAX` (proportion of population aged 65 years and more), unit `PC` (percentage). The CSV covers 38 German NUTS 2 regions across 2014–2025. The 2023 observations carry the `b` flag (break in time series), which must be disclosed when interpreting trends. Regional averages are not population-weighted national estimates.
