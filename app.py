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
    return render_template("order.html")

@app.route('/orderbase')
def orderbase():
    sql = "SELECT base_name, base_image FROM base "
    results = query_db(sql)
    return render_template("orderbase.html", results=results)

@app.route('/ordertopping')
def ordertopping():
    sql = "SELECT topping_name, topping_image FROM topping "
    results = query_db(sql)
    return render_template("ordertopping.html", results=results)

@app.route('/orderside')
def orderside():
    sql = "SELECT side_name, side_image FROM sides "
    results = query_db(sql)
    return render_template("orderside.html", results=results)



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
def baseimage(id):
    #just one noodle based on the id 
    sql = "SELECT base_image from base"
    result=query_db(sql,(id,),True)
    return str(result)

if __name__ == "__main__":
    app.run(debug=True)
