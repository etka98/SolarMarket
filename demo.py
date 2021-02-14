from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine 
import pandas as pd
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text

Server = 'DESKTOP-10VUPTF'
Database = 'SolarMarket'
Driver = 'ODBC Driver 17 for SQL Server'
Database_Con = f'mssql://@{Server}/{Database}?driver={Driver}'
engine = create_engine(Database_Con)
con = engine.connect()
db = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)
app.secret_key = "31"


@app.route("/register", methods=["POST", "GET"])
def signUp():
	if request.method == "POST":
		name = request.form["name"]
		surname = request.form["surname"]
		phone = request.form["phone"]
		email = request.form["email"]
		birthdate = request.form["birthdate"]
		password = request.form["password"]
		if request.form["usertype"] == "cus":
			userType = False
		else:
			userType = True
		db.execute("INSERT INTO [dbo].[User] (name, surname, phoneNumber, mail, birthDate, password, typeOfUsers) VALUES (:name, :surname, :phoneNumber, :mail, :birthDate, :password, :typeOfUsers)",
            {"name": name, "surname": surname, "phoneNumber": str(phone), "mail": email, "birthDate": birthdate, "password": password, "typeOfUsers": userType}) 
		db.commit()
		return redirect(url_for("login"))
	else:
		if "email" in session:
			return redirect(url_for("login"))
		return render_template("register.html") 
	

@app.route("/" , methods=["POST", "GET"])
def welcomePage():
	if "email" in session:
		return redirect(url_for("login"))
	return render_template("welcome.html")



@app.route("/login", methods=["POST", "GET"])
def login():
	if request.method == "POST":
		session.permanent = True
		email = request.form["email"]
		password = request.form["password"]
		existFlag = db.execute(text('SELECT Count(*) FROM [dbo].[User] WHERE mail = :email and password = :password') , {'email': email, 'password': password}).fetchone()
		if int(existFlag[0]) == 1:
			session["email"] = email
			session["password"] = password
			email = session["email"]
			password = session["password"]
			usertype = db.execute(text('select typeOfUsers from [dbo].[User] where mail = :email and password = :password'), {'email': email, 'password': password}).fetchone()
			if usertype[0] == True:
				return redirect(url_for("sellerHome"))
			else:
				return redirect(url_for("customerHome"))
		elif int(existFlag[0]) == 0:
			return render_template("login.html")	
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			usertype = db.execute(text('select typeOfUsers from [dbo].[User] where mail = :email and password = :password'), {'email': email, 'password': password}).fetchone()
			if usertype[0] == True:
				return redirect(url_for("sellerHome"))
			else:
				return redirect(url_for("customerHome"))
		return render_template("login.html")

@app.route("/sellerHome", methods=["POST", "GET"])
def sellerHome():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		flagBtn = request.form["btn"]
		if flagBtn[len(flagBtn)-1] == "A":
			db.execute(text('update Offer set approval = :approval where id = :id'), {'approval': True, 'id': flagBtn[0:len(flagBtn)-1]})
			db.commit()
		else:
			db.execute(text('DELETE FROM Offer WHERE id = :id'), {'id': flagBtn[0:len(flagBtn)-1]})
			db.commit()
		return redirect(url_for("sellerHome"))
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			ofList = db.execute(text('select o.bid, o.customerID, o.id from Seller s, [dbo].[User] u, Product p, Customer c, Offer o where u.mail = :email and u.id = s.userID and p.sellerID = s.id and o.productID = p.id and c.id = o.customerID and o.approval = 0'), {'email': email}).fetchall()
			nameList = []
			for of in ofList:
				nameO = db.execute(text('select u.name, u.surname from [dbo].[User] u, Customer c where :cID = c.id and c.userID = u.id'), {'cID': of[1]}).fetchone()
				nameList.append(nameO)
			size = len(ofList)
			productSize = db.execute(text('select count(*) from [dbo].[User] u, Seller s, Product p where :email = u.mail and u.id = s.userID and s.id = p.sellerID'), {'email': email}).fetchone()
			nameSurname = db.execute(text('select u.name, u.surname from [dbo].[User] u where :email = u.mail'), {'email': email}).fetchone()
			adSize = db.execute(text('select count(*) from [dbo].[User] u, Seller s, Ad a where :email = u.mail and u.id = s.userID and s.id = a.sellerID'), {'email': email}).fetchone()
			fee = db.execute(text('select s.feePercent from [dbo].[User] u, Seller s, Ad a where :email = u.mail and u.id = s.userID'), {'email': email}).fetchone()
			return render_template("sellerHomePage.html", ofList=ofList, nameList=nameList, size=size, productSize=productSize, nameSurname=nameSurname, adSize=adSize, fee=int(fee[0]*100)/100.0)
		else:
			return redirect(url_for("login"))

@app.route("/customerHome", methods=["POST", "GET"])
def customerHome():
	if request.method == "POST":
		btn = request.form["offerB"]
		session["adId"] = btn
		return redirect(url_for("makeOffer"))
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			adsList = db.execute(text('select u.name, u.surname, u.phoneNumber, u.mail, p.location, p.locationArea, p.capacity, a.price, a.photo , a.id from Product p, Ad a, Seller s, [dbo].[User] u where a.productID = p.id and a.sellerID = s.id and p.sellerID = s.id and u.id = s.userID')).fetchall()
			nameSurname = db.execute(text('select u.name, u.surname from [dbo].[User] u where :email = u.mail'), {'email': email}).fetchone()
			return render_template("customerHomePage.html", adsList=adsList , nameSurname=nameSurname)
		else:
			return redirect(url_for("login"))

@app.route("/editProfil", methods=["POST", "GET"])
def editProfil():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		name = request.form["name"]
		surname = request.form["surname"]
		phone = request.form["phone"]
		db.execute(text('update [dbo].[User] set name = :name, surname = :surname, phoneNumber = :phone where mail = :email'), {'email': email, 'name': name, 'surname': surname, 'phone': phone})
		nameSurname = db.execute(text('select u.name, u.surname from [dbo].[User] u where :email = u.mail'), {'email': email}).fetchone()
		db.commit()
		return render_template("edit_profile.html", nameSurname=nameSurname)
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			nameSurname = db.execute(text('select u.name, u.surname from [dbo].[User] u where :email = u.mail'), {'email': email}).fetchone()
			return render_template("edit_profile.html", nameSurname=nameSurname)
		else:
			return redirect(url_for("login"))	

@app.route("/myOffer", methods=["POST", "GET"])
def myOffer():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		btnD = request.form['btnO']
		if btnD[len(btnD)-1] == "U": 
			session["uOfferId"] = btnD[0:len(btnD)-1]
			return redirect(url_for("updateOffer"))
		else:
			print(btnD[0:len(btnD)-1])
			db.execute(text('DELETE FROM Offer WHERE id = :id'), {'id': btnD[0:len(btnD)-1]})
			db.commit()
		return redirect(url_for("myOffer"))
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			offerList = db.execute(text('select a.price, p.location, p.locationArea, p.capacity, o.bid, o.id from [dbo].[User] u, Customer c, Ad a, Offer o, Product p where :email = u.mail and u.id = c.userID and c.id = o.customerID and a.productID = o.productID and p.id = o.productID'), {'email': email}).fetchall()
			nameSurname = db.execute(text('select u.name, u.surname from [dbo].[User] u where :email = u.mail'), {'email': email}).fetchone()
			return render_template("myOffer.html", offerList=offerList, nameSurname=nameSurname)
		else:
			return redirect(url_for("login"))	

@app.route("/logout")
def logout():
	session.pop("email", None)
	session.pop("password", None)
	return redirect(url_for("welcomePage"))

@app.route("/addProduct", methods=["POST", "GET"])
def addProduct():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		konum =  request.form["konum"]
		boyut =  request.form["boyut"]
		kapasite =  request.form["kapasite"]
		sellerID = db.execute(text('select s.id from [dbo].[User] u, Seller s where :email = u.mail and u.id = s.userID'), {'email': email}).fetchone()
		db.execute(text("INSERT INTO Product (sellerID, location, locationArea, capacity) VALUES (:sellerID, :location, :locationArea, :capacity)"), {'sellerID' : sellerID[0], 'location' : konum, 'locationArea' : boyut, 'capacity' : kapasite})
		db.commit()
		return redirect(url_for("addProduct"))
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			return render_template("addProduct.html")
		else:
			return redirect(url_for("login"))

@app.route("/makeOffer", methods=["POST", "GET"])
def makeOffer():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		price = request.form["fiyat"]
		adId = session['adId']
		pId = db.execute(text('select a.productID from Ad a where a.id = :adId'), {'adId' : adId}).fetchone()
		cId = db.execute(text('select c.id from [dbo].[User] u, Customer c where u.mail = :email and c.userID = u.id'), {'email': email}).fetchone()
		db.execute(text('INSERT INTO Offer (productID, customerID, bid) VALUES (:pId, :cId, :price)'), {'pId': pId[0], 'cId': cId[0], 'price': price})
		db.commit()
		return redirect(url_for("login"))
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			return render_template("makeOffer.html")
		else:
			return redirect(url_for("login"))


@app.route("/publishAd", methods=["POST", "GET"])
def publishAd():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		productId = request.form["productId"]
		fiyat = request.form["fiyat"]
		prductIdList = db.execute(text('select p.id from [dbo].[User] u, Seller s, Product p where :email = u.mail and u.id = s.userID and s.id = p.sellerID'), {'email': email}).fetchall()
		sellerID = db.execute(text('select s.id from [dbo].[User] u, Seller s where :email = u.mail and u.id = s.userID'), {'email': email}).fetchone()
		db.execute(text("INSERT INTO Ad (price, productID, sellerID) VALUES (:price, :productID, :sellerID)"), {'price' : fiyat, 'productID' : productId, 'sellerID' : sellerID[0]})
		db.commit()
		return render_template("publishAd.html", prductIdList=prductIdList)
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			prductIdList = db.execute(text('select p.id from [dbo].[User] u, Seller s, Product p where :email = u.mail and u.id = s.userID and s.id = p.sellerID'), {'email': email}).fetchall()
			return render_template("publishAd.html", prductIdList=prductIdList)
		else:
			return redirect(url_for("login"))

@app.route("/updateOffer", methods=["POST", "GET"])
def updateOffer():
	if request.method == "POST":
		email = session["email"]
		password = session["password"]
		price = request.form["fiyat"]
		uOfferId = session['uOfferId']
		db.execute(text('update Offer set bid = :bid where id = :id'), {'bid': price, 'id': uOfferId})
		db.commit()
		return redirect(url_for("login"))
	else:
		if "email" in session:
			email = session["email"]
			password = session["password"]
			return render_template("updateOffer.html")
		else:
			return redirect(url_for("login"))

if __name__ == "__main__":
	app.run(debug=True)




