"""Render Phase4 reports from machine-readable artifacts; never edits older reports."""
import csv,json,re,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from run_phase4 import OUT,write
R=Path('research_outputs/reports')
def read(n):return json.loads((OUT/n).read_text())
def rows(n):return list(csv.DictReader((OUT/n).open()))
def f(x):
    if x is None or x=='':return 'N/A'
    if isinstance(x,(float,np.floating)):return f'{x:.4f}'
    return str(x)
def table(headers,data):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(f(x) for x in row)+' |' for row in data)+'\n'
def report(name,text):
    # Format prose without changing code IDs, paths, equations, or URLs.
    chunks=re.split(r'(```[\s\S]*?```|`[^`]*`|\]\([^)]+\))',text)
    words='The|the|Only|only|All|all|every|with|With|at|by|is|Is|than|and|of|from|for|in|to|both|has|have|not|No|uses|makes|correct|about|range|changes|counts|count|depth|cap|bound|spans|contributes|average|passes|pass|plus|detects|missing|misses|detect|sum|supply|over|overall|across|on|remain|remains|recalls|recall|High|confidence|mean|same|batch|seed|gamma|total|after|epochs|epoch'
    for j in range(0,len(chunks),2):
        chunks[j]=re.sub(r'\b('+words+r')(?=[0-9−])',r'\1 ',chunks[j])
        chunks[j]=re.sub(r'(?<=[0-9])(?=(?:times|correct|region|regions|model|models|class|classes|whole|steps|step|epochs|epoch|selected|pixels|pixel|dates|months|years|independent|new|original|tests)\b)',' ',chunks[j])
        chunks[j]=chunks[j].replace('bounded[','bounded [').replace('3region','3 region').replace('2epochs','2 epochs').replace('64steps','64 steps').replace('32steps','32 steps').replace('a inferred','an inferred')
    (R/name).write_text(''.join(chunks).strip()+'\n')
def short(g):return g.split(':')[-1].replace('_S050','')
def macro(m):return m['macro_f1']
def high(m):return m['per_class'][2]['f1']
def artifact(name):return f'[`{name}`](../phase4/{name})'

def main():
    results=read('results.json');selection=read('selection.json');specs=read('specifications.json');cal=read('calibration.json');temps=read('temperatures.json');rob=rows('robustness_metrics.csv');diag=read('lr_rf_diagnostics.json');train=read('train_test_minority_diagnostics.json');shift=read('shift_association.json');temporal=read('temporal_shift.json');ig=read('integrated_gradients.json');repro=read('reproduction_check.json');preserve=read('preservation_check.json')
    testxml=ET.parse(OUT/'pytest_results.xml').getroot();testcount=sum(int(e.attrib.get('tests',0)) for e in testxml.findall('testsuite'));assert sum(int(e.attrib.get('failures',0))+int(e.attrib.get('errors',0)) for e in testxml.findall('testsuite'))==0
    overall=selection['overall'];cnn=selection['cnn'];lr='baseline_LogisticRegression';rf='baseline_RandomForest';gs=sorted(results[lr]['test_groups']);base=results[cnn]['test']
    limitations='The v2 subset is label-enriched: High prevalence is 0.242% in Train, 0.645% in Validation, and 8.811% in Test. Precision and calibration are conditional on that composition. There are two training components, one validation component and only three held-out connected geographic components; component separation does not certify separate lakes or independent bloom episodes. References are processed/resampled CyAN DN classes, not in-situ cell counts, toxin measurements, or verified 20 m biological ground truth. Neural budgets remain only 3 epochs (SmallSegCNN) / 2 epochs (DeepLab), random initialization, one seed. These are controlled short-budget experiments, not converged architecture comparisons.'
    select_text=f'The preregistered validation winner is `{overall}` (validation Macro F1 {macro(results[overall]["validation"]):.4f}; validation High F1 {high(results[overall]["validation"]):.4f}). It fails to demonstrate High detection on Validation. `{cnn}` is the highest-ranked CNN (validation Macro F1 {macro(results[cnn]["validation"]):.4f}; Low/Moderate/High F1 '+ '/'.join(f'{c["f1"]:.4f}' for c in results[cnn]['validation']['per_class'])+'). **No CNN meets both preregistered Low>=0.50 and Moderate>=0.25 floors.** This CNN is a diagnostic fallback, not an eligible deployment choice. Ablations are excluded from winner selection by registration.'
    # Central reliability matrix: separate pools, explicit unavailable comparisons.
    matrix=[]
    for i,r in results.items():
        matrix.append({'model':i,'benchmark':'v2_288_pairs','random_macro_f1':None,'geographic_macro_f1':macro(r['test']),'high_f1':high(r['test']),'worst_region_high_f1':min(high(v) for v in r['test_groups'].values()),'ece':cal.get(i,{}).get('raw',{}).get('overall',{}).get('ece'),'robustness_worst_delta_macro_f1':min(float(v['delta_macro_f1']) for v in rob) if i==cnn else None})
    pilot=json.loads(Path('research_outputs/phase3_pilot/results.json').read_text());matched=read('matched_pilot_calibration.json')
    for i in pilot['random']['models']:
        matrix.append({'model':i,'benchmark':'matched_pilot_272_pairs','random_macro_f1':pilot['random']['models'][i]['test']['macro_f1_fixed_three_zero_division'],'geographic_macro_f1':pilot['geographic']['models'][i]['test']['macro_f1_fixed_three_zero_division'],'high_f1':None,'worst_region_high_f1':None,'ece':matched['geographic'].get(i,{}).get('calibration',{}).get('ece'),'robustness_worst_delta_macro_f1':None})
    with (OUT/'model_reliability_matrix.csv').open('w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=list(matrix[0]));w.writeheader();w.writerows(matrix)
    matheads=['Model','Random Macro F1','Geographic Macro F1','High F1','Worst-region High F1','ECE','Worst robustness ΔMacro F1']
    def matrows(pool):return [[d[k] for k in ['model','random_macro_f1','geographic_macro_f1','high_f1','worst_region_high_f1','ece','robustness_worst_delta_macro_f1']] for d in matrix if d['benchmark']==pool]
    matrix_text='# Model reliability matrix\n\n'+select_text+'\n\n## Frozen v2, 288 pairs\n\n'+table(matheads,matrows('v2_288_pairs'))+'\n## Matched original pilot, 272 pairs\n\n'+table(matheads,matrows('matched_pilot_272_pairs'))+'\nN/A means unmeasured or undefined, never zero. v2 models have no matched Random Test fit. The old pilot has no High Test pixels, so its High F1 is undefined. Fixed-three-class Macro F1 assigns zero contribution to an unsupported class; do not compare these two tables as a causal random/geographic split effect. ECE is uncalibrated top-label ECE; temperature variants are in CALIBRATION_ANALYSIS.md. Robustness was measured only for the registered diagnostic CNN; value is the worst of 12 fixed perturbations. Predictive ranking, calibration and reliability can disagree.\n\n'+artifact('model_reliability_matrix.csv')
    report('MODEL_RELIABILITY_MATRIX.md',matrix_text)
    # Regional answers.
    hardest=[]
    for i,r in results.items():
        hard=min(r['test_groups'],key=lambda g:macro(r['test_groups'][g]));worst=min(r['test_groups'],key=lambda g:high(r['test_groups'][g]));cm=np.array(r['test']['confusion_matrix']);fn=cm.sum(1)-np.diag(cm)
        hardest.append([i,short(hard),macro(r['test_groups'][hard]),['Low','Moderate','High'][fn.argmax()],int(cm[2,1]),int(cm[2,0]),r['test']['per_class'][2]['predicted_proportion'],short(worst),high(r['test_groups'][worst])])
    regional_table=table(['Model','Lowest-Macro region','Macro F1','Most FN (absolute)','High→Moderate','High→Low','Predicted High fraction','Lowest-High region','High F1'],hardest)
    support=table(['Region','Valid pixels','True Low fraction','True Moderate fraction','True High fraction','High support'],[[short(g),results[lr]['test_groups'][g]['valid_pixels'],*[c['true_proportion'] for c in results[lr]['test_groups'][g]['per_class']],results[lr]['test_groups'][g]['per_class'][2]['support']] for g in gs])
    selected_regions=table(['Model','Region','Macro F1','High P','High R','High F1'],[[i,short(g),macro(results[i]['test_groups'][g]),*[results[i]['test_groups'][g]['per_class'][2][k] for k in ['precision','recall','f1']]] for i in [overall,lr,rf,cnn] for g in gs])
    similarity=next(r for r in rows('error_similarity.csv') if {r['model_a'],r['model_b']}=={lr,rf})
    report('REGIONAL_FAILURE_ANALYSIS.md',f'''# Regional failure analysis

There is no model-independent hardest region. For LR the lowest Macro F1 is 7_5_X1800_Y1700 (0.5906), but the lowest High F1 is 6_2_X0650_Y0900 (0.4006). For the diagnostic CNN the lowest Macro F1 is 6_2_X0500_Y1150 (0.2973), and its lowest High F1 is 6_2_X0650_Y0900 (0.1616). The validation-selected NDCI fails High in both 6_2 regions.

{support}
{selected_regions}
## Answers across every model

“Most FN” counts erroneous pixels by true class, so each wrong prediction counts once. It is not an FP+FN double count. Low dominates absolute errors for LR/RF because Low is common; Moderate has a larger conditional error burden than Low in several models. See per-class recall for prevalence-independent interpretation.

{regional_table}
High is mainly confused with Moderate for the frozen LR/RF/NDCI: LR has 15,114 High→Moderate versus 1,667 High→Low; RF has 34,649 versus 3,096. Pooled RF predicts just 33 High pixels versus 37,768 true High pixels; each modified RF predicts one High pixel, and it is false. LR predicts 34,568 High pixels, below support, but still misses 16,781 High pixels while introducing 13,581 false High predictions. The diagnostic CNN predicts 74,414 High pixels: overprediction and substantial misses coexist. Underprediction is not universal—SmallSegCNN predicts High almost everywhere.

LR/RF pixel prediction agreement is {float(similarity['prediction_agreement']):.4f}; wrong-pixel Jaccard is {float(similarity['error_jaccard']):.4f}, and High-miss Jaccard is {float(similarity['high_miss_jaccard']):.4f}. Shared confusion with Moderate does not mean equal geographic behavior. All pairwise comparisons are in {artifact('error_similarity.csv')}.

{artifact('regional_failure_metrics.csv')} contains TP/FP/FN, precision/recall/F1, class support, predicted counts, true/predicted proportions and Macro F1 for all 20 models × 3 regions × 3 classes. {artifact('results.json')} stores every confusion matrix. [All-model confusion figures](../phase4/plots/all_confusion_matrices.png).

{limitations}
''')
    # Controlled experiments.
    exp_table=table(['Experiment','Validation Macro F1','Test Macro F1','High P','High R','High F1','Moderate F1','Low F1'],[[i,macro(r['validation']),macro(r['test']),*[r['test']['per_class'][2][k] for k in ['precision','recall','f1']],r['test']['per_class'][1]['f1'],r['test']['per_class'][0]['f1']] for i,r in results.items() if specs[i]['family'] not in ['NDCI','NDVI','FAI','B8AB4','B3B2'] and specs[i]['variant']!='band_ablation'])
    audit=read('sampling_audit.json')
    report('CLASS_IMBALANCE_EXPERIMENTS.md',f'''# Controlled class-imbalance experiments

Eight new imbalance experiment IDs were registered. Four original learned baselines remain unchanged. Weighted fits and sampling fits are separate; focal has gamma=2 without class weights. CNN architecture, epochs, seed, augmentation, optimizer and checkpoint rule are unchanged. The source of class counts differs appropriately: classical weights use the exact sampled training labels; CNN weights use all valid training-mask labels.

{exp_table}
Classical sampled counts: {audit['original_counts']}. Inverse-frequency weights: {audit['weight_vector']}. Balanced draws: {audit['balanced_counts']}; effective unique counts: {audit['balanced_unique_counts']}. All 8,180 High draws repeat only 56 unique sampled pixels. Rebalancing does not create geographic or biological diversity. CNN counts are [205627,61588,647], with weights N/(3*n_c).

Weighted/balanced LR sacrifices some overall and High F1 relative to the original LR on Test. Neither weighted nor balanced RF detects a true High pixel. Weighted DeepLab improves Test Macro F1 from 0.3627 to 0.4407 and High F1 from 0.2700 to 0.3522, but validation Moderate F1 remains 0.1895, below the fixed 0.25 guard. Focal loss does not establish a useful improvement in this budget. SmallSegCNN remains collapsed. A high High recall alone is not useful.

Within-run checkpoint selection remains minimum unweighted validation CE, so changing loss is the only neural intervention. Across-run choice is by validation Macro F1 with the registered guard. All ablations preserve the chosen parent's weighted loss. No architecture/loss combination was added based on Test.

{artifact('experiment_metrics.csv')} includes full validation and Test metrics. Model training JSON files record completed epochs, selected epochs, class weights and warnings. This is one seed and a short budget; differences are descriptive, with no significance claim.
''')
    # LR/RF.
    coeff=rows('feature_importance_coefficients.csv');topcoef=sorted(coeff,key=lambda r:abs(float(r['high_minus_moderate_coefficient'])),reverse=True)[:6];toprf=sorted(coeff,key=lambda r:float(r['rf_impurity_importance']),reverse=True)[:6]
    train_table=table(['Model','Pool','High support','High recall','High F1','Mean P(High) on true High'],[[k,p,v['metrics']['per_class'][2]['support'],v['metrics']['per_class'][2]['recall'],v['metrics']['per_class'][2]['f1'],v['true_high_mean_probability']] for k,d in train.items() for p,v in d.items()])
    report('LR_VS_RF_ANALYSIS.md',f'''# Why LR and RF differ on High

The discrepancy reproduces from the frozen checkpoints and identical 24,540 sampled training pixels: 18,260 Low, 6,224 Moderate, only 56 High (0.2282%). Both original models have class_weight=None. Both use the same 22 features (12 reflectance bands, five verified indices, five missing-index indicators). LR standardizes features using the training sample; RF uses raw feature scales, which is appropriate for tree splits. There is no evidence that a bad RF implementation explains the result.

{train_table}
A critical caution: LR recalls **none of the 56 sampled training High pixels**, yet recalls 55.57% of High Test pixels. RF recalls 41.07% on those training pixels but only 0.0609% on geographic Test. Training resubstitution is not validation. LR's better Test score therefore cannot be described as robustly learned High discrimination across pools: shifted feature/label composition can put more Test pixels on the High side of its fitted global decision surface. This is a plausible mechanism, not a causal identification or evidence of leakage; the frozen split/data hashes and exact shared training sample were checked.

## Probability and ranking evidence

True High Test pixels have mean P(High)=0.5483 under LR versus 0.0566 under RF; medians are 0.6739 versus 0.0324. RF's High ROC AUC=0.7978 and AP=0.2801 show nonzero ranking information even while the argmax almost never selects High. LR High AUC=0.9022 and AP=0.5233 are higher on this selected Test pool. No Test threshold was fitted. ROC/PR are one-v-rest and AP depends on the enriched prevalence.

[Probability histograms](../phase4/plots/lr_rf_high_probability_histograms.png), [per-class ROC/PR](../phase4/plots/lr_rf_roc_pr.png), [confusion matrices](../phase4/plots/all_confusion_matrices.png), {artifact('lr_rf_probability_summary.csv')}, {artifact('lr_rf_roc_pr_metrics.csv')}.

## Tree depth, leaves and minority representation

All 64 trees reach the fixed depth cap12; min_samples_leaf=2, max_features=sqrt. Across {diag['total_leaves']:,} leaves, only {diag['total_high_majority_leaves']} ({diag['total_high_majority_leaves']/diag['total_leaves']:.2%}) have High as the majority class. Per-tree bootstrap High counts range {diag['bootstrap_high_count_range'][0]}–{diag['bootstrap_high_count_range'][1]}; the minority is present, not silently dropped. Leaf files record original High occupancy, in-bag unique sample counts, bootstrap-weighted counts and all three class fractions. Sparse minority leaves, depth-limited partitions, local support and averaging are consistent with RF's low High probabilities under shift, but this analysis does not isolate their individual causal contributions. Weighted/sampled RF still has zero High Test recall, so “class imbalance alone” is not an established explanation.

{artifact('rf_tree_diagnostics.csv')}; {artifact('rf_leaf_composition.csv')}.

## Feature interpretation

Largest absolute LR High-minus-Moderate standardized logit coefficients:

{table(['Feature','Coefficient per training SD'],[[r['feature'],float(r['high_minus_moderate_coefficient'])] for r in topcoef])}
Largest RF impurity importances:

{table(['Feature','Impurity importance'],[[r['feature'],float(r['rf_impurity_importance'])] for r in toprf])}
LR coefficients are in standardized feature units; High-minus-Moderate is a pairwise log-odds contrast, not a causal effect. Correlated bands/derived indices can redistribute coefficients. RF impurity importance has split-opportunity and correlation biases and is not on the same numerical scale as LR coefficients. Do not rank models by coefficient magnitude.

[High versus Moderate training distributions](../phase4/plots/high_moderate_feature_distributions.png); [feature effects](../phase4/plots/lr_rf_feature_effects.png); {artifact('feature_importance_coefficients.csv')}; {artifact('training_feature_distributions.csv')}; {artifact('class_conditional_spectral_shift.csv')}.

The supported explanation is a combination of very sparse minority support, differing decision geometry and geographic/class-conditional distribution changes. The experiment does not prove one cause, and the LR Test advantage is not a validation-selected deployment result.
''')
    # Shifts.
    shift_table=table(['Region','Mean absolute 12-band SMD','LR High F1','CNN High F1'],[[short(g),shift['mean_absolute_band_smd'][g],high(results[lr]['test_groups'][g]),high(results[cnn]['test_groups'][g])] for g in gs])
    report('REGIONAL_DISTRIBUTION_SHIFT.md',f'''# Regional spectral distribution shift

{shift_table}
**No: the region with the largest aggregate spectral shift does not have the worst High performance.** 7_5_X1800_Y1700 has the largest mean absolute band SMD (0.4101), yet LR and the diagnostic CNN have their highest regional High F1 there. 6_2_X0650_Y0900 has the smallest shift (0.1665), but their lowest High F1. The three-region Spearman rank association is +1 for these two models; with n=3 this is only a description, not evidence of a general positive relationship or a causal mechanism.

For all 12 bands and all five previously verified indices (NDCI, NDVI, FAI, B8AB4, B3B2), every finite valid-reference pixel contributes to mean, median, SD and 5/25/75/95 percentiles. Undefined indices are counted and excluded feature-wise. Reflectance is the author's DN/10000 transform. SMD=(region mean−Train mean)/Train SD; Wasserstein distance is also divided by Train SD. This training-SD convention is explicit, not a pooled-SD effect size. No distributional p-values or additional divergence searches are used. Train is the frozen two-component training pool.

Pooled spectral changes mix class prevalence and within-class changes. {artifact('class_conditional_spectral_shift.csv')} provides matching per-class comparisons; the train High class has only 647 pixels and these are spatially correlated. Low aggregate shift can hide localized/class-specific shift, and high pooled shift can reflect the intentional High enrichment. Geography, date and class prevalence are confounded here.

{artifact('spectral_summaries.csv')}; {artifact('spectral_shift.csv')}; {artifact('shift_association.json')}; [shift heatmap](../phase4/plots/spectral_shift.png).

{limitations}
''')
    temporal_table=table(['Region','Unique dates','Months represented','2019 patches','2020 patches','Patch-month TV vs Train','LR High F1'],[[short(g),temporal[g]['unique_dates'],temporal[g]['months_observed'],temporal[g]['years']['2019'],temporal[g]['years']['2020'],temporal[g]['patch_month_total_variation'],high(results[lr]['test_groups'][g])] for g in gs])
    report('TEMPORAL_SHIFT_ANALYSIS.md',f'''# Temporal composition and reliability

{temporal_table}
The worst LR/CNN High-F1 region, 6_2_X0650_Y0900, also has the largest patch-month distribution difference from Train (total variation0.6146). That alignment is descriptive. It does not establish that seasonality caused the failure: only three regions exist and date, location, High prevalence and selection mechanism change together.

{artifact('temporal_distributions.csv')} reports month, year and DJF/MAM/JJA/SON calendar bins with both patch weighting and unique-date weighting, including zero-count months. Unique dates are not independent bloom events; multiple spatial patches on the same date must not be treated as independent acquisitions. All pools cover only2019–2020; no future-year generalization was evaluated. Regional coverage ranges14–27 dates across6–10 months, with empty seasons/months and High-enriched anchor selection. Seasonal bins are descriptive calendar bins, not a inferred ecological season model.

{artifact('temporal_shift.json')}; [month composition](../phase4/plots/temporal_shift.png). Sparse coverage prevents strong temporal attribution or season-specific operating claims.
''')
    # Calibration.
    caltable=table(['Model','ECE','NLL','Brier','High ECE','High predictions ≥0.8','Precision of those High predictions'],[[i,*[d['raw']['overall'][k] for k in ['ece','nll','brier','high_ece','high_confidence_predictions','high_confidence_precision']]] for i,d in cal.items()])
    ttable=table(['Neural model','Validation-fitted T','ECE before','ECE after','NLL before','NLL after','Brier before','Brier after'],[[i,t['temperature'],*[cal[i][mode]['overall'][metric] for metric in ['ece','nll','brier'] for mode in ['raw','temperature']]] for i,t in temps.items()])
    matchtable=table(['Pilot model','Random ECE','Geographic ECE','Random NLL','Geographic NLL'],[[i,*[matched[s][i]['calibration'][m] for m in ['ece','nll'] for s in ['random','geographic']]] for i in matched['random']])
    report('CALIBRATION_ANALYSIS.md',f'''# Confidence reliability and validation-only temperature scaling

**Model confidence is not generally trustworthy under this geographic shift.** LR's pooled High predictions with confidence>=0.8 are correct only60.96% of the time (27,846 predictions); in 6_2_X0650_Y0900 they are correct46.55% of the time (449 predictions). The diagnostic CNN makes510 such High predictions and none is correct. These are correlated pixel counts, not510 independent failure events. RF makes no High predictions at that confidence: N/A precision is not zero or perfect calibration.

## Uncalibrated geographic Test

{caltable}
Top-label ECE uses15 equal-width bins of maximum probability and correctness. High ECE uses P(High) against the one-v-rest binary label on all valid pixels. Multiclass Brier is the mean sum of3 squared probability errors (range0–2); High Brier is binary. Multiclass and binary High NLL use log probabilities clipped at1e-12. Confidence quantiles, bin populations and all corresponding region-specific metrics are in {artifact('calibration.json')} and {artifact('calibration_metrics.csv')}. Every probabilistic model has an overall +3region reliability figure, for both top-label and High. Five thresholded spectral indices have no learned probabilities; calibration is N/A.

Pooled ECE can conceal class failure: RF has lower top-label ECE than LR while missing nearly all High pixels. ECE binning, prevalence and pooling matter; ECE alone is not a reliability score. High one-v-rest metrics are also dominated numerically by non-High pixels, so inspect High-prediction precision and support alongside them.

## Neural temperature scaling

{ttable}
A positive scalar T minimizes validation NLL only, bounded[0.05,20]. Temperatures and their validation objectives were frozen before new Test evaluation. All9 neural checkpoints including ablations were calibrated; all18 validation/Test argmax comparisons remain exactly unchanged, hence accuracy and every confusion matrix are unchanged. SmallSegCNN variants reach the upper bound20, reflecting near-uniformization of a poor classifier; the bound is disclosed rather than expanded after Test inspection.

For the diagnostic CNN, T=1.0638 lowers Test NLL1.1237→1.1124 but increases ECE0.1131→0.1231 and Brier0.5536→0.5572. Temperature scaling is not a guaranteed simultaneous improvement under shift. The original DeepLab lowers pooled ECE but worsens NLL; pooled changes can also differ by region. Calibration does not repair discrimination, geography or missing minority support.

[Temperature-scaling method: Guo et al.2017](https://proceedings.mlr.press/v70/guo17a.html). {artifact('temperatures.json')}; [diagnostic CNN reliability diagrams](../phase4/plots/calibration_deep_weighted.png); [LR reliability diagrams](../phase4/plots/calibration_baseline_LogisticRegression.png).

## Fair random-versus-geographic comparison

{matchtable}
Only these reloaded original models share the same272-pair pilot pool and original protocol. Both pilot Test partitions have zero High support, so High sensitivity/calibration claims cannot be evaluated there (binary High false-positive scoring still exists). {artifact('matched_pilot_calibration.json')} preserves exact pilot confusion reproduction. Do not compare pilot Random Test directly to v2 Geographic Test: data pool, training data and class support differ.
''')
    # Robustness.
    rtable=table(['Transform','Severity','Macro F1','ΔMacro F1','High F1','ΔHigh F1','Values clipped fraction'],[[r['kind'],r['level'],*[float(r[k]) for k in ['perturbed_macro_f1','delta_macro_f1','perturbed_high_f1','delta_high_f1','fraction_values_clipped']]] for r in rob])
    report('ROBUSTNESS_ANALYSIS.md',f'''# Controlled multispectral robustness

The registered diagnostic CNN is `{cnn}`; it failed the validation Moderate guard. Original Test Macro F1={macro(base):.4f}; High F1={high(base):.4f}. All12 severity settings were registered before Test evaluation.

{rtable}
Brightness/contrast use common gain1.05/1.15 across bands. Contrast is about each band's image mean. Noise is one shared spatial Gaussian field across bands (reflectance sigma0.002/0.005), deliberately a correlated perturbation rather than an asserted MSI sensor-noise model. Blur uses the same spatial Gaussian kernel per band, sigma0.5/1pixel; resolution is64→48/32→64 with antialiased bilinear interpolation. Center masks are14×14 and25×25 pixels (4.79%/15.26% area), filled with training band means. This masking is **obstruction artifact stress**, not a physical cloud or radiative-transfer simulation. Labels and valid-pixel eligibility remain unchanged, including occluded reference pixels.

Transforms operate on all12 reflectance bands before fixed Train normalization, with shared parameters and fixed per-sample seeds. Outputs clip to[0,1.5]; clipping is part of the intervention. Contrast-moderate clips5.96% of channel values and noise-moderate4.75%, so those results combine the nominal perturbation and nonnegativity clipping; they must not be called pure gain/noise effects. Even the mild settings are synthetic approximations. No band-independent RGB augmentation was used. Zero/ignored-context pixels can change and influence model context, while only valid reference pixels are scored.

Worst pooled Macro F1 decrease is−0.0064 (contrast-moderate); worst High F1 decrease is−0.0278 (brightness-moderate). Blur can improve the score in this short-budget model. A small perturbation delta does not demonstrate reliability when baseline three-class performance is weak; it can reflect persistent errors. Regional changes can cancel when pooled. {artifact('robustness_by_region.csv')} exposes those differences.

{artifact('robustness_metrics.csv')}; [robustness figure](../phase4/plots/robustness.png). No confidence interval or real-cloud generalization claim is warranted.
''')
    # Bands.
    bandrows=[]
    for i,label in [(cnn,'All12'),('ablation_rgb','RGB'),('ablation_visible_rededge_nir','Visible + red-edge/NIR'),('ablation_compact_hab','Compact HAB ingredients')]:
        r=results[i];bandrows.append([label,macro(r['validation']),macro(r['test']),high(r['test']),macro(r['test'])-macro(base),min(high(v) for v in r['test_groups'].values())])
    bandtable=table(['Band set','Validation Macro F1','Test Macro F1','Test High F1','ΔTest Macro vs All12','Worst-region High F1'],bandrows)
    report('BAND_ABLATION.md',f'''# Registered band ablation

{bandtable}
All12 versus RGB improves Test Macro F1 by{macro(base)-macro(results['ablation_rgb']['test']):.4f} and High F1 by{high(base)-high(results['ablation_rgb']['test']):.4f} in this one fixed run. The8-band visible/red-edge/NIR variant has higher Macro F1 than All12 but lower High F1. The compact4-band variant does not establish parity. These descriptive differences suggest spectral information beyond RGB can help in this protocol; they do not prove a stable multispectral advantage or an optimal band set. Validation ordering differs, all runs are short and single-seed, and no ablation replaces the previously locked winner.

| Set | Verified array bands |
| --- | --- |
| All12 | B01,B02,B03,B04,B05,B06,B07,B08,B8A,B09,B11,B12 |
| RGB | B02,B03,B04 (display order B04/B03/B02) |
| Visible + red-edge/NIR | B02,B03,B04,B05,B06,B07,B08,B8A |
| Compact HAB ingredients | B04,B05,B8A,B11 |

The compact set supplies the previously verified NDCI red/red-edge ingredients and FAI red/narrow-NIR/SWIR ingredients. It is literature-informed, not a claim that this exact subset is a published optimum. Band mapping was checked against the pinned author data pipeline and [Copernicus MSI band documentation](https://sentiwiki.copernicus.eu/web/s2-mission). Prior project equations are from [Schloer and Hänsch,2025](https://doi.org/10.1109/JSTARS.2025.3629586). Nominal wavelengths used for FAI are approximations, not spacecraft-specific response integration.

All runs use DeepLabV3/ResNet18, weighted CE, same seed42, batch8, Adam and2epochs, no pretrained weights, same split and train-only normalization. They retain the12-channel architecture and mask inactive normalized channels to0 during training, validation and inference: this is train-mean imputation, not literal zero reflectance. Consequently the experiment controls architecture/parameter count while changing available information; it does not measure parameter efficiency of a native3-channel CNN. The All12 result reuses the parent checkpoint without retraining.

{artifact('experiment_metrics.csv')}; {artifact('specifications.json')}; validation epoch histories under`../phase4/models/ablation_*_training.json`. No exhaustive band search or Test-based subset tuning occurred.
''')
    # Explainability/error examples.
    examples=read('error_examples.json');missing=[short(v['region'])+': '+v['category'] for v in examples['records'] if v['selected'] is None]
    igtable=table(['Region','Target High pixels','32-step relative residual','64-step relative residual','Attribution L1 change32→64'],[[short(v['region']),v['target_pixels'],v['steps32']['relative_residual'],v['steps64']['relative_residual'],v['relative_l1_change_32_to_64']] for v in ig['records']])
    report('EXPLAINABILITY_ANALYSIS.md',f'''# Segmentation attribution and deterministic error examples

The single primary method is integrated gradients of the **mean High logit over a fixed valid true-High pixel region**. This scalar is obtained from the segmentation output directly; it is not an image-classification Grad-CAM target. Per region, choose the patch with maximum true-High pixel support, tie by ascending sample_id. Fix the target mask throughout the integration path. Baseline is normalized zero (training per-band means); integrate from it to the observed12-band patch using trapezoidal32 and64 steps in eval mode. Report the64-step attribution, both completeness checks and their L1 change.

{igtable}
The64-step completeness residual is1.75%,9.49%,2.49% of the target-logit change, respectively. The6_2_X0650 case is numerically less reliable (9.49%, improved from23.28% at32steps); the7_5 case also changes11.46% in attribution L1 between resolutions. These are approximate exploratory maps, not fully converged quantitative band rankings. Small logit changes and cancellation make relative residuals sensitive; absolute residuals and target changes are saved.

The maps measure model-output sensitivity along a particular baseline-to-image path. Attribution can occur outside the target mask or on ignored context because the CNN uses a spatial receptive field. Absolute band attribution aggregates both positive and negative effects and is not directly a causal importance estimate. Correlated bands, standardized coordinates and an artificial mean-spectrum baseline influence the result; the interpolation path need not represent physically realizable water. B05 is prominent in two examples and B03 in the third, consistent with sensitivity to visible/red-edge inputs, but this does not prove cyanobacteria-specific reasoning or explain geographic failure causally. No claim of toxin or concentration reasoning is made.

[Integrated-gradients method: Sundararajan et al.2017](https://proceedings.mlr.press/v70/sundararajan17a.html). {artifact('integrated_gradients.json')} and per-region`ig_*.npz` retain signed per-band maps and target masks.

## Deterministic error panels

For each region and each of7 categories—correct Low, correct Moderate, correct High, High→Moderate, High→Low, false High, and error at confidence>=0.8—select the patch with highest mean confidence over qualifying pixels, tie by sample_id. This intentionally selects extreme diagnostic examples and is not a representative sample of frequency. “Correct Low example” means qualifying Low pixels exist, not that its whole patch is correct. The same patch may appear in multiple categories. All valid-region pixels remain visible in the panels. RGB uses the fixed B04/B03/B02 stretch0–0.2 reflectance and gamma1/2.2; display scaling does not enter model inference.

Missing categories: {('; '.join(missing)) if missing else 'none; all21 region/category combinations have qualifying pixels'}.

Each row displays RGB, reference classes, prediction, error and uncalibrated confidence, with qualifying count and confidence. {artifact('error_examples.json')} records sample IDs, scores and categories, enabling exact reproduction.

'''+ '\n'.join(f'- [{short(g)} error panel](../phase4/plots/errors_{short(g)}.png); [IG panel](../phase4/plots/ig_{short(g)}.png)' for g in gs))
    # Uncertainty and final assessment.
    loo=rows('leave_one_region_out.csv');uncertainty=table(['Model','Regional High F1 min','Regional High F1 max','LOO pooled High F1 min','LOO pooled High F1 max'],[[i,min(high(v) for v in results[i]['test_groups'].values()),max(high(v) for v in results[i]['test_groups'].values()),min(float(r['high_f1']) for r in loo if r['experiment_id']==i),max(float(r['high_f1']) for r in loo if r['experiment_id']==i)] for i in [overall,lr,rf,cnn]])
    final=f'''# Final reliability assessment

**Final scientific claim: LIMITED evidence for reliable three-class geographic generalization.**

**Ability:** Sentinel-2 multispectral features contain useful predictive information about the released CyAN-derived classes in this selected sample. The unchanged LR reaches Test Macro F1=0.6983 and High F1=0.5803, with High F1=0.4006–0.5964 across the three regions. All12 outperforms RGB in the controlled diagnostic CNN run. These are evidence of association and partial discrimination, not a direct field validation of bloom risk, toxicity or cell concentration.

**Reliability:** The prospective selection rule chooses NDCI, whose High F1 is0 on Validation and0.0006 on Test; it fails High in two held-out regions. No CNN passes both validation class guards. LR's apparent Test advantage was already known and does not justify selecting it after viewing Test; it also misses all sampled training High pixels and all validation High pixels. Its high-confidence High precision varies sharply by region. RF misses almost all High and weighting/sampling does not fix it. The diagnostic CNN has510 high-confidence High false positives and no true positives at that threshold. These results do not support dependable geographic three-class risk decisions.

{select_text}

## Geographic uncertainty

{uncertainty}
These are observed geographic ranges and leave-one-region-out sensitivity, **not confidence intervals**. Each leave-one-out estimate sums confusion counts over the other2whole regions before scoring; no individual-pixel bootstrap is used. Only3selected connected components cannot supply a reliable population-level interval. 7_5_X1800_Y1700 contributes27,850 of37,768 High Test pixels (73.74%); pooled metrics are heavily influenced by that region. Report all3regions rather than attaching pseudo-precise confidence to428,659 correlated pixels.

{artifact('leave_one_region_out.csv')}; [central reliability matrix](MODEL_RELIABILITY_MATRIX.md).

## What Phase4 resolves

The LR/RF difference is reproducible, the minority class is not missing from RF trees, and reweighting is insufficient. Larger aggregate spectral shift does not identify the worst High region. Temporal composition is also shifted, but the three-region evidence cannot identify causation. Temperature scaling can improve one calibration metric and worsen another without changing any classification. Mild synthetic perturbation stability coexists with poor baseline reliability. Integrated gradients supplies approximate exploratory model sensitivity, not causal explanation.

## Limitations and Phase5

{limitations}

Phase5 should prioritize additional independently held-out geographic components and independent validation regions with substantial, diverse High support; preserve v2 as an already-used benchmark and create a new external holdout before further optimization. Recover lake/scene/footprint metadata and validate temporal/event independence. Establish longer, train/validation-only convergence schedules and repeated seeds within a fixed budget, then reassess imbalance and band effects on the new holdout. Validate against independent in-situ biological/toxin measurements before any operational risk interpretation. Predefine per-class and worst-region operating requirements and calibration/abstention evaluation using validation data. Do not build a frontend or present these models as deployment-ready.
'''
    report('FINAL_RELIABILITY_ASSESSMENT.md',final)
    maxround=max(v['max_absolute_difference'] for v in repro['rf_probability_roundoff'])
    report('PHASE_4_REPRODUCTION.md',f'''# Phase4 reproducibility

{testcount} tests pass, including all103 pre-existing tests unchanged and20 new tests covering class weighting, focal loss, calibration, temperature, all6 perturbation families, band mapping, failure metrics, deterministic selection, integration completeness, registration and preservation. The real-data integration tests additionally validate selection and regional sums. {artifact('pytest_results.xml')}.

All20 model specifications were reloaded for validation and Test. {repro['exact_confusion_matrices']} confusion matrices and{repro['exact_class_prediction_caches']} class-prediction caches reproduce exactly. All9 validation temperature fits reproduce and18 validation/Test argmax checks remain unchanged. RF probability sums vary by at most{maxround:.3g} under the unchanged parallel n_jobs=2 setting; probability tolerance is1e-12 absolute,0relative. This floating-point summation issue does not change any predicted class or matrix. The initial failed bitwise RF probability check and correction are disclosed in {artifact('IMPLEMENTATION_NOTES.md')}.

{preserve['checked']} prior files remain SHA-256-identical, including all Phase3.5 reports, splits, metrics, checkpoints/configurations and the original pilot artifacts. Phase4 has new directories/IDs and does not overwrite them. No WaterSense-AI files were changed. Registration/config/protocol hashes, validation-selection-before-Test timestamp order, specification and temperature hashes are verified. {artifact('preservation_check.json')}; {artifact('reproduction_check.json')}.

Run from the AquaVision-AI root with the existing pinned `.venv`:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_phase4.py
.venv/bin/python scripts/analyze_phase4.py
.venv/bin/python scripts/diagnose_phase4_training.py
.venv/bin/python scripts/report_phase4.py
```

The analysis scripts reuse immutable checkpoints. `scripts/run_phase4.py` intentionally refuses to run when selection.json already exists. To reproduce fitting, use a separate scratch clone/workspace containing the frozen input manifests and model baselines, with a new empty Phase4 output directory; never delete/overwrite the delivered evidence. Registration is in`data/metadata/phase4/preregistration.json`; exact source snapshots are hashed in run_contract.json and the final delivery manifest. IDs/seeds/protocol and normalization are saved with each checkpoint. Data hashes are verified before fitting. No new imagery was downloaded in Phase4.

The final delivery manifest inventories Phase4 code, configs, metadata, reports and output artifacts with byte sizes/SHA-256. Probabilistic inputs/logits and class maps are cached for independent metric recomputation. Reproduction means these local pinned versions and data; bitwise results on different numerical libraries/hardware are not promised.
''')
    report('PHASE_4_STATUS.md',f'''# Executive conclusion

**Phase4 complete. Final scientific claim: LIMITED evidence for reliable three-class geographic generalization.** The project demonstrates partial predictive ability on CyAN-derived reference classes, but validation selection, minority behavior and confidence reliability do not support dependable unseen-region operation. 11 new model fits were evaluated: 8 imbalance variants and3 band ablations, alongside 9 frozen baselines. No frontend was built.

# Best validation-selected model

{select_text}

[Registered selection protocol](MODEL_SELECTION_PROTOCOL.md). The original LR has the highest observed Test Macro F1, but it is not the validation-selected winner.

# Geographic generalization

{selected_regions}

The validation-selected NDCI has Test Macro F1=0.5185, High F1=0.0006. The original LR has0.6983/0.5803. The diagnostic weighted DeepLab has0.4407/0.3522. [Model reliability matrix](MODEL_RELIABILITY_MATRIX.md) separates the old matched random/geographic pilot from v2; v2 has no matched Random result.

# High-risk performance

37,768 High Test pixels are present, so failure is now measurable. RF predicts High only33times (23correct); weighted and balanced RF each predict one false High pixel and detect no true High pixels. LR detects20,987 High pixels while missing16,781. The selected NDCI misses37,756. High recall by itself is insufficient: SmallSegCNN's near-universal High output has very poor precision.

# Regional variability

The hardest region depends on model and metric. LR High F1 spans0.4006–0.5964; diagnostic CNN spans0.1616–0.4546. One region contributes73.74% of High Test support. [Regional failure analysis](REGIONAL_FAILURE_ANALYSIS.md) and machine-readable TP/FP/FN/proportions cover every20model×3region×3class combination.

# Class-imbalance experiments

Same-pixel LR/RF weighted fits, same-pool balanced sampling, and loss-only weighted/focal CNN variants are complete. Repeated sampling reuses 56 unique High training pixels. RF High failure persists; weighted DeepLab improves but does not pass the validation guard. [Full controlled comparison](CLASS_IMBALANCE_EXPERIMENTS.md).

# Distribution shift

The region with the largest average12-band shift has the best LR/CNN High F1; the worst High region has the smallest spectral mean shift and largest monthly composition difference. Neither observation establishes causation with3regions. [Spectral analysis](REGIONAL_DISTRIBUTION_SHIFT.md); [temporal analysis](TEMPORAL_SHIFT_ANALYSIS.md).

# Calibration

LR High predictions at confidence>=0.8 are correct60.96% pooled and46.55% in its worst High region. The diagnostic CNN's 510 high-confidence High predictions are all false. Validation-only temperature scaling preserves every argmax; for that CNN NLL improves while ECE and Brier worsen. [Calibration analysis](CALIBRATION_ANALYSIS.md).

# Robustness

12 registered multispectral perturbations were evaluated. Worst pooled Macro decrease −0.0064; worst High-F1 decrease −0.0278. Low baseline reliability prevents a robustness claim from these small deltas. Clipping and synthetic-mask limitations are explicit. [Robustness analysis](ROBUSTNESS_ANALYSIS.md).

# Multispectral ablation

All12 versus RGB increases Test Macro F1 by{macro(base)-macro(results['ablation_rgb']['test']):.4f} and High F1 by{high(base)-high(results['ablation_rgb']['test']):.4f}. The8-band visible/red-edge/NIR model has higher Macro but lower High F1 than All12. This single-seed short-budget experiment is suggestive, not a stable superiority claim. [Band ablation](BAND_ABLATION.md).

# Explainability

21 deterministic region/category examples show RGB/reference/prediction/error/confidence. Segmentation-targeted integrated gradients covers one fixed High mask per region; numerical residuals and baseline limitations are disclosed. It is sensitivity analysis, not causal proof. [Explainability and error panels](EXPLAINABILITY_ANALYSIS.md).

# Statistical uncertainty

{uncertainty}

Observed ranges and leave-one-region-out sensitivity are descriptive only. No pixel bootstrap or misleading population confidence interval was produced with only3selected geographic components.

# Tests

**{testcount} tests pass: all103 original tests plus20 new tests.** Original expected outputs were not changed. [Test results](../phase4/pytest_results.xml).

# Reproducibility

**100 confusion matrices and40 class-prediction caches reproduce exactly; 177 prior files remain unchanged.** Nine validation-fitted temperatures reproduce and18 argmax checks pass. Parallel RF probabilities differ only by up to{maxround:.3g}, explicitly logged without changing classes. [Reproduction report](PHASE_4_REPRODUCTION.md).

# Remaining limitations

{limitations} Validation is one region; labels, acquisition timing and selection enrichment can confound apparent geographic transfer. We do not claim independent biological episodes, toxin prediction, calibrated natural-population risk, or model convergence.

# Final scientific claim

**LIMITED.** Sentinel-2 contains predictive information for the released CyAN-derived classes, but current models and selection procedures do not establish reliable three-class discrimination across unseen geography. [Final research answer](FINAL_RELIABILITY_ASSESSMENT.md).

# Recommendation for Phase 5

Expand independent training/validation/held-out geography and real High events, recover source geospatial metadata, validate against independent biological references, and predefine convergence/multiple-seed studies and a new external Test set. Keep v2 frozen as an already-inspected benchmark. Defer deployment and frontend work.
''')
    write(OUT/'report_summary.json',{'claim':'LIMITED','best_validation_model':overall,'diagnostic_cnn':cnn,'cnn_eligible':selection['cnn_eligible'],'tests':testcount,'old_tests':103,'new_tests':testcount-103,'models':len(results),'new_fits':11,'exact_confusion_matrices':repro['exact_confusion_matrices'],'frozen_files_unchanged':preserve['checked']})
    print('Phase4 reports rendered.',flush=True)
if __name__=='__main__':main()
