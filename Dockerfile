FROM python:3.9.4-buster

WORKDIR /opt/app

COPY requirements.txt /opt/app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


