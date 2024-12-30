FROM python:3.10-slim

ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV http_proxy=""
ENV https_proxy=""


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*  

WORKDIR /projetGLBDD

RUN python -m pip install --upgrade pip


COPY requirements.txt /projetGLBDD/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /projetGLBDD/

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=BackendProjetGLBDD.settings

CMD ["python","manage.py","runserver","0.0.0.0:8000"]

RUN apt-get update && apt-get install -y postgresql-client
