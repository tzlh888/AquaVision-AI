from pathlib import Path
import importlib
import numpy as np
import pytest
from aquavision.evaluation.segmentation import metrics


def test_weighted_f1_does_not_replace_macro_or_high_metrics(monkeypatch):
    monkeypatch.syspath_prepend(str(Path('scripts').resolve()))
    add_weighted=importlib.import_module('run_phase3_5').add_weighted
    m=add_weighted(metrics(np.array([[2,0,0],[1,0,0],[0,0,1]])))
    assert m['macro_f1']==pytest.approx(.6)
    assert m['weighted_f1']==pytest.approx(.65)
    assert m['per_class'][1]['recall']==0
    assert m['per_class'][2]['recall']==1
