# Pilot versus expanded evaluation

Phase 3's 272 pairs were selected without reading labels, and its fixed random and geographic tests happened to contain no High reference pixels. This was a **sampling-support limitation**, not proof that the original 24,518-pair pool lacks High. The complete new census finds 123 High-bearing pairs and 99,620 High pixels in 3 components in that original pool.

Phase 3.5 froze geographic/date/class-support criteria before model evaluation, indexed all six archives, and screened reference masks before fetching additional inputs. It did not move old test patches, overwrite results or select geography using scores. 42 pilot artifacts retain their original SHA-256 values.

| Model | Pilot geographic macro F1* | v2 macro F1 | Pilot High F1 | v2 High F1 |
|---|---:|---:|---|---:|
| NDCI | 0.4185 | 0.5185 | N/A (no support) | 0.0006 |
| NDVI | 0.2599 | 0.4141 | N/A (no support) | 0.0000 |
| FAI | 0.2781 | 0.3089 | N/A (no support) | 0.3425 |
| B8AB4 | 0.2891 | 0.3653 | N/A (no support) | 0.0025 |
| B3B2 | 0.4503 | 0.4212 | N/A (no support) | 0.0000 |
| LogisticRegression | 0.3266 | 0.6983 | N/A (no support) | 0.5803 |
| RandomForest | 0.3768 | 0.4794 | N/A (no support) | 0.0012 |
| SmallSegCNN | 0.2676 | 0.0632 | N/A (no support) | 0.1627 |
| DeepLabV3_ResNet18 | 0.3222 | 0.3627 | N/A (no support) | 0.2700 |

*Pilot macro averaged three slots with undefined-class score set to zero; its test contained no High pixels. The numbers are not like-for-like estimates of the same three-class distribution. Model families/configuration are unchanged, but training observations, independent regions and test prevalence differ. Each model was refitted on v2 training only; old checkpoints were not overwritten.

A valid expanded benchmark asks a harder scientific question because it requires actual High detection in multiple held-out regions. Whether a particular pooled number decreases is not a validity criterion. Support enrichment and changed geography prevent claiming a pure causal change in generalization difficulty from these scores alone.

Outcome: **B — Partial evidence**. Logistic regression provides genuine but partial High-detection evidence: pooled High precision 0.6071, recall 0.5557, F1 0.5803; its region-specific High recall ranges from 0.2793 to 0.5900, and F1 from 0.4006 to 0.5964. The equal-region mean High recall is 0.4767, below the pooled recall. One test component contributes 73.74% of High pixels, so pooled metrics overweight that geography.

Random forest reaches 0.7477 accuracy but High recall is only 0.000609: it effectively misses High. SmallSegCNN's High recall 0.9886 comes with precision 0.0887; widespread High predictions do not constitute useful detection. DeepLab's pooled High F1 is 0.2700, with zero High recall in 1 of the three held-out regions. Short unweighted training prevents attributing these failures to inherent architectural limits.

**Why B, not A:** all three classes and the preregistered regional support are now present, but High performance varies materially by region/model, only three test components were assessed, and evaluation prevalence is deliberately enriched. The benchmark passes its operational support gate; strong reliability evidence remains insufficient.

Scores changed in both directions: for example, SmallSegCNN macro F1 fell while logistic regression increased. This does not isolate a pure geography effect because the support distribution and training pool changed. Detailed group results follow in PHASE_3_5_STATUS.md.
