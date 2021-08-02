from flask import *
# import sqlite3, hashlib, os
import pymongo
import hashlib
import certifi
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS, cross_origin
from wsgiref import simple_server

app = Flask(__name__,template_folder="templates")
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)
template_folder="template"

# Load environment variables
load_dotenv()

# Function to connect to the MongoDB Atlas
def mongodb_connect():
    url = os.getenv('connection')
    ca = certifi.where()
    client = pymongo.MongoClient(url, tlsCAFile=ca)
    return client

# Function to generate the userId for new users
def generate_userId():
    with mongodb_connect() as conn:
        counter = conn['Users']['userId_counter'].find_one({'_id':'userId_counter'})['counter']
        conn['Users']['userId_counter'].update_one({'_id':'userId_counter'}, {'$inc':{'counter':1}})
    return str(counter + 1)

def getLoginDetails():
    with mongodb_connect() as conn:
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            # cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session['email'], ))
            # userId, firstName = cur.fetchone()
            user_data = conn['Users']['Users'].find_one({'email':session['email']})
            userId, firstName = user_data['userId'], user_data['firstName']
            # cur.execute("SELECT count(productId) FROM kart WHERE userId = ?", (userId, ))
            # noOfItems = cur.fetchone()[0]
            noOfItems = conn['Karts']['Karts'].count_documents({'userId':userId})
    return (loggedIn, firstName, noOfItems)

@app.route("/")
@cross_origin()
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    with mongodb_connect() as conn:
        # cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        # itemData = cur.fetchall()
        # cur.execute('SELECT categoryId, name FROM categories')
        # categoryData = cur.fetchall()
        categoryData = list(conn['Categories']['Categories'].find({}))
        itemData = []
        for category in categoryData:
            items = list(conn['Products'][category['name']].find({}, {'_id':0, 'productId':1, 'name':1, 'price':1, 'description':1, 'image':1, 'stock':1, 'categoryId':1}).limit(7))
            itemData.append(items)
    # itemData = parse(itemData)
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)

@app.route("/add",methods=['GET','POST'])
@cross_origin()
def admin():
    with mongodb_connect() as conn:
        # cur.execute("SELECT categoryId, name FROM categories")
        # categories = cur.fetchall()
        categories = list(conn['Categories']['Categories'].find({}))
    return render_template('add.html', categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
@cross_origin()
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        stock = request.form['stock']
        categoryId = request.form['category']

        #Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with mongodb_connect() as conn:
            # try:
            #     cur.execute('''INSERT INTO products (name, price, description, image, stock, categoryId) VALUES (?, ?, ?, ?, ?, ?)''', (name, price, description, imagename, stock, categoryId))
            #     conn.commit()
            #     msg="added successfully"
            # except:
            #     msg="error occured"
            #     conn.rollback()
            # print(msg)
            categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
            conn['Products'][categoryName].insert_one({'name':name, 'price':price, 'description':description, 'image':imagename, 'stock':stock, 'categoryId':categoryId})
        return redirect(url_for('root'))

@app.route("/remove")
@cross_origin()
def remove():
    with mongodb_connect() as conn:
        # cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        # data = cur.fetchall()
        data = []
        for category in conn['Categories']['Categories'].find({}):
            items = list(conn['Products'][category['name']].find({}, {'_id':0, 'productId':1, 'name':1, 'price':1, 'description':1, 'image':1, 'stock':1, 'categoryId':1}).limit(7))
            data.append(items)
    return render_template('remove.html', data=data)

@app.route("/removeItem")
@cross_origin()
def removeItem():
    productId = request.args.get('productId')
    categoryId = request.args.get('categoryId')
    with mongodb_connect() as conn:
        # try:
        #     cur.execute('DELETE FROM products WHERE productID = ?', (productId, ))
        #     conn.commit()
        #     msg = "Deleted successsfully"
        # except:
        #     conn.rollback()
        #     msg = "Error occured"
        # print(msg)
        categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
        conn['Products'][categoryName].delete_one({'productId':productId})
    return redirect(url_for('root'))

@app.route("/displayCategory")
@cross_origin()
def displayCategory():
        loggedIn, firstName, noOfItems = getLoginDetails()
        categoryId = request.args.get("categoryId")
        with mongodb_connect() as conn:
            # cur.execute("SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = ?", (categoryId, ))
            # data = cur.fetchall()
            categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
            data = list(conn['Products'][categoryName].find({}, {'_id':0, 'productId':1, 'name':1, 'price':1, 'description':1, 'image':1, 'stock':1, 'categoryId':1}).limit(7))
        # categoryName = data[0][4]
        # data = parse(data)
        return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryName=categoryName)

@app.route("/account/profile")
@cross_origin()
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
@cross_origin()
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with mongodb_connect() as conn:
        # cur.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = ?", (session['email'], ))
        # profileData = cur.fetchone()
        profileData = conn['Users']['Users'].find_one({'email':session['email']})
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
@cross_origin()
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with mongodb_connect() as conn:
            # cur.execute("SELECT userId, password FROM users WHERE email = ?", (session['email'], ))
            # userId, password = cur.fetchone()
            user_data = conn['Users']['Users'].find_one({'email':session['email']})
            userId, password = user_data['userId'], user_data['password']
            if password == oldPassword:
                # try:
                #     cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                #     conn.commit()
                #     msg="Changed successfully"
                # except:
                #     conn.rollback()
                #     msg = "Failed"
                # return render_template("changePassword.html", msg=msg)
                conn['Users']['Users'].update_one({'userId':userId}, {'$set':{'password':newPassword}})
                msg="Changed successfully"
            else:
                msg = "Wrong password"
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")

@app.route("/updateProfile", methods=["GET", "POST"])
@cross_origin()
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with mongodb_connect() as conn:
                # try:
                #     cur.execute('UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?', (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))
                #     con.commit()
                #     msg = "Saved Successfully"
                # except:
                #     con.rollback()
                #     msg = "Error occured"
            conn['Users']['Users'].update_one({'email':session['email']}, {'$set':{'firstName':firstName, 'lastName':lastName, 'address1':address1, 'address2':address2, 'zipcode':zipcode, 'city':city, 'state':state, 'country':country, 'phone':phone, 'email': email}})
            session['email'] = email
        return redirect(url_for('editProfile'))

@app.route("/loginForm")
@cross_origin()
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
@cross_origin()
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/productDescription")
@cross_origin()
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    categoryId = request.args.get('categoryId')
    with mongodb_connect() as conn:
        # cur.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ?', (productId, ))
        # productData = cur.fetchone()
        categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
        productData = conn['Products'][categoryName].find_one({'productId':productId}, {'_id':0, 'productId':1, 'name':1, 'price':1, 'description':1, 'image':1, 'stock':1, 'categoryId':1})
    return render_template("productDescription.html", data=productData, loggedIn = loggedIn, firstName = firstName, noOfItems = noOfItems)

@app.route("/addToCart")
@cross_origin()
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = request.args.get('productId')
        categoryId = request.args.get('categoryId')
        with mongodb_connect() as conn:
            # cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'], ))
            # userId = cur.fetchone()[0]
            # try:
            #     cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
            #     conn.commit()
            #     msg = "Added successfully"
            # except:
            #     conn.rollback()
            #     msg = "Error occured"
            userId = conn['Users']['Users'].find_one({'email':session['email']})['userId']
            conn['Karts']['Karts'].insert_one({'userId':userId, 'productId':productId, 'categoryId':categoryId})
        return redirect(url_for('root'))

@app.route("/cart")
@cross_origin()
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with mongodb_connect() as conn:
        # cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        # userId = cur.fetchone()[0]
        # cur.execute("SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = ?", (userId, ))
        # products = cur.fetchall()
        userId = conn['Users']['Users'].find_one({'email':session['email']})['userId']
        products = []
        for kart_item in conn['Karts']['Karts'].find({'userId':userId}):
            productId, categoryId = kart_item['productId'], kart_item['categoryId']
            categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
            productData = conn['Products'][categoryName].find_one({'productId':productId}, {'_id':0, 'productId':1, 'name':1, 'price':1, 'image':1, 'categoryId':1})
            products.append(productData)
    totalPrice = 0
    for row in products:
        totalPrice += float(row['price'])
    totalPrice = round(totalPrice, 2)
    return render_template("cart.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/removeFromCart")
@cross_origin()
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = request.args.get('productId')
    categoryId = request.args.get('categoryId')
    with mongodb_connect() as conn:
        # cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        # userId = cur.fetchone()[0]
        # try:
        #     cur.execute("DELETE FROM kart WHERE userId = ? AND productId = ?", (userId, productId))
        #     conn.commit()
        #     msg = "removed successfully"
        # except:
        #     conn.rollback()
        #     msg = "error occured"
        userId = conn['Users']['Users'].find_one({'email':session['email']})['userId']
        conn['Karts']['Karts'].delete_one({'userId':userId, 'productId':productId, 'categoryId':categoryId})
    return redirect(url_for('root'))

@app.route("/checkout")
@cross_origin()
def checkout():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with mongodb_connect() as conn:
        # cur.execute("SELECT userId FROM users WHERE email = ?", (email, ))
        # userId = cur.fetchone()[0]
        # cur.execute("SELECT products.price FROM products, kart WHERE products.productId = kart.productId AND kart.userId = ?", (userId, ))
        # products = cur.fetchall()
        userId = conn['Users']['Users'].find_one({'email':session['email']})['userId']
        totalPrice = 0
        for kart_item in conn['Karts']['Karts'].find({'userId':userId}):
            productId, categoryId = kart_item['productId'], kart_item['categoryId']
            categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
            productPrice = conn['Products'][categoryName].find_one({'productId':productId})['price']
            totalPrice += float(productPrice)
    return render_template("checkout.html", totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/order_confirmation")
@cross_origin()
def order_confirmation():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with mongodb_connect() as conn:
        # cur.execute("SELECT userId, totalExp FROM users WHERE email = ?", (email, ))
        # userDetails = cur.fetchone()
        # userId = userDetails[0]
        # totalExp = userDetails[1] if userDetails[1] is not None else 0
        user_data = conn['Users']['Users'].find_one({'email':session['email']})
        userId, totalExp = user_data['userId'], user_data['totalExp']
        if not totalExp:
            totalExp = '0'
        # Add total expenditure
        # cur.execute("SELECT products.price FROM products, kart WHERE products.productId = kart.productId AND kart.userId = ?", (userId, ))
        # products = cur.fetchall()
        totalPrice = 0
        for kart_item in conn['Karts']['Karts'].find({'userId':userId}):
            productId, categoryId = kart_item['productId'], kart_item['categoryId']
            categoryName = conn['Categories']['Categories'].find_one({'categoryId':categoryId})['name']
            productPrice = conn['Products'][categoryName].find_one({'productId':productId})['price']
            totalPrice += float(productPrice)
        totalExp = str(float(totalExp) + totalPrice)
        print(totalExp)
        # cur.execute("UPDATE users set totalExp = ? WHERE userId = ?", (totalExp, userId))
        conn['Users']['Users'].update_one({'userId':userId}, {'$set':{'totalExp':totalExp}})
        # Empty the cart
        # try:
        #     cur.execute("DELETE FROM kart WHERE userId = ?", (userId, ))
        #     conn.commit()
        #     msg = "removed successfully"
        # except:
        #     conn.rollback()
        #     msg = "error occured"
        conn['Karts']['Karts'].delete_many({'userId':userId})
    # Update number of items in cart
    noOfItems = 0
    return render_template("order_confirmation.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/cancel_order")
@cross_origin()
def cancel_order():
    msg = 'Order Cancelled!!!'
    print(msg)
    return redirect(url_for('root'))

@app.route("/logout")
@cross_origin()
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    # cur.execute('SELECT email, password FROM users')
    # data = cur.fetchall()
    # for row in data:
    #     if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
    #         return True
    # return False
    with mongodb_connect() as conn:
        user_password = conn['Users']['Users'].find_one({'email':email})['password']
        if user_password == hashlib.md5(password.encode()).hexdigest():
            return True
    return False

@app.route("/register", methods = ['GET', 'POST'])
@cross_origin()
def register():
    if request.method == 'POST':
        #Parse form data    
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        with mongodb_connect() as conn:
            # try:
            #     cur = con.cursor()
            #     cur.execute('INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, address1, address2, zipcode, city, state, country, phone))
            #
            #     con.commit()
            #
            #     msg = "Registered Successfully"
            # except:
            #     con.rollback()
            #     msg = "Error occured"
            if conn['Users']['Users'].find_one({'email':email}) is None:
                userId = generate_userId()
                conn['Users']['Users'].insert_one({'userId':userId, 'password':hashlib.md5(password.encode()).hexdigest(), 'email':email, 'firstName':firstName, 'lastName':lastName, 'address1':address1, 'address2':address2, 'zipcode':zipcode, 'city':city, 'state':state, 'country':country, 'phone':phone})
                msg = 'Registered Successfully!'
            else:
                msg = 'Error occured! User already exists!'
        return render_template("login.html", error=msg)

@app.route("/registerationForm")
@cross_origin()
def registrationForm():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

if __name__ == '__main__':
    app.run(debug=True)
