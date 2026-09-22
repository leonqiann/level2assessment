
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
    db = get_db()
    cur = get_db().execute(query, args)
    
    db.commit()

    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# =============================================================================
# ROUTE HANDLERS
# =============================================================================


@app.route("/")
def home():
    # Fetch customer order relational data for home view
    sql = "SELECT orderbase_id, orderside_id FROM customer_order LEFT JOIN base ON customer_order.orderbase_id = base.id LEFT JOIN sides ON customer_order.orderside_id = sides.id"
    results = query_db(sql)
    return render_template("home.html", results=results)


@app.route("/order")
def order():
    # Fetch preview images for bases, toppings, and sides
    sql = "select base_image from base"
    bases = query_db(sql)
    sql = "select side_image from sides"
    sides = query_db(sql)

    return render_template(
        "order.html", bases=bases, sides=sides
    )


@app.route("/orderbase")
def orderbase():
    # Fetch base options for base menu
    sql = "SELECT base_name, base_image FROM base "
    results = query_db(sql)
    return render_template("orderbase.html", results=results)



@app.route("/orderside")
def orderside():
    # Fetch side options for side menu
    sql = "SELECT side_name, side_image FROM sides "
    results = query_db(sql)
    return render_template("orderside.html", results=results)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    '''Route for signup page'''
    
    if 'user' in session:
        flash("You are already logged in!", "error")
    

    
    
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        address = request.form['address']
        
        existing_user = query_db("SELECT id FROM customer WHERE username =?", [username], one=True)
        if existing_user is not None:
            flash("That username already exists, please log in or use a different name.")
        else:
            hashed_password = generate_password_hash(password)
        
        # Execute the INSERT statement (query_db commits automatically)
            sql = "INSERT INTO customer (username, password, address) VALUES (?, ?, ?)"
            query_db(sql, (username, hashed_password, address))
        
            flash("Sign Up Successful", "success")
            return redirect("/login")
        
    return render_template('signup.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    '''Route for login Page'''
    
    if 'user' in session:
        flash("You are already logged in!", "error")
    
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        sql = "SELECT username, password FROM customer WHERE username = ?"
        user = query_db(sql, (username,), one=True)
        
        if user:
            # (0 is username, 1 is password)
            if check_password_hash(user[1], password):
                session['user'] = user[0]
                session['cart'] = []
                flash("Logged in successfully", "success")
            else:
             flash("Password incorrect", "error")
        else:
            flash("Username does not exist", "error")
            
    return render_template('login.html')

@app.route("/logout")
def logout():
    # Render logout page
    # clear all user data from session
    session.clear()
    
    return render_template("logout.html")



@app.route("/cart")
def cart():
    
    if 'user' not in session:
        flash("You must be logged in to view your cart", "error")
        return redirect('/login')
    
    
    username = session['user']
    sql_user = "SELECT id FROM customer WHERE username = ?"
    user = query_db(sql_user, (username,), one=True)

    if not user:
        session.clear()
        flash("User session invalid, please log in again", "error")
        return redirect('/login')
    
    customer_id = user[0]

    sql_cart = """
        SELECT customer_order.id, base.base_name, sides.side_name
        FROM customer_order
        LEFT JOIN orderbase ON customer_order.orderbase_id = orderbase.id
        LEFT JOIN base ON orderbase.base_id = base.id
        LEFT JOIN orderside ON customer_order.orderside_id = orderside.id
        LEFT JOIN sides ON orderside.side_id = sides.id
        WHERE customer_order.customer_id = ?
    """
    cart_items = query_db(sql_cart, (customer_id,))
    # Render shopping cart page
    return render_template("cart.html", cart_items=cart_items)


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

# error 404 handler
@app.errorhandler(404)
def not_found(_):
    """Show a page when a route/resource doesn't exist"""
    return render_template('404.html'), 404

# error 500 handler
@app.errorhandler(500)
def internal_error(_):
    """Show a page for unhandled server errors"""
    return render_template('500.html'), 500



# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Start development server with debugging enabled
    app.run(debug=True)