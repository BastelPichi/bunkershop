from flask import Flask, request, render_template
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import sqlite3
import sys


dbpath = "./orders.db"

conn = sqlite3.connect(dbpath)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS orders(txid string, id integer)")
cur.execute("CREATE TABLE IF NOT EXISTS products(id integer primary key autoincrement, name string, price integer, description string, seller integer, instock integer)")
cur.execute("CREATE TABLE IF NOT EXISTS sellers(id integer primary key autoincrement, name string)")
conn.commit()
conn.close()

app = Flask(__name__)

def gettx(txid, price):
    try:
        rpc_connection = AuthServiceProxy("http://user:pass@127.0.0.1:22555")

        for i in range(0, 9):
            transaction = rpc_connection.gettxout(txid, i)

            if transaction == None:
                continue

            bal = transaction["value"]

            if price + 2 > bal > price - 2:
                print(transaction)
                if transaction["scriptPubKey"]["addresses"][0] == "BHKGATf2uX1TcrPimU137dvaAm4EY78yz7":
                    return True
                else:
                    continue

            else:
                continue
        return False

    except JSONRPCException:
        return False




@app.route("/")
def index():
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    data = cur.execute("SELECT id, name, price FROM products")
    data = data.fetchall()
    print(data)
    conn.commit()
    conn.close()
    return render_template("index.html", data=data)


@app.route("/desc/<int:pid>")
def desc(pid):
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    data = cur.execute("SELECT name, price, description FROM products WHERE id = (?)", (pid,))
    data = data.fetchone()
    if data == None:
        conn.close()
        return "Don't seems like we have that product..."
    conn.commit()
    conn.close()
    descc = data[2].replace("&br", "<br>")
    return render_template("desc.html", i=data, desc=descc, pid=pid)

@app.route("/order/<int:id>")
def order(id):
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()
    data = cur.execute("SELECT name, price, instock FROM products WHERE id = (?)", (id,))
    data = data.fetchone()

    if data == None:
        conn.commit()
        conn.close()
        return "hmmmmmmm. Don't seems like were having that product."

    name = data[0]
    price = data[1]
    instock = data[2]

    if instock == 0:
        conn.commit()
        conn.close()
        return "Sorry, someone else just bought the product."

    return render_template("order.html", name=name, price=price, id=id)


@app.route("/txid", methods=["POST"])
def txid():
    transaction = request.form.get("txid")
    cusemail = request.form.get("email")
    id = request.form.get("id")

    if (transaction == None) or (cusemail == None) or (id == None) or not (id.isnumeric()):
        return "Something went wrong."

    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()

    id = int(id)

    product = cur.execute("SELECT price, instock, seller FROM products WHERE id = (?)", (id,))

    product = product.fetchone()

    if product == None:
        conn.commit()
        conn.close()
        return "Something went wrong."

    price = product[0]
    instock = product[1]
    seller = product[2]

    tx = gettx(transaction, price)

    new = cur.execute("SELECT id FROM orders WHERE txid = (?)", (transaction,))

    new = new.fetchone()

    if tx == False or new != None:
        conn.commit()
        conn.close()
        return "The txid don't seems to be correct or is already used. If you think this is a mistake, contact us."

    if instock == 0:
        return "Dont seems to be in stock anymore. If you have lost any funds, contact us."

    cur.execute("UPDATE products SET instock = instock - 1")

    seller = cur.execute("SELECT name FROM sellers WHERE id = (?)", (seller,))

    seller = seller.fetchone()

    seller = seller[0]

    import sellers

    sel = sellers.buy(transaction, seller, id, cusemail)


    if sel == None:
        conn.commit()
        conn.close()
        return "Something went wrong."

    elif sel == False:
        conn.commit()
        conn.close()
        return "Something went wrong. Contact us if you believe you lost any funds."

    cur.execute("INSERT INTO orders VALUES (?, ?)", (transaction, id))
    conn.commit()
    conn.close()

    return "Success! You should recieve your order within the time stated on the article description."

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run()
