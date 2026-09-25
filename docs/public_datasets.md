# Public datasets

Eight public datasets were added to test whether the C4b / complement picture generalises beyond the in-house spatial data. All are whole-transcriptome; seven are single-cell or single-nucleus, one is spatial.

| Dataset | GEO | Species, modality | Comparison | Why |
| --- | --- | --- | --- | --- |
| Park et al. 2023, AD hippocampus | GSE224398 | mouse scRNA-seq | App^NL-G-F^ vs control, 1/3/6 mo | the dataset in which the C4b⁺ DA-oligodendrocyte state was described |
| Aging snRNA-seq, hippocampus + caudate putamen | GSE212576 | mouse snRNA-seq | old vs young | aging counterpart already used in this repo |
| Ximerakis et al. 2019, whole brain | GSE129788 | mouse scRNA-seq | old vs young | independent aging dataset with author cell types |
| Kaya et al. 2022, aged white vs grey matter | GSE202579 | mouse scRNA-seq | WM vs GM at 24 mo (WT and Rag1-KO) | interferon-responsive oligodendrocytes in aging white matter |
| Zhou et al. 2020, 5XFAD | GSE140511 | mouse snRNA-seq | 5XFAD vs non-Tg, 7 and 15 mo, ± Trem2-KO | second AD model |
| Chen et al. 2020, Spatial Transcriptomics | GSE152506 | mouse ST | App^NL-G-F^ vs WT, 3–18 mo | whole-transcriptome spatial AD data; C4b is a plaque-induced gene |
| Jäkel et al. 2019, MS white matter | GSE118257 | human snRNA-seq | MS lesion types vs control | human MS oligodendrocytes |
| Absinta et al. 2021, chronic active MS | GSE180759 | human snRNA-seq | lesion edge / core / periplaque vs control | human MS lesion rim biology |

## Workflow

```bash
OLIGOC4B_PUBLIC_RAW_DIR=/path/to/raw sh scripts/download_public_datasets.sh   # ~5 GB from GEO, parallel + resumable
# then run notebooks/build/build_public_datasets.ipynb
# then notebooks/analysis/analysis_public_datasets_complement.ipynb
```

`scripts/oligoc4b_public.py` holds one loader per dataset (`LOADERS`) and writes `<OLIGOC4B_PUBLIC_PROCESSED_DIR>/<name>.h5ad`. Every object has raw counts in `layers["counts"]`, log-normalised `X` and a harmonised `obs`:

| Column | Meaning |
| --- | --- |
| `dataset`, `species`, `modality` | provenance |
| `sample` | library / donor used for pseudobulk |
| `group`, `group_ref` | two-level comparison and its reference level (e.g. `AD` vs `WT`, `Old` vs `Young`, `MS` vs `Ctrl`, `WM` vs `GM`) |
| `cell_type_coarse` | Oligodendrocyte, OPC, Microglia, Astrocyte, Neuron, Endothelial, Vascular/Fibroblast, Immune (lymphoid/myeloid), Ependymal, Other, or `spot` |
| `cell_type_original` | author annotation when deposited |
| `condition_original` | author lesion / tissue labels (human MS) |

Author cell-type labels are used where deposited (Ximerakis, Jäkel, Absinta); otherwise clusters are annotated from marker-gene scores (`annotate_by_markers`). The build notebook prints a cross-tab of author labels vs coarse types for checking.

## Format notes (things that cost time once)

- GEO occasionally answers a parallel request with a ~1 KB HTML error page; the download script rejects those and can be re-run.
- Kaya 2022: the deposited 10x matrices are all 24-month-old animals (WT and Rag1-KO, white and grey matter); the paper's young-vs-aged comparison is Smart-seq2 and not deposited as a matrix. R turned `-1` barcode suffixes into `.1` in the matrix headers.
- Zhou 2020: region-named libraries (`WT_Cor`, `WT_Hip`, …) are the 15-month cohort, numbered ones (`WT1`, …) the 7-month cohort.
- Chen 2020: comma-separated despite the `.txt` extension, spots × genes, missing values mean zero, spot ids are `<sample>__<x>_<y>`; genotype and age come from the GSM metadata.
- Ximerakis 2019: metadata cell names are `Aging_mouse_brain_portal_data_<k>_<barcode>`, matrix columns are `<k>_<barcode>`.
- Absinta 2021: matrix barcodes repeat across donors, so annotation is matched by position; the loader verifies alignment (PLP1 in annotated oligodendrocytes vs others, observed ratio 15×). The author `immune` cluster is microglia/macrophages and is mapped to `Microglia`.
- Human C4A/C4B have <25 UMIs in both MS datasets: multi-mapping between the paralogs, not absence.
- Park OPC and neuron labels from the marker annotation are unreliable; oligodendrocyte and microglia labels were validated in all datasets.
