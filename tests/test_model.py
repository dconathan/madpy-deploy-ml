import warnings

warnings.simplefilter("ignore", category=DeprecationWarning)

import model
import constants
import tensorflow as tf
import warnings
import os
import numpy as np
import warnings


def test_get_data():
    X, y = model.get_data()
    assert isinstance(X, list)
    assert isinstance(y, list)
    assert len(X) == len(y) > 0
    assert len(set(y)) == 2
    assert all(isinstance(x, str) for x in X)
    assert all(isinstance(i, int) for i in y)


def test_tokenizer():
    if not os.path.exists(constants.TOKENIZER_PICKLE):
        warnings.warn(
            f"{constants.TOKENIZER_PICKLE} not found, skipping test_tokenizer()"
        )
        return

    t = model.get_tokenizer()
    assert isinstance(t, tf.keras.preprocessing.text.Tokenizer)
    assert len(t.word_counts) > 0


def test_model():
    if not os.path.exists(constants.MODEL_FILE):
        warnings.warn(f"{constants.MODEL_FILE} not found, skipping test_model()")
        return

    m = model.get_model()
    assert isinstance(m, tf.keras.Model)

    X = np.random.randint(0, 10, (1, 32))

    y_hat = m.predict(X)

    y = float(y_hat[0][1])

    assert 0 < y_hat[0][1] < 1


def test_model_performance():
    if not os.path.exists(constants.MODEL_FILE):
        warnings.warn(
            f"{constants.MODEL_FILE} not found, skipping test_model_performance()"
        )
        return
    if not os.path.exists(constants.TOKENIZER_PICKLE):
        warnings.warn(
            f"{constants.TOKENIZER_PICKLE} not found, skipping test_model_performance()"
        )
        return

    m = model.get_model()
    tokenizer = model.get_tokenizer()

    texts, labels = model.get_data()

    X = tokenizer.texts_to_sequences(texts)
    X = tf.keras.preprocessing.sequence.pad_sequences(X, maxlen=16)
    y = tf.keras.utils.to_categorical(labels)

    accuracy = m.evaluate(X, y)[1]

    assert accuracy > 0.9
