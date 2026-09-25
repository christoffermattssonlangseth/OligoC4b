# Notebook Guide

Plain-language summaries of every analysis notebook in `notebooks/`, written for collaborators.

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
| `analysis_Xenium_AD_further_exporation.ipynb` | analysis | reads `Xenium_AD_mouse.h5ad` |
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

### `analysis_Xenium_AD_further_exporation.ipynb` — modeling C4b over disease course
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

Headline findings (details and numbers in the notebook):
- **C5** (mouse gene `Hc`) is not on the AD panel and is essentially not transcribed in tissue in EAE (≤0.5 % of cells) or the aging brain (~1 % of spots). C5 is plasma-derived; assessing C5a/C5b-9 needs protein staining.
- **C5a receptors** are myeloid. C5ar1 is in ~20–45 % of microglia / macrophages / infiltrating myeloid cells and <3 % of oligodendrocytes; C5ar2 is low everywhere. Oligodendrocytes, including C4b⁺ DA-oligos, do not express them intrinsically (any signal inside oligodendrocyte segments has no rank correlation with C4b, i.e. spill-over). But C5aR1⁺ cells are ~2× enriched within 30 µm of C4b-high oligodendrocytes across 87 EAE samples (paired Wilcoxon p ≈ 4×10⁻⁷). Per-cell C5ar1 in myeloid cells is flat across lesion distance and unchanged by EAE; the tissue-level gradient is cell recruitment.
- **C1q** is microglial. In Visium it rises with age in parallel with C4b and ranks among the top ~50 of 16 k genes correlated with C4b in white-matter-rich spots. In Xenium AD the spatial coupling of C1q⁺ microglia to C4b-high oligodendrocytes is weak and only seen in the two oldest sections; C3⁺ astrocytes, by contrast, are ~3× enriched around C4b-high oligodendrocytes in every section.
- **Cfb** is an EAE-lesion-induced myeloid gene (strong induction in microglia, ~67 % of macrophages positive, steep lesion gradient, 1.7× enriched around C4b-high oligodendrocytes) and essentially absent in the aging brain. Not on the AD panel. In the sorted Falcão MOLs it is the one panel gene with an intrinsic component: detected in 13 % of EAE-cluster MOLs vs 2 % of control MOLs and ~5× enriched in C4b⁺ MOLs.
- **Lesion-distance matching** (section 2.5b) does not remove the neighbourhood effect: stratified by `lesion_distance_bin` the C5aR1⁺ ratio is ~2 (76 samples, 84 % > 1), and 2.2 in `non_lesion` cells. Near lesions (50–200 µm) the ratio is ~1; far from lesions it is 1.7–2.3, so C4b-high oligodendrocytes mark myeloid-rich micro-niches outside lesions.
- **Sorted single cells (Falcão et al. 2018, section 5)** confirm the receptors are not oligodendrocyte-intrinsic: C5ar1 in 2.6 % and C5ar2 in 0.6 % of EAE-cluster MOLs versus 76 % / 9 % of microglia; Hc (C5) in <1 % of any cell type. Caveat: C1q/C3 show up in 15–25 % of EAE MOLs there, suggesting some ambient contamination, so the intrinsic-Cfb result should be re-checked in the Park AD and aging snRNA-seq data once rebuilt.

### `build_public_datasets.ipynb` — public GEO datasets → harmonised h5ad
Runs the loaders in `scripts/oligoc4b_public.py` on files fetched by `scripts/download_public_datasets.sh` (Park 2023 AD hippocampus, aging snRNA-seq HIP/CP, Ximerakis 2019 aging brain, Kaya 2022 aged white vs grey matter, Zhou 2020 5XFAD, Chen 2020 Spatial Transcriptomics AD, Jäkel 2019 and Absinta 2021 human MS). Each object gets the same `obs` columns (`dataset`, `species`, `modality`, `sample`, `group`, `group_ref`, `cell_type_coarse`, `cell_type_original`) so the analysis notebook can loop over them. Prints a per-dataset summary and a cross-tab of author labels vs coarse types for checking the annotation.

### `analysis_public_datasets_complement.ipynb` — complement panel across the public datasets
Same questions as the in-house complement notebook, asked of the eight public datasets: which cell types express C4b, C1q, C3, C5 (`Hc`), C5aR1/2 and Cfb; pseudobulk disease/age effects in oligodendrocytes and microglia; co-expression with C4b inside oligodendrocytes and the genome-wide rank of each complement gene among C4b-correlated genes; human MS by lesion type; and the spatial AD dataset across spots and genotype/age. Ends with a cross-dataset summary and interpretation.

Headline findings:
- **C4b** rises in oligodendrocytes with age in every aging dataset (log2FC ≈ 2–3), is far higher in aged white than grey matter (77 % of aged WM oligodendrocytes C4b⁺, Kaya 2022) and up ~2.8 log2 in 5XFAD; in the Chen spatial data its spot-level correlates are the plaque-induced / DAM genes. **Human C4A/C4B cannot be quantified** in the MS snRNA-seq data (<25 UMIs in 17–66 k nuclei): the paralogs are near-identical and multi-mapping reads are discarded.
- **C5a receptors are myeloid in all eight datasets**: C5ar1 in 6–38 % of microglia versus ≤0.9 % of oligodendrocytes (mouse) and ≤0.6 % (human MS). Microglial C5AR1 is highest at chronic active MS lesion edges (Absinta).
- **C5**: ≤0.3 % of any mouse cell type. In human white matter a low glial C5 transcript exists (2–7 % of oligodendrocytes/astrocytes) and goes down, not up, in MS oligodendrocytes.
- **C1q** is microglial; the 30 % "oligodendrocyte" detection seen only in droplet scRNA-seq is ambient RNA (1–6 % in snRNA-seq). It tracks C4b at the tissue level in the spatial AD data (rank 11–18 of ~14 k genes) but not inside oligodendrocyte nuclei.
- **Cfb is silent** outside EAE (≤0.2 % of microglia, ≤0.1 % of oligodendrocytes in every AD/aging dataset), so it marks active inflammatory demyelination rather than the age-/amyloid-associated C4b⁺ state.
- Genome-wide, the C4b⁺ oligodendrocyte program is the same everywhere (Serpina3n #1, then MHC-I / interferon genes, Klk6, Apod, Trf, Cd9); the only complement genes that join it are C4a and the membrane regulators Cd59a and Cr1l/Crry, i.e. protection against complement rather than complement receptors.

---

## Shared C4b gene-discovery suite

Most notebooks run the same 3–4 complementary methods on a DA-oligo subset. They answer different questions and surface different gene sets:

1. **Correlation** — pairwise, linear. Recovers the classic immune signature (Serpina3n, H2-D1, B2m).
2. **LassoCV regression** — multivariate, redundancy-aware. Adds structural / degenerative players (App, Mapt, Mag, Stat3).
3. **Mutual information** — captures nonlinear associations correlation misses (trafficking, metabolism, axon–glia communication).
4. **Cell-level co-expression probability** — confirms cell identity and state (Mbp, Cnp, Mag for identity; Gfap, Cryab, Mapt for degeneration).

Together they paint C4b+ DA-oligos as bona fide oligodendrocytes in a reactive / degenerative state tied to a complement / MHC-I immune axis.
