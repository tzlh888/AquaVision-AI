"""Pixel confusion matrices with explicit absent-class semantics."""
import numpy as np
from aquavision.data.labels import IGNORE_INDEX


def confusion(target, prediction):
    target, prediction = np.asarray(target), np.asarray(prediction)
    if target.shape != prediction.shape:
        raise ValueError('Shape mismatch')
    valid = target != IGNORE_INDEX
    t, p = target[valid], prediction[valid]
    if not np.isin(t, [0,1,2]).all() or not np.isin(p, [0,1,2]).all():
        raise ValueError('Non-class target/prediction on valid pixel')
    return np.bincount(t.astype(int)*3+p.astype(int), minlength=9).reshape(3,3)


def metrics(matrix):
    cm = np.asarray(matrix)
    if cm.shape != (3,3) or (cm<0).any():
        raise ValueError('Expected nonnegative 3x3 confusion matrix')
    tp, actual, predicted = np.diag(cm), cm.sum(1), cm.sum(0)
    f1 = np.divide(2*tp, actual+predicted, out=np.zeros(3,dtype=float), where=(actual+predicted)>0)
    per = []
    for i,name in enumerate(('Low','Moderate','High')):
        per.append({'class':name, 'support':int(actual[i]), 'predicted':int(predicted[i]),
                    'precision':float(tp[i]/predicted[i]) if predicted[i] else None,
                    'recall':float(tp[i]/actual[i]) if actual[i] else None,
                    'f1':float(f1[i]) if actual[i] else None})
    return {'confusion_matrix':cm.tolist(), 'valid_pixels':int(actual.sum()),
            'accuracy':float(tp.sum()/actual.sum()) if actual.sum() else None,
            'macro_f1_fixed_three_zero_division':float(f1.mean()) if actual.sum() else None,
            'macro_f1_supported':float(f1[actual>0].mean()) if actual.sum() else None,
            'all_three_classes_present':bool((actual>0).all()), 'per_class':per}
