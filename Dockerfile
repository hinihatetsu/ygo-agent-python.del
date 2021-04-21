FROM python:3.8.9-buster

WORKDIR /opt/app

COPY requirements.txt /opt/app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt