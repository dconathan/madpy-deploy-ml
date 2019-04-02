import os

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

DATA_JSON = os.path.join(DATA_DIR, "rt-polarity.json")

S3_BUCKET = os.environ.get("PROJECT_BUCKET")
if S3_BUCKET is None:
    raise EnvironmentError("PROJECT_BUCKET environment variable not set")
MODEL_S3_FILE = os.path.join(S3_BUCKET, "model.h5")
MODEL_FILE = os.path.join(DATA_DIR, "model.h5")
TOKENIZER_PICKLE = os.path.join(DATA_DIR, "tokenizer.pickle")
TOKENIZER_S3_PICKLE = os.path.join(S3_BUCKET, "tokenizer.pickle")
