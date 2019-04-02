# Deploying a Production Ready Machine Learning API

Madpy (Madison Python) Meetup talk, 4/11/2019

> When it comes to machine learning, most of the research and emphasis is on the development side, but the deployment side can be just as fun. The goal of this talk is go over the basics of deploying a production ready app for serving a machine learning model. I will be using AWS but the ideas generalize. I will demonstrate some basic architectures we use at American Family Insurance. Some familiarity with cloud computing and/or machine learning is helpful but definitely not required.

Links: 
- [Meetup event page](https://www.meetup.com/MadPython/events/258928634/)
- [Github repo](https://github.com/dconathan/madpy-deploy-ml)

## Summary

This repo contains code and configuration for deploying a sentiment text classificatier trained using Tensorflow/Keras.  The quickstart section will get you a working version of the model locally.  The next section is about setting up infrastructure and deploying it on AWS using Terraform.

Check out:
- [model.py](src/model.py) for code to download data, train/save model, and predict
- <src/app.py> for the falcon WSGI app that serves the model
- <infra/> for the terraform modules (to provision AWS services)
- <Dockerfile>



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

Predict using model:
```
python src/main.py predict this movie rocked!
```

Run tests:
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

## Introduction 

Blah blah blah