# base images
#FROM python:3.9
FROM tiangolo/uwsgi-nginx-flask:python3.9
# you can use alpine image for light weight.
# FROM python:3.9-alpine
# workdir is used to set the pwd inside docker container
WORKDIR /app

COPY src/requirements.txt /app/requirements.txt
# Install pip dependancy.
RUN pip install -r /app/requirements.txt
# copy whole directory inside /code working directory.
COPY ./src /app
# This command execute at the time when conatiner start.
#CMD ["python", "main.py"]
