# 🧪 C4b Co-expression Analysis in DA-Oligodendrocytes

We applied multiple complementary methods to explore the gene programs co-expressed with **C4b** in DA-oligodendrocytes. Each method provides a different perspective on the biology.

---

## 🔬 Methods

1. **Correlation (Pearson)**  
   Measures linear co-expression between genes and C4b.  
   → Identifies broad gene modules moving together with C4b.

2. **LASSO Regression**  
   Sparse regression model predicting C4b from all other genes.  
   → Highlights non-redundant predictors that uniquely explain C4b expression.

3. **Mutual Information (MI)**  
   Captures nonlinear associations (e.g. threshold-dependent or conditional expression).  
   → Finds hidden links missed by correlation.

4. **Cell-level Co-expression Probability**  
   Calculates the fraction of C4b+ cells also expressing each gene.  
   → Reveals “hard co-activation rules” (which genes are nearly always on in C4b+ cells).

---

## 📊 Main Takeaways

- **Immune–complement program**  
  - *Serpina3n, H2-D1, H2-K1, B2m, Psmb8, Nlrc5, C3*  
  - Strongly co-expressed → points to an **MHC-I / interferon-driven immune axis** in C4b+ OLs.

- **Oligodendrocyte lineage identity**  
  - *Mbp, Mag, Cnp, Cldn11, Car2, Nkx6-2*  
  - Confirms C4b+ cells remain OLs despite immune activation.

- **Stress & degeneration markers**  
  - *App, Mapt, Cryab, Stmn4, Klk6, Stat3*  
  - Indicate **cytoskeletal remodeling and degenerative stress** programs.

- **Metabolic & lysosomal remodeling**  
  - *Plin4, Apod, ScarB2, Lamp1, Aldoa*  
  - Suggest **lipid droplet accumulation, lysosomal stress, and altered metabolism**.

- **Trafficking & axon–glia crosstalk**  
  - *Rab7, Kif1b, Sv2a, Cd81, Rac1*  
  - Highlight **vesicle transport and glia–neuron communication** pathways.

---

## 🧩 Integrated View

C4b+ DA-oligodendrocytes represent a **multi-program reactive OL state** that combines:

- **Immune activation** (complement & MHC-I)  
- **Lineage stability** (myelin/OL genes remain expressed)  
- **Degenerative stress** (cytoskeleton, APP/tau, heat-shock)  
- **Metabolic imbalance** (lipid droplets, lysosomes)  
- **Cross-talk with neurons/immune cells** (axon–glia and vesicle trafficking genes)

---

✦ Using these four approaches together allows us to capture **different layers of the biology**:  
- *Correlation*: broad immune program  
- *Lasso*: essential non-redundant predictors  
- *MI*: nonlinear hidden associations  
- *Co-expression*: invariant features of C4b+ cells
