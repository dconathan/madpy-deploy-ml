# Deploying a Production Ready Machine Learning API

Madpy (Madison Python) Meetup talk, 4/11/2019

> When it comes to machine learning, most of the research and emphasis is on the development side, but the deployment side can be just as fun. The goal of this talk is go over the basics of deploying a production ready app for serving a machine learning model. I will be using AWS but the ideas generalize. I will demonstrate some basic architectures we use at American Family Insurance. Some familiarity with cloud computing and/or machine learning is helpful but definitely not required.

Links: 
- [Meetup event page](https://www.meetup.com/MadPython/events/258928634/)
- [Github repo](https://github.com/dconathan/madpy-deploy-ml)

## Summary

This repo contains code and configuration for deploying a sentiment text classifier trained using Tensorflow/Keras.  The quickstart section will get you a working version of the model locally.  The next section will detail an architecture for deploying it to the cloud, and set up infrastructure to deploy it on AWS using Terraform.

Check out:
- [model.py](src/model.py) for code to download data, train/save model, and predict
- [app.py](src/app.py>) for the falcon WSGI app that serves the model
- [infra/](infra) for the terraform modules (to provision AWS services)

## Setup

First clone the repo:
```
git clone https://github.com/dconathan/madpy-deploy-ml.git
cd madpy-deploy-ml
```

This repo uses [pipenv](https://pipenv.readthedocs.io/en/latest/) to set up the virtual environment, and was developed and tested using Python 3.7.  It will probably work with 3.6 too, but no promises.  To create/setup and activate the environment:

```
pipenv sync
pipenv shell
```

## Quickstart

Train a model:
```
python src/main.py train
```

Predict using the model:
```
python src/main.py predict this movie rocked!
```

Run tests (`pipenv sync --dev` first if you don't have pytest installed):
```
pytest
```

Start a server running locally that serves the model:
```
gunicorn app:api
```

Call it using `curl`:
```
curl localhost:8000/predict -X POST -H "content-type: application/json" -d '{"text":"hello world"}'
```


## Architecture 

### Summary

 - At the core of everything is [model.py](src/model.py)
    - It trains a model and can load it to predict
 - A simple WSGI app wraps the model
    - The model code, WSGI app, and environment are wrapped in a Docker image
 - An S3 bucket provides a persistant location for the model artifact(s)
    - This allows us to run the model anywhere as long as we have access to the bucket
    - The model code is written to automatically download the model from S3 if not found locally
 - The Docker image is built locally and uploaded to a private container registry
 - An EC2 instance pulls and runs the image automatically as a systemd service

 ### Key Points

 - Infrastructure as code
 - Configure using environment variables
 - Documentation is key!
