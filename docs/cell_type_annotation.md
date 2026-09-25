# How cell types were assigned

Every dataset in this repository carries a `cell_type_coarse` label with ten possible values: Oligodendrocyte, OPC, Microglia, Astrocyte, Neuron, Endothelial, Vascular/Fibroblast, Immune (lymphoid/myeloid), Ependymal, Other (spatial data use `spot`). Two routes produce it, depending on what the authors deposited. The original author label, where one exists, is always kept in `cell_type_original`.

## Route 1: author annotations, mapped to coarse types

Used when the deposited data contain a cell-type column: Ximerakis 2019 (Single Cell Portal metadata), Jäkel 2019 (`Celltypes`), Absinta 2021 (`cell_type`), Schirmer 2019 (UCSC `cell_type`), Lerma-Martin 2024 (per-cell-type h5ad files plus `subtype`), Falcão 2018 (`Renamed_clusternames`), and the in-house Xenium objects (`cellType`, `cell_type`).

Author labels are mapped with case-insensitive substring rules (`map_original_to_coarse` in `scripts/oligoc4b_public.py`), first match wins: `opc|precursor|progenitor|cop|nfol` → OPC; `oligo|^ol|^mol|myelin` → Oligodendrocyte; `microglia|^mg|^mic` → Microglia; `astro` → Astrocyte; `neuron|^ex|^in|gaba|glut|granule|pyram` → Neuron; `endo|^ec` → Endothelial; `peri|fibro|vlmc|vascular|mural|smooth|leptomen|stromal` → Vascular/Fibroblast; `t.?cell|b.?cell|lymph|macro|monocy|myeloid|immune|dendritic|nk|neutro` → Immune; `ependym|choroid|tanycyte` → Ependymal. Dataset-specific overrides exist where the generic rules would mislead: Absinta's `immune` cluster is their microglia/macrophage population and is mapped to Microglia (their `lymphocytes` stay Immune); Ximerakis's abbreviations (OLG, ASC, MG, EC, PC, VLMC, ABC, EPC, CPC, TNC, …) have their own rule set; Lerma-Martin coarse types come from the file each nucleus was deposited in (OL, OPC, MG, AS, NEU, EC, BC), while the finer `subtype` (e.g. `OL_Dis1`, `OL_Homeo2`) is kept as the original label.

The build notebook prints, for each of these datasets, a cross-tab of `cell_type_original` versus `cell_type_coarse` so the mapping can be audited row by row.

## Route 2: marker-based cluster annotation where no labels were deposited

Used for Park 2023, the aging snRNA-seq (HIP/CP), Zhou 2020 5XFAD, Kaya 2022, Leng 2021, Sadick 2022, the LPC + cuprizone dataset and the Serpina3n-cKO cuprizone dataset. The in-house Xenium AD object was annotated earlier with an LLM-assisted method (`mllmcelltype`) in `build_Xenium_AD_mouse.ipynb` and is not covered here.

Steps (`standard_process` and `annotate_by_markers` in `scripts/oligoc4b_public.py`):

1. QC: cells with fewer than 200 detected genes removed; mitochondrial fraction cut at 5% (nuclei) or 10% (whole cells); genes in fewer than 3 cells removed. Leng deposits raw Cell Ranger matrices, so cells are first called with a 500-UMI / 300-gene floor.
2. Normalise to 10,000 counts per cell, log1p, 2,000 highly variable genes, 30 principal components, k-nearest-neighbour graph, Leiden clustering at resolution 1.0.
3. Score every cell (`scanpy.tl.score_genes`) for nine marker sets:

| Coarse type | Markers (mouse symbols; human uses the upper-cased orthologs) |
| --- | --- |
| Oligodendrocyte | Plp1, Mbp, Mog, Mag, St18, Cldn11, Mobp |
| OPC | Pdgfra, Cspg4, Vcan, Ptprz1 |
| Microglia | Hexb, Cx3cr1, Csf1r, P2ry12, Tmem119, C1qa |
| Astrocyte | Aqp4, Gja1, Slc1a3, Aldoc, Gfap, Slc1a2 |
| Neuron | Rbfox3, Snap25, Syt1, Slc17a7, Gad1, Gad2, Meg3 |
| Endothelial | Cldn5, Flt1, Pecam1, Ly6c1 |
| Vascular/Fibroblast | Vtn, Pdgfrb, Dcn, Col1a2, Rgs5, Acta2 |
| Immune (lymphoid/myeloid) | Ptprc, Cd3e, Skap1, Cd74, Mrc1, Lyz2, Cd79a |
| Ependymal | Ccdc153, Foxj1, Tmem212, Rarres2 |

4. Z-score each marker score across cells (so sets with many or strongly expressed genes do not dominate), average per Leiden cluster, and give every cluster the type with the highest mean score. The per-cluster score matrix is stored in `adata.uns["cluster_marker_scores"]`.

## Validation and known weak spots

The build notebook checks each coarse type against one canonical marker per type (Plp1, Hexb, Aqp4, Snap25, Pdgfra; human orthologs for human data) and reports the fraction of cells detecting it.

- Oligodendrocyte clusters are 96–100% Plp1/PLP1⁺ and microglia clusters 92–100% Hexb⁺ in every mouse dataset. These two labels are the ones the complement analyses rely on, and the only ones used to build the oligodendrocyte atlas.
- Park 2023: the clusters labelled OPC and Neuron are unreliable (Pdgfra 4%, Snap25 8%); few neurons survive that dissociation. Not used.
- Sadick 2022: myeloid cells were assigned to Immune rather than Microglia, so that dataset has no Microglia row in the summaries.
- Serpina3n-cKO cuprizone: the Microglia cluster has low C1q detection and the few C4b⁺ oligodendrocyte nuclei carry microglial genes; the dataset is of limited use.
- Human snRNA-seq: HEXB is a weak microglial marker in nuclei, so human microglia validation relies on the author labels where available (Jäkel, Absinta, Schirmer, Lerma-Martin) and on C1Q/C3 detection otherwise (Leng).
- Nuclei from active demyelinating lesions (LPC, cuprizone) carry microglial ambient RNA, so microglial genes detected in oligodendrocyte nuclei there should not be read as intrinsic expression.

## Where to look

- Code: `standard_process`, `annotate_by_markers`, `map_original_to_coarse`, `DEFAULT_LABEL_RULES`, `MARKERS_MOUSE` in `scripts/oligoc4b_public.py`; dataset-specific rules inside each `load_*` function.
- Audit output: cross-tabs and marker checks in `notebooks/build/build_public_datasets.ipynb`.
