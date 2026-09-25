#!/usr/bin/env python3
"""Pull selected figures out of the executed notebooks into report/figures/ as PNG files.

Each entry maps an output file name to (notebook path, substring that identifies the code cell, index of the image
within that cell's outputs). Run from the repo root after the notebooks have been executed:

    python report/collect_figures.py
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

INHOUSE = ROOT / "notebooks/analysis/analysis_spatial_complement_C5_C1q_Cfb.ipynb"
PUBLIC = ROOT / "notebooks/analysis/analysis_public_datasets_complement.ipynb"
ATLAS = ROOT / "notebooks/analysis/analysis_oligodendrocyte_atlas.ipynb"

# name -> (notebook, cell-source substring, image index within the cell, optional: pick by second substring)
FIGURES = {
    # in-house spatial notebook
    "inhouse_xenium_ad_course.png": (INHOUSE, "sns.relplot(data=tidy", -1),
    "inhouse_xenium_ad_celltype_dotplot.png": (INHOUSE, 'dotplot(ad_ad, genes + present(ad_ad, ["Serpina3n", "Plp1", "Itgam"])', 0),
    "inhouse_eae_celltype_dotplot.png": (INHOUSE, 'dotplot(ad_eae, genes_eae + present(ad_eae, ["Serpina3n", "Mbp", "Itgam"])', 0),
    "inhouse_eae_pseudobulk.png": (INHOUSE, "g = sns.catplot(data=tidy, x=\"cell_type\"", 0),
    "inhouse_eae_neighbourhood_ratio.png": (INHOUSE, 'sns.boxplot(data=long, x="target", y="ratio"', 0),
    "inhouse_eae_lesion_matched.png": (INHOUSE, 'sns.pointplot(data=pb_plot', 0),
    "inhouse_eae_spatial_peak.png": (INHOUSE, 'spatial_panel(ad_eae, "sample_name", s', 0),
    "inhouse_visium_age.png": (INHOUSE, 'g = sns.catplot(data=tidy, x="age_group"', 0),
    "inhouse_falcao_dotplot.png": (INHOUSE, "dotplot(ad_f, genes_f", 0),
    # public datasets notebook
    "public_detection_oligodendrocyte.png": (PUBLIC, 'heat(h, f"{ct}: fraction of cells with ≥1 UMI', 0),
    "public_detection_microglia.png": (PUBLIC, 'heat(h, f"{ct}: fraction of cells with ≥1 UMI', 1),
    "public_log2fc_oligodendrocyte.png": (PUBLIC, 'heat(d, f"{ct}: pseudobulk log2 fold change', 0),
    "public_log2fc_microglia.png": (PUBLIC, 'heat(d, f"{ct}: pseudobulk log2 fold change', 1),
    "public_c4b_correlation.png": (PUBLIC, 'heat(R, "Spearman correlation with C4b inside oligodendrocytes', 0),
    # atlas notebook (optional; skipped if not executed yet)
    "atlas_umap_dataset_species.png": (ATLAS, 'sc.pl.umap(atlas, color=["ds", "species"]', 0),
    "atlas_umap_clusters_labels.png": (ATLAS, 'sc.pl.umap(atlas, color=["leiden_0.5", "ol_subtype_pred"]', 0),
    "atlas_umap_scores.png": (ATLAS, 'sc.pl.umap(atlas, color=["C4b_log", "score_C4b_program"', 0),
    "atlas_cluster_composition.png": (ATLAS, "sns.heatmap(comp.loc[:, CLUST.index]", 0),
    "atlas_complement_de.png": (ATLAS, "Complement genes in the C4b-high vs homeostatic contrast", 0),
    "atlas_genetic_dependency.png": (ATLAS, "fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))", 0),
}


def images_in_cell(cell: dict) -> list[bytes]:
    out = []
    for o in cell.get("outputs", []):
        data = o.get("data", {})
        if "image/png" in data:
            out.append(base64.b64decode(data["image/png"]))
    return out


def main() -> int:
    missing = []
    for name, (nb_path, needle, idx) in FIGURES.items():
        if not nb_path.exists():
            missing.append((name, "notebook missing")); continue
        nb = json.loads(nb_path.read_text())
        found = False
        for cell in nb["cells"]:
            if cell["cell_type"] != "code" or needle not in "".join(cell["source"]):
                continue
            imgs = images_in_cell(cell)
            if not imgs:
                continue
            try:
                (OUT / name).write_bytes(imgs[idx])
                found = True
                break
            except IndexError:
                pass
        if not found:
            missing.append((name, "no image"))
        else:
            print(f"wrote {name}")
    for name, why in missing:
        print(f"skipped {name}: {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
