# Data

Source: Eurostat `demo_r_d2jan`, [dataset page](https://ec.europa.eu/eurostat/databrowser/view/demo_r_d2jan/default/table?lang=en).

## Reproducible download

From the repository root, install dependencies and run:

```bash
python -m pip install -r requirements.txt
python src/download_data.py
```

The script downloads the compressed TSV to `data/raw/demo_r_d2jan.tsv.gz`, checks the gzip file and Eurostat TSV header, and writes a local metadata sidecar with retrieval time, source URL, response headers, time columns, file size, and SHA-256 checksum. Raw data and metadata are ignored by Git. To deliberately replace an existing download, run `python src/download_data.py --force`.

The downloader does not filter or clean observations. It retrieves the full current dataset so later analysis can apply explicit, auditable filters. The source may be revised by Eurostat; record the retrieval timestamp and checksum when reproducing results.

- [Dataset page](https://ec.europa.eu/eurostat/databrowser/view/demo_r_d2jan/default/table?lang=en)
- [Eurostat SDMX 2.1 API documentation](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/sdmx2-1/data-query)

Before analysis, inspect the TSV header and dataset dimensions. Confirm the exact codes for Germany NUTS 2 geographies, total sex, total population, and population aged 65+. Check units and observation flags. Do not assume category codes without checking Eurostat's data structure and codelists.