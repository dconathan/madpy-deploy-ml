# Deploying a Production Ready Machine Learning API

Madpy (Madison Python) Meetup talk, 4/11/2019

> When it comes to machine learning, most of the research and emphasis is on the development side, but the deployment side can be just as fun. The goal of this talk is go over the basics of deploying a production ready app for serving a machine learning model. I will be using AWS but the ideas generalize. I will demonstrate some basic architectures we use at American Family Insurance. Some familiarity with cloud computing and/or machine learning is helpful but definitely not required.

Links: 
- [Meetup event page](https://www.meetup.com/MadPython/events/258928634/)
- [Github repo](https://github.com/dconathan/madpy-deploy-ml)

## Summary

This repo contains code and configuration for deploying a sentiment text classifier trained using Tensorflow/Keras.  The quickstart section will get you a working version of the model locally.  The next section will detail an architecture for deploying it to the cloud, followed by a tutorial on provisioning and deploying to AWS using Terraform.

Check out:
- [model.py](src/model.py) for code to download data, train/save model, and predict
- [app.py](src/app.py) for the falcon WSGI app that serves the model
- [infra/](infra) for the terraform modules (to provision AWS services)

## Setup

### Python

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

### Terraform

For the steps involving provisioning AWS resources, you need [terraform](https://www.terraform.io/) installed and appropriate AWS credientials.  See the [terraform AWS authentication](https://www.terraform.io/docs/providers/aws/index.html#authentication) section for more details (I use environment variables).

At the time of giving this talk, I am using:

```
$ terraform --version
Terraform v0.11.13
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

![architecture](img/arch.png)

### Summary

 - At the core of everything is [model.py](src/model.py)
    - It trains, saves, and uploads the model
    - It has a `predict` function that applies the model
 - A simple WSGI app serves the model
 - The model code, WSGI app, and environment are packaged into a Docker image
 - AWS infrastructure provisioned using Terraform
   - An **S3 bucket** provides a persistant location for the model artifact(s)
      - This allows us to run the model anywhere as long as we have access to the bucket
      - The model code is written to automatically download the model from S3 if not found locally
   - A **container registry** stores/serves the docker images
      - The Docker image is built locally and uploaded to the registry
   - An **EC2 server** instance pulls and runs the image automatically as a systemd service

 ### Key Points

 - Infrastructure as code
 - Configure using environment variables for reusability/modularity


## Provisioning and Deployment

First check out the [.env](.env) file, specifically the first section:

```
# define your project and environment
PROJECT_NAME=madpy-test
PROJECT_ENV=dev
```

Names of all the resources will derive from these variables.  S3 bucket and ECR names must be unique so you will need to change the `PROJECT_NAME` to something new.  The `PROJECT_ENV` variable lets you set up two or more versions of the whole stack if that's needed.

> **Note:** A typical pattern might have you develop in a `PROJECT_ENV=dev` environment, switch to `PROJECT_ENV=qa` for testing, and use `PROJECT_ENV=prod` for a critical, client-facing environment.

### S3 bucket

Navigate to `infra/bucket/` and check out the [main.tf](infra/bucket/main.tf).

This contains JSON-like code (a "terraform module") for configuring an S3 bucket.

   - The first 2 sections declare variables
      - These are set from the environment variables in our [.env](.env) file
   - The `provider` section sets the AWS region according to the variable
   - The `resource` section declares that we want an S3 bucket with the given name.  
      - Check out the [terraform `aws_s3_bucket` argument reference](https://www.terraform.io/docs/providers/aws/r/s3_bucket.html#argument-reference) for all the allowable arguments
      - The defaults are sane enough for our use case









