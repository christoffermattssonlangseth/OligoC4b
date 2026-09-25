"""Loaders and shared helpers for the public-dataset extension of the complement / C4b analysis.

Every loader returns an AnnData with raw counts in ``.layers["counts"]``, log-normalised ``.X`` and a harmonised
``obs`` containing at least:

- ``dataset``            short dataset name
- ``species``            "mouse" | "human"
- ``modality``           "scRNA" | "snRNA" | "spatial"
- ``sample``             biological / library sample used for pseudobulk
- ``group``              two-level comparison label (e.g. "AD" vs "WT", "Old" vs "Young", "MS" vs "Ctrl")
- ``group_ref``          the reference level of ``group``
- ``cell_type_coarse``   one of ``COARSE_TYPES`` (spatial data: "spot")
- ``cell_type_original`` author annotation when available

Configuration is via environment variables ``OLIGOC4B_PUBLIC_RAW_DIR`` (downloaded GEO files, one sub-folder per
accession) and ``OLIGOC4B_PUBLIC_PROCESSED_DIR`` (output h5ad files).
"""
from __future__ import annotations

import glob
import gzip
import os
import re
import tarfile
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp
from anndata import AnnData

# --------------------------------------------------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------------------------------------------------

RAW_DIR = os.getenv("OLIGOC4B_PUBLIC_RAW_DIR", "../data/public/raw")
PROCESSED_DIR = os.getenv("OLIGOC4B_PUBLIC_PROCESSED_DIR", "../data/public/processed")

COARSE_TYPES = ["Oligodendrocyte", "OPC", "Microglia", "Astrocyte", "Neuron", "Endothelial", "Vascular/Fibroblast",
                "Immune (lymphoid/myeloid)", "Ependymal", "Other"]

# mouse symbol -> human symbol for the complement panel and context genes
MOUSE_TO_HUMAN = {
    "C4b": "C4B", "C4a": "C4A", "C1qa": "C1QA", "C1qb": "C1QB", "C1qc": "C1QC", "C3": "C3", "C3ar1": "C3AR1",
    "Hc": "C5", "C5": "C5", "C5ar1": "C5AR1", "C5ar2": "C5AR2", "Cfb": "CFB", "Cfh": "CFH", "Cfd": "CFD",
    "C6": "C6", "C9": "C9", "Cr1l": "CR1L", "Cd55": "CD55", "Cd59a": "CD59", "Serpina3n": "SERPINA3",
    "Plp1": "PLP1", "Mbp": "MBP", "Gfap": "GFAP", "Itgam": "ITGAM", "Itgax": "ITGAX", "Hexb": "HEXB",
    "Cx3cr1": "CX3CR1", "B2m": "B2M", "H2-D1": "HLA-A", "H2-K1": "HLA-B",
}

PANEL = {
    "C4 (reference)":             ["C4b", "C4a"],
    "C1q (classical initiation)": ["C1qa", "C1qb", "C1qc"],
    "C3 / C3a receptor":          ["C3", "C3ar1"],
    "C5 / C5a receptors":         ["Hc", "C5ar1", "C5ar2"],
    "Alternative pathway":        ["Cfb", "Cfh", "Cfd"],
    "Terminal / regulators":      ["C6", "C9", "Cr1l", "Cd55", "Cd59a"],
}
ALL_GENES = [g for gs in PANEL.values() for g in gs]
FOCUS = ["C4b", "C1qa", "C1qb", "C1qc", "C3", "Hc", "C5ar1", "C5ar2", "Cfb"]

# marker sets for coarse annotation (mouse symbols; human handled by upper-casing with a few exceptions)
MARKERS_MOUSE = {
    "Oligodendrocyte": ["Plp1", "Mbp", "Mog", "Mag", "St18", "Cldn11", "Mobp"],
    "OPC": ["Pdgfra", "Cspg4", "Vcan", "Ptprz1"],
    "Microglia": ["Hexb", "Cx3cr1", "Csf1r", "P2ry12", "Tmem119", "C1qa"],
    "Astrocyte": ["Aqp4", "Gja1", "Slc1a3", "Aldoc", "Gfap", "Slc1a2"],
    "Neuron": ["Rbfox3", "Snap25", "Syt1", "Slc17a7", "Gad1", "Gad2", "Meg3"],
    "Endothelial": ["Cldn5", "Flt1", "Pecam1", "Ly6c1"],
    "Vascular/Fibroblast": ["Vtn", "Pdgfrb", "Dcn", "Col1a2", "Rgs5", "Acta2"],
    "Immune (lymphoid/myeloid)": ["Ptprc", "Cd3e", "Skap1", "Cd74", "Mrc1", "Lyz2", "Cd79a"],
    "Ependymal": ["Ccdc153", "Foxj1", "Tmem212", "Rarres2"],
}


def _to_human(sym: str) -> str:
    return MOUSE_TO_HUMAN.get(sym, sym.upper())


def markers_for(species: str) -> Dict[str, List[str]]:
    if species == "mouse":
        return MARKERS_MOUSE
    return {k: [_to_human(g) for g in v] for k, v in MARKERS_MOUSE.items()}


# --------------------------------------------------------------------------------------------------------------------
# generic IO helpers
# --------------------------------------------------------------------------------------------------------------------

def raw_path(acc: str, *parts: str) -> str:
    return os.path.join(RAW_DIR, acc, *parts)


def read_dense_table_sparse(path: str, sep: Optional[str] = None, chunksize: int = 2000, index_col: int = 0,
                            dtype=np.float32) -> AnnData:
    """Read a (genes x cells) or (cells x genes) dense text matrix in chunks into a sparse AnnData (cells x genes)."""
    if sep is None:
        sep = "," if path.endswith(".csv") or path.endswith(".csv.gz") else "\t"
    blocks, index = [], []
    columns = None
    for chunk in pd.read_csv(path, sep=sep, index_col=index_col, chunksize=chunksize, low_memory=False):
        if columns is None:
            columns = chunk.columns
        blocks.append(sp.csr_matrix(np.nan_to_num(chunk.to_numpy(dtype=dtype), nan=0.0)))
        index.extend(chunk.index.astype(str))
    X = sp.vstack(blocks).tocsr()
    rows, cols = np.asarray(index), np.asarray(columns).astype(str)
    # orientation: genes are usually rows in GEO tables; decide by which axis looks like gene symbols
    def looks_like_genes(names):
        s = pd.Series(names[: min(len(names), 2000)])
        return s.str.match(r"^[A-Za-z][A-Za-z0-9\-\.]{1,15}$").mean() > 0.9 and not s.str.contains("_|-1$|:").mean() > 0.5
    if looks_like_genes(rows) and not looks_like_genes(cols) or (X.shape[0] > X.shape[1] and looks_like_genes(rows)):
        X, obs_names, var_names = X.T.tocsr(), cols, rows
    else:
        obs_names, var_names = rows, cols
    ad = AnnData(X=X, obs=pd.DataFrame(index=obs_names), var=pd.DataFrame(index=var_names))
    ad.var_names_make_unique()
    return ad


def read_10x_dir_any(prefix: str) -> AnnData:
    """Read a 10x triplet given a file prefix such as '.../GSM123_sample_' (handles genes.tsv / features.tsv)."""
    files = glob.glob(prefix + "*")
    mtx = [f for f in files if "matrix.mtx" in f][0]
    barcodes = [f for f in files if "barcodes" in f][0]
    feats = [f for f in files if "features" in f or "genes" in f][0]
    ad = sc.read_mtx(mtx).T
    bc = pd.read_csv(barcodes, header=None, sep="\t")[0].astype(str).values
    ft = pd.read_csv(feats, header=None, sep="\t")
    sym = ft[1].astype(str).values if ft.shape[1] > 1 else ft[0].astype(str).values
    ad.obs_names, ad.var_names = bc, sym
    ad.var["gene_id"] = ft[0].astype(str).values
    ad.var_names_make_unique()
    return ad


def parse_gsm_metadata(acc: str) -> pd.DataFrame:
    """Parse the GEO 'form=text&view=brief' sample dump saved as gsm_metadata.txt into a DataFrame indexed by GSM."""
    path = raw_path(acc, "gsm_metadata.txt")
    rows, cur = [], None
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("^SAMPLE"):
                cur = {"gsm": line.split("=")[1].strip()}
                rows.append(cur)
            elif cur is not None and line.startswith("!Sample_title"):
                cur["title"] = line.split("=", 1)[1].strip()
            elif cur is not None and line.startswith("!Sample_organism_ch1"):
                cur["organism"] = line.split("=", 1)[1].strip()
            elif cur is not None and line.startswith("!Sample_characteristics_ch1"):
                kv = line.split("=", 1)[1].strip()
                if ":" in kv:
                    k, v = kv.split(":", 1)
                    cur[k.strip().lower().replace(" ", "_")] = v.strip()
    return pd.DataFrame(rows).set_index("gsm")


# --------------------------------------------------------------------------------------------------------------------
# generic processing
# --------------------------------------------------------------------------------------------------------------------

def standard_process(ad: AnnData, species: str, min_genes: int = 200, min_cells: int = 3, max_mt_pct: float = 10.0,
                     n_top_genes: int = 2000, n_pcs: int = 30, leiden_res: float = 1.0, batch_key: Optional[str] = None,
                     do_cluster: bool = True) -> AnnData:
    """QC -> normalise -> log1p -> HVG -> PCA -> neighbours -> leiden. Raw counts kept in layers['counts']."""
    ad = ad.copy()
    ad.var_names_make_unique()
    ad.obs_names_make_unique()
    mt_prefix = "mt-" if species == "mouse" else "MT-"
    ad.var["mt"] = ad.var_names.str.startswith(mt_prefix)
    sc.pp.calculate_qc_metrics(ad, qc_vars=["mt"], inplace=True, percent_top=None)
    sc.pp.filter_cells(ad, min_genes=min_genes)
    if max_mt_pct is not None:
        ad = ad[ad.obs["pct_counts_mt"] < max_mt_pct].copy()
    sc.pp.filter_genes(ad, min_cells=min_cells)
    ad.layers["counts"] = ad.X.copy()
    sc.pp.normalize_total(ad, target_sum=1e4)
    sc.pp.log1p(ad)
    if do_cluster:
        sc.pp.highly_variable_genes(ad, n_top_genes=n_top_genes, batch_key=batch_key)
        sc.pp.pca(ad, n_comps=n_pcs, use_highly_variable=True)
        sc.pp.neighbors(ad, n_pcs=n_pcs)
        sc.tl.leiden(ad, resolution=leiden_res, key_added="leiden")
    return ad


def annotate_by_markers(ad: AnnData, species: str, cluster_key: str = "leiden", min_margin: float = 0.0) -> AnnData:
    """Cluster-level coarse annotation: score each marker set per cell, average per cluster, assign the best set."""
    markers = markers_for(species)
    scores = {}
    for ct, genes in markers.items():
        genes = [g for g in genes if g in ad.var_names]
        if not genes:
            continue
        sc.tl.score_genes(ad, genes, score_name=f"score_{ct}", use_raw=False)
        scores[ct] = ad.obs[f"score_{ct}"]
    S = pd.DataFrame(scores)
    S = (S - S.mean()) / S.std(ddof=0)          # z-score so that sets with many/strong genes do not dominate
    cl = ad.obs[cluster_key].astype(str)
    cl_mean = S.groupby(cl.values).mean()
    best = cl_mean.idxmax(axis=1)
    margin = cl_mean.max(axis=1) - cl_mean.apply(lambda r: r.nlargest(2).iloc[-1], axis=1)
    best[margin < min_margin] = "Other"
    ad.obs["cell_type_coarse"] = pd.Categorical(cl.map(best).values, categories=COARSE_TYPES)
    ad.uns["cluster_marker_scores"] = cl_mean.round(3).to_dict()
    return ad


def map_original_to_coarse(labels: Iterable[str], mapping: Dict[str, str], default: str = "Other") -> pd.Categorical:
    """Map author labels to COARSE_TYPES using substring rules (first match wins, case-insensitive)."""
    out = []
    for lab in labels:
        s = str(lab).lower()
        hit = default
        for pat, ct in mapping.items():
            if re.search(pat, s):
                hit = ct
                break
        out.append(hit)
    return pd.Categorical(out, categories=COARSE_TYPES)


DEFAULT_LABEL_RULES = {
    r"^opc|precursor|progenitor|cop\b|nfol|committed": "OPC",
    r"oligo|^ol\b|^mol|myelin": "Oligodendrocyte",
    r"microglia|^mg\b|^mic|immune.*mg": "Microglia",
    r"astro|^ast": "Astrocyte",
    r"neuron|^ex|^in\b|^inh|gaba|glut|granule|pyram|^nrgn|^neu": "Neuron",
    r"endo|^ec\b|vascular endoth": "Endothelial",
    r"peri|fibro|vlmc|vascular|mural|smooth|^abc|leptomen|stromal": "Vascular/Fibroblast",
    r"t.?cell|b.?cell|lymph|macro|monocy|myeloid|immune|dendritic|nk\b|neutro|\bdc\b": "Immune (lymphoid/myeloid)",
    r"ependym|choroid|tanycyte": "Ependymal",
}


def finalize(ad: AnnData, dataset: str, species: str, modality: str, group_ref: str) -> AnnData:
    ad.obs["dataset"] = dataset
    ad.obs["species"] = species
    ad.obs["modality"] = modality
    ad.obs["group_ref"] = group_ref
    for c in ["sample", "group"]:
        ad.obs[c] = ad.obs[c].astype(str)
    if "cell_type_coarse" not in ad.obs:
        ad.obs["cell_type_coarse"] = pd.Categorical(["spot" if modality == "spatial" else "Other"] * ad.n_obs)
    return ad


# --------------------------------------------------------------------------------------------------------------------
# dataset loaders
# --------------------------------------------------------------------------------------------------------------------

def load_park_ad() -> AnnData:
    """GSE224398 - Park et al., scRNA-seq of AppNL-G-F (A) vs control (C) mouse hippocampus at 1, 3, 6 months."""
    acc = "GSE224398"
    ads = []
    for f in sorted(glob.glob(raw_path(acc, "*_filtered_feature_bc_matrix.h5"))):
        m = re.search(r"(GSM\d+)_([AC])_(\d+)m_", os.path.basename(f))
        a = sc.read_10x_h5(f)
        a.var_names_make_unique()
        a.obs["gsm"], a.obs["genotype"], a.obs["age_months"] = m.group(1), {"A": "AppNL-G-F", "C": "Control"}[m.group(2)], int(m.group(3))
        a.obs["sample"] = f"{m.group(2)}_{m.group(3)}m"
        ads.append(a)
    ad = sc.concat(ads, join="outer", label="batch", index_unique="-")
    ad.obs["group"] = ad.obs["genotype"].map({"AppNL-G-F": "AD", "Control": "WT"})
    ad = standard_process(ad, "mouse", max_mt_pct=10, leiden_res=1.0)
    ad = annotate_by_markers(ad, "mouse")
    return finalize(ad, "Park2023_AD_hippocampus_scRNA", "mouse", "scRNA", "WT")


def load_aging_snrna() -> AnnData:
    """GSE212576 - snRNA-seq of mouse hippocampus (HIP) and caudate putamen (CP), young (Y) vs old (O)."""
    acc = "GSE212576"
    ads = []
    for mtx in sorted(glob.glob(raw_path(acc, "*_matrix.mtx.gz"))):
        prefix = mtx.replace("matrix.mtx.gz", "")
        m = re.search(r"(GSM\d+)_(HIP|CP)_([YO])_(\d+)_", os.path.basename(mtx))
        a = read_10x_dir_any(prefix)
        a.obs["gsm"], a.obs["region"], a.obs["age_group"], a.obs["replicate"] = m.group(1), m.group(2), {"Y": "Young", "O": "Old"}[m.group(3)], m.group(4)
        a.obs["sample"] = f"{m.group(2)}_{m.group(3)}{m.group(4)}"
        ads.append(a)
    ad = sc.concat(ads, join="outer", label="batch", index_unique="-")
    ad.obs["group"] = ad.obs["age_group"]
    ad = standard_process(ad, "mouse", max_mt_pct=5, leiden_res=1.0)
    ad = annotate_by_markers(ad, "mouse")
    return finalize(ad, "Aging_snRNA_HIP_CP_mouse", "mouse", "snRNA", "Young")


def load_ximerakis() -> AnnData:
    """GSE129788 - Ximerakis et al. 2019, scRNA-seq of whole young (2-3 mo) vs old (21-23 mo) mouse brain, with author cell types.

    The author metadata (Single Cell Portal export) names cells 'Aging_mouse_brain_portal_data_<k>_<barcode>'; the
    library index k is matched to the GEO sample matrices by barcode overlap.
    """
    acc = "GSE129788"
    meta = pd.read_csv(raw_path(acc, "GSE129788_Supplementary_meta_data_Cell_Types_Etc.txt.gz"), sep="\t", index_col=0, skiprows=[1])
    # metadata NAME = 'Aging_mouse_brain_portal_data_<k>_<barcode>'; matrix columns are '<k>_<barcode>'
    meta.index = meta.index.astype(str).str.replace(r"^Aging_mouse_brain_portal_data_", "", regex=True)
    ads = []
    for f in sorted(glob.glob(raw_path(acc, "GSM*_10X.txt.gz"))):
        m = re.search(r"(GSM\d+)_([YO]X\d+[LRX])_10X", os.path.basename(f))
        a = read_dense_table_sparse(f, sep="\t")
        a.obs["gsm"], a.obs["sample"] = m.group(1), m.group(2)
        a.obs["age_group"] = "Young" if m.group(2).startswith("Y") else "Old"
        hit = a.obs_names.isin(meta.index)
        a.obs["cell_type_original"] = pd.Series(a.obs_names, index=a.obs_names).map(meta["cell_type_age"].str.replace(r"_(young|old)$", "", regex=True)).astype(str).values
        a.obs["cell_class_original"] = pd.Series(a.obs_names, index=a.obs_names).map(meta["cell_classes"]).astype(str).values
        print(f"  {m.group(2)}: {hit.mean():.2f} of {a.n_obs} cells have author metadata")
        ads.append(a)
    ad = sc.concat(ads, join="outer", label="batch", index_unique=None)
    ad = ad[ad.obs["cell_type_original"] != "nan"].copy()      # keep author-QC'd cells only
    ad.obs["group"] = ad.obs["age_group"]
    ad = standard_process(ad, "mouse", max_mt_pct=None, leiden_res=1.0, do_cluster=False)
    rules = {r"^opc": "OPC", r"^olg|^ol\b|oligo|^nfol|^mfol|^cop": "Oligodendrocyte", r"^mg\b|microglia": "Microglia",
             r"^asc|astro": "Astrocyte", r"^neur|^m?nb|^nrp|^gaba|^glut|^dopa|^chol|^nend|^imneur|^ex|^in\b|^oeg": "Neuron",
             r"^ec\b|endo": "Endothelial", r"^pc\b|^vsmc|^vlmc|^abc|^hb_vc|^hb|peri|fibro|hemoglobin|^arp": "Vascular/Fibroblast",
             r"^mac|^mnc|^dc|^tnk|^nk|^t_|neut|imm|lymph|^bc|mono": "Immune (lymphoid/myeloid)",
             r"^epc|^cpc|^tnc|^hypepc|ependym|choroid|tanyc": "Ependymal"}
    ad.obs["cell_type_coarse"] = map_original_to_coarse(ad.obs["cell_type_original"], rules)
    return finalize(ad, "Ximerakis2019_aging_brain_scRNA", "mouse", "scRNA", "Young")


def load_zhou_5xfad() -> AnnData:
    """GSE140511 (mouse part) - Zhou et al. 2020 snRNA-seq, WT / Trem2-KO x 5XFAD, cortex (Cor) and hippocampus (Hip), 7 and 15 months."""
    acc = "GSE140511"
    ads = []
    for mtx in sorted(glob.glob(raw_path(acc, "GSM*_matrix.mtx.gz"))):
        base = os.path.basename(mtx).replace("_matrix.mtx.gz", "")
        gsm, name = base.split("_", 1)
        # human samples in this SuperSeries are named differently (e.g. AD1, C1); keep only mouse-style names
        if not re.search(r"(WT|Trem2|5XFAD)", name):
            continue
        a = read_10x_dir_any(mtx.replace("matrix.mtx.gz", ""))
        a.obs["gsm"], a.obs["sample"] = gsm, name
        a.obs["fad"] = "5XFAD" if "5XFAD" in name else "nonTg"
        a.obs["trem2"] = "Trem2_KO" if "Trem2" in name else "Trem2_WT"
        a.obs["region"] = "Cortex" if "Cor" in name else ("Hippocampus" if "Hip" in name else "unknown")
        a.obs["age_months"] = 15 if re.search(r"_(Cor|Hip)$", name) else 7   # region-named libraries are the 15-month cohort
        ads.append(a)
    ad = sc.concat(ads, join="outer", label="batch", index_unique="-")
    ad.obs["group"] = ad.obs["fad"].map({"5XFAD": "AD", "nonTg": "WT"})
    ad = standard_process(ad, "mouse", max_mt_pct=5, leiden_res=1.0)
    ad = annotate_by_markers(ad, "mouse")
    return finalize(ad, "Zhou2020_5XFAD_snRNA", "mouse", "snRNA", "WT")


def load_jakel() -> AnnData:
    """GSE118257 - Jäkel et al. 2019, human snRNA-seq of MS white matter lesions and controls, with author annotation."""
    acc = "GSE118257"
    ad = read_dense_table_sparse(raw_path(acc, "GSE118257_MSCtr_snRNA_ExpressionMatrix_R.txt.gz"), sep="\t")
    ann = pd.read_csv(raw_path(acc, "GSE118257_MSCtr_snRNA_FinalAnnotationTable.txt.gz"), sep="\t")
    key = next((c for c in ann.columns if c.lower() in ("detected", "cell", "cellid", "cell_id", "barcode")), ann.columns[0])
    ann = ann.set_index(key)
    ann.index = ann.index.astype(str)
    ad = ad[ad.obs_names.isin(ann.index)].copy()
    ann = ann.loc[ad.obs_names]
    for c in ann.columns:
        ad.obs[c] = ann[c].values
    ct_col = next((c for c in ann.columns if "celltype" in c.lower().replace("_", "")), None)
    ad.obs["cell_type_original"] = ad.obs[ct_col].astype(str) if ct_col else "unknown"
    # annotation columns: Detected, genes, Sample, Condition (Ctrl/MS), Lesion (Ctrl, NAWM, A, CA, CI, RM), Clusters_res08, Celltypes
    sample_col = next((c for c in ann.columns if c.lower() in ("sample", "sample_id", "sampleid", "patient", "library")), None)
    ad.obs["sample"] = ad.obs[sample_col].astype(str) if sample_col else "unknown"
    lesion_col = next((c for c in ann.columns if c.lower() == "lesion"), None)
    cond_col = next((c for c in ann.columns if c.lower() == "condition"), lesion_col)
    ad.obs["condition_original"] = ad.obs[lesion_col].astype(str).values if lesion_col else "unknown"
    cond = ad.obs[cond_col].astype(str) if cond_col else pd.Series("unknown", index=ad.obs_names)
    ad.obs["group"] = np.where(cond.str.contains("ctr|control|ctrl", case=False), "Ctrl", "MS")
    ad = standard_process(ad, "human", max_mt_pct=None, leiden_res=1.0, do_cluster=False)
    ad.obs["cell_type_coarse"] = map_original_to_coarse(ad.obs["cell_type_original"], DEFAULT_LABEL_RULES)
    return finalize(ad, "Jakel2019_MS_human_snRNA", "human", "snRNA", "Ctrl")


def load_absinta() -> AnnData:
    """GSE180759 - Absinta et al. 2021, human snRNA-seq of chronic active MS lesions (edge/core/periplaque) and controls."""
    acc = "GSE180759"
    ad = read_dense_table_sparse(raw_path(acc, "GSE180759_expression_matrix.csv.gz"), sep=",")
    ann = pd.read_csv(raw_path(acc, "GSE180759_annotation.txt.gz"), sep="\t")
    # annotation columns: nucleus_barcode, NBB_case, pathology, seurat_cluster, cell_type
    key = next((c for c in ann.columns if c.lower() in ("nucleus_barcode", "cell", "cellid", "cell_id", "barcode", "id", "unnamed: 0")), ann.columns[0])
    ann[key] = ann[key].astype(str)
    if not ann[key].is_unique and "NBB_case" in ann.columns:
        # barcodes repeat across cases; the matrix columns are expected to carry a case prefix/suffix
        for fmt in ("{case}_{bc}", "{bc}_{case}", "{case}-{bc}", "{bc}-{case}"):
            cand = [fmt.format(case=c, bc=b) for c, b in zip(ann["NBB_case"].astype(str), ann[key])]
            if len(ad.obs_names.intersection(cand)) > 0.5 * ad.n_obs:
                ann[key] = cand
                break
    if len(ad.obs_names.intersection(ann[key])) < 0.5 * ad.n_obs and len(ann) == ad.n_obs:
        # fall back to positional matching (matrix and annotation exported in the same order)
        ann[key] = list(ad.obs_names)
    ann = ann.set_index(key)
    ann.index = ann.index.astype(str)
    ad = ad[ad.obs_names.isin(ann.index)].copy()
    ann = ann.loc[ad.obs_names]
    for c in ann.columns:
        ad.obs[c] = ann[c].values
    ct_col = next((c for c in ann.columns if c.lower() in ("cell_type", "celltype", "cell type")), None) or \
        next((c for c in ann.columns if "type" in c.lower()), None)
    ad.obs["cell_type_original"] = ad.obs[ct_col].astype(str) if ct_col else "unknown"
    # sanity check of the cell/annotation alignment: PLP1 must be highest in annotated oligodendrocytes
    if "PLP1" in ad.var_names:
        is_ol = ad.obs["cell_type_original"].str.contains("oligo", case=False).values
        plp1 = np.asarray(ad[:, "PLP1"].X.todense()).ravel()
        ratio = (plp1[is_ol].mean() + 1e-9) / (plp1[~is_ol].mean() + 1e-9)
        print(f"  alignment check: mean PLP1 counts oligodendrocytes/others = {ratio:.1f} (expect >> 1)")
        if ratio < 3:
            raise RuntimeError("Absinta annotation does not align with the expression matrix; check barcode matching")
    sample_col = next((c for c in ann.columns if c.lower() in ("nbb_case", "sample", "sample_id", "sampleid", "patient", "donor", "library")), None)
    cond_col = next((c for c in ann.columns if c.lower() in ("pathology", "lesion", "lesion_type", "region", "tissue", "condition", "group")), None)
    ad.obs["sample"] = ad.obs[sample_col].astype(str) if sample_col else "unknown"
    cond = ad.obs[cond_col].astype(str) if cond_col else pd.Series("unknown", index=ad.obs_names)
    ad.obs["condition_original"] = cond.values
    ad.obs["group"] = np.where(cond.str.contains("ctr|control|ctrl|healthy", case=False), "Ctrl", "MS")
    ad = standard_process(ad, "human", max_mt_pct=None, leiden_res=1.0, do_cluster=False)
    rules = {r"^immune$": "Microglia", r"^lymph": "Immune (lymphoid/myeloid)"}   # Absinta 'immune' = microglia/macrophages
    rules.update(DEFAULT_LABEL_RULES)
    ad.obs["cell_type_coarse"] = map_original_to_coarse(ad.obs["cell_type_original"], rules)
    return finalize(ad, "Absinta2021_MS_human_snRNA", "human", "snRNA", "Ctrl")


def load_chen_st() -> AnnData:
    """GSE152506 - Chen et al. 2020, Spatial Transcriptomics (ST arrays) of AppNL-G-F (TG) vs WT mouse brain at 3-18 months.

    Despite the .txt extension the table is comma-separated, spots x genes, with spot ids '<sample>__<x>_<y>' and
    missing values for zeros.
    """
    acc = "GSE152506"
    ad = read_dense_table_sparse(raw_path(acc, "GSE152506_raw_counts.txt.gz"), sep=",")
    gsm = parse_gsm_metadata(acc)
    ids = pd.Series(ad.obs_names, index=ad.obs_names)
    ad.obs["sample"] = ids.str.replace(r"__.*$", "", regex=True).values
    xy = ids.str.extract(r"__(\d+(?:\.\d+)?)_(\d+(?:\.\d+)?)$")
    if xy.notna().all(axis=None):
        ad.obsm["spatial"] = xy.astype(float).to_numpy()
    t2gsm = gsm.reset_index().set_index("title")
    for col in ["genotype", "age", "strain"]:
        if col in gsm.columns:
            ad.obs[col] = ad.obs["sample"].map(t2gsm[col]).astype(str).values
    ad.obs["group"] = ad.obs["genotype"].map({"TG": "AD", "WT": "WT"}).fillna("unknown") if "genotype" in ad.obs else "unknown"
    ad = standard_process(ad, "mouse", min_genes=100, max_mt_pct=None, leiden_res=0.5, do_cluster=False)
    return finalize(ad, "Chen2020_ST_AppNLGF_mouse", "mouse", "spatial", "WT")


def load_kaya() -> AnnData:
    """GSE202579 - Kaya et al. 2022, 10x scRNA-seq of 24-month-old WT and Rag1-KO mouse white matter (WM) vs grey matter (GM).

    The 10x libraries are all aged (24 mo); the young-vs-aged comparison of the paper is Smart-seq2 and not deposited as a
    matrix. The comparison here is therefore aged white matter vs aged grey matter, with Rag1-KO (no functional
    lymphocytes) as a genetic control kept in ``obs['genotype']``.
    """
    acc = "GSE202579"
    parts = []
    for mat, meta_f, geno in [("GSE202579_10X_WT.FACS_allctype_rawcounts.tsv.gz", "GSE202579_Metadata_allctypes_WTLibs.csv.gz", "WT"),
                              ("GSE202579_10X_Rag1KO_allctype_rawcounts.tsv.gz", "GSE202579_Metadata_allctypes_Rag1KOLibs.csv.gz", "Rag1KO")]:
        a = read_dense_table_sparse(raw_path(acc, mat), sep="\t")
        meta = pd.read_csv(raw_path(acc, meta_f), index_col=0)
        meta.index = meta.index.astype(str)
        # R turned '-' into '.' in the matrix column names
        a.obs_names = [n.replace(".", "-") for n in a.obs_names]
        common = a.obs_names.intersection(meta.index)
        if len(common) < 0.5 * a.n_obs and len(meta) == a.n_obs:
            meta.index = list(a.obs_names)
            common = a.obs_names
        a = a[a.obs_names.isin(common)].copy()
        meta = meta.loc[a.obs_names]
        for c in meta.columns:
            a.obs[c] = meta[c].values
        a.obs["genotype"] = geno
        parts.append(a)
    ad = sc.concat(parts, join="outer", label="batch", index_unique="-")
    tissue_col = next((c for c in ad.obs.columns if c.lower() == "tissue"), None)
    lib_col = next((c for c in ad.obs.columns if c.lower() == "library"), None)
    ad.obs["region"] = ad.obs[tissue_col].astype(str).map({"WhiteM": "WM", "GreyM": "GM"}).fillna(ad.obs[tissue_col].astype(str)) if tissue_col else "unknown"
    ad.obs["sample"] = ad.obs[lib_col].astype(str) if lib_col else (ad.obs["genotype"] + "_" + ad.obs["region"])
    ad.obs["group"] = ad.obs["region"].astype(str)
    ad.obs["age_months"] = 24
    ad = standard_process(ad, "mouse", max_mt_pct=10, leiden_res=1.0)
    ad = annotate_by_markers(ad, "mouse")
    return finalize(ad, "Kaya2022_aged_WM_vs_GM_scRNA", "mouse", "scRNA", "GM")


LOADERS = {
    "Park2023_AD_hippocampus_scRNA": load_park_ad,
    "Aging_snRNA_HIP_CP_mouse": load_aging_snrna,
    "Ximerakis2019_aging_brain_scRNA": load_ximerakis,
    "Zhou2020_5XFAD_snRNA": load_zhou_5xfad,
    "Jakel2019_MS_human_snRNA": load_jakel,
    "Absinta2021_MS_human_snRNA": load_absinta,
    "Chen2020_ST_AppNLGF_mouse": load_chen_st,
    "Kaya2022_aged_WM_vs_GM_scRNA": load_kaya,
}


def build_all(only: Optional[Iterable[str]] = None, overwrite: bool = False) -> Dict[str, str]:
    """Run the loaders and write <PROCESSED_DIR>/<name>.h5ad. Returns name -> path for successful builds."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    out = {}
    names = list(only) if only else list(LOADERS)
    for name in names:
        path = os.path.join(PROCESSED_DIR, f"{name}.h5ad")
        if os.path.exists(path) and not overwrite:
            print(f"[skip] {name} exists")
            out[name] = path
            continue
        print(f"[build] {name} ...", flush=True)
        try:
            ad = LOADERS[name]()
            ad.write(path)
            out[name] = path
            print(f"[done] {name}: {ad.n_obs} cells x {ad.n_vars} genes; groups={ad.obs['group'].value_counts().to_dict()}", flush=True)
        except Exception as exc:  # keep going with the other datasets
            print(f"[FAILED] {name}: {type(exc).__name__}: {exc}", flush=True)
    return out


def processed_paths() -> Dict[str, str]:
    return {os.path.basename(p)[:-5]: p for p in sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.h5ad")))}
