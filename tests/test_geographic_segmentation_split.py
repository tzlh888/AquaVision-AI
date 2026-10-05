import pytest
from aquavision.data.geographic_split import spatial_rows, author_partition, experiment_partitions, validate_geographic, ratio_diagnostics, freeze_json


def row(x,y=0,tile='6_2',day=1):
    sid=f'{tile}_X{x:04d}_Y{y:04d}_S050_2020_01_{day:02d}_x0_y0_64x64_1'
    return {'sample_id':sid,'sen2_member':sid+'_sen2.npy'}


def test_transitive_diagonal_and_repeated_dates():
    rows=[row(0),row(50,50),row(100,100),row(0,day=2),row(500),row(0,tile='7_2')]
    enriched=spatial_rows(rows)
    assert len({r['spatial_group_id'] for r in enriched[:4]})==1
    assert len({r['spatial_group_id'] for r in enriched})==3
    a={r['sample_id']:'train' for r in rows}; a[rows[2]['sample_id']]='test'
    with pytest.raises(ValueError,match='leakage'): validate_geographic(rows,a)
    a={r['sample_id']:'train' for r in rows}; a[rows[3]['sample_id']]='test'
    with pytest.raises(ValueError,match='leakage'): validate_geographic(rows,a)


def test_author_coin_toss_exact_and_disconnected():
    rows=[row(x) for x in (0,100,200,300,400)]
    a=author_partition(rows)
    assert list(a.values())==['train','train','train','train','test']
    assert author_partition(rows[::-1])==a
    d=ratio_diagnostics(rows,a)
    assert d['train']['fraction']==.8 and d['test']['patches']==1


def test_deterministic_threeway_and_frozen(tmp_path):
    rows=[row(x,day=d) for x in (0,500,1000,1500) for d in (1,2,3)]
    a=experiment_partitions(rows)
    assert a==experiment_partitions(rows[::-1])
    validate_geographic(rows,a['geographic'])
    assert set(a['geographic'].values())=={'train','validation','test'}
    freeze_json(tmp_path/'split.json',a); freeze_json(tmp_path/'split.json',a)
    with pytest.raises(FileExistsError): freeze_json(tmp_path/'split.json',{})


def test_grid_mismatch_and_missing_assignment():
    with pytest.raises(ValueError): spatial_rows([row(3)])
    with pytest.raises(ValueError): spatial_rows([row(0),row(0)])
    with pytest.raises(ValueError): validate_geographic([row(0)],{})
