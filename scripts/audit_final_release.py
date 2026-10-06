"""Read-only scientific verification, writing new audit artifacts only in Phase5.

--metadata-only checks published metrics/documents without loading checkpoints.
--full additionally requires original local arrays, predictions, and checkpoints.
Neither mode trains, selects new models, downloads data, or rewrites Phase4.
"""
import argparse,csv,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from aquavision.evaluation.segmentation import metrics
from aquavision.evaluation.reliability import choose_models

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research_outputs/phase5'
PATTERN=r'ground[ -]truth|pollution detection|accurately generalizes|reliable (?:three.class geographic )?generalization|cells\s*/\s*ml|best model|state.of.the.art'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def pointer(data,path):
    if path=='len(samples)':return len(data['samples'])
    if path.startswith('regional_high_range:'):
        vals=[r['per_class'][2]['f1'] for r in data[path.split(':',1)[1]]['test_groups'].values()];return [min(vals),max(vals)]
    for k in path.split('/'):data=data[int(k)] if isinstance(data,list) else data[k]
    return data

def preservation(full):
    expected=read('data/metadata/phase5/preservation_manifest.json')['files'];amendment=read('data/metadata/phase5/public_release_sanitization.json')['files'];missing=[];changed=[];sanitized=[];checked=0
    for p,h in expected.items():
        path=ROOT/p
        if not path.exists():missing.append(p);continue
        checked+=1;observed=sha(path)
        if observed==h:continue
        release_change=amendment.get(p,{})
        if release_change.get('before_sha256')==h and release_change.get('after_sha256')==observed:sanitized.append(p)
        else:changed.append(p)
    assert not changed,changed
    if full:assert not missing,missing
    return {'expected_files':len(expected),'checked_files':checked,'original_hash_matches':checked-len(sanitized),'documented_public_release_path_sanitizations':sanitized,'changed_files':changed,'unavailable_files':missing,'complete_local_preservation':not missing and not changed,'frozen_v2_sha256':sha(ROOT/'data/metadata/phase3_5/geographic_split_v2.json')}

def metric_tables():
    results=read('research_outputs/phase4/results.json');specs=read('research_outputs/phase4/specifications.json');selection=read('research_outputs/phase4/selection.json');count=0
    for i,r in results.items():
        for m in [r['validation'],r['test'],*r['test_groups'].values()]:
            cm=np.asarray(m['confusion_matrix']);computed=metrics(cm)
            for k,v in computed.items():
                if k=='per_class':
                    for c,actual in enumerate(v):
                        for key,value in actual.items():assert m[k][c][key]==value,(i,c,key)
                        expected={'tp':int(cm[c,c]),'fp':int(cm[:,c].sum()-cm[c,c]),'fn':int(cm[c].sum()-cm[c,c]),'true_proportion':float(cm[c].sum()/cm.sum()),'predicted_proportion':float(cm[:,c].sum()/cm.sum())}
                        assert all(m[k][c][key]==value for key,value in expected.items())
                else:assert m[k]==v,(i,k)
            assert m['macro_f1']==computed['macro_f1_fixed_three_zero_division'];count+=1
        assert np.array_equal(np.sum([m['confusion_matrix'] for m in r['test_groups'].values()],axis=0),r['test']['confusion_matrix'])
    candidates={i:r['validation'] for i,r in results.items() if specs[i]['variant']!='band_ablation'}
    neural={i for i in candidates if specs[i]['family'] in ['SmallSegCNN','DeepLabV3_ResNet18']}
    chosen=choose_models(candidates,neural)
    assert all(selection[k]==v for k,v in chosen.items())
    start=read('research_outputs/phase4/test_evaluation_start.json');reg=read('data/metadata/phase4/preregistration.json')
    assert reg['registered_utc']<selection['selected_utc']<start['started_utc']
    assert start['selection_sha256']==sha(ROOT/'research_outputs/phase4/selection.json')
    assert start['temperature_sha256']==sha(ROOT/'research_outputs/phase4/temperatures.json')
    assert reg['split_sha256']==sha(ROOT/'data/metadata/phase3_5/geographic_split_v2.json')
    with (ROOT/'research_outputs/tables/final_results.csv').open() as f:rows=list(csv.DictReader(f))
    exact=read('research_outputs/phase5/central_results.json');assert len(rows)==len(exact)==6
    for row,source in zip(rows,exact):
        for k,v in source.items():
            if v is None:assert row[k]==''
            elif isinstance(v,(int,float)):assert float(row[k])==v,(source['experiment_id'],k)
            else:assert row[k]==v
        i=row['experiment_id']
        for col,p,metric in [('Validation Macro F1','validation','macro_f1'),('Validation High F1','validation','high'),('Geographic Macro F1','test','macro_f1'),('Geographic High F1','test','high')]:
            value=results[i][p]['per_class'][2]['f1'] if metric=='high' else results[i][p][metric];assert float(row[col])==value
        cal=read('research_outputs/phase4/calibration.json');expected=cal.get(i,{}).get('raw',{}).get('overall',{}).get('ece')
        assert (float(row['ECE']) if row['ECE'] else None)==expected
    return {'confusion_matrices_recomputed':count,'regional_sums_exact':True,'selection_recomputed_from_validation':chosen,'registration_order_verified':True,'central_csv_rows_verified':len(rows)}

def documents():
    report=(ROOT/'research_outputs/reports/RESEARCH_RESULTS.md').read_text();abstract=report.split('## Abstract\n\n')[1].split('\n## 1.')[0]
    words=len(abstract.split());assert 150<=words<=250
    assert len(re.findall(r'^## [0-9]+\.',report,re.M))==19
    portfolio=(ROOT/'research_outputs/reports/PORTFOLIO_SUMMARY.md').read_text();assert 600<=len(portfolio.split())<=900
    application=(ROOT/'research_outputs/reports/APPLICATION_DESCRIPTION.md').read_text();assert 150<=len(application.split())<=220
    cv=(ROOT/'research_outputs/reports/CV_DESCRIPTION.md').read_text();one=cv.split('## One-line version\n\n')[1].split('\n\n##')[0];assert len(one.split())<=35
    readme=(ROOT/'README.md').read_text();claims=read('research_outputs/phase5/readme_claim_sources.json')['claims']
    for c in claims:
        assert c['readme_snippet'] in readme,c['id']
        assert (ROOT/c['source']).exists(),c['source']
        if 'verified_value' in c:assert pointer(read(c['source']),c['locator'])==c['verified_value'],c['id']
    for s in ['LIMITED','No CNN passed','0.5803','validation High F1 = 0']:assert s in readme,s
    figures=read('research_outputs/phase5/figure_manifest.json');assert figures['core_figure_count']==len(figures['figures'])==10
    for v in figures['figures']:
        for k in ['png','svg']:assert (ROOT/v[k]).exists()
    protected=read('data/metadata/phase5/preservation_manifest.json')['files'];public=[ROOT/'README.md',ROOT/'research_outputs/tables/final_results.md']+[p for p in (ROOT/'research_outputs/reports').glob('*.md') if str(p.relative_to(ROOT)) not in protected]
    links=0
    for p in public:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if link.startswith(('https:','http:','#')):continue
            target=link.split('#')[0]
            resolved=(p.parent/target).resolve()
            # The metadata audit report links to the JSON produced by this same invocation.
            assert resolved.exists() or resolved==OUT/'metadata_audit.json',(str(p),link);links+=1
        # Direct positive slogans, as opposed to explicit negative conclusions.
        assert not re.search(r'(?i)the model generalizes successfully|achieves reliable three.class geographic generalization|state.of.the.art performance|accurately generalizes',p.read_text()),p
    return {'abstract_words':words,'portfolio_words':len(portfolio.split()),'application_words':len(application.split()),'cv_one_line_words':len(one.split()),'canonical_numbered_sections':19,'readme_provenance_records':len(claims),'core_figures':10,'public_local_links_verified':links,'public_documents':len(public)}

def claim_scan():
    command=['rg','--json','-n','-i','--hidden','--no-ignore','-g','*.{md,py,mjs,json,txt,csv,tsv,yml,yaml,toml,html,xml,log,svg}','-g','!.git/**','-g','!.venv/**','-g','!tmp/**','-g','!**/node_modules/**','-g','!**/__pycache__/**','-g','!**/.pytest_cache/**','-g','!**/claim_occurrences.json','-g','!**/claim_scan_raw.jsonl',PATTERN,'.']
    proc=subprocess.run(command,cwd=ROOT,capture_output=True,text=True);assert proc.returncode in [0,1],proc.stderr
    matches=[]
    for line in proc.stdout.splitlines():
        value=json.loads(line)
        if value['type']!='match':continue
        d=value['data'];p=d['path']['text'].removeprefix('./');raw=d['lines']['text'].rstrip();terms=[m['match']['text'] for m in d['submatches']]
        if p.startswith(('data/metadata/sources/','data/metadata/phase2_sources/')):scope='primary-source snapshot';decision='Preserve original wording; externally authored material excluded from AquaVision outcome claims.'
        elif p=='data/README.md' or p=='data/metadata/phase5/README_before_phase5.md':scope='historical overview';decision='Preserved as historical scope, explicitly annotated in ARCHIVE_INDEX; not current public overview.'
        elif p.startswith('research_outputs/reports/') and p in read('data/metadata/phase5/preservation_manifest.json')['files']:scope='frozen historical/scientific report';decision='Preserve exact evidence; scope explained in ARCHIVE_INDEX. Physical conversion remains unsupported and no stable-transfer outcome is claimed.'
        elif p.startswith(('scripts/','src/','tests/','configs/')):scope='implementation/test/protocol text';decision='Terms are validation refusals, test fixtures, search patterns or historical report templates; not positive final claims.'
        elif p.startswith('research_outputs/phase5/'):scope='release provenance/audit';decision='Review trail or explicit methodological limitation; numerical sources remain linked.'
        elif p.startswith(('data/metadata/','research_outputs/phase')):scope='saved provenance/experiment metadata';decision='Preserve recorded protocol and source context; no retrospective scientific rewriting.'
        else:scope='current public document';decision='Explicit limitation, research question, or qualified interpretation; manually reviewed in the release audit.'
        encoded=raw.encode('utf-8');contexts=[]
        for item in d['submatches']:
            start=item['start'];end=item['end'];left=max(0,start-160);right=min(len(encoded),end+160)
            context=encoded[left:right].decode('utf-8',errors='replace').replace('\n',' ').strip()
            contexts.append({'term':item['match']['text'],'start_byte':start,'end_byte':end,'context':context})
        matches.append({'path':p,'line':d['line_number'],'terms':terms,'line_bytes':len(encoded),'line_sha256':hashlib.sha256(encoded).hexdigest(),'contexts':contexts,'scope':scope,'disposition':decision})
    write('claim_occurrences.json',{'pattern':PATTERN,'scope':'All repository-owned text including ignored source snapshots. Binary arrays/PDFs, Git internals, dependency environments and temporary generated work are excluded; cached extracted source text is included. This inventory excludes itself to avoid recursive copies.','occurrences':matches})
    counts={}
    for r in matches:counts[r['scope']]=counts.get(r['scope'],0)+1
    return {'matched_lines':len(matches),'matched_term_occurrences':sum(len(r['terms']) for r in matches),'scope_counts':counts,'manual_review_required':'See FINAL_RELEASE_AUDIT.md; phrase occurrence alone is not a misleading claim.'}

def full_reload():
    import torch
    from run_phase4 import context,predict,summarize,probabilities,neural
    from aquavision.data.segmentation_dataset import verify_samples
    from aquavision.evaluation.reliability import calibration
    torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
    specs=read('research_outputs/phase4/specifications.json');results=read('research_outputs/phase4/results.json');temps=read('research_outputs/phase4/temperatures.json');cals=read('research_outputs/phase4/calibration.json');parts=context();verify_samples(sum(parts.values(),[]));count=0;predcount=0;argmax=0;maxrf=0.;calchecks=0
    for i,spec in specs.items():
        for partition in ['validation','test']:
            observed=predict(spec,parts[partition]);saved=np.load(ROOT/f'research_outputs/phase4/{i}_{partition}.npz')
            for k,v in observed.items():
                if k=='prob' and spec['family']=='RandomForest':
                    maxrf=max(maxrf,float(np.max(np.abs(v-saved[k]))));assert np.allclose(v,saved[k],rtol=0,atol=1e-12)
                else:assert np.array_equal(v,saved[k]),(i,partition,k)
            pooled,groups=summarize(observed,parts[partition]);assert pooled==results[i][partition];count+=1;predcount+=1
            if partition=='test':
                for g,m in groups.items():assert m==results[i]['test_groups'][g];count+=1
            if neural(spec):assert np.array_equal(probabilities(observed,temps[i]['temperature']).argmax(-1),observed['pred']);argmax+=1
            if partition=='test' and i in cals:
                cached={k:saved[k] for k in saved.files};y=cached['y'];valid=y!=-100
                selectors={'overall':np.ones(len(y),bool),**{g:np.array([r['spatial_group_id']==g for r in parts['test']]) for g in groups}}
                for mode,data in cals[i].items():
                    p=probabilities(cached,temps[i]['temperature'] if mode=='temperature' else 1.)
                    for g,sel in selectors.items():assert calibration(y[sel][valid[sel]],p[sel][valid[sel]])==data[g];calchecks+=1
        print('Reloaded',i,flush=True)
    return {'exact_confusion_matrices':count,'exact_class_prediction_caches':predcount,'temperature_argmax_checks':argmax,'calibration_groups_exact':calchecks,'maximum_rf_probability_roundoff':maxrf,'verified_input_pairs':sum(map(len,parts.values())),'training_performed':False}

def main():
    import os
    os.chdir(ROOT);parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--metadata-only',action='store_true');group.add_argument('--full',action='store_true');args=parser.parse_args();OUT.mkdir(exist_ok=True)
    audit={'mode':'full' if args.full else 'metadata-only','preservation':preservation(args.full),'metrics':metric_tables(),'documents':documents(),'claim_scan':claim_scan()}
    xml=OUT/'pytest_results.xml'
    if xml.exists():
        suites=ET.parse(xml).getroot().findall('testsuite');audit['tests']={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']};assert audit['tests']['tests']>=123 and audit['tests']['failures']==audit['tests']['errors']==0
        if args.full:assert audit['tests']['skipped']==0
    else:audit['tests']={'status':'No local Phase5 pytest run available; not verified by this invocation'}
    audit['checkpoint_reload']=full_reload() if args.full else {'status':'Not requested; public-metadata audit does not verify local checkpoints/caches'}
    audit['passed']=True;write('final_audit.json' if args.full else 'metadata_audit.json',audit);print(json.dumps({k:v for k,v in audit.items() if k not in ['preservation','metrics']},indent=2),flush=True)
if __name__=='__main__':main()
