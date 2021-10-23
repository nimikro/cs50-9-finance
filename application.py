import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Store username
    username = db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"]

    # Retrieve stock symbol and number of shares
    stocks = db.execute("SELECT symbol, shares FROM portfolio WHERE username = :username", username=username)

    # Find the total_sum of all stocks
    total_sum = []

    # Get all stock information for every stock symbol
    for stock in stocks:
        symbol = str(stock["symbol"])
        shares = int(stock["shares"])
        name = lookup(symbol)["name"]
        price = lookup(symbol)["price"]
        total = shares*price
        stock["name"] = name
        stock["price"] = usd(price)
        stock["total"] = usd(total)
        total_sum.append(float(total))

    # Retrieve cash available and creat cash total
    cash_available = db.execute("SELECT cash FROM users WHERE username = :username", username=username)[0]["cash"]
    cash_total = sum(total_sum) + cash_available

    return render_template("index.html", stocks = stocks, cash_available=usd(cash_available), cash_total=usd(cash_total))



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Look up the stock and store dictionary results in data
        stock_name = lookup(request.form.get("symbol"))

        # If the stock_name is invalid
        if stock_name == None:
            return apology("invalid symbol", 400)

        # Get number of shares
        shares = request.form.get("shares")

        # If shares are invalid, return an error
        if int(shares) < 0 or not shares.isdigit() or not float(shares).is_integer():
            return apology("Shares need to be a positive integer", 400)

        # Select user's cash
        cash = db.execute("SELECT cash FROM users WHERE id = :uid", uid=int(session['user_id']))

        # Calculate value of stock as stock*shares
        value = stock_name["price"] * int(shares)

        # If the user don't have enough money, return with error
        if int(cash[0]["cash"]) < value:
            return apology("Not enough money to proceed", 403)

        # Otherwise complete purchase
        else:
            # Subtract the value of purchase from the user's cash
            db.execute("UPDATE users SET cash = cash - :value WHERE id = :uid", value=value, uid=int(session['user_id']))

            # Add the transaction to the user's history
            db.execute("INSERT INTO history (username, operation, symbol, price, shares) VALUES (:username, 'BUY', :symbol, :price, :shares)",
            username=db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"],
            symbol=stock_name['symbol'], price=stock_name['price'], shares=request.form.get('shares'))

            # If the stock does not exist in portfolio add the stock, else update user's portfolio
            check = db.execute("SELECT shares FROM portfolio WHERE username = :username AND symbol = :symbol",
                            username=db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"],
                            symbol=stock_name["symbol"])

            if not check:
                db.execute("INSERT INTO portfolio (username, symbol, shares) VALUES (:username, :symbol, :shares)",
                username=db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"],
                symbol=stock_name["symbol"], shares=int(request.form.get("shares")))

            # Else update portfolio
            else:
                db.execute("UPDATE portfolio SET username=:username, symbol=:symbol, shares=shares+:shares WHERE symbol=:symbol",
                username=db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"],
                symbol=stock_name["symbol"], shares=int(request.form.get("shares")))

        # Go to portfolio
        return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Store username
    username = db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"]

    # Retrieve stock symbol and number of shares
    stocks = db.execute("SELECT operation, symbol, price, date, time, shares FROM history WHERE username = :username", username=username)

    # Add stock name into stocks variable
    for stock in stocks:
        symbol = str(stock["symbol"])
        name = lookup(symbol)["name"]
        stock["name"] = name
        stock["price"] = usd(int(stock["shares"])*stock["price"])
        if stock["operation"] == 'SELL':
            stock["shares"] = -stock["shares"]

    return render_template("history.html", stocks=stocks)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Look up the symbol and store dictionary results in data
        data = lookup(request.form.get("symbol"))

        # If the symbol is invalid
        if data == None:
            return apology("invalid symbol", 400)

        # Otherwise return and print the data
        else:
            return render_template("quoted.html", name=data["name"], symbol=data["symbol"], price=usd(data["price"]))


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirm password was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Check confirm password:
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords dont match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username is not taken
        if len(rows) != 0:
            return apology("username already taken", 400)

        # Store user to database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Store the username
    username = db.execute("SELECT username FROM users WHERE id = :uid", uid=int(session['user_id']))[0]["username"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Look up the stock and store dictionary results in data
        stock_name = lookup(request.form.get("symbol"))

        # If the stock_name is invalid
        if stock_name == None:
            return apology("invalid symbol", 400)

        # Look for shares of the stock in user's portfolio
        user_shares = db.execute("SELECT shares FROM portfolio WHERE username = :uid AND symbol = :symbol", uid=username, symbol=str(request.form.get("symbol")))[0]["shares"]

        # If user doesn't have any shares of that specific stock, return an apology
        if user_shares == 0:
            return apology("you do not own any shares of that stock", 400)

        # Get number of shares
        shares = request.form.get("shares")

        # Calculate value of stock as stock*shares
        value = stock_name["price"] * int(shares)

        # If shares are invalid, return an error
        if int(shares) < 1 or not shares.isdigit() or not shares:
            return apology("share number is invalid", 400)

        # If the number of shares that the user is trying to sell is greater than the number of shares he owns, return an apology
        elif int(shares) > user_shares:
             return apology("you do not own that many shares of that stock", 400)

        # Complete sale
        else:

            # Add the value of the sale to the user's cash
            db.execute("UPDATE users SET cash=cash+:value WHERE id = :uid", value=value, uid=int(session['user_id']))

            # Add the transaction to the user's history
            db.execute("INSERT INTO history (username, operation, symbol, price, shares) VALUES (:username, 'SELL', :symbol, :price, :shares)",
            username=username, symbol=stock_name['symbol'], price=stock_name['price'], shares=request.form.get('shares'))

            # Remove the stock from the user's portfolio if the user is selling all the shares
            if int(user_shares) == int(shares):
                db.execute("DELETE FROM portfolio WHERE username = :username AND symbol = :symbol",
                            username=username, symbol=str(request.form.get("symbol")))

            # Update portfolio, if the user is selling some of the shares
            if int(user_shares) > int(shares):
                 db.execute("UPDATE portfolio SET shares=shares-:shares WHERE username = :username and symbol = :symbol",
                            shares=shares, username=username, symbol=str(request.form.get("symbol")))


        # Go to portfolio
        return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        #Pass symbols from portfolio to sell list
        symbols = db.execute("SELECT symbol FROM portfolio WHERE username = :username", username=username)

        return render_template("sell.html", symbols=symbols)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
