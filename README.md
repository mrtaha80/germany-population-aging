# Population ageing across German regions

A reproducible portfolio project comparing Eurostat's published share of residents aged 65+ across Germany's NUTS 2 regions.

**Current status:** refreshed data pipeline, automated tests, interactive dashboard preview, and Power BI starter files are available. A native `.pbix` still needs to be created in Power BI Desktop.

## Interactive dashboard

[Open the German regional ageing dashboard](https://app.clickup.com/90122145635/artifact/2kxv5kv3-572?version=1)

The dashboard shows the regional median trend, 2025 regional ranking, selected-region trajectory, and percentage-point change since 2014. It is descriptive and does not establish causes of population change.

## Research question and measure

How did the share of people aged 65 years and over change across Germany's NUTS 2 regions from 2014 to 2025?

Use Eurostat indicator `PC_Y65_MAX`, **Proportion of population aged 65 years and more**, in unit `PC` (percentage), from [`demo_r_pjanind2`](https://ec.europa.eu/eurostat/databrowser/product/view/demo_r_pjanind2). This is already a percentage: do not divide it again by population or rebuild it from single-age values.

The first table explored, `demo_r_d2jan`, lacks usable German regional observations for some oldest single-age groups in 2014–2025. Its interim CSV is not used for findings; the project now uses Eurostat's published regional share indicator.

## Reproduce the data pipeline

```powershell
py -m pip install -r requirements.txt
py src/download_data.py
py src/inspect_data.py
py src/clean_data.py
py -m unittest discover -s tests -v
```

Raw and processed local data are excluded from Git. The scripts record source/retrieval metadata and preserve Eurostat flags. See [`data/README.md`](data/README.md).

## Power BI files

See [`powerbi/README.md`](powerbi/README.md) for the import steps and caveats. The folder includes a regional CSV, theme, DAX measures, and a build guide. In Power Query, unpivot the year columns to create a long table for line charts. The `b` observation flag marks a break in the time series in 2023 and must be disclosed. Regional averages are not population-weighted national estimates.

## Analysis plan

1. Validate the indicator, unit, German NUTS 2 coverage, flags, and years.
2. Compare regional trajectories and changes in percentage points.
3. Build the Power BI report and save the `.pbix` after validating the visuals.
4. Write findings and limitations from the refreshed dataset; do not infer causes from descriptive shares alone.

## Repository map
- `src/`: download, inspect, and clean scripts.
- `tests/`: automated checks with synthetic fixtures.
- `data/`: source instructions and local raw/processed data.
- `powerbi/`: regional data and Power BI starter pack.
- `notebooks/`, `reports/`: future exploration and written results.

## Kurz auf Deutsch
Dieses Portfolio-Projekt vergleicht den Eurostat-Anteil der Bevölkerung ab 65 Jahren in den NUTS-2-Regionen Deutschlands. Verwendet wird der Indikator `PC_Y65_MAX` aus `demo_r_pjanind2` (Einheit `PC`, Prozent). Das Dashboard und die Power-BI-Startdateien sind im Repository dokumentiert. Die 2023er Werte tragen den Hinweis `b` für einen Zeitreihenbruch. Ergebnisse sind deskriptiv und erklären nicht die Ursachen der Veränderungen.
