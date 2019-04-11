import falcon
from model import predict
import os
import sys
import logging


logger = logging.getLogger(__name__)


api = falcon.API()


class Health:
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.body = "OK"
        resp.content_type = falcon.MEDIA_TEXT


class Predict:
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.body = self.on_post.__doc__
        resp.content_type = falcon.MEDIA_TEXT

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        """
        post /predict

        Predicts the sentiment of an input text using a model trained on movie reviews.
        Return value is a score beteen 0 and 1.
        Above 0.5 is considered positive sentiment.

        Inputs:
            text (string)
        Outputs:
            score (float)

        Example input:
        {
            "text": "this movie really sucked"
        }

        Example output:
        {
            "score": 0.1
        }
        """

        text = req.media.get("text")

        if text is None:
            raise falcon.HTTPMissingParam("text")

        if not isinstance(text, str):
            raise falcon.HTTPInvalidParam(
                f"expected a string, got a {type(text).__name__}", "text"
            )

        resp.media = {"score": predict(text)}


api.add_route("/predict", Predict())
api.add_route("/", Health())


if "pytest" not in sys.modules:
    logger.info("warming up model")
    predict("warm up!")
    logger.info("model is ready")
