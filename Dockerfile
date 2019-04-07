FROM python:3.7

RUN pip install pipenv

COPY Pipfile* ./

RUN pipenv install --deploy --system

COPY src/ .

ARG PROJECT_BUCKET
ENV PROJECT_BUCKET $PROJECT_BUCKET

CMD ["gunicorn", "-b", "0.0.0.0", "app:api"]
