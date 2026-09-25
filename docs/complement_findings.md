# Complement beyond C4b: what the analyses showed

Question from the group lead (September 2026): *have we checked C5 and the C5 receptors in our spatial datasets when checking C4b, and also C1q and Cfb?*

Notebooks: `notebooks/analysis/analysis_spatial_complement_C5_C1q_Cfb.ipynb` (in-house Xenium AD, Xenium EAE, Visium aging, plus the Falcão scRNA-seq check) and `notebooks/analysis/analysis_public_datasets_complement.ipynb` (sixteen public datasets, see [`public_datasets.md`](public_datasets.md)). Each notebook ends with a written interpretation; this page is the condensed version.

## What is measurable where

Xenium is a targeted assay, so the first result is panel content. Mouse C5 is annotated as `Hc`.

| Gene | Xenium AD (347 genes) | Xenium EAE (5K panel) | Visium / all public data |
| --- | --- | --- | --- |
| C4b | ✓ | ✓ | ✓ |
| C1qa / C1qb / C1qc | ✓ | ✗ | ✓ |
| C3 | ✓ | ✓ | ✓ |
| C3ar1 | ✗ | ✓ | ✓ |
| C5 (`Hc`) | ✗ | ✓ | ✓ |
| C5ar1 / C5ar2 | ✗ | ✓ | ✓ |
| Cfb | ✗ | ✓ | ✓ |

Human C4A/C4B are not quantifiable in any of the eight human datasets (5–470 UMIs in 17–107 k nuclei, 19–242 UMIs in 28–70 k Visium spots): the paralogs are near-identical and multi-mapping reads are discarded by Cell Ranger / Space Ranger.

## C4b itself

- Rises in oligodendrocytes with age in every aging dataset (pseudobulk log2FC ≈ 2–3), is far higher in aged white than grey matter (77 % of aged white-matter oligodendrocytes C4b⁺ in Kaya et al. 2022), is up ~2.8 log2 in 5XFAD oligodendrocytes, and rises with toxic demyelination (8 % → 16 % of oligodendrocyte nuclei after cuprizone, 34 % after LPC).
- In spatial AD data (Chen et al. 2020) its spot-level correlates are the plaque-induced / DAM genes (C4a, Cst7, Gfap, Tyrobp, Trem2, Apoe, C1qa–c, Serpina3n).
- The C4b⁺ oligodendrocyte program is the same everywhere: Serpina3n is the #1 C4b-correlated gene in three of four mouse datasets, followed by the MHC-I / interferon module (H2-D1, B2m, H2-K1, Ifi27, Irf9, Stat3), Klk6, Apod, Trf, Cd9, Cldn11.

## C5 (`Hc` / C5)

- Mouse: ≤0.5 % of cells of any type in EAE, ≤0.3 % in all six public mouse datasets, ~1 % of Visium spots; no disease or age change. C5 is plasma-derived, so the C5/C5a arm has to be assessed at protein level (C5a, C5b-9 staining).
- Human: a low glial C5 transcript exists in every human dataset (oligodendrocytes 2–11 %, astrocytes 4–17 %, OPCs 3–17 %), unchanged across Braak stages and unchanged or lower in MS lesions (Jäkel log2FC −1.5, p = 0.004). Not a disease-responsive transcript.

## C5a receptors

- C5ar1 is myeloid in every dataset: 20–45 % of microglia / macrophages / infiltrating myeloid cells in EAE, 6–38 % of mouse microglia in the public data (highest in aged white matter), 3–17 % of human microglia nuclei. Oligodendrocytes, including C4b⁺ DA oligodendrocytes, are ≤1 % positive in all nineteen datasets, and sorted single cells (Falcão) confirm this is not spill-over. In human MS, microglial C5AR1 peaks at chronic active lesion edges (Absinta 14.5 % vs 4.5 % control; Lerma-Martin 25 % vs 8 %, log2FC 1.3, p = 0.056) and the matched Lerma-Martin Visium shows 8.5-fold higher C5AR1 in chronic active lesion spots than in control white matter.
- Per-cell C5ar1 in myeloid cells is flat across lesion distance and unchanged by EAE; the tissue-level gradient toward lesions is cell recruitment.
- Spatially, C5aR1⁺ cells are about twice as enriched within 30 µm of C4b-high oligodendrocytes as of C4b-negative ones (87 EAE samples, paired Wilcoxon p ≈ 4×10⁻⁷). This survives matching for lesion distance (median ratio 1.96 over 76 samples) and restricting to non-lesion tissue (2.2). Near lesions the ratio is ~1 because everything is myeloid-dense; far from lesions it is 1.7–2.3, so C4b-high oligodendrocytes mark myeloid-rich micro-niches outside lesions.
- C5ar2 follows the same pattern at lower levels.

## C1q

- Microglial everywhere (76–100 % of mouse microglia). The ~30 % detection inside "oligodendrocytes" seen only in droplet scRNA-seq (Park, Kaya) is ambient RNA; in nuclei it is 1–6 %.
- Rises with age together with C4b in Visium and ranks in the top ~50 of 16 k genes correlated with C4b in white-matter spots; in the Chen spatial AD data it ranks 11–18 of ~14 k. Inside oligodendrocyte nuclei the coupling is weak (5XFAD rank 233–482, aging > 2,800).
- In the Xenium AD sections, C1q⁺ microglia are enriched around C4b-high oligodendrocytes only in the two oldest sections; C3⁺ astrocytes are ~3× enriched in every section.

## Cfb

- An EAE-lesion myeloid gene: 67 % of lesion macrophages, induced ~10-fold in EAE microglia, steep lesion gradient, 1.7× enriched around C4b-high oligodendrocytes. In the sorted Falcão data it is the one panel gene with a modest intrinsic component in disease-associated oligodendrocytes (13 % vs 2 % of control, ~5× enriched in C4b⁺ cells).
- Silent everywhere else: ≤0.2 % of microglia and ≤0.1 % of oligodendrocytes in every AD and aging dataset, 0.2–1.6 % of microglia after LPC / cuprizone, ~0.4 % of Visium spots; in human MS only chronic-active-lesion microglia show it (Lerma-Martin 2.8 % vs 0.8 %). Cfb therefore marks active inflammatory demyelination rather than the age- or amyloid-associated C4b⁺ state.

## Complement genes that do join the C4b⁺ program

C4a (spatial AD rank 1; 4-fold detection enrichment in aged white-matter oligodendrocytes) and the membrane regulators Cd59a (ranks 117–269) and Cr1l / Crry (ranks ~1,100–1,250). No receptor, Cfb or Hc ranks in the top 1,000 anywhere. C4b⁺ oligodendrocytes up-regulate protection against complement deposition, not complement receptors.

## Caveats and open items

1. EAE neighbourhood tests use the existing `lesion_distance_bin` calls; bins closer than 50 µm had too few C4b-negative oligodendrocytes to test.
2. The Xenium AD time course has one section per genotype × age; those trends are descriptive.
3. Coarse annotation of the public datasets is marker-based for Park, aging snRNA-seq, Zhou, Kaya, Leng, Sadick, LPC/cuprizone and Serpina3n-cKO; only the oligodendrocyte and microglia labels were validated (Plp1 ≈ 100 %, Hexb 92–100 %). Park OPC / neuron labels are unreliable; Sadick's myeloid cells fell under "Immune".
8. Nuclei from active demyelinating lesions (LPC, cuprizone) carry microglial ambient RNA: C1q / Apoe / Ctsd co-vary with C4b in those "oligodendrocyte" nuclei and should not be read as intrinsic. The Serpina3n-cKO cuprizone set has no usable C4b⁺ oligodendrocyte population (2 %, microglial correlates).
4. Pseudobulk tests are underpowered for Park (3 vs 3 pooled libraries) and the human datasets (1–2 control donors).
5. The Kaya 10x libraries are all 24 months old: the comparison is white vs grey matter in aged brain, not young vs aged.
6. Human C4A/C4B would need a multi-mapping-aware re-quantification (e.g. STARsolo with EM, or a merged C4A/C4B reference).
7. C5 protein, C5a and C5b-9 deposition are wet-lab questions.
