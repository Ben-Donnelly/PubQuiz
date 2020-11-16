from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from firebase import firebase

from wtforms import Form, IntegerField, DateField, PasswordField, StringField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)

@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/leaderboard")
def arts():
    user_result = firebase.get("/pubquiztracker/Users", "")
    user_d = {k : v['Name'] for k, v in enumerate(user_result.values())}


    score_result = firebase.get("/pubquiztracker/Scores", "")

    dates_set = set()
    scores_l = []
    for k in score_result:
        res = score_result[k]
        dates_set.add(res['Date'])
        scores_l.append(res['Score'])


    user_d = {k: v['Name'] for k, v in enumerate(user_result.values())}

    return render_template("leaderboard.html", headers=user_d, num_rows=len(dates_set), scores=scores_l)


class register_form(Form):
    name = StringField('Name', [validators.Length(min=2, max=25)])
    username = StringField('Username', [validators.Length(min=3, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=40)])
    password = PasswordField('Password', [
        validators.data_required(),
        validators.EqualTo('confirm', message='Passwords do not match.'),
        validators.length(min = 6)
    ])
    confirm = PasswordField('Confirm password')


@app.route("/register", methods = ["GET", "POST"])
def register():
    form = register_form(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        data = {
            "Name": name,
            "Email": email,
            "Username": username,
            "Password": password
        }

        firebase.post("/pubquiztracker/Users", data)

        flash("Registration successful!", 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#  Login

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #  Get form fields
        email = request.form['email']
        password_candidate = request.form['password']

        check_pass = ""
        username = ""
        result = firebase.get("/pubquiztracker/Users", "")
        for k, v in result.items():
            pot_user = v["Email"]
            if pot_user == email:
                username = v['Username']
                check_pass = v['Password']
                break

        if check_pass:

            if sha256_crypt.verify(password_candidate, check_pass):
                #  Passed
                session['logged_in'] = True
                session['username'] = username

                flash("You are now logged in!", 'success')
                return redirect(url_for('dashboard'))
            else:
                error_msg = "Invalid login"
                return render_template("login.html", error=error_msg)

        else:
            error_msg = "Email or password does not match"
            return render_template("login.html", error=error_msg)

    return render_template("login.html")

  # Check user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorised, please login", 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("You have been successfully logged out!", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@is_logged_in
def dashboard():
    return render_template("dashboard.html")



class ScoreForm(Form):
    score = IntegerField('Score', [validators.data_required(message="You need to enter your score as a number")])

    date = DateField('Date')


@app.route("/add/score", methods=['GET', 'POST'])
@is_logged_in
def add_score():
    form = ScoreForm(request.form)
    if request.method == "POST" and form.validate():
        print(request.form)
        score = request.form['score']
        date = request.form['date']
        data = {
            "Date": date,
            "Name": session["username"],
            "Score": score,
        }

        firebase.post("/pubquiztracker/Scores", data)


        flash("Score entered!", "success")

        return redirect(url_for("dashboard"))
    return render_template("add-score.html", form=form)

if __name__ == "__main__":
    app.secret_key = '>\xcdN\x9f\xcc\x0f<\xec\xb0x\x8em~\xc6\x16\xae~?&\xc2\x81\xa9\xa1&'
    app.run(debug=True)
