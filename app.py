
import sqlite3
from flask import Flask, g, render_template, session, flash, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash


# Database file location
DATABASE = "wokthiswayimproved.db"

app = Flask(__name__)
app.config['SECRET_KEY'] = "key123"


# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================


def get_db():
    """Opens a database connection if one does not exist for current context."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Closes database connection when request context ends."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """Executes SQL query and returns fetched results safely."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# =============================================================================
# ROUTE HANDLERS
# =============================================================================


@app.route("/")
def home():
    # Fetch customer order relational data for home view
    sql = "SELECT orderbase_id, ordertopping_id, orderside_id FROM customer_order LEFT JOIN topping ON customer_order.ordertopping_id = topping.id LEFT JOIN base ON customer_order.orderbase_id = base.id LEFT JOIN sides ON customer_order.orderside_id = sides.id"
    results = query_db(sql)
    return render_template("home.html", results=results)


@app.route("/order")
def order():
    # Fetch preview images for bases, toppings, and sides
    sql = "select base_image from base"
    bases = query_db(sql)
    sql = "select topping_image from topping"
    toppings = query_db(sql)
    sql = "select side_image from sides"
    sides = query_db(sql)

    return render_template(
        "order.html", bases=bases, toppings=toppings, sides=sides
    )


@app.route("/orderbase")
def orderbase():
    # Fetch base options for base menu
    sql = "SELECT base_name, base_image FROM base "
    results = query_db(sql)
    return render_template("orderbase.html", results=results)


@app.route("/ordertopping")
def ordertopping():
    # Fetch topping options for topping menu
    sql = "SELECT topping_name, topping_image FROM topping "
    results = query_db(sql)
    return render_template("ordertopping.html", results=results)


@app.route("/orderside")
def orderside():
    # Fetch side options for side menu
    sql = "SELECT side_name, side_image FROM sides "
    results = query_db(sql)
    return render_template("orderside.html", results=results)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    ''' # Route for signup page'''
    if request.method == "POST":
        # add username & password to db
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        # hash with hash thingy
        hashed_password = generate_password_hash(password)
        # put into db
        sql = "INSERT INTO customer (username,password,address) VALUES (?,?,?)"
        query_db(sql, (username, hashed_password, address))
        flash("Sign Up Successful", "success")
        return redirect("/login")
    return render_template('signup.html')


@app.route("/cart")
def cart():
    # Render shopping cart page
    return render_template("cart.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    '''Route for login Page'''
    # if the user posts a username and password
    if request.method == "POST":
        # get the username and password
        username = request.form['username']
        password = request.form['password']
        # try to find this user in the database
        sql = "SELECT * FROM customer WHERE username = ?"
        user = query_db(sql=sql, args=(username,), one=True)
        if user:
            # we got a user!!
            # check password matches-
            if check_password_hash(user[2], password):
                # we are logged in successfully
                # Store the username in the session
                session['user'] = user
                flash("Logged in successfully", "success")
                session['cart'] = []
                return redirect("/menu")
            flash("Password incorrect", "error")
        else:
            flash("Username does not exist", "error")
    # render this template regardless of get/post
    return render_template('login.html')



@app.route("/about")
def about():
    # Render static about page
    return render_template("about.html")


@app.route("/contact")
def contact():
    # Render static contact page
    return render_template("contact.html")


@app.route("/base/<int:id>")
def baseimage(id):
    # Fetch single base image by ID parameter
    sql = "SELECT base_image from base"
    result = query_db(sql, (id,), True)
    return str(result)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Start development server with debugging enabled
    app.run(debug=True)