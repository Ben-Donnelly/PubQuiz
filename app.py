from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
#from data import articles
from flask_mysqldb import MySQL
from wtforms import Form, IntegerField, DateField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

#articles_var = articles()
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route("/leaderboard")
def arts():
    cur = mysql.connection.cursor()

    #  Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template("leaderboard.html", articles=articles)
    else:
        msg = "No articles found"
        return render_template("leaderboard.html", msg=msg)
    #  Close connection
    cur.close()


@app.route('/article/<string:id>/')
def article(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    return render_template('article.html', article=article)

class register_form(Form):
    # name = StringField('Name', [validators.Length(min=2, max=25)])
    # username = StringField('Username', [validators.Length(min=4, max=25)])
    # email = StringField('Email', [validators.Length(min=6, max=40)])
    password = PasswordField('Password', [
        validators.data_required(),
        validators.EqualTo('confirm', message='Passwords do not match.')
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

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) values(%s, %s, %s, %s)", (name, email, username, password))

        mysql.connection.commit()

        cur.close()

        flash("Registration successful!", 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)

#  Login

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #  Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #  Create cursor
        cur = mysql.connection.cursor()

        #  Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            #  Compare passwords

            if sha256_crypt.verify(password_candidate, password):
                #  Passed
                session['logged_in'] = True
                session['username'] = username

                flash("You are now logged in!", 'success')
                return redirect(url_for('dashboard'))
            else:
                error_msg = "Invalid login"
                return render_template("login.html", error=error_msg)

            #  Close connection

        else:
            cur.close()  # 16:13 in video (assume its meant to be in that else block before return)
            error_msg = "Username not found"
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
    #  Create cursor
    cur = mysql.connection.cursor()

    #  Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template("dashboard.html", articles=articles)
    else:
        msg = "No articles found"
        return render_template("dashboard.html", msg=msg)
    #  Close connection
    cur.close()


class ArticleForm(Form):
    score = IntegerField('Score', [validators.data_required(message="You need to enter your score as a number")])

    date = DateField('Date')


@app.route("/add_article", methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        print(request.form)
        score = request.form['score']
        date = request.form['date']
        #  Create cursor
        cur = mysql.connection.cursor()

        #  Execute

        cur.execute("INSERT INTO articles (title, author, body) VALUES (%s, %s, %s)", (score, session["username"], date))

        #  Commit
        mysql.connection.commit()

        #  Close
        cur.close()

        flash("Article created", "success")

        return redirect(url_for("dashboard"))
    return render_template("add_article.html", form=form)

#  Edit articles
@app.route("/edit_article/<string:id>", methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #  Create cursor
    cur = mysql.connection.cursor()

    #  Get article by ID

    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    #  Get form
    form = ArticleForm(request.form)

    #  Populate article form fields

    form.title.data = article['title']
    form.body.data = article["body"]

    if request.method == "POST" and form.validate():
        title = request.form['title']
        body = request.form['body']

        #  Create cursor
        cur = mysql.connection.cursor()

        #  Execute

        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title, body, id))

        #  Commit
        mysql.connection.commit()

        #  Close
        cur.close()

        flash("Article Updated", "success")

        return redirect(url_for("dashboard"))
    return render_template("edit_article.html", form=form)

# Delete articles
@app.route('/delete_article/<string:id>',  methods=['POST'])
@is_logged_in
def delete_article(id):
    #  Create cursor
    cur = mysql.connection.cursor()

    #  Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    #  Commit
    mysql.connection.commit()

    #  Close
    cur.close()

    flash("Article Deleted", "success")

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.secret_key = '>\xcdN\x9f\xcc\x0f<\xec\xb0x\x8em~\xc6\x16\xae~?&\xc2\x81\xa9\xa1&'
    app.run(debug=True)
