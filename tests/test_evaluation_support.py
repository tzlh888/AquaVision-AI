import pytest
from aquavision.data.evaluation_support import group_support,qualifies,choose_groups,validate_support
from aquavision.data.geographic_split import spatial_rows

C={'test_high_components':3,'validation_high_components':1,'train_high_components':2,'test_source_tiles':2,'high_dates_per_component':2,'minimum_date_span_days':30,'high_patch_positions_per_component':2,'minimum_high_pixels_per_component':100,'all_three_classes_each_split':True}


def fixtures():
    rows=[]
    for i in range(6):
        tile='6_2' if i<3 else '7_2';x=(i%3)*300
        for j,d in enumerate(('2020_01_01','2020_03_01')):
            sid=f'{tile}_X{x:04d}_Y0000_S050_{d}_x{j*64}_y0_64x64_1'
            rows.append({'sample_id':sid,'sen2_member':sid+'_sen2.npy','member':sid+'_cyan.npy','tile':tile,'date':d.replace('_','-'),
                         'patch_row':j*64,'patch_col':0,'low_pixels':100,'moderate_pixels':100,'high_pixels':100})
    return spatial_rows(rows)


def test_support_and_deterministic_split():
    rows=fixtures();groups=group_support(rows)
    allocation=choose_groups(groups,C)
    assert allocation==choose_groups(groups[::-1],C)
    assignments={r['sample_id']:allocation[r['spatial_group_id']] for r in rows}
    support=validate_support(rows,assignments,C,grid_context=rows)
    assert next(r for r in support if r['split']=='test')['qualified_high_groups']==3


def test_pixels_cannot_replace_groups_dates_or_positions():
    rows=fixtures();g=group_support(rows[:2])[0];assert qualifies(g,C)
    for bad in ({**g,'high_date_count':1},{**g,'high_date_span_days':29},{**g,'high_patch_positions':1}):
        assert not qualifies({**bad,'high_pixels':1000000},C)
    with pytest.raises(ValueError,match='qualifying'):choose_groups([g],C)


def test_high_absent_duplicates_and_group_leakage_rejected():
    rows=fixtures();allocation=choose_groups(group_support(rows),C)
    a={r['sample_id']:allocation[r['spatial_group_id']] for r in rows}
    missing=[{**r,'high_pixels':0} if a[r['sample_id']]=='test' else r for r in rows]
    with pytest.raises(ValueError,match='class'):validate_support(missing,a,C)
    with pytest.raises(ValueError,match='Duplicate'):validate_support(rows+[rows[0]],a,C)
    b=dict(a);b[rows[0]['sample_id']]='validation' if a[rows[0]['sample_id']]!='validation' else 'train'
    with pytest.raises(ValueError,match='leakage'):validate_support(rows,b,C)


def test_adjacent_region_cannot_be_relabelled_as_independent():
    rows=fixtures();a=choose_groups(group_support(rows),C)
    assignments={r['sample_id']:a[r['spatial_group_id']] for r in rows}
    broken=[{**r,'spatial_group_id':'invented'} if i==0 else r for i,r in enumerate(rows)]
    with pytest.raises(ValueError,match='identity'):validate_support(broken,assignments,C,grid_context=rows)
