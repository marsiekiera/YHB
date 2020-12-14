# YHB - Your Home Budget

Your Home Budget is python (flask) web application.

## Installation

Download the repository and use on of the below method

### 1. Using the docker

You need [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/).

In the repository location enter the following commands in linux terminal:
```bash
cd flask
```
```bash
docker-compose build
```
```bash
docker-compose up
```

Open browser and go to the [http://127.0.0.1:8084](http://127.0.0.1:8084)

To quit use keyboard shortcuts CTRL + C, then command:
```bash
docker-compose down
```

### 2. By creating a virtual environment

You need python 3 installed.

In the repository location enter the following commands in linux terminal (if python or pip command doesn't work, try python3 and pip3 instead of):
```bash
cd flask
```
```bash
python -m venv env
```
```bash
source env/bin/activate
```
```bash
pip install -r requirements.txt 
```
```bash
cd app/static
```
```bash
npm install chart.js --save
```
```bash
cd -
```
```bash
export FLASK_APP=run.py
```
```bash
flask run
```
To quit use keyboard shortcuts CTRL + C

### Log-in to app

If you don't want to register, you can use the below login detail:
* Login: demo
* Password: 1@Qw