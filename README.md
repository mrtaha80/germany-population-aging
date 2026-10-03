# Population ageing across German regions

A reproducible portfolio project comparing Eurostat's published share of residents aged 65+ across Germany's NUTS 2 regions.

**Current status:** pipeline switched to Eurostat's direct regional 65+ proportion indicator. No interpretation of regional trends has been written yet.

## Research question
How did the share of people aged 65 years and over change across Germany's NUTS 2 regions from 2014 to 2025?

## Measure
Use Eurostat indicator `PC_Y65_MAX`, **Proportion of population aged 65 years and more**, in unit `PC` (percentage), from [`demo_r_pjanind2`](https://ec.europa.eu/eurostat/databrowser/product/view/demo_r_pjanind2). The indicator is already a percentage. Do not divide it again by total population and do not reconstruct it from incomplete single-age groups.

The first table tried, `demo_r_d2jan`, provides single-year ages but the German regional extract has no usable `Y95`–`Y99` or `Y_OPEN` observations for 2014–2025. That CSV is an intermediate failed attempt, not an analytical result. The new pipeline uses the official regional share indicator instead.

## Reproduce

```powershell
py -m pip install -r requirements.txt
py src/download_data.py
py src/inspect_data.py
py src/clean_data.py
py -m unittest discover -s tests -v
```

The raw Eurostat data and local download metadata are kept out of Git. The processed CSV is also local by default. See [`data/README.md`](data/README.md) for sources and commands.

## Planned analysis
1. Validate the official indicator, percentage unit, German NUTS 2 coverage, flags, and years.
2. Compare regional trajectories from 2014 to 2025 and calculate percentage-point changes.
3. Create a Power BI dashboard with time trends, latest-year ranking, and change since 2014.
4. Write evidence-based findings and limitations after the refreshed data passes checks.

A changing share is descriptive; it does not by itself explain why a region's population structure changed.

## Repository map
- `src/`: download, inspect, and clean scripts.
- `tests/`: automated checks using synthetic fixtures.
- `data/`: source instructions and local raw/processed data.
- `notebooks/`, `reports/`, `powerbi/`: exploration, findings, and dashboard deliverables.

## Kurz auf Deutsch
Dieses Projekt vergleicht den Eurostat-Anteil der Bevölkerung ab 65 Jahren in den NUTS-2-Regionen Deutschlands. Verwendet wird der Indikator `PC_Y65_MAX` aus `demo_r_pjanind2` (Einheit `PC`, Prozent). Das ist ein veröffentlichter Anteil; er wird nicht erneut durch die Gesamtbevölkerung geteilt. Ergebnisse folgen erst nach Datenprüfung.
