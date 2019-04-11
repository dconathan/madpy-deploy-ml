from typing import List, Tuple
import tarfile
import time
import tensorflow as tf
import os
import json
import pickle
import functools
import logging
import s3fs
import constants

# logging stuff
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
tf.logging.set_verbosity(logging.ERROR)

# cache for tokenizer/model
cache = functools.lru_cache(128)


def predict(text: str) -> float:
    """
    Implements the full text to score pipeline, downloading files from project s3 bucket if necessary. 
    This *should* either return the score or raise an error about a missing piece along the way.

    Model/tokenizer is cached in memory so subsequent calls will be faster than the first
    """
    logger.debug(f"predicting on {len(text)} chars, {len(text.split())} tokens")
    t0 = time.time()

    tokenizer = get_tokenizer()

    # preprocess texts into lists of indices
    X = tokenizer.texts_to_sequences([text])
    X = tf.keras.preprocessing.sequence.pad_sequences(X, maxlen=16)

    model = get_model()

    y_hat = model.predict(X)
    score = float(y_hat[0][1])

    logger.debug(f"predicting is done, took {time.time() - t0:.2f}s")

    return score


def train():
    """
    Trains and saves the model (hdf5 file) and tokenizer (pickle file)
    """
    logger.info("training...")

    texts, labels = get_data()

    logger.debug("fitting tokenizer")
    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.fit_on_texts(texts)

    logger.debug(f"saving tokenizer to {constants.TOKENIZER_PICKLE}")
    with open(constants.TOKENIZER_PICKLE, "wb") as f:
        pickle.dump(tokenizer, f)

    logger.debug("preprocessing data")
    X = tokenizer.texts_to_sequences(texts)
    X = tf.keras.preprocessing.sequence.pad_sequences(X, maxlen=16)
    y = tf.keras.utils.to_categorical(labels)

    logger.debug("building model")
    i = tf.keras.layers.Input(shape=(None,))
    embeddings = tf.keras.layers.Embedding(len(tokenizer.word_counts) + 1, 8)(i)
    lstm = tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(8))(embeddings)
    output = tf.keras.layers.Dense(2, activation="softmax")(lstm)
    model = tf.keras.Model(inputs=i, outputs=output)
    model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["acc"])

    logger.debug("fitting model")
    model.fit(X, y, validation_split=0.1, epochs=10, batch_size=512)

    logger.debug(f"saving model to {constants.MODEL_FILE}")
    model.save(constants.MODEL_FILE)
    logger.info("done training")


def upload_tokenizer():
    """
    Uploads the tokenizer pickle file to the project s3 bucket
    """
    logger.info(
        f"uploading tokenizer from {constants.TOKENIZER_PICKLE} to {constants.TOKENIZER_S3_PICKLE}"
    )
    s3 = s3fs.S3FileSystem()

    if not s3.exists(constants.S3_BUCKET):
        logger.error(f"s3 bucket {constants.S3_BUCKET} does not exist")

    s3.put(constants.TOKENIZER_PICKLE, constants.TOKENIZER_S3_PICKLE)
    logger.info("done uploading tokenizer")


def download_model():
    """
    Downloads the model hdf5 file from project s3 bucket to local data folder
    """
    logger.info(
        f"downloading model from {constants.MODEL_S3_FILE} {constants.MODEL_FILE}"
    )
    s3 = s3fs.S3FileSystem()
    if not s3.exists(constants.MODEL_S3_FILE):
        if not s3.exists(constants.S3_BUCKET):
            logger.error(f"s3 bucket {constants.S3_BUCKET} does not exist")
        else:
            logger.error(f"Could not find {constants.MODEL_S3_FILE}.  Need to upload?")
    s3.get(constants.MODEL_S3_FILE, constants.MODEL_FILE)
    logger.info("done downloading model")


def upload_model():
    """
    Uploads model hdf5 file from local data folder to project s3 bucket
    """
    logger.info(
        f"uploading model from {constants.MODEL_FILE} to {constants.MODEL_S3_FILE}"
    )
    s3 = s3fs.S3FileSystem()
    if not os.path.exists(constants.MODEL_FILE):
        logger.error(f"Could not find {constants.MODEL_FILE}.  Need to train?")
    if not s3.exists(constants.S3_BUCKET):
        logger.error(f"s3 bucket {constants.S3_BUCKET} does not exist")
    s3.put(constants.MODEL_FILE, constants.MODEL_S3_FILE)
    logger.info("done uploading model")


@cache
def get_model() -> tf.keras.Model:
    """
    Returns the keras Model object, ready to predict.  Downloads the file if it doesn't exist.

    Result is cached
    """
    t0 = time.time()
    logger.info("getting and caching model")
    if not os.path.exists(constants.MODEL_FILE):
        download_model()
    model = tf.keras.models.load_model(constants.MODEL_FILE)
    logger.info(f"got model, took {time.time() - t0:.2f}s")
    return model


@cache
def get_tokenizer() -> tf.keras.preprocessing.text.Tokenizer:
    """
    Returns the keras Tokenizer object, ready to tokenize.
    Reads from local file if it exists,
    otherwise reads directly from S3 (does not download the file).

    Result is cached
    """
    t0 = time.time()
    logger.info("getting and caching tokenizer")
    if os.path.exists(constants.TOKENIZER_PICKLE):
        with open(constants.TOKENIZER_PICKLE, "rb") as f:
            logger.info(f"got tokenizer, took {time.time() - t0:.2f}s")
            return pickle.load(f)
    s3 = s3fs.S3FileSystem()
    if not s3.exists(constants.TOKENIZER_S3_PICKLE):
        if not s3.exists(constants.S3_BUCKET):
            logging.error(f"s3 bucket {constants.S3_BUCKET} does not exist")
        else:
            logging.error(
                f"Could not find {constants.TOKENIZER_S3_PICKLE}. Need to upload?"
            )
    with s3.open(constants.TOKENIZER_S3_PICKLE, "rb") as f:
        tokenizer = pickle.load(f)
    logger.info(f"got tokenizer, took {time.time() - t0:.2f}s")
    return tokenizer


def get_data() -> Tuple[List[str], List[int]]:
    """
    Downloads tar.gz of raw data if it doesn't exist.
    Cleans and saves as JSON file locally.
    Will load from JSON file if exists.

    Returns the data as a list of sentences (strings) and
    0/1 for negative/positive sentiment.
    """

    if os.path.exists(constants.DATA_JSON):

        logger.debug(f"loading training data from {constants.DATA_JSON}")

        with open(constants.DATA_JSON) as f:
            return json.load(f)

    else:

        logger.debug(f"downloading training data from {constants.DATA_URL}")

        filename = tf.keras.utils.get_file("rt-polaritydata.tar.gz", constants.DATA_URL)

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
