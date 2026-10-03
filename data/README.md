# Data

## Official measure

Use Eurostat dataset [`demo_r_pjanind2`](https://ec.europa.eu/eurostat/databrowser/product/view/demo_r_pjanind2), *Population structure indicators by NUTS 2 region*. The project measure is indicator `PC_Y65_MAX`, labelled **Proportion of population aged 65 years and more**, in unit `PC` (percentage). This is a published proportion, not a count; do not divide it by population total or sum individual ages.

Eurostat also reports its NUTS 2 structure indicators via [the dataset API](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanind2?lang=EN). Dataset dimensions are annual frequency, demographic indicator, unit, geography, and time. Source can be revised; downloader metadata stores retrieval time and checksum.

## Reproducible download

From the repository root:

```powershell
py -m pip install -r requirements.txt
py src/download_data.py
```

This saves `data/raw/demo_r_pjanind2.tsv.gz` and a local metadata JSON sidecar. Raw files are ignored by Git. Use `py src/download_data.py --force` to replace an existing download. The script validates gzip integrity, expected dataset dimensions, and annual columns.

## Inspect and clean

```powershell
py src/inspect_data.py
py src/clean_data.py
```

The audit prints available indicator and unit codes and checks German NUTS 2 coverage. The cleaner filters annual data, `PC_Y65_MAX`, unit `PC`, and Germany's four-character NUTS 2 codes; it preserves observation flags and outputs the published share plus percentage-point change since 2014. It does not impute missing values.

Output: `data/processed/germany_nuts2_population_aging_2014_2025.csv`. Record the retrieval date and checksum when reproducing results.
