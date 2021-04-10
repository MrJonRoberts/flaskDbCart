from flask import Flask, render_template, request
import csv
from io import TextIOWrapper
import json
from data.db_wrapper import Db

UPLOAD_FOLDER = 'UPLOADS'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app = Flask(__name__)



# global user for all pages
userLoggedIn = {"username": "", "isAdmin": False}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    global userLoggedIn
    username = userLoggedIn['username']
    isAdmin = userLoggedIn['isAdmin']
    return render_template("home.html", username=username, isAdmin=isAdmin)


@app.route("/login", methods=['GET', 'POST'])
def login():
    global userLoggedIn
    username = userLoggedIn['username']
    isAdmin = userLoggedIn['isAdmin']

    # check user is already logged in
    if username != "":
        return render_template("home.html", username=username, isAdmin=isAdmin)

    # note not secure!
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        print(f"U: {username} P: {password}" )
        # get user name and password from data base and check here
        with Db() as db:
            sql = "SELECT username, password, isAdmin from user where username = ? and password = ?"
            data = (username, password)
            rs = db.query(sql, data)
            # get first entry
            rs = rs[0]

            if rs is not None:
                isAdmin = False
                if rs['isAdmin'] == True:
                    isAdmin=True
                return render_template("home.html", username=username, isAdmin=isAdmin)

        return render_template("login.html", msg="INCORRECT USERNAME OR PASSWORD")
    else:
        return render_template("login.html")


@app.route("/admin_upload", methods=['GET', 'POST'])
def admin_upload():
    global userLoggedIn
    username = userLoggedIn['username']
    isAdmin = userLoggedIn['isAdmin']

    # check if is admin
    if isAdmin == False:
        return render_template("home.html", username=username, isAdmin=isAdmin)
    if request.method == 'POST':
        # Create variable for uploaded file
        print(request.files)
        f = TextIOWrapper(request.files['file'], encoding="utf-8-sig")

        # store the file contents as a string
        fstring = f.read()
        # uncomment the following to debug:
        # for line in fstring.splitlines():
        #     print(line)

        # create list of dictionaries keyed by header row
        listOfManufact = getListOfManufacturers()



        csv_dicts = [{k: v for k, v in row.items()} for row in
                     csv.DictReader(fstring.splitlines(), skipinitialspace=True)]

        # do something list of dictionaries
        for bike in csv_dicts:
            print(bike)
            manId = getKey(bike['Manufacturer'], listOfManufact)
            print(manId)
            sql = "INSERT INTO bikes ('name', 'manufacturer', 'gear_rating', 'wheel_rating', "\
                  "'suspension_rating', 'price') VALUES (?, ?, ?, ?,?,?)"
            data = (bike['Bike Name'], manId, bike['gear_rating'], bike['wheel_rating'],
                    bike['suspension_rating'], bike['price'])
            with Db() as db:
                bikeId = db.insert(sql,data)

                # get spec ids
                sql = "SELECT id from specs where name = ? and value =?"
                data = ("gear", bike['gear'])
                gearId = db.query(sql, data)
                if not gearId:
                    gearId = 0
                else:
                    gearId = gearId[0]['id']
                data = ("suspension",bike['suspension'])
                suspensionId = db.query(sql, data)
                if not suspensionId:
                    suspensionId = 0
                else:
                    suspensionId = suspensionId[0]['id']
                data = ("wheel",bike['wheels'])
                wheelId = db.query(sql, data)
                if not wheelId:
                    wheelId = 0
                else:
                    wheelId = wheelId[0]['id']

                # inserts
                sql = "INSERT INTO bike_spec (bikeId, specId) VALUES (?,?)"

                data = (bikeId, gearId)
                db.insert(sql, data)
                data = (bikeId, suspensionId)
                db.insert(sql, data)
                data = (bikeId, wheelId )
                db.insert(sql, data)

                

        return json.dumps(csv_dicts)
    else:
        return render_template("admin_upload.html")

@app.route("/list")
def list_bikes():
    global userLoggedIn
    username = userLoggedIn['username']
    isAdmin = userLoggedIn['isAdmin']

    bikeList = ["There are no bikes that match your choices..."]
    # get list of bikes from database:  adust based on user preferences ...
    sql = "select b.name, b.price, m.name as manufacturer, b.id from bikes b  "\
        "join manufacturer m on b.manufacturer = m.id"

    with Db() as db:
        bikeList = db.query(sql)

        if bikeList != None:
            bikeData = []

            for b in bikeList:
                bike = {}
                # get list of specs:
                sql = "select s.name, s.value from bike_spec bs join specs s on bs.specId = s.id where bs.bikeId =?"
                data = (b['id'],)
                specList = db.query(sql, data)
                sList = []

                for spec in specList:
                    name = spec['name']
                    value = spec['value']

                    if value == "" or value is None or value == 0:
                        value = "NA"


                    s = { f"{name}": value }

                    sList.append(s)


                bike = {"name": b['name'], "price": b['price'], "id": b['id'], "man": b['manufacturer'], "specs": sList}

                bikeData.append(bike)

    return render_template("list_bikes.html", bikeList=bikeData)

@app.route("/addToCart/<id>")
def addToCart(id=None):
    global userLoggedIn
    username = userLoggedIn['username']
    isAdmin = userLoggedIn['isAdmin']
    if id == None:
        return render_template("home.html", username=username, isAdmin=isAdmin)

    sql = "select b.name, b.price, m.name as manufacturer, b.id from bikes b  " \
          "join manufacturer m on b.manufacturer = m.id WHERE b.id = ?"
    data = (id, )

    with Db() as db:
        # get bike

        b = db.query(sql, data)
        # get first bike
        b = b[0]

        sql = "select s.name, s.value from bike_spec bs join specs s on bs.specId = s.id where bs.bikeId =?"

        data = (id,)
        specList = db.query(sql, data)
        sList = []

        for spec in specList:
            name = spec['name']
            value = spec['value']

            if value == "" or value is None or value == 0:
                value = "NA"

            s = {f"{name}": value}

            sList.append(s)

        bike = {"name": b['name'], "price": b['price'], "id": b['id'], "man": b['manufacturer'], "specs": sList}
        return render_template('cart.html',  bike=bike)

@app.route("/checkout/<cartId>")
def checkout(cartId=None):
    return "CHECKOUT!"

@app.route("/logout")
def logout():
    global userLoggedIn
    userLoggedIn['username'] = ""
    userLoggedIn['isAdmin'] = False

def getListOfManufacturers():
    with Db() as db:
        sql = "SELECT * FROM MANUFACTURER order by id"
        data = ()
        rs = db.query(sql, data)
    return rs

def getKey(val, dict):
    print(f"finding {val} in {dict}")
    for item in dict:
        for key, value in item.items():
            print(key, value)
            if val == value:
                return item['id']

    return "key doesn't exist"

if __name__ == '__main__':
    app.run()

