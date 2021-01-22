from flask import Flask, render_template, flash, redirect, url_for, session, request
from firebase import firebase
from datetime import date as sys_date
from wtforms import Form, IntegerField, PasswordField, StringField, validators, ValidationError
from wtforms.fields.html5 import EmailField, DateField
from passlib.hash import sha256_crypt
from functools import wraps
from io import BytesIO
import matplotlib.pyplot as plt
import base64
from flask_caching import Cache
import matplotlib
matplotlib.use('Agg')

# AWS WSGI looks for application by default
app = Flask(__name__)
app.config['SECRET_KEY'] = '>\xcdN\x9f\xcc\x0f<\xec\xb0x\x8em~\xc6\x16\xae~?&\xc2\x81\xa9\xa1&'

cache = Cache(app)

firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/leaderboard")
@cache.cached()
def leaderboard():
    score_result = firebase.get("/pubquiztracker/Scores", "")

    scores_l = []
    m_rows = 0

    for k, v in score_result.items():
        # Makes list of lists of each users scores
        individual_user_scores = score_result[k]
        scores_l.append(individual_user_scores['Scores'])

        # If 1 person has done 10 quizzes but another only 1 | 2 | 3 | ... | 9
        # We still need 10 rows
        m_rows = max(m_rows, len(v['Scores']))

    # Use of dictionary for better integrity
    user_d = {k: v for k, v in enumerate(list(score_result.keys()))}

    # For total scores row
    t_scores = [sum(i) for i in scores_l]

    return render_template("leaderboard.html", num_users=user_d, num_rows=m_rows, scores=scores_l, tot_scores=t_scores)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=2, max=25)])
    username = StringField('Username', [validators.Length(min=3, max=25)])
    email = EmailField('Email', [validators.Length(min=6, max=40)])
    password = PasswordField('Password', [
        validators.data_required(),
        validators.EqualTo('confirm', message='Passwords do not match.'),
        validators.length(min=4)
    ])
    confirm = PasswordField('Confirm password')


@app.route("/register", methods=["GET", "POST"])
def register():
    flash("This application was made for a small number of people and so no new users are able to register at this "
          "point. Please contact the site owner if you have any questions. This page is left in for "
          "demonstration purposes only", 'warning')
    form = RegisterForm(request.form)

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
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


#  Login
def check_user():
    email = request.form['email']
    result = firebase.get("/pubquiztracker/Users", "")
    for k, v in result.items():
        pot_user = v["Email"]
        if pot_user == email:
            return (v['Username'], v['Password'])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password_candidate = request.form['password']
        creds = check_user()
        if creds:
            username = creds[0]
            check_pass = creds[1]

            if sha256_crypt.verify(password_candidate, check_pass):
                #  Passed
                session['logged_in'] = True
                session['username'] = username
                session['email'] = request.form['email']

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
    return render_template("dashboard.html", curr_user=session['username'])


def get_scores_for_update(new_score, u_name):
    try:
        u_list = firebase.get(f"/pubquiztracker/Scores/{u_name}", "")['Scores']

        u_list.append(new_score)
    except TypeError:
        u_list = [new_score]

    return u_list


class ScoreForm(Form):
    score = IntegerField("Score", [validators.data_required(message="You need to enter your score as a number")])
    date = DateField("Date")


@app.route("/add/score", methods=['GET', 'POST'])
@is_logged_in
def add_score():
    form = ScoreForm(request.form)
    cache.clear()

    if request.method == "POST" and form.validate():
        print(request.form)
        score = request.form['score']
        date = form.date.data

        if date > sys_date.today():
            flash("Date cannot be in the future!", "danger")
            return redirect(url_for("add_score"))

        new_score = get_scores_for_update(int(score), session["username"])
        data = {
            "Scores": new_score
        }

        firebase.put("/pubquiztracker/Scores", session["username"], data)

        flash("Score entered!", "success")

        return redirect(url_for("dashboard"))
    return render_template("add-score.html", form=form)


@app.route("/update/scores")
@is_logged_in
@cache.cached()
def update_scores():
    flash("This page is currently being implemented, no functionality is available yet!", "info")

    score_result = firebase.get(f"/pubquiztracker/Scores/{session['username']}", "")

    scores_l = []
    for k in score_result:
        scores_l = score_result[k]

    values = len(scores_l)

    return render_template("updateScores.html", curr_user=session['username'], num_rows=values, scores=scores_l)


@app.route(f"/<string:curr_user>_stats")
@cache.cached()
@is_logged_in
def stats(curr_user):
    fig, ax = plt.subplots()

    score_result = firebase.get(f"/pubquiztracker/Scores/{curr_user}", "")

    scores_l = []
    for k in score_result:
        scores_l = score_result[k]

    img = BytesIO()
    len_scores = len(scores_l)
    x = [f"{i+1}" for i in range(len_scores)]

    average = sum(scores_l) / len_scores
    # Don't want to return e.g 20.0, but do want to return e.g 20.5
    # So if the value is x.0, then just cast to int
    if average.is_integer():
        average = int(average)

    best = max(scores_l)
    worst = min(scores_l)

    s_stats = [average, best, worst]

    plt.plot(x, scores_l, '--ko', label="Your scores")
    plt.hlines(y=average, xmin=0, xmax=len(scores_l)-1, label="Average")
    ax.set_xlabel('Week No.')

    plt.legend()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    return render_template('curUserStats.html', plot_url=plot_url, curr_user=session['username'], score_stats=s_stats)


@app.route(f"/overall/stats")
@is_logged_in
@cache.cached()
def overall_stats():
    score_result = firebase.get(f"/pubquiztracker/Scores", "")
    img = BytesIO()
    img1 = BytesIO()

    graph_usernames = list(score_result.keys())
    graph_scores = list(sum(i['Scores']) for i in score_result.values())

    fig1, ax1 = plt.subplots()
    ax1.pie(graph_scores, labels=graph_usernames, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    pie_url = base64.b64encode(img.getvalue()).decode('utf8')

    plt.barh(graph_usernames, graph_scores)
    plt.savefig(img1, format='png')
    plt.close()
    img.seek(0)
    bar_url = base64.b64encode(img1.getvalue()).decode('utf8')
    return render_template('overallStats.html', pie_url=pie_url, bar_url=bar_url)


if __name__ == "__main__":
    app.run(debug=True)
