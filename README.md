# cs50-1-finance - Summary
Web application via which users can “buy” and “sell” stocks. This is an exercise for Harvard's CS50 online course.

![finance web app](https://github.com/Nimikro/cs50-9-finance/blob/main/finance.png)

# About this program
This application uses Python, HTML and styling with Bootstrap. It also uses IEX API to get the stocks values in real time and a SQL database to store users information, such as username, a hash of the password, the stocks they bought or sold and the history of all transactions they made.

# Usage

You will need [Python](https://www.python.org/downloads/) and [Flask](https://flask.palletsprojects.com/en/1.1.x/installation/) installed on your computer to run this application.

Start by installing [Python 3](https://www.python.org/downloads/). Here's a [guide on the installation](https://wiki.python.org/moin/BeginnersGuide/Download). Once you have Python, and clonned this repository, run the following commands:

To install pip, run:
```
sudo apt install python3-pip
```
To install Flask, run:
```
sudo apt install python3-flask
```
To install this project's dependecies, run:
```
pip3 install -r requirements.txt
```
Define the correct file as the default Flask application:

Unix Bash (Linux, Mac, etc.):
```
export FLASK_APP=application.py
```
Windows CMD:
```
set FLASK_APP=application.py
```
Windows PowerShell:
```
$env:FLASK_APP = "application.py"
```
Also, make sure to use the API_KEY command in the project files to connect to the IEX API
```
export API_KEY=value
```
Run Flask and you're good to go!
```
flask run
```

