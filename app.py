from flask import render_template, request, redirect, session, url_for, flash, g, send_from_directory, Flask
from forms import RegisterForm, LoginForm, DonorDetailsForm
from datetime import timedelta
import pyrebase
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.config['SECRET_KEY'] = "c6e803cd18a8c528c161eb9fcf013245248506ffb540ff70"
csrf = CSRFProtect(app)

firebaseConfig = {'apiKey': "AIzaSyAVuqBowMNrsbyKa6l7nGu3NgYmVrsDZsI",
                  'authDomain': "speculo-5e735.firebaseapp.com",
                  'projectId': "speculo-5e735",
                  'storageBucket': "speculo-5e735.appspot.com",
                  'messagingSenderId': "595206851375",
                  'appId': "1:595206851375:web:abea4b66bde0d218956fda",
                  'measurementId': "G-ZNK0DXHYEJ",
                  'databaseURL': "https://speculo-5e735-default-rtdb.asia-southeast1.firebasedatabase.app/"
                  }
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()


def get_individual_donor_list(email):
    email = email.replace("~", "@").replace("`", ".")
    c = 1
    res = list()
    data_file = db.child("Data").get()
    for details in data_file.each():
        if details.val()["Donor mail"] == email:
            res.append([details.val(), c])
            c += 1
    return res


def get_complete_donor_list():
    c = 1
    res = list()
    data_file = db.child("Data").get()
    for details in data_file.each():
        if details.val()["Distributor mail"] == "Not claimed":
            res.append([details.val(), details.key(), c])
            c += 1
    return res


def get_individual_distributor_list(email):
    email = email.replace("~", "@").replace("`", ".")
    c = 1
    res = list()
    data_file = db.child("Data").get()
    for details in data_file.each():
        if details.val()["Distributor mail"] == email:
            res.append([details.val(), c])
            c += 1
    return res


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'GET':
        if g.user is not None:
            return redirect(url_for('account_page'))
    message = ""
    sumessage = ""
    passerror = ""
    login_form = LoginForm()
    session.pop('logged_in', None)
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        try:
            auth.sign_in_with_email_and_password(email, password)
            session['email'] = email
            session['logged_in'] = True
            sumessage = "Successfully logged in"
            return redirect(url_for("account_page"))
        except:
            message = "Invalid email or password.Try again"
    return render_template("login.html", form=login_form, ermessage=message, sumessage=sumessage, pass_error=passerror)


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == 'GET':
        if g.user is not None:
            return redirect(url_for('account_page'))
    message = ""
    ermessage = ""
    register_form = RegisterForm()
    session.pop('logged_in', None)
    if register_form.validate_on_submit():
        try:
            email = register_form.email_address.data
            password = register_form.email_address.data
            category = register_form.radio_btn.data
            auth.create_user_with_email_and_password(email, password)
            session['logged_in'] = True
            session['email'] = email
            message = "Successfully Registered"
            username = email.replace("@", "~").replace(".", "`")
            db.child("Category").update({username: category})
            return redirect(url_for("account_page"))
        except Exception as e:
            ermessage = e
    return render_template("register.html", form=register_form, regermessage=ermessage, regmessage=message)


@app.route("/account", methods=["POST", "GET"])
def account_page():
    if g.user is None:
        return redirect(url_for('login'))
    category = None
    key_email = session["email"].replace("@", "~").replace(".", "`")
    data_file = db.child("Category").get()
    for details in data_file.each():
        if details.key() == key_email:
            category = details.val()
    donor_form = DonorDetailsForm()
    if request.method == "POST":
        if category == "Donor":
            if donor_form.validate_on_submit():
                info = dict()  # must include getting all the info and adding to the database
                info["Donor name"] = donor_form.name.data
                info["Location"] = donor_form.location.data
                info["Contact details"] = donor_form.contact.data
                info["Food details"] = donor_form.food.data
                info["Donor mail"] = session['email']
                info["Distributor mail"] = "Not claimed"
                db.child("Data").push(info)
        else:
            key = request.form["key"]
            db.child("Data").child(key).update({"Distributor mail": session['email']})
        return redirect(url_for('account_page'))

    if category == "Donor":
        l = get_individual_donor_list(session['email'])
        return render_template("donor.html",user=session['email'], data=l, form=donor_form)
    else:
        donor_list = get_complete_donor_list()
        distributor_list = get_individual_distributor_list(session['email'])
        return render_template("distributor.html", user=session['email'] ,donor_list=donor_list, distributor_list=distributor_list)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route("/reset-pass", methods=["POST", "GET"])
def reset_pass():
    if g.user is None:
        return redirect(url_for('login'))
    auth.send_password_reset_email(session['email'])
    return redirect(url_for('logout'))


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=3)
    g.user = None
    if 'logged_in' in session:
        g.user = session['logged_in']

if __name__ == "__main__":
    app.run()
