from typing import List, Tuple
import tarfile
import time
import gzip
import tensorflow as tf
import os
import json
import pickle
import functools
import logging
import s3fs


import constants

cache = functools.lru_cache(128)


def get_data() -> Tuple[List[str], List[int]]:
    """
    Reads training data from a local json file, downloads file if it doesn't exist.
    """

    if os.path.exists(constants.DATA_JSON):

        with open(constants.DATA_JSON) as f:
            return json.load(f)

    else:

        DATA_URL = "http://www.cs.cornell.edu/people/pabo/movie-review-data/rt-polaritydata.tar.gz"

        filename = tf.keras.utils.get_file("rt-polaritydata.tar.gz", DATA_URL)

        texts = []
        labels = []

        with tarfile.open(filename, "r:gz") as f:
            for member in f.getmembers():
                if member.name.endswith("neg"):
                    x = f.extractfile(member)
                    for line in x:
                        texts.append(line.decode("latin").strip())
                        labels.append(0)
                elif member.name.endswith("pos"):
                    x = f.extractfile(member)
                    for line in x:
                        texts.append(line.decode("latin").strip())
                        labels.append(1)

        with open(constants.DATA_JSON, "w") as f:
            json.dump([texts, labels], f)

        return texts, labels


def train():
    """
    Trains and saves the model (hdf5 file) and tokenizer (pickle file)
    """

    texts, labels = get_data()

    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.fit_on_texts(texts)

    with open(constants.TOKENIZER_PICKLE, "wb") as f:
        pickle.dump(tokenizer, f)

    X = tokenizer.texts_to_sequences(texts)
    X = tf.keras.preprocessing.sequence.pad_sequences(X, maxlen=16)
    y = tf.keras.utils.to_categorical(labels)

    i = tf.keras.layers.Input(shape=(None,))
    embeddings = tf.keras.layers.Embedding(len(tokenizer.word_counts) + 1, 16)(i)
    lstm = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(8))(embeddings)
    output = tf.keras.layers.Dense(2, activation="softmax")(lstm)

    model = tf.keras.Model(inputs=i, outputs=output)

    model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["acc"])

    model.fit(X, y, validation_split=0.1, epochs=10, batch_size=1024)

    model.save(constants.MODEL_FILE)


def upload_tokenizer():
    """
    Uploads the tokenizer pickle file to the project s3 bucket
    """
    s3 = s3fs.S3FileSystem()
    if not s3.exists(constants.S3_BUCKET):
        raise FileNotFoundError(f"s3 bucket {constants.S3_BUCKET} does not exist")
    print("uploading tokenizer...")
    s3.put(constants.TOKENIZER_PICKLE, constants.TOKENIZER_S3_PICKLE)
    print("done")


def download_model():
    """
    Downloads the model hdf5 file from project s3 bucket to local data folder
    """
    s3 = s3fs.S3FileSystem()
    if not s3.exists(constants.MODEL_S3_FILE):
        if not s3.exists(constants.S3_BUCKET):
            raise FileNotFoundError(f"s3 bucket {constants.S3_BUCKET} does not exist")
        raise FileExistsError(
            f"Could not find {constants.MODEL_S3_FILE}.  Need to upload?"
        )
    print("downloading model...")
    s3.get(constants.MODEL_S3_FILE, constants.MODEL_FILE)
    print("done")


def upload_model():
    """
    Uploads model hdf5 file from local data folder to project s3 bucket
    """
    s3 = s3fs.S3FileSystem()
    if not os.path.exists(constants.MODEL_FILE):
        raise FileNotFoundError(
            f"Could not find {constants.MODEL_FILE}.  Need to train?"
        )
    if not s3.exists(constants.S3_BUCKET):
        raise FileNotFoundError(f"s3 bucket {constants.S3_BUCKET} does not exist")
    print("uploading model")
    s3.put(constants.MODEL_FILE, constants.MODEL_S3_FILE)
    print("done")


@cache
def get_model() -> tf.keras.Model:
    """
    Returns the keras Model object, ready to predict.  Downloads the file if it doesn't exist.

    Result is cached
    """
    print("getting model")
    if not os.path.exists(constants.MODEL_FILE):
        download_model()
    return tf.keras.models.load_model(constants.MODEL_FILE)


@cache
def get_tokenizer() -> tf.keras.preprocessing.text.Tokenizer:
    """
    Returns the keras Tokenizer object, ready to tokenize.  Reads from local file if it exists, otherwise reads directly from S3 (does does download the file).

    Result is cached
    """
    if os.path.exists(constants.TOKENIZER_PICKLE):
        with open(constants.TOKENIZER_PICKLE, "rb") as f:
            return pickle.load(f)
    s3 = s3fs.S3FileSystem()
    if not s3.exists(constants.TOKENIZER_S3_PICKLE):
        if not s3.exists(constants.S3_BUCKET):
            raise FileNotFoundError(f"s3 bucket {constants.S3_BUCKET} does not exist")
        raise FileNotFoundError(
            f"Could not find {constants.TOKENIZER_S3_PICKLE}. Need to upload?"
        )
    print("downloading tokenizer")
    with s3.open(constants.TOKENIZER_S3_PICKLE, "rb") as f:
        return pickle.load(f)


def predict(text: str) -> float:
    """
    Implements the full text to score pipeline, downloading files from project s3 bucket if necessary.

    This *should* either return the score or raise an error about a missing piece along the way.

    Model/tokenizer is cached in memory so subsequent calls will be faster than the first
    """
    print("predicting")

    model = get_model()
    tokenizer = get_tokenizer()

    X = tokenizer.texts_to_sequences([text])
    X = tf.keras.preprocessing.sequence.pad_sequences(X, maxlen=32)

    y_hat = model.predict(X)
    score = float(y_hat[0][1])

    print("done")

    return score
