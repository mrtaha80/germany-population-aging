# Population ageing across German regions

A portfolio project using Eurostat data to compare population ageing across Germany's NUTS 2 regions.

**Status:** project scaffold; analysis not started. No results or conclusions are claimed yet.

## Research question
How did the share of people aged 65 and over change across Germany's NUTS 2 regions from 2014 to the latest complete year available in Eurostat?

## Planned measures
- Population aged 65 and over (`Y_GE65` if available in the dataset age dimension).
- Total population (`TOTAL`).
- 65+ share = population aged 65+ / total population × 100.
- Change in percentage points between 2014 and the latest complete year.

Before analysis, verify the dataset's dimensions, units, age codes, regional codes, time coverage, missing values, and flags. Use the same year and geography definitions for numerator and denominator. Do not add age bands if `Y_GE65` is already an aggregate.

## Data
Official source: Eurostat, [Population on 1 January by age, sex and NUTS 2 region (`demo_r_d2jan`)](https://ec.europa.eu/eurostat/databrowser/view/demo_r_d2jan/default/table?lang=en).

- [Eurostat dataset API, compressed TSV](https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_d2jan?format=TSV&compressed=true)
- [Eurostat API format documentation](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/sdmx2-1/data-query)
- Download the source data yourself; raw data files are intentionally not committed. See [`data/README.md`](data/README.md).

## Planned workflow
1. Inspect and download the source data, record the retrieval date and dataset metadata.
2. Filter to Germany's NUTS 2 regions, total sex, total population, and the 65+ age aggregate.
3. Validate units, completeness, duplicate keys, and aggregation logic.
4. Calculate the 65+ share and change over time with Python/pandas.
5. Create a Power BI dashboard with a trend view, latest-year regional comparison, and change since 2014.
6. Document findings, caveats, and reproducible steps.

## Repository map
- `data/`: instructions and local-data location; raw files are not tracked.
- `notebooks/`: exploratory work.
- `src/`: reusable analysis code.
- `reports/`: written findings and charts.
- `powerbi/`: dashboard project and screenshots.

## Reproducibility
Python 3.11 or newer is recommended. Create an environment, install the packages in `requirements.txt`, download the source file following `data/README.md`, then run the notebook in `notebooks/` once it is added.

## Limitations to investigate
- Eurostat regional data can be revised and can contain flags or missing values.
- NUTS regional boundaries/classifications can change; document which classification is used and how codes are handled.
- A change in the 65+ share describes population structure, not the causes of demographic change.
- This repository currently contains a plan only; findings will be added after the data is checked.

## Short summary auf Deutsch
Dieses Portfolio-Projekt untersucht, wie sich der Anteil der Bevölkerung ab 65 Jahren zwischen 2014 und dem letzten vollständigen verfügbaren Jahr in den NUTS-2-Regionen Deutschlands verändert hat. Datengrundlage ist Eurostat (`demo_r_d2jan`). Die Analyse und ihre Ergebnisse werden erst nach Prüfung der Daten ergänzt.
