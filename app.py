from flask import Flask, g, render_template
import sqlite3

DATABASE = 'wokthiswayimproved.db'

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv   

@app.route('/')
def home():
    #home page just the mouthwatering spicy noodles
    sql = "SELECT orderbase_id, ordertopping_id, orderside_id FROM customer_order LEFT JOIN topping ON customer_order.ordertopping_id = topping.id LEFT JOIN base ON customer_order.orderbase_id = base.id LEFT JOIN sides ON customer_order.orderside_id = sides.id"
    results = query_db(sql)
    return render_template("home.html", results=results)

@app.route('/order')
def order():
    sql = "SELECT orderbase_id, ordertopping_id, orderside_id FROM customer_order LEFT JOIN topping ON customer_order.ordertopping_id = topping.id LEFT JOIN base ON customer_order.orderbase_id = base.id LEFT JOIN sides ON customer_order.orderside_id = sides.id"
    results = query_db(sql)
    return render_template("order.html", results=results)

@app.route('/cart')
def cart():
    return render_template("cart.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route("/base/<int:id>")
def bike(id):
    #just one noodle based on the id 
    sql = "SELECT base_name, base_price, base_image FROM customer_order LEFT JOIN topping ON customer_order.topping_id = topping.id LEFT JOIN base ON customer_order.base_id = base.id LEFT JOIN sides ON customer_order.side_id = sides.id WHERE base_name = 'MOUTHWATERING FIERY SPICY NOODLES KNOCKOUT'"
    result=query_db(sql,(id,),True)
    return str(result)

if __name__ == "__main__":
    app.run(debug=True)
