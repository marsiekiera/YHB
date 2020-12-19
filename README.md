# YHB - Your Home Budget

Your Home budget is python web application. It was created to help you control your expenses.

Features available in the app:
* user registration and login
* change user login and password or delete user
* add your accounts, edit, hide, and delete
* transfer money between accounts
* add, edit or delete payee and category
* add a transaction with a given date, type (withdrawal or deposit), and assignment to the payee and category
* freely modification of an existing transaction - change date, account, type, payee, category and also delete it
* view transactions assigned to account, payee or category
* see the current and previous month's expenses on the chart.


## Tech
I used the following technologies to build the Your Home Budget:

* [Flask] - [Python] web application framework depends on the [Jinja] template engine and the [Werkzeug] WSGI toolkit
* [Sqlite] - database engine
* [Bootstrap] - CSS framework
* [Chart.js] - JavaScript library for data visualization

## Installation 
Download the repository and use on of the below method

### 1. By creating a virtual environment

To use this method, you will need installed [python 3] and [pip]
In the repository location enter the following commands in linux terminal (if python or pip command doesn't work, try python3 and pip3 instead of):
```sh
$ cd flask
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt 
$ cd app/static
$ npm install chart.js --save
$ cd -
$ export FLASK_APP=run.py
$ flask run
```
To quit use keyboard shortcuts CTRL + C

### 2. Using the docker
To use this method, you will need installed [docker] and [docker-compose].
In the repository location enter the following commands in linux terminal:
```bash
$ cd flask
$ docker-compose build
$ docker-compose up
```
Open browser and go to the [http://127.0.0.1:8084](http://127.0.0.1:8084)

To quit use keyboard shortcuts CTRL + C, then command:
```bash
$ docker-compose down
```

### Log-in to app

If you don't want to register, you can use the below login detail of demo account:
* Login: demo
* Password: 1@Qw

[//]: # (These are reference links used in the body http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [git-repo-url]: <https://github.com/marsiekiera/YHB.git>
   [yhb]: <https://github.com/marsiekiera/YHB>
   [flask]: <https://flask.palletsprojects.com>
   [sqlite]: <https://www.sqlite.org>
   [bootstrap]: <https://getbootstrap.com>
   [chart.js]: <https://www.chartjs.org>
   [jinja]: <https://jinja.palletsprojects.com>
   [Werkzeug]: <https://werkzeug.palletsprojects.com>
   [python 3]: <https://www.python.org>
   [docker]: <https://docs.docker.com/get-docker>
   [docker-compose]: <https://docs.docker.com/compose/install>
   [pip]: <https://pip.pypa.io/en/stable/installing>