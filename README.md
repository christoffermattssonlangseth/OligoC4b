# OligoC4b

Notebook-based exploratory analysis of C4b-associated gene programs in disease-associated oligodendrocytes across single-cell, single-nucleus, Visium, and Xenium datasets.

## Scope

This repository collects exploratory analyses around reactive oligodendrocyte states with a focus on **C4b / C4B** expression across:

- mouse Alzheimer's disease datasets
- aging mouse brain datasets
- mouse EAE datasets
- human oligodendrocyte data from Jäkel et al.

The repo is intentionally notebook-first. The goal is to keep the analytical narrative visible while adding enough structure for reproducibility and collaboration.

## Repository Layout

- `notebooks/`: analysis notebooks grouped by dataset and modality
- `scripts/check_notebooks.py`: local and CI notebook hygiene checks
- `environment.yml`: base conda environment for running the notebooks
- `.env.example`: local dataset path and secret configuration template
- `CONTRIBUTING.md`: conventions for extending the repository safely

## Quick Start

```bash
conda env create -f environment.yml
conda activate oligoc4b
python -m ipykernel install --user --name oligoc4b --display-name "oligoc4b"
cp .env.example .env
jupyter lab
```

Run the notebook hygiene checks before committing:

```bash
python scripts/check_notebooks.py
```

## Configuration

Several notebooks now read dataset locations from environment variables instead of hard-coded local paths. Copy `.env.example` to `.env` and fill in the paths relevant to your machine.

| Variable | Purpose |
| --- | --- |
| `OLIGOC4B_JAKEL_H5AD` | Human Jäkel et al. AnnData file |
| `OLIGOC4B_XENIUM_EAE_H5AD` | Processed Xenium EAE AnnData file |
| `OLIGOC4B_XENIUM_AD_H5AD` | Processed Xenium AD AnnData (`Xenium_AD_mouse.h5ad`); optional, defaults to `../data/` |
| `OLIGOC4B_VISIUM_AGING_H5AD` | Processed Visium aging AnnData (`visum_aging_brain.h5ad`); optional, defaults to `../data/` |
| `OLIGOC4B_SC_AD_MOUSE_RAW_DIR` | Raw 10x HDF5 directory for the Park mouse AD dataset |
| `OLIGOC4B_SNRNASEQ_AGING_RAW_DIR` | Raw matrix triplets for the aging mouse snRNA-seq dataset |
| `OLIGOC4B_XENIUM_AD_RAW_DIR` | Xenium AD output directory |
| `OLIGOC4B_VISIUM_AGING_RAW_DIR` | Raw Visium matrix directory for the aging mouse dataset |
| `OLIGOC4B_VISIUM_AGING_SPATIAL_DIR` | Spatial image and metadata directory for the Visium aging dataset |
| `OPENAI_API_KEY` | Optional; required only for notebooks using `mllmcelltype` |

## Notebook Inventory

Notebooks are prefixed by role so it is obvious which ones to run first:

- **`build_*`** ingest raw data and write a processed `.h5ad`. Run these first.
- **`analysis_*`** load a processed `.h5ad` and run downstream analyses.

| Notebook | Role | Focus |
| --- | --- | --- |
| `notebooks/build_Xenium_AD_mouse.ipynb` | build | Mouse Xenium AD integration, clustering, LLM-assisted annotation → `Xenium_AD_mouse.h5ad` |
| `notebooks/build_Visium_aging_mouse_brain.ipynb` | build | Visium aging mouse brain preprocessing + spatial coords → `visum_aging_brain.h5ad` |
| `notebooks/build_snRNAseq_aging_mouse_brain.ipynb` | build | snRNA-seq aging mouse brain preprocessing and downstream C4b analysis |
| `notebooks/build_sc_AD_mouse_Park.ipynb` | build | scRNA-seq analysis of a mouse AD dataset from Park et al. |
| `notebooks/analysis_Xenium_AD_compartment_identification.ipynb` | analysis | Compartment-level analysis in Xenium AD tissue |
| `notebooks/analysis_Xenium_AD_further_exporation.ipynb` | analysis | Follow-up Xenium AD analyses and model-based exploration |
| `notebooks/analysis_Visum_aging_age_associated_changes.ipynb` | analysis | Age-associated changes in Visium aging data |
| `notebooks/analysis_Xenium_EAE_mouse.ipynb` | analysis | Mouse Xenium EAE analysis focused on C4b-positive oligodendrocytes |
| `notebooks/analysis_sc_EAE_falcao_mouse.ipynb` | analysis | scRNA-seq analysis of mouse EAE data from Falcao et al. |
| `notebooks/analysis_sc_jäkel_human.ipynb` | analysis | Human oligodendrocyte analysis using the Jäkel et al. dataset |
| `notebooks/analysis_spatial_complement_C5_C1q_Cfb.ipynb` | analysis | C5 / C5a receptors, C1q and Cfb across all three spatial datasets, in relation to C4b⁺ oligodendrocytes |

For plain-language, per-notebook summaries written for collaborators, see [`NOTEBOOKS.md`](NOTEBOOKS.md).

## Current Biological Readout

Across datasets, the working interpretation is that **C4b-positive oligodendrocytes represent a reactive but lineage-retaining state** with several recurring features:

- immune and complement activation, including MHC-I and interferon-linked genes
- retained oligodendrocyte identity, with core myelin and lineage markers still present
- stress-associated remodeling, including cytoskeletal and degeneration-linked programs
- metabolic and lysosomal changes consistent with a perturbed homeostatic state
- altered neuron-glia or immune-glia communication signatures

The core exploratory strategy combines correlation, sparse regression, mutual information, and cell-level co-expression to capture complementary views of the same state.

## Complement Beyond C4b: C5, C5a Receptors, C1q and Cfb

Follow-up question from the group: *have we checked C5 and the C5 receptors (and C1q, Cfb) in the spatial datasets, not just C4b?* This is addressed in `notebooks/analysis_spatial_complement_C5_C1q_Cfb.ipynb`. The first constraint is panel content, because Xenium is targeted:

| Gene | Xenium AD (347 genes) | Xenium EAE (5K panel) | Visium aging |
| --- | --- | --- | --- |
| C4b | ✓ | ✓ | ✓ |
| C1qa / C1qb / C1qc | ✓ | ✗ | ✓ |
| C3 | ✓ | ✓ | ✓ |
| C3ar1 | ✗ | ✓ | ✓ |
| C5 (mouse gene symbol `Hc`) | ✗ | ✓ | ✓ |
| C5ar1 / C5ar2 | ✗ | ✓ | ✓ |
| Cfb | ✗ | ✓ | ✓ |

C5 (`Hc`), its receptors and Cfb are therefore measurable in Xenium EAE and Visium but not in Xenium AD; C1q only in Xenium AD and Visium.

Current readout (see the notebook's interpretation cell and `NOTEBOOKS.md`):

- C4b⁺ oligodendrocytes do not express C5, C5ar1 or C5ar2 themselves in any dataset, and local C5 (`Hc`) transcription is near-absent in tissue, so the C5/C5a arm needs protein-level assessment.
- C5aR1 is confined to microglia and infiltrating myeloid cells, yet C5aR1⁺ cells are about twice as enriched within 30 µm of C4b-high oligodendrocytes as of C4b-negative ones across 87 EAE samples. Cfb⁺ and C3aR1⁺ cells show the same pattern.
- C1q (microglial) rises with age together with C4b in Visium and is among the top C4b-correlated genes in white matter; its spatial coupling to C4b⁺ oligodendrocytes in the AD sections is weak.
- Cfb is strongly induced in EAE lesion myeloid cells and essentially absent in the aging brain.

## Reproducibility Notes

- Raw data and large derived files are intentionally kept out of git.
- Notebook checks enforce valid JSON, block hard-coded user-home paths in source cells, and verify that referenced environment variables are documented in `.env.example`.
- Some notebooks include rendered outputs for interpretability; avoid committing secrets or machine-specific paths in source cells.
