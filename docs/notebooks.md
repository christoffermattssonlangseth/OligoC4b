# Notebook Guide

Plain-language summaries of every notebook in `notebooks/build/` and `notebooks/analysis/`, written for collaborators. Findings are collected in [`complement_findings.md`](complement_findings.md); dataset details in [`public_datasets.md`](public_datasets.md).

All notebooks investigate the same biological question — **what genes are associated with C4b expression in disease-associated oligodendrocytes (DA-oligos)** — across different datasets and modalities (scRNA-seq, snRNA-seq, Visium, Xenium).

## How the notebooks are organized

Notebooks are prefixed by role so the run order is obvious from the file listing:

- **`build_*`** ingest raw data and write a processed `.h5ad`. **Run these first.**
- **`analysis_*`** load a processed `.h5ad` and run focused downstream analyses.

| Notebook | Role | Produces / Reads |
| --- | --- | --- |
| `build_Xenium_AD_mouse.ipynb` | build | → `Xenium_AD_mouse.h5ad` |
| `build_Visium_aging_mouse_brain.ipynb` | build | → `visum_aging_brain.h5ad` |
| `build_snRNAseq_aging_mouse_brain.ipynb` | build | raw triplets → AnnData |
| `build_sc_AD_mouse_Park.ipynb` | build | raw 10x H5 → AnnData |
| `analysis_Xenium_AD_compartment_identification.ipynb` | analysis | reads `Xenium_AD_mouse.h5ad` |
| `analysis_Xenium_AD_further_exploration.ipynb` | analysis | reads `Xenium_AD_mouse.h5ad` |
| `analysis_Visum_aging_age_associated_changes.ipynb` | analysis | reads `visum_aging_brain.h5ad` |
| `analysis_Xenium_EAE_mouse.ipynb` | analysis | reads processed h5ad |
| `analysis_sc_EAE_falcao_mouse.ipynb` | analysis | reads processed h5ad |
| `analysis_sc_jäkel_human.ipynb` | analysis | reads processed h5ad |
| `analysis_spatial_complement_C5_C1q_Cfb.ipynb` | analysis | reads `Xenium_AD_mouse.h5ad`, the Xenium EAE h5ad and `visum_aging_brain.h5ad` |
| `build_public_datasets.ipynb` | build | GEO downloads → eight harmonised public `.h5ad` files (`scripts/oligoc4b_public.py`) |
| `analysis_public_datasets_complement.ipynb` | analysis | reads the eight public `.h5ad` files |

---

## `build_*` — pipeline notebooks (raw data → h5ad)

### `build_Xenium_AD_mouse.ipynb` — Xenium spatial, mouse AD (main pipeline)
Foundational, largest notebook. Builds AnnData from raw Xenium runs (10x H5 + `cell_info`) → QC (min 30 counts, 15 genes) → normalize (target sum 100) / log1p → PCA → neighbors → UMAP → Leiden (resolution 2). Annotates clusters with `mllmcelltype` (LLM-based annotation). Sets spatial coordinates from cell centroids, maps each cell to model (wildtype / TgCRND8) and age (months). Compares **C4b** by model, subsets oligodendrocytes, and runs the C4b gene-discovery suite (see below). Produces `Xenium_AD_mouse.h5ad`, the input for the two `analysis_Xenium_AD_*` notebooks.

### `build_Visium_aging_mouse_brain.ipynb` — Visium spatial, aging mouse brain
Heavy preprocessing notebook. Reads raw 10x triplets (barcodes / features / `matrix.mtx`), concatenates samples, and loads spatial coordinates from `*_spatial` folders (pixel positions). QC → normalize / log1p → HVG (2000) → PCA → neighbors → UMAP → Leiden. Plots clusters in spatial layout per section. Examines **C4b** by age group plus spatial and co-expression analysis. Produces `visum_aging_brain.h5ad`.

### `build_snRNAseq_aging_mouse_brain.ipynb` — snRNA-seq, aging mouse brain
Reads raw 10x triplets → concat → QC → normalize / log1p → HVG (2000) → PCA → neighbors → UMAP → Leiden. Maps GSM IDs to region / age / replicate. Annotates with `mllmcelltype`. Looks at **C4b** vs age (months), then runs the full gene-discovery suite (correlation / regression / mutual information / co-expression probability).

### `build_sc_AD_mouse_Park.ipynb` — scRNA-seq, mouse AD (Park et al.)
Builds AnnData from raw 10x H5 files → QC (mito < 10%, > 200 genes) → normalize / log1p → HVG (5000) → PCA → neighbors → UMAP → Leiden (resolution 0.8). Annotates with `mllmcelltype`. Maps GSM IDs to condition and age. Subsets oligodendrocytes and compares **C4b** by condition (violin / dotplot vs Serpina3n).

---

## `analysis_*` — downstream notebooks (load h5ad)

### `analysis_Xenium_AD_compartment_identification.ipynb` — spatial compartments
Loads `Xenium_AD_mouse.h5ad`. Defines spatial neighborhoods with a custom `spatial_neigbourshoods` function (100 µm radius), then clusters neighborhoods by their cell-type composition into tissue **compartments** (Leiden). Compares **C4b** expression across compartments, computes Moran's I spatial autocorrelation, and scores complement genes.

### `analysis_Xenium_AD_further_exploration.ipynb` — modeling C4b over disease course
Loads `Xenium_AD_mouse.h5ad`. Models **C4b** across the AD time course: mean C4b by age × model (lineplot), then formal statistical models — a `MixedLM` of `C4b_log1p ~ age_months * C(model) + C(compartment)` within oligodendrocytes. Extends to a multi-gene panel (Serpina3n, Gfap, H2-D1, B2m, Mbp, Plp1).

### `analysis_Visum_aging_age_associated_changes.ipynb` — age-associated changes
Loads `visum_aging_brain.h5ad`. Pseudobulks per sample, ranks genes by correlation with age, and reports the top genes increasing and decreasing with age. General aging analysis (not C4b-specific).

### `analysis_Xenium_EAE_mouse.ipynb` — Xenium spatial, mouse EAE (most annotated)
Loads processed h5ad → normalize / log1p. Subsets "DA Oligodendrocytes" and runs the full **C4b** co-expression workflow with extensive markdown interpretation: correlation, LassoCV, sub-clustering of C4b+ cells, mutual information, and cell-level co-expression probability. Markdown cells narrate the biology — an MHC-I / interferon immune axis, a stress / lipid-droplet cluster, trafficking and degeneration signatures.

### `analysis_sc_EAE_falcao_mouse.ipynb` — scRNA-seq, mouse EAE (Falcão et al. 2018)
Loads pre-processed `.h5ad`, subsets EAE DA-oligodendrocytes, and identifies **C4b** co-expressed genes three ways: correlation (dotplot), LassoCV regression, and mutual information.

### `analysis_sc_jäkel_human.ipynb` — scRNA-seq, human oligodendrocytes (Jäkel et al.)
Smallest notebook. Loads h5ad → normalize / log1p → dotplot of **C4B** (human ortholog). A cross-species sanity check.

### `analysis_spatial_complement_C5_C1q_Cfb.ipynb` — C5, C5a receptors, C1q and Cfb across the spatial datasets
Answers the group-lead question *"have you checked C5 and the C5 receptors (and C1q, Cfb) when checking C4b?"*. Loads all three spatial objects (Xenium AD, Xenium EAE, Visium aging; any missing file is skipped). For each dataset it (1) reports which complement genes are actually on the panel, (2) shows which cell types express them and how they change with disease / age (pseudobulk per sample where replicates exist), (3) tests cell-level co-expression with **C4b** inside oligodendrocytes and ranks the genes among all panel genes correlated with C4b, and (4) asks spatially whether receptor-expressing cells (C1q⁺ microglia in AD; C5ar1⁺ / C5ar2⁺ / Cfb⁺ cells in EAE) sit closer to C4b-high than to C4b-negative oligodendrocytes (30 µm neighbourhoods, paired test across samples). Ends with a cross-dataset availability table and a written interpretation.

Findings: see [`complement_findings.md`](complement_findings.md).

### `build_public_datasets.ipynb` — public GEO datasets → harmonised h5ad
Runs the loaders in `scripts/oligoc4b_public.py` on files fetched by `scripts/download_public_datasets.sh` (Park 2023 AD hippocampus, aging snRNA-seq HIP/CP, Ximerakis 2019 aging brain, Kaya 2022 aged white vs grey matter, Zhou 2020 5XFAD, Chen 2020 Spatial Transcriptomics AD, Jäkel 2019 and Absinta 2021 human MS). Each object gets the same `obs` columns (`dataset`, `species`, `modality`, `sample`, `group`, `group_ref`, `cell_type_coarse`, `cell_type_original`) so the analysis notebook can loop over them. Prints a per-dataset summary and a cross-tab of author labels vs coarse types for checking the annotation.

### `analysis_public_datasets_complement.ipynb` — complement panel across the public datasets
Same questions as the in-house complement notebook, asked of the eight public datasets: which cell types express C4b, C1q, C3, C5 (`Hc`), C5aR1/2 and Cfb; pseudobulk disease/age effects in oligodendrocytes and microglia; co-expression with C4b inside oligodendrocytes and the genome-wide rank of each complement gene among C4b-correlated genes; human MS by lesion type; and the spatial AD dataset across spots and genotype/age. Ends with a cross-dataset summary and interpretation.

Findings: see [`complement_findings.md`](complement_findings.md).

---

## Shared C4b gene-discovery suite

Most notebooks run the same 3–4 complementary methods on a DA-oligo subset. They answer different questions and surface different gene sets:

1. **Correlation** — pairwise, linear. Recovers the classic immune signature (Serpina3n, H2-D1, B2m).
2. **LassoCV regression** — multivariate, redundancy-aware. Adds structural / degenerative players (App, Mapt, Mag, Stat3).
3. **Mutual information** — captures nonlinear associations correlation misses (trafficking, metabolism, axon–glia communication).
4. **Cell-level co-expression probability** — confirms cell identity and state (Mbp, Cnp, Mag for identity; Gfap, Cryab, Mapt for degeneration).

Together they paint C4b+ DA-oligos as bona fide oligodendrocytes in a reactive / degenerative state tied to a complement / MHC-I immune axis.
