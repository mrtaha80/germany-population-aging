# Data

Source: Eurostat `demo_r_d2jan`, [dataset page](https://ec.europa.eu/eurostat/databrowser/view/demo_r_d2jan/default/table?lang=en).

Download the compressed TSV from:

`https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_d2jan?format=TSV&compressed=true`

Save the downloaded file under `data/raw/`. Do not commit raw files. Record the retrieval date, source URL, dataset code, and the period downloaded in your analysis notes.

Before filtering, inspect the TSV header and dataset dimensions. Confirm the exact codes for Germany NUTS 2 geographies, total sex, total population, and population aged 65+. Check the units and observation flags. Do not assume code labels without checking Eurostat's data structure/codelists.