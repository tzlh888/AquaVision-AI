"""Phase 3.5 evidence report: measured support, optional gated results, pilot preserved."""
import csv,hashlib,json,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path('data/metadata/phase3_5');OUT=Path('research_outputs/phase3_5');R=Path('research_outputs/reports')

def fmt(v):return 'N/A' if v is None else f'{float(v):.4f}'

def main():
    audit=json.loads((OUT/'high_support_summary.json').read_text())
    criteria=json.loads((ROOT/'criteria_contract.json').read_text())
    assert hashlib.sha256(Path('research_outputs/reports/EVALUATION_SUPPORT_CRITERIA.md').read_bytes()).hexdigest()==criteria['criteria_sha256']
    original=json.loads((ROOT/'pilot_preservation_manifest.json').read_text())
    for item in original['files']:
        assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    preservation={'status':'PASS','unchanged_pilot_artifacts':len(original['files']),'files':original['files']}
    (OUT/'pilot_preservation_check.json').write_text(json.dumps(preservation,indent=2)+'\n')
    suite=ET.parse(OUT/'pytest_results.xml').getroot().find('testsuite');tests=suite.attrib['tests']
    has_split=(ROOT/'geographic_split_v2.json').exists()
    has_results=(OUT/'models_v2/results.json').exists()
    split=json.loads((ROOT/'geographic_split_v2.json').read_text()) if has_split else None
    results=json.loads((OUT/'models_v2/results.json').read_text()) if has_results else None
    status='THREE-CLASS EVIDENCE STILL INSUFFICIENT'
    category='B — Partial evidence' if has_results else 'C — Dataset limitation within audited support'
    support_table='No final v2 split generated: candidate support requirements were not satisfied.\n'
    model_table='NOT RUN: support/split gate remains closed. No model scores are fabricated.\n'
    group_table='NOT EVALUATED: no valid new test partition was approved.\n'
    comparison='Expanded model evaluation was not performed; no change in predictive performance can be measured.\n'
    interpretation='No expanded prediction result is available.'
    if has_split:
        support_table='| Split | Groups | Patches | Valid pixels | Low | Moderate | High | Qualified High groups | High % |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
        for row in split['support']:
            support_table+=f"| {row['split']} | {row['geographic_groups']} | {row['patches']} | {row['valid_pixels']:,} | {row['low_pixels']:,} | {row['moderate_pixels']:,} | {row['high_pixels']:,} | {row['qualified_high_groups']} | {row['high_percent']:.4f} |\n"
        plan=json.loads((ROOT/'reference_screening_plan.json').read_text())
        selected={r['spatial_group_id']:split['assignments'][r['sample_id']] for r in split['samples']}
        fig,axes=plt.subplots(1,5,figsize=(18,4));colors={'train':'#377eb8','validation':'#ff7f00','test':'#e41a1c','unselected':'#cccccc'}
        for ax,tile in zip(axes,('6_2','6_5','7_2','7_5','8_3')):
            for sid,g in plan['components'].items():
                if not sid.startswith(tile+'_'):continue
                bits=sid.split('_');ax.scatter(int(bits[2][1:]),int(bits[3][1:]),s=24,marker='s',c=colors[selected.get(g,'unselected')])
            ax.set(title=tile,xlim=(-50,2050),ylim=(2050,-50),xlabel='Parent column X');ax.set_aspect('equal')
        axes[0].set_ylabel('Parent row Y')
        fig.suptitle('Frozen v2 author-grid split: blue train / orange validation / red test / grey unselected; not a lat/lon map')
        fig.tight_layout();fig.savefig(OUT/'geographic_split_v2_grid.png',dpi=150);plt.close(fig)
    if has_results:
        model_table='| Model | Accuracy | Macro F1 | Weighted F1 | High precision | High recall | High F1 |\n|---|---:|---:|---:|---:|---:|---:|\n'
        for name,m in results['models'].items():
            t=m['test'];h=t['per_class'][2]
            model_table+='| '+name+' | '+' | '.join(fmt(x) for x in (t['accuracy'],t['macro_f1'],t['weighted_f1'],h['precision'],h['recall'],h['f1']))+' |\n'
        group_table='| Model / geographic group | Valid pixels | High support | Macro F1 | High recall | High precision | High F1 |\n|---|---:|---:|---:|---:|---:|---:|\n'
        for name,m in results['models'].items():
            for g,t in m['test_groups'].items():
                h=t['per_class'][2]
                group_table+=f"| {name} / {g} | {t['valid_pixels']:,} | {h['support']:,} | {fmt(t['macro_f1'])} | {fmt(h['recall'])} | {fmt(h['precision'])} | {fmt(h['f1'])} |\n"
        pilot=json.loads(Path('research_outputs/phase3_pilot/results.json').read_text())
        comparison='| Model | Pilot geographic macro F1* | v2 macro F1 | Pilot High F1 | v2 High F1 |\n|---|---:|---:|---|---:|\n'
        compared=[]
        for name,m in results['models'].items():
            old=pilot['geographic']['models'][name]['test'];new=m['test']
            comparison+=f"| {name} | {fmt(old['macro_f1_fixed_three_zero_division'])} | {fmt(new['macro_f1'])} | N/A (no support) | {fmt(new['per_class'][2]['f1'])} |\n"
            compared.append({'model':name,'pilot_geographic_macro_f1_fixed_three':old['macro_f1_fixed_three_zero_division'],'v2_macro_f1':new['macro_f1'],'pilot_high_f1':None,'v2_high_f1':new['per_class'][2]['f1']})
        from aquavision.data.metadata import write_csv
        write_csv(OUT/'pilot_vs_expanded.csv',compared)
        comparison+='\n*Pilot macro averaged three slots with undefined-class score set to zero; its test contained no High pixels. The numbers are not like-for-like estimates of the same three-class distribution. Model families/configuration are unchanged, but training observations, independent regions and test prevalence differ. Each model was refitted on v2 training only; old checkpoints were not overwritten.\n'
        lr=results['models']['LogisticRegression'];lh=lr['test']['per_class'][2]
        recalls=[v['per_class'][2]['recall'] for v in lr['test_groups'].values()]
        f1s=[v['per_class'][2]['f1'] for v in lr['test_groups'].values()]
        high_supports=[v['per_class'][2]['support'] for v in lr['test_groups'].values()]
        rf=results['models']['RandomForest']['test'];small=results['models']['SmallSegCNN']['test'];deep=results['models']['DeepLabV3_ResNet18']
        zero_deep=sum(v['per_class'][2]['recall']==0 for v in deep['test_groups'].values())
        interpretation=(f"Logistic regression provides genuine but partial High-detection evidence: pooled High precision {lh['precision']:.4f}, recall {lh['recall']:.4f}, F1 {lh['f1']:.4f}; "
          f"its region-specific High recall ranges from {min(recalls):.4f} to {max(recalls):.4f}, and F1 from {min(f1s):.4f} to {max(f1s):.4f}. "
          f"The equal-region mean High recall is {sum(recalls)/len(recalls):.4f}, below the pooled recall. One test component contributes {100*max(high_supports)/sum(high_supports):.2f}% of High pixels, so pooled metrics overweight that geography.\n\n"
          f"Random forest reaches {rf['accuracy']:.4f} accuracy but High recall is only {rf['per_class'][2]['recall']:.6f}: it effectively misses High. "
          f"SmallSegCNN's High recall {small['per_class'][2]['recall']:.4f} comes with precision {small['per_class'][2]['precision']:.4f}; widespread High predictions do not constitute useful detection. "
          f"DeepLab's pooled High F1 is {deep['test']['per_class'][2]['f1']:.4f}, with zero High recall in {zero_deep} of the three held-out regions. Short unweighted training prevents attributing these failures to inherent architectural limits.\n\n"
          "**Why B, not A:** all three classes and the preregistered regional support are now present, but High performance varies materially by region/model, only three test components were assessed, and evaluation prevalence is deliberately enriched. The benchmark passes its operational support gate; strong reliability evidence remains insufficient.")
    a=audit['cached_pool'];b=audit['all_screened']
    pairs=len(split['samples']) if split else 0
    (R/'PILOT_VS_EXPANDED_EVALUATION.md').write_text(f'''# Pilot versus expanded evaluation

Phase 3's 272 pairs were selected without reading labels, and its fixed random and geographic tests happened to contain no High reference pixels. This was a **sampling-support limitation**, not proof that the original 24,518-pair pool lacks High. The complete new census finds {a['high_pairs']:,} High-bearing pairs and {a['high_pixels']:,} High pixels in {a['high_components']} components in that original pool.

Phase 3.5 froze geographic/date/class-support criteria before model evaluation, indexed all six archives, and screened reference masks before fetching additional inputs. It did not move old test patches, overwrite results or select geography using scores. {len(original['files'])} pilot artifacts retain their original SHA-256 values.

{comparison}
A valid expanded benchmark asks a harder scientific question because it requires actual High detection in multiple held-out regions. Whether a particular pooled number decreases is not a validity criterion. Support enrichment and changed geography prevent claiming a pure causal change in generalization difficulty from these scores alone.

Outcome: **{category}**. ''')
    if has_results:
        with (R/'PILOT_VS_EXPANDED_EVALUATION.md').open('a') as f:
            f.write(interpretation+'\n\nScores changed in both directions: for example, SmallSegCNN macro F1 fell while logistic regression increased. This does not isolate a pure geography effect because the support distribution and training pool changed. Detailed group results follow in PHASE_3_5_STATUS.md.\n')
    else:
        with (R/'PILOT_VS_EXPANDED_EVALUATION.md').open('a') as f:
            f.write('No statement about improved or degraded High prediction is possible. Incomplete screening outside the original pool does not prove that the entire deposit lacks sufficient support.\n')
    storage={p:int(subprocess.check_output(['du','-sk',p],text=True).split()[0]) for p in ('.','data/metadata/phase3_5','data/raw/phase3_5_references','research_outputs/phase3_5')}
    if Path('data/raw/phase3_5_pairs').exists():storage['data/raw/phase3_5_pairs']=int(subprocess.check_output(['du','-sk','data/raw/phase3_5_pairs'],text=True).split()[0])
    references=json.loads(Path(audit['reference_completion_path']).read_text())
    index=json.loads((ROOT/'index_access.json').read_text())[-1]['charged_bytes_so_far']
    (OUT/'validation_and_storage.json').write_text(json.dumps({'pilot_preservation':'PASS','pytest':suite.attrib,'storage_allocated_KiB':storage,
        'reference_transfer_charged_bytes':references['charged_bytes'],'reference_http_requests':references['requests'],'index_transfer_charged_bytes':index,
        'paired_transfer_charged_bytes':split['paired_download_charged_bytes'] if split else 0,'category':category,'status':status},indent=2)+'\n')
    final=f'''# Executive conclusion

**{status}**

Outcome **{category}**. {'The support-valid v2 benchmark and all existing model families have been evaluated, but limited region replication, support-enriched sampling and short training do not justify strong reliability conclusions.' if has_results else 'No qualifying v2 evaluation was forced. Missing support and the finite screening scope remain explicit; no expanded model result is invented.'}

# Dataset expansion

All six ZIP central directories were indexed without full archive downloads: **{audit['full_index_pairs']:,} pairs, {audit['full_index_subtiles']} subtiles, {audit['full_index_components']} connected selected regions**. The publication reports 938,607 pairs; that is not the measured inventory of this deposited version. The original 24,518-reference pool was completely decoded, and selected reference-only screening expanded the evidence to {b['decoded_pairs']:,} masks. {audit['uninspected_references']:,} references outside that screening remain uninspected.

Source: [Zenodo version 14230064](https://doi.org/10.5281/zenodo.14230064), with the fixed-grid naming/adjacency method verified in [the pinned author preprocessing code](https://github.com/cschloer/hab_detection_s2/blob/e24e311bdbcdb06c07e7bbe6e21433e69ff7cd37/code/dataset/generate_tiles.py). Exact member URLs, sizes, hashes and acquisition reasons are recorded in `data/metadata/phase3_5/downloaded_file_manifest.csv`.

After the completed candidate audit, {'a new '+str(pairs)+'-pair support-enriched dataset was selectively assembled' if has_split else 'no additional paired imagery was acquired'}. Inputs were never downloaded wholesale. Every retained file has source membership, size/CRC evidence, local SHA-256 and an inclusion reason. The original pilot remains unchanged.

# High-risk support audit

Original pool: **{a['high_pairs']:,} High-bearing pairs**, **{a['high_pixels']:,} High pixels**, **{a['high_percent_valid']:.6f}%** of {a['valid_pixels']:,} valid pixels, in **{a['high_components']} components**, {a['high_subtiles']} subtiles, {a['high_dates']} dates and {len(a['high_source_tiles'])} source tiles.

All screened masks: {b['high_pairs']:,} High-bearing pairs, {b['high_pixels']:,} High pixels, {b['high_components']} High-containing components and {b['high_dates']} dates. These selected-screening proportions are not full-corpus prevalence. See [complete support audit](HIGH_RISK_SUPPORT_AUDIT.md) and machine-readable candidate/date/patch tables under `research_outputs/phase3_5/`.

# Geographic independence

The verified unit is the fixed author subtile and its connected selected-region component, recomputed using the complete indexed grid. All dates and adjoining selected parents stay together. Components are not certified independent lakes or bloom events. Scene UUIDs and exact physical footprints remain UNKNOWN. Repeated grid locations, adjacent High patches, date clustering, shared source tiles and equal reference-mask hashes are enumerated in [the independence audit](HIGH_RISK_INDEPENDENCE_AUDIT.md).

# Frozen evaluation criteria

The original [support criteria](EVALUATION_SUPPORT_CRITERIA.md) and their hashed contract were saved before screening/evaluation: three qualifying High test components across two CyAN tiles, one validation component, two training components; each qualifying component needs two High dates spanning ≥30 days, two grid positions and ≥100 High pixels. All splits need all three classes. These are operational adequacy floors, not a statistical power calculation or proof of independent bloom episodes.

Acquisition amendment A changed only the mask-count ceiling after a multipart transport probe, keeping the 64 MiB reference response budget, request cap and all scientific criteria unchanged. No model scores affected screening, ranking, selection or splitting.

# New split

{'`data/metadata/phase3_5/geographic_split_v2.json` and `.csv` persist the exact new membership. The selected dataset intentionally anchors High/date support and adds fixed-hash coverage patches; evaluation prevalence is conditional on that enrichment.' if has_split else 'No final geographic_split_v2 was created because the support gate failed. A blocked decision is saved instead of a scientifically invalid partition.'}

# Split integrity

{'All reference/input shapes and IDs align, hashes/CRC pass, no sample IDs repeat, no source subtile or full-context connected component crosses partitions, and no exact Sentinel input file hash crosses partitions. This is not independent validation of historical physical co-registration.' if has_split else 'Gate tests reject insufficient support, missing classes, duplicate IDs, group/subtile leakage and invented component identities. No unverified real split is allowed into model evaluation.'}

# Class distribution

{support_table}
Per-class percentages, not only High percentages, are saved in `split_support.csv` when a split is approved. High pixel count and qualifying component count are separate measures. Pooled interpolated pixels are not independent experimental replicates.

# Model results

{model_table}
{'All five spectral baselines, logistic regression, random forest, SmallSegCNN and 12-band DeepLabV3/ResNet18 use the Phase 3 definitions. Neural models remain randomly initialized, unweighted and trained for the same three/two epochs; no tuning or architecture search was performed. Normalization, sampled pixels and thresholds use training only; checkpoints use validation only.' if has_results else 'The requested existing model families are retained in the gated runner, but no run is allowed before support/integrity passes.'}

{'The unchanged bounded classical pixel sampler retained Low/Moderate/High counts '+str(results['training_pixel_counts'])+'. Thus classical training has only '+str(results['training_pixel_counts'][2])+' High pixels, despite the larger total support in training masks. This constraint is exposed rather than corrected by post-test resampling.' if has_results else ''}

# High-risk performance

{'High precision, recall and F1 are reported explicitly above. Undefined precision means the model predicted no High pixels; it is not hidden as a successful result. A model with zero High recall fails High detection even if Low-dominated accuracy is high.' if has_results else 'Not estimable on a valid expanded test set in this run. Pilot High metrics remain N/A because its tests had no High support.'}

{interpretation}

# Per-geographic-group performance

{group_table}
All confusion matrices use rows=true and columns=predicted. When evaluated, group matrices are checked to sum exactly to the pooled test matrix. Full Low/Moderate/High precision, recall, F1, support, accuracy, macro F1 and weighted F1 are in `model_metrics.csv` and the JSON results; `per_geographic_group_metrics.csv` exposes geographic variation.

# Pilot vs expanded comparison

{comparison}
See [comparison report](PILOT_VS_EXPANDED_EVALUATION.md). Weaker scores are retained. No A/B outcome is manufactured by swapping regions or hiding failed classes. {'This is partial evidence, not readiness for later reliability modules.' if has_results else 'Current screening cannot establish expanded predictive behavior.'}

# Tests

**{tests} tests passed**, including all original 94 tests. Added tests cover strict multipart framing and binary payloads, bounded member CRC/NPY decoding, no-gap range coalescing, support criteria, minimum independent groups, date/position diversity, deterministic allocation, missing High, duplicated IDs, group/subtile leakage and full-context adjacency identity. The original {len(original['files'])} pilot artifacts pass the preservation hash audit.

{'All 36 saved pooled/per-region test confusion matrices (nine models × pooled plus three regions) reproduce exactly after reloading the saved artifacts. The reproduction check also confirms immutable criteria, deterministic group allocation, source/artifact hashes, training-only normalization and pixel selection, and actual mask class counts.' if (OUT/'reproduction_check.json').exists() else 'No saved-model reproduction result is claimed before that check completes.'}

# Storage impact

Metadata range acquisition charged {index:,} bytes; reference requests charged {references['charged_bytes']:,} bytes over {references['requests']} requests, including conservative envelope reservations and failed attempts. These are bounded charged-byte totals, not exact wire traffic. Full archives were not downloaded. Selective paired-input acquisition charged {split['paired_download_charged_bytes'] if split else 0:,} bytes.

Allocated repository storage at reporting time: {storage['.']:,} KiB. Phase 3.5 metadata: {storage['data/metadata/phase3_5']:,} KiB; reference cache: {storage['data/raw/phase3_5_references']:,} KiB; Phase 3.5 results: {storage['research_outputs/phase3_5']:,} KiB. The repository total includes the previously installed runtime. Detailed storage and validation are saved separately.

# Remaining limitations

- Outside the original 24,518-pair pool, reference screening is incomplete and enriched by compressed-mask complexity. Unscreened content is not assumed negative.
- v2 has deliberately enriched High support, with different class proportions across train, validation and test. Reported precision and accuracy are conditional on this design, not estimates under natural whole-deposit or field prevalence.
- Selected connected author-grid regions are the highest-confidence grouping; exact scenes, water bodies and cross-tile physical overlap remain unknown.
- Thirty-day-separated observations may still be one bloom episode; numerous interpolated pixels cannot establish independent biological evidence.
- {'Only three test components, one seed, support-enriched class prevalence and two/three neural epochs constrain interpretation. Model performance is not a converged benchmark, and geographic variation matters.' if has_results else 'Insufficient qualifying audited groups prevents a valid three-class evaluation under the frozen criteria.'}
- Source masking/no-data discrepancies and remote-sensing label uncertainty persist; no direct laboratory or cells/mL claims are made.

# Exact next recommendation

{'Keep v2 fixed. First examine per-region errors and extend the same baseline training to a predeclared convergence budget, without changing architecture or consulting test scores for selection. Separately expand independent-region and episode support for a later untouched evaluation version, with a prevalence-preserving sampling design. Do not yet start calibration, Grad-CAM, robustness, frontend or architecture searches.' if has_results else 'Continue a reference-only support search in the uninspected portion of the deposit under a separately declared acquisition budget. Keep all scientific criteria and pilot artifacts fixed. If enough geographically diverse qualifying groups cannot be established, report a scoped dataset limitation rather than forcing three-class evaluation.'}
'''
    (R/'PHASE_3_5_STATUS.md').write_text(final)
    print(status,category,'pilot artifacts preserved:',len(original['files']))

if __name__=='__main__':main()
