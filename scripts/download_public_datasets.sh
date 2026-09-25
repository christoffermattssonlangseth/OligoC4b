#!/bin/sh
# Download the public datasets used by notebooks/build/build_public_datasets.ipynb (parallel, resumable, ~15 GB).
# Usage: OLIGOC4B_PUBLIC_RAW_DIR=/path/to/raw sh scripts/download_public_datasets.sh
BASE=${OLIGOC4B_PUBLIC_RAW_DIR:?set OLIGOC4B_PUBLIC_RAW_DIR to the download folder}
mkdir -p $BASE
get() { # get <dir> <url>  (parallel-safe; writes .part then renames)
  d=$BASE/$1; mkdir -p $d; f=$d/$(basename $2)
  if [ -s "$f" ]; then echo "skip $f"; return; fi
  echo "GET $2"; curl -sL --retry 3 -C - -o "$f.part" "$2" || { echo "FAILED $2"; return; }
  # GEO occasionally answers a parallel request with a small HTML error page: reject those
  if head -c 200 "$f.part" | grep -qi "<html\|<?xml"; then echo "HTML-ERROR $2 (retry later)"; rm -f "$f.part"; return; fi
  mv "$f.part" "$f" && echo "OK $(basename $f)"
}
geo_gsm_meta() { curl -s -o $BASE/$1/gsm_metadata.txt "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=$1&targ=gsm&form=text&view=brief"; }
S=https://ftp.ncbi.nlm.nih.gov/geo/series
get GSE224398 $S/GSE224nnn/GSE224398/suppl/GSE224398_RAW.tar &
get GSE212576 $S/GSE212nnn/GSE212576/suppl/GSE212576_RAW.tar &
get GSE129788 $S/GSE129nnn/GSE129788/suppl/GSE129788_RAW.tar &
get GSE140511 $S/GSE140nnn/GSE140511/suppl/GSE140511_RAW.tar &
get GSE118257 $S/GSE118nnn/GSE118257/suppl/GSE118257_MSCtr_snRNA_ExpressionMatrix_R.txt.gz &
get GSE180759 $S/GSE180nnn/GSE180759/suppl/GSE180759_expression_matrix.csv.gz &
get GSE152506 $S/GSE152nnn/GSE152506/suppl/GSE152506_raw_counts.txt.gz &
get GSE202579 $S/GSE202nnn/GSE202579/suppl/GSE202579_10X_WT.FACS_allctype_rawcounts.tsv.gz &
get GSE202579 $S/GSE202nnn/GSE202579/suppl/GSE202579_10X_Rag1KO_allctype_rawcounts.tsv.gz &
(
get GSE129788 $S/GSE129nnn/GSE129788/suppl/GSE129788_Supplementary_meta_data_Cell_Types_Etc.txt.gz
get GSE118257 $S/GSE118nnn/GSE118257/suppl/GSE118257_MSCtr_snRNA_FinalAnnotationTable.txt.gz
get GSE180759 $S/GSE180nnn/GSE180759/suppl/GSE180759_annotation.txt.gz
for f in GSE202579_10X_WT.RagKO_Microglia.filtered_rawcounts.tsv.gz GSE202579_10X_WT.RagKO_Oligos.filtered_rawcounts.tsv.gz GSE202579_Metadata_Microglia_RagKO.WT.csv.gz GSE202579_Metadata_Oligo_RagKO.WT.csv.gz GSE202579_Metadata_allctypes_Rag1KOLibs.csv.gz GSE202579_Metadata_allctypes_WTLibs.csv.gz; do
  get GSE202579 $S/GSE202nnn/GSE202579/suppl/$f
done
for acc in GSE224398 GSE212576 GSE129788 GSE140511 GSE118257 GSE180759 GSE152506 GSE202579; do geo_gsm_meta $acc; done
) &
wait
# ---- round 2: human AD, demyelination models, more human MS (snRNA-seq + Visium) ----
get GSE147528 $S/GSE147nnn/GSE147528/suppl/GSE147528_RAW.tar &
get GSE167494 $S/GSE167nnn/GSE167494/suppl/GSE167494_RAW.tar &
get GSE293850 $S/GSE293nnn/GSE293850/suppl/GSE293850_RAW.tar &
get GSE319903 $S/GSE319nnn/GSE319903/suppl/GSE319903_RAW.tar &
get GSE279181 $S/GSE279nnn/GSE279181/suppl/GSE279181_RAW.tar &
get GSE277435 $S/GSE277nnn/GSE277435/suppl/GSE277435_RAW.tar &
get Schirmer2019 https://cells.ucsc.edu/ms/exprMatrix.tsv.gz &
(
for ct in OL OPC MG AS NEU EC BC; do get GSE279180 $S/GSE279nnn/GSE279180/suppl/GSE279180_ctype_${ct}.h5ad; done
get Schirmer2019 https://cells.ucsc.edu/ms/meta.tsv
for acc in GSE147528 GSE167494 GSE293850 GSE319903 GSE279180 GSE279181 GSE277435; do geo_gsm_meta $acc; done
) &
wait
for acc in GSE224398 GSE212576 GSE129788 GSE140511 GSE147528 GSE167494 GSE293850 GSE319903 GSE279181 GSE277435; do
  d=$BASE/$acc; if [ -s $d/${acc}_RAW.tar ] && [ ! -f $d/.extracted ]; then (cd $d && tar -xf ${acc}_RAW.tar && touch .extracted && echo "extracted $acc"); fi
done
echo ALL_DONE
