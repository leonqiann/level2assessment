"""Wok This Way - Flash app for noodle ordering """
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
def close_connection(_):
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
    """Fetch customer order relational data for home view"""
    sql = """SELECT orderbase_id, orderside_id FROM customer_order
    LEFT JOIN base ON customer_order.orderbase_id = base.id 
    LEFT JOIN sides ON customer_order.orderside_id = sides.id"""
    results = query_db(sql)
    return render_template("home.html", results=results)


@app.route("/order")
def order():
    """preview images for bases, toppings, and sides"""
    sql = "select base_image from base"
    bases = query_db(sql)
    sql = "select side_image from sides"
    sides = query_db(sql)

    return render_template(
        "order.html", bases=bases, sides=sides
    )


@app.route("/orderbase")
def orderbase():
    """noodle options for noodle menu"""
    sql = "SELECT base_name, base_image, base_price, id FROM base "
    results = query_db(sql)
    return render_template("orderbase.html", results=results)

@app.route("/orderside")
def orderside():
    """side options for side menu"""
    sql = "SELECT side_name, side_image, side_price, id FROM sides "
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
            flash("That username already exists, please log in or use a different name.", "error")
        else:
            hashed_password = generate_password_hash(password)
        # Execute the INSERT statement (query_db commits automatically)
            sql = "INSERT INTO customer (username, password, address) VALUES (?, ?, ?)"
            query_db(sql, (username, hashed_password, address))
            flash("Sign Up Successful, please log in.", "success")
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
            # 0 is username, 1 is password
            # check the password hash against the password
            if check_password_hash(user[1], password):
                session['user'] = user[0]
                session['cart'] = []
                flash("Logged in successfully", "success")
            # if password doesnt match, flash error message
            else:
                flash("Password incorrect", "error")
            # if username doesnt exist, flash error message
        else:
            flash("Username does not exist", "error")
    return render_template('login.html')

@app.route("/logout")
def logout():
    """clear session and log out user"""
    #clears session
    session.clear()
    return render_template("logout.html")

@app.route("/cart")
def cart():
    """show cart for user if logged in"""
    #if user isnt logged in redirect to login page
    if 'user' not in session:
        flash("You must be logged in to view your cart", "error")
        return redirect('/login')

    username = session['user']
    user = query_db("SELECT id FROM customer WHERE username = ?", (username,), one=True)
    if not user:
        session.clear()
        flash("User session invalid, please log in again", "error")
        return redirect('/login')

    customer_id = user[0]

    sql_bases = """
        SELECT base.base_name, SUM(orderbase.base_quantity) AS qty,
        base.base_price AS price
        FROM customer_order
        JOIN orderbase ON customer_order.orderbase_id = orderbase.id
        JOIN base ON orderbase.base_id = base.id
        WHERE customer_order.customer_id = ?
        GROUP BY base.base_name
    """
    sql_sides = """
        SELECT sides.side_name, SUM(orderside.side_quantity) AS qty,
        sides.side_price AS price
        FROM customer_order
        JOIN orderside ON customer_order.orderside_id = orderside.id
        JOIN sides ON orderside.side_id = sides.id
        WHERE customer_order.customer_id = ?
        GROUP BY sides.side_name
    """
    bases = query_db(sql_bases, (customer_id,))
    sides = query_db(sql_sides, (customer_id,))

    return render_template("cart.html", bases=bases, sides=sides)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    """add items to the shopping cart for the logged-in user"""
    print(request.form)
    # has to be logged in to add to cart
    if 'user' not in session:
        flash("You must be logged in to add items to your cart", "error")
        return redirect('/login')

    item_type = request.form.get("item_type")   # base or side
    try:
        #turn values into integers, if can't, then flash error message & redirect order page
        item_id = int(request.form.get("item_id", ""))
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        flash("Invalid item or quantity", "error")
        return redirect('/order')

    # validate item type and quantity
    if item_type not in ("base", "side") or not 1 <= quantity <= 10:
        flash("Invalid item or quantity", "error")
        return redirect('/order')

    # find user id from username in this session
    user = query_db("SELECT id FROM customer WHERE username = ?",
                    (session['user'],), one=True)
    #if not found, clear session and flash error message
    if not user:
        session.clear()
        flash("User session invalid, please log in again", "error")
        return redirect('/login')
    # insert into orderbase/orderside and customer_order tables
    db = get_db()
    # if item_type is base, insert into orderbase and customer_order tables
    if item_type == "base":
        cur = db.execute(
            "INSERT INTO orderbase (base_id, base_quantity) VALUES (?, ?)",
            (item_id, quantity))
        db.execute(
            "INSERT INTO customer_order (customer_id, orderbase_id) VALUES (?, ?)",
            (user[0], cur.lastrowid))
    # if item_type is side, insert into orderside and customer_order tables
    else:
        cur = db.execute(
            "INSERT INTO orderside (side_id, side_quantity) VALUES (?, ?)",
            (item_id, quantity))
        db.execute(
            "INSERT INTO customer_order (customer_id, orderside_id) VALUES (?, ?)",
            (user[0], cur.lastrowid))
    db.commit()

    return redirect(request.referrer)

@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    """clear cart """
    # has to be logged in
    if 'user' not in session:
        flash("You must be logged in to do that", "error")
        return redirect('/login')

    user = query_db("SELECT id FROM customer WHERE username = ?",
                    (session['user'],), one=True)
    if not user:
        session.clear()
        flash("User session invalid, please log in again", "error")
        return redirect('/login')

    customer_id = user[0]
    db = get_db()

    # Delete the orderbase or orderside rows this customer's orders point to.
    db.execute("""
        DELETE FROM orderbase WHERE id IN (
            SELECT orderbase_id FROM customer_order
            WHERE customer_id = ? AND orderbase_id IS NOT NULL
        )
    """, (customer_id,))
    db.execute("""
        DELETE FROM orderside WHERE id IN (
            SELECT orderside_id FROM customer_order
            WHERE customer_id = ? AND orderside_id IS NOT NULL
        )
    """, (customer_id,))
    db.execute("DELETE FROM customer_order WHERE customer_id = ?", (customer_id,))
    db.commit()

    flash("Cart cleared", "success")
    return redirect('/cart')

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    """remove one item from cart"""
    #has to be loged in
    if 'user' not in session:
        flash("You must be logged in to do that", "error")
        return redirect('/login')

    # find users customer id from username in session
    user = query_db("SELECT id FROM customer WHERE username = ?",
                    (session['user'],), one=True)
    #if user not found clear session
    if not user:
        session.clear()
        flash("User session invalid, please log in again", "error")
        return redirect('/login')

    customer_id = user[0]
    item_type = request.form.get("item_type")
    item_name = request.form.get("item_name")
    db = get_db()

    if item_type == "base":
        #find orderbase id and quantity for customer
        row = db.execute("""
            SELECT orderbase.id, orderbase.base_quantity
            FROM customer_order
            JOIN orderbase ON customer_order.orderbase_id = orderbase.id
            JOIN base ON orderbase.base_id = base.id
            WHERE customer_order.customer_id = ? AND base.base_name = ?
            LIMIT 1
        """, (customer_id, item_name)).fetchone()

        if row:
            orderbase_id, current_qty = row
            #if quantity > 1 decrease by 1or else delete the orderbase row
            if current_qty > 1:
                db.execute("UPDATE orderbase SET base_quantity = base_quantity - 1 WHERE id = ?",
                           (orderbase_id,))
            else:
                db.execute("DELETE FROM customer_order WHERE orderbase_id = ?", (orderbase_id,))
                db.execute("DELETE FROM orderbase WHERE id = ?", (orderbase_id,))
    else:
        #find orderside id and quantity for customer
        row = db.execute("""
            SELECT orderside.id, orderside.side_quantity
            FROM customer_order
            JOIN orderside ON customer_order.orderside_id = orderside.id
            JOIN sides ON orderside.side_id = sides.id
            WHERE customer_order.customer_id = ? AND sides.side_name = ?
            LIMIT 1
        """, (customer_id, item_name)).fetchone()

        if row:
            orderside_id, current_qty = row
            #if quantity > 1 decrease by 1 or else delete the orderside row
            if current_qty > 1:
                db.execute("UPDATE orderside SET side_quantity = side_quantity - 1 WHERE id = ?",
                           (orderside_id,))
            else:
                db.execute("DELETE FROM customer_order WHERE orderside_id = ?", (orderside_id,))
                db.execute("DELETE FROM orderside WHERE id = ?", (orderside_id,))

    db.commit()
    flash("Item(s) removed", "success")
    return redirect('/cart')


@app.route("/about")
def about():
    """about page"""
    return render_template("about.html")


@app.route("/contact")
def contact():
    """contact page"""
    return render_template("contact.html")

@app.route("/checkout", methods=["POST"])
def checkout():
    """checkout page"""
    if 'user' in session:
        user = query_db("SELECT id FROM customer WHERE username = ?",
                        (session['user'],), one=True)
        if user:
            customer_id = user[0]
            db = get_db()

            db.execute("""
                DELETE FROM orderbase WHERE id IN (
                    SELECT orderbase_id FROM customer_order
                    WHERE customer_id = ? AND orderbase_id IS NOT NULL
                )
            """, (customer_id,))
            db.execute("""
                DELETE FROM orderside WHERE id IN (
                    SELECT orderside_id FROM customer_order
                    WHERE customer_id = ? AND orderside_id IS NOT NULL
                )
            """, (customer_id,))
            db.execute("DELETE FROM customer_order WHERE customer_id = ?", (customer_id,))
            db.commit()
    return render_template("checkout.html")


@app.route("/base/<int:base_id>")
def baseimage(base_id):
    """Fetch single base image by ID parameter"""
    sql = "SELECT base_image from base WHERE id = ?"
    result = query_db(sql, (base_id,), True)
    return str(result)

# error 404 handler
@app.errorhandler(404)
def not_found(_):
    """Show a page when a route doesn't exist"""
    return render_template('404.html'), 404

# error 500 handler
@app.errorhandler(500)
def internal_error(_):
    """Show a page for unhandled server errors"""
    return render_template('500.html'), 500





if __name__ == "__main__":
    # Start development server with debugging enabled
    app.run(debug=True)
