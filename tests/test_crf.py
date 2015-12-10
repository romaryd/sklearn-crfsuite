# -*- coding: utf-8 -*-
import os
import pickle

import pytest
from sklearn.cross_validation import cross_val_score

from sklearn_crfsuite import CRF


ALGORITHMS =  ["lbfgs", "l2sgd", "pa", "ap", "arow"]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_crf(xseq, yseq, algorithm):
    crf = CRF(algorithm)
    crf.fit([xseq], [yseq])

    y_pred = crf.predict([xseq])
    if algorithm != 'ap':  # Averaged Perceptron is regularized too much
        assert y_pred == [yseq]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("use_dev", [True, False])
def test_crf_verbose(xseq, yseq, algorithm, use_dev):
    crf = CRF(algorithm, verbose=True)

    if use_dev:
        X_dev, y_dev = [xseq], [yseq]
    else:
        X_dev, y_dev = None, None

    crf.fit(
        X=[xseq, xseq],
        y=[yseq, yseq],
        X_dev=X_dev,
        y_dev=y_dev
    )
    y_pred = crf.predict([xseq])
    if algorithm != 'ap':  # Averaged Perceptron is regularized too much
        assert y_pred == [yseq]


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_crf_marginals(xseq, yseq, algorithm):
    crf = CRF(algorithm)
    crf.fit([xseq], [yseq])

    y_pred_marginals = crf.predict_marginals([xseq])
    assert len(y_pred_marginals) == 1
    marginals = y_pred_marginals[0]
    assert len(marginals) == len(yseq)

    labels = crf.tagger_.labels()
    for m in marginals:
        assert isinstance(m, dict)
        assert set(m.keys()) == set(labels)
        assert abs(sum(m.values()) - 1.0) < 1e-6


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_predict_without_fit(xseq, algorithm):
    crf = CRF(algorithm)
    with pytest.raises(Exception):
        crf.predict([xseq])


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_crf_score(xseq, yseq, algorithm):
    crf = CRF(algorithm)
    crf.fit([xseq], [yseq])

    score = crf.score([xseq], [yseq])
    if algorithm != 'ap':
        assert score == 1.0
    else:  # Averaged Perceptron is regularized too much
        assert score > 0.8


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_crf_pickling(xseq, yseq, algorithm):
    crf = CRF(algorithm=algorithm)
    crf.fit([xseq], [yseq])
    data = pickle.dumps(crf, protocol=pickle.HIGHEST_PROTOCOL)

    crf2 = pickle.loads(data)
    score = crf2.score([xseq], [yseq])
    if algorithm != 'ap':
        assert score == 1.0
    else:  # Averaged Perceptron is regularized too much
        assert score > 0.8
    assert crf2.algorithm == algorithm


def test_crf_model_filename(xseq, yseq, tmpdir):
    path = os.path.join(str(tmpdir), "foo.crfsuite")
    assert not os.path.exists(path)

    # model file is created at a specified location
    crf = CRF(model_filename=path)
    crf.fit([xseq], [yseq])
    assert os.path.exists(path)

    # it is possible to load the model just by passing a file name
    crf2 = CRF(model_filename=path)
    assert crf2.score([xseq], [yseq]) == 1.0

    # crf is picklable
    data = pickle.dumps(crf, protocol=pickle.HIGHEST_PROTOCOL)
    crf3 = pickle.loads(data)
    assert crf3.score([xseq], [yseq]) == 1.0


def test_cross_validation(xseq, yseq):
    crf = CRF()
    X = [xseq] * 20
    y = [yseq] * 20
    scores = cross_val_score(crf, X, y, n_jobs=5, cv=5)
    assert scores.mean() == 1.0


def test_crf_dev_bad_arguments(xseq, yseq):
    crf = CRF()
    X = [xseq] * 20
    y = [yseq] * 20
    with pytest.raises(ValueError):
        crf.fit(X, y, X)
