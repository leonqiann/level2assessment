from flask import Flask, g
import sqlite3

DATABASE = 'wokthisway.db'

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
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT base_name, base_price, base_image FROM customer_order LEFT JOIN sides ON customer_order.side_id = sides.id  LEFT JOIN topping ON customer_order.topping_id = topping.id LEFT JOIN base ON customer_order.base_id = base.id WHERE base_name = 'MOUTHWATERING FIERY SPICY NOODLES KNOCKOUT'"
    cursor.execute(sql)
    results = cursor.fetchall()
    return str(results)

if __name__ == "__main__":
    app.run(debug=True)
