from flask import Flask, render_template, flash, redirect, url_for, session, request
from firebase import firebase
from wtforms import Form, IntegerField, DateField, PasswordField, StringField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from flask_caching import Cache

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 3600
}

app = Flask(__name__)
app.config.from_mapping(config)
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
def arts():
    user_result = firebase.get("/pubquiztracker/Users", "")

    score_result = firebase.get("/pubquiztracker/Scores", "")

    scores_l = []
    for k in score_result:
        res = score_result[k]
        scores_l.append(res['Scores'])

    # print(scores_l)
    values = list(k['Scores'] for k in score_result.values())
    values = (max(map(len, values)))
    user_d = {k: v['Name'] for k, v in enumerate(user_result.values())}
    # print(f"num_users: {user_d}\nnum_rows: {values}\nscores_l: {scores_l}")
    tot_scores = [sum(i) for i in scores_l]
    # print(tot_scores)
    return render_template("leaderboard.html", num_users=user_d, num_rows=values, scores=scores_l, tot_scores=tot_scores)


class register_form(Form):
    name = StringField('Name', [validators.Length(min=2, max=25)])
    username = StringField('Username', [validators.Length(min=3, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=40)])
    password = PasswordField('Password', [
        validators.data_required(),
        validators.EqualTo('confirm', message='Passwords do not match.'),
        validators.length(min=4)
    ])
    confirm = PasswordField('Confirm password')


@app.route("/register", methods=["GET", "POST"])
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

        firebase.put("/pubquiztracker/Users", username, data)

        flash("Registration successful!", 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


#  Login
def checkUser():
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
        creds = checkUser()
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


class ScoreForm(Form):
    score = IntegerField('Score', [validators.data_required(message="You need to enter your score as a number")])

    date = DateField('Date')


def getScoresForUpdate(newScore, uName):
    try:
        uList = firebase.get(f"/pubquiztracker/Scores/{uName}", "")['Scores']

        uList.append(newScore)
    except TypeError:
        uList = [newScore]

    return(uList)


@app.route("/add/score", methods=['GET', 'POST'])
@is_logged_in
def add_score():
    form = ScoreForm(request.form)

    cache.clear()

    if request.method == "POST" and form.validate():
        print(request.form)
        score = request.form['score']
        newScores = getScoresForUpdate(int(score), session["username"])
        data = {
            "Scores": newScores
        }
        firebase.put("/pubquiztracker/Scores", session["username"], data)

        flash("Score entered!", "success")

        return redirect(url_for("dashboard"))
    return render_template("add-score.html", form=form)

@app.route("/update/scores")
@is_logged_in
def update_scores():
    score_result = firebase.get(f"/pubquiztracker/Scores/{session['username']}", "")

    scores_l = []
    for k in score_result:
        scores_l = score_result[k]

    print(scores_l)
    values = len(scores_l)
    print(f"user: {session['username']}\nnum_rows: {values}\nscores_l: {scores_l}")

    return render_template("updateScores.html", curr_user=session['username'], num_rows=values, scores=scores_l)
    # return render_template("updateScores.html", curr_user=session['username'], num=getScoresForUpdate)

@app.route(f"/<string:curr_user>_stats")
@cache.cached()
@is_logged_in
def stats(curr_user):
    score_result = firebase.get(f"/pubquiztracker/Scores/{session['username']}", "")

    scores_l = []
    for k in score_result:
        scores_l = score_result[k]

    img = BytesIO()
    len_scores = len(scores_l)
    x = [f"Week: {i+1}" for i in range(len_scores)]

    average = sum(scores_l) / len_scores
    if average.is_integer():
        average = int(average)
    best = max(scores_l)
    worst = min(scores_l)

    score_stats = [average, best, worst]


    plt.plot(x, scores_l, '--ko', label="Your scores")
    plt.hlines(y=average, xmin=0, xmax=len(scores_l)-1, label="Average")
    # plt.legend(bbox_to_anchor=(1, 1), loc="center left", borderaxespad=0)
    plt.legend()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')


    return render_template('curUserStats.html', plot_url=plot_url, curr_user=session['username'], score_stats=score_stats)

@app.route(f"/overall/stats")
@is_logged_in
@cache.cached()
def overall_stats():
    score_result = firebase.get(f"/pubquiztracker/Scores", "")
    img = BytesIO()
    img1 = BytesIO()

    # Hacky (works so good enough for now), ****FIX LATER****
    x = list(score_result.keys())
    y = list(sum(i['Scores']) for i in score_result.values())

    print(x)
    print(y)

    data = dict(zip(x, y))

    labels = list(data.keys())
    sizes = list(data.values())

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.


    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    pie_url = base64.b64encode(img.getvalue()).decode('utf8')

    plt.barh(x, y)
    plt.savefig(img1, format='png')
    plt.close()
    img.seek(0)
    bar_url = base64.b64encode(img1.getvalue()).decode('utf8')
    return render_template('overallStats.html', pie_url=pie_url, bar_url=bar_url)

# with app.test_request_context():
#     print(url_for('overall_stats'))
if __name__ == "__main__":
    app.secret_key = '>\xcdN\x9f\xcc\x0f<\xec\xb0x\x8em~\xc6\x16\xae~?&\xc2\x81\xa9\xa1&'
    app.run(debug=True)
