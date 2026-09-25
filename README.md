# OligoC4b

Notebook-based exploratory analysis of C4b-associated gene programs in disease-associated oligodendrocytes across single-cell, single-nucleus, Visium and Xenium datasets, extended to the wider complement system (C1q, C3, C5 and its receptors, Cfb) and to sixteen public datasets (mouse AD, aging and demyelination models, spatial AD, human AD and MS).

## Layout

```
notebooks/
  build/      raw data -> processed .h5ad (run first)
  analysis/   downstream analyses on the processed .h5ad files
scripts/
  check_notebooks.py            notebook hygiene checks (local + CI)
  oligoc4b_public.py            loaders for the public GEO datasets
  download_public_datasets.sh   parallel, resumable GEO download
docs/
  notebooks.md                  plain-language guide to every notebook
  complement_findings.md        what the complement analyses showed
  public_datasets.md            the public datasets: accessions, workflow, caveats
```

Raw data and `.h5ad` files are kept out of git; notebooks read them from `data/` (relative `../../data/`) or from the environment variables below.

## Quick start

```bash
conda env create -f environment.yml
conda activate oligoc4b
python -m ipykernel install --user --name oligoc4b --display-name "oligoc4b"
cp .env.example .env          # fill in the paths you need
jupyter lab
python scripts/check_notebooks.py   # before committing
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `OLIGOC4B_JAKEL_H5AD` | Human Jäkel et al. AnnData file |
| `OLIGOC4B_XENIUM_EAE_H5AD` | Processed Xenium EAE AnnData file |
| `OLIGOC4B_XENIUM_AD_H5AD` | Processed Xenium AD AnnData (optional, defaults to `data/`) |
| `OLIGOC4B_VISIUM_AGING_H5AD` | Processed Visium aging AnnData (optional, defaults to `data/`) |
| `OLIGOC4B_FALCAO_H5AD` | Falcão et al. 2018 EAE scRNA-seq AnnData (optional, defaults to `data/`) |
| `OLIGOC4B_SC_AD_MOUSE_RAW_DIR` | Raw 10x HDF5 directory for the Park mouse AD dataset |
| `OLIGOC4B_SNRNASEQ_AGING_RAW_DIR` | Raw matrix triplets for the aging mouse snRNA-seq dataset |
| `OLIGOC4B_XENIUM_AD_RAW_DIR` | Xenium AD output directory |
| `OLIGOC4B_VISIUM_AGING_RAW_DIR` | Raw Visium matrix directory for the aging mouse dataset |
| `OLIGOC4B_VISIUM_AGING_SPATIAL_DIR` | Spatial image and metadata directory for the Visium aging dataset |
| `OLIGOC4B_PUBLIC_RAW_DIR` | Downloaded public GEO files, one sub-folder per accession |
| `OLIGOC4B_PUBLIC_PROCESSED_DIR` | Output folder for the harmonised public-dataset `.h5ad` files |
| `OPENAI_API_KEY` | Optional; only for notebooks using `mllmcelltype` |

## Notebooks

| Notebook | Focus |
| --- | --- |
| `build/build_Xenium_AD_mouse.ipynb` | Mouse Xenium AD (TgCRND8 time course) integration, clustering, annotation → `Xenium_AD_mouse.h5ad` |
| `build/build_Visium_aging_mouse_brain.ipynb` | Visium aging mouse brain preprocessing → `visum_aging_brain.h5ad` |
| `build/build_snRNAseq_aging_mouse_brain.ipynb` | snRNA-seq aging mouse brain preprocessing and C4b analysis |
| `build/build_sc_AD_mouse_Park.ipynb` | scRNA-seq of the Park et al. mouse AD dataset |
| `build/build_public_datasets.ipynb` | Sixteen public datasets (GEO / UCSC) → harmonised `.h5ad` |
| `analysis/analysis_Xenium_AD_compartment_identification.ipynb` | Spatial compartments and C4b in Xenium AD |
| `analysis/analysis_Xenium_AD_further_exploration.ipynb` | C4b over the AD time course, mixed models |
| `analysis/analysis_Visum_aging_age_associated_changes.ipynb` | Age-associated genes in Visium aging data |
| `analysis/analysis_Xenium_EAE_mouse.ipynb` | C4b⁺ oligodendrocytes in Xenium EAE |
| `analysis/analysis_sc_EAE_falcao_mouse.ipynb` | C4b co-expression in Falcão et al. EAE scRNA-seq |
| `analysis/analysis_sc_jäkel_human.ipynb` | Human C4B in Jäkel et al. oligodendrocytes |
| `analysis/analysis_spatial_complement_C5_C1q_Cfb.ipynb` | C5, C5a receptors, C1q and Cfb across the in-house spatial datasets |
| `analysis/analysis_public_datasets_complement.ipynb` | The same complement panel across the public datasets |

Plain-language summaries of each notebook are in [`docs/notebooks.md`](docs/notebooks.md).

## Findings in brief

C4b⁺ oligodendrocytes are a reactive but lineage-retaining state marked by Serpina3n and an MHC-I / interferon module, rising with age, amyloid pathology and demyelination. They do not express C5 or the C5a receptors themselves, in any of eleven datasets; instead, C5aR1⁺ myeloid cells are enriched in their spatial neighbourhood in EAE. C1q is microglial and tracks C4b at tissue level; Cfb is induced only in inflammatory (EAE) lesions. The complement genes that join the oligodendrocyte program are C4a and the membrane regulators Cd59a and Cr1l. Full detail, numbers and caveats: [`docs/complement_findings.md`](docs/complement_findings.md).
