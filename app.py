from flask import Flask, render_template, flash, redirect, url_for, session, request
from firebase import firebase
from datetime import date as sys_date
from wtforms import Form, IntegerField, PasswordField, StringField, validators
from wtforms.fields.html5 import EmailField, DateField
from passlib.hash import sha256_crypt
from functools import wraps
from io import BytesIO
import matplotlib.pyplot as plt
from base64 import b64encode
from flask_cors import CORS
import matplotlib
from statistics import mean
matplotlib.use('Agg')

app = Flask(__name__)
app.config['SECRET_KEY'] = '>\xcdN\x9f\xcc\x0f<\xec\xb0x\x8em~\xc6\x16\xae~?&\xc2\x81\xa9\xa1&'
CORS(app)

firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)


@app.route('/')
def index():
	return render_template('home.html')


@app.route('/about')
def about():
	return render_template('about.html')


def get_required_data(parent_dir="Scores", user_name="", endpoint=""):
	return firebase.get(f"/pubquiztracker/{parent_dir}/{user_name}", endpoint)


@app.route("/leaderboard")
def leaderboard():
	score_result = get_required_data()

	scores_l = []
	m_rows = 0

	for k, v in score_result.items():
		# Makes list of lists of each users scores
		individual_user_scores = score_result[k]
		scores_l.append(individual_user_scores['Scores'])

		# If 1 person has done 10 quizzes but another only 1 | 2 | 3 | ... | 9
		# We still need 10 rows
		m_rows = max(m_rows, v['num_entries'])

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

	return render_template('register.html', form=form)


#  Login
def check_user():
	email = request.form['email']
	result = get_required_data(parent_dir="Users")
	for k, v in result.items():
		pot_user = v["Email"]
		if pot_user == email:
			return v['Username'], v['Password']


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
	curr_user = session['username']
	session.clear()
	flash(f"You have been successfully logged out!\nBye {curr_user}! 😥", "success")
	return redirect(url_for("login"))


@app.route("/dashboard")
@is_logged_in
def dashboard():
	return render_template("dashboard.html", curr_user=session['username'])


def get_scores_for_update(new_score, u_name):
	try:
		# Gets all scores list for current user
		u_list = get_required_data(user_name=u_name)['Scores']
		# Adds new score
		u_list.append(new_score)
	except TypeError:
		flash("Something went wrong, tell Ben and give him the values you put in for score and date!", "danger")
		return redirect(url_for("add_score"))

	return u_list


class ScoreForm(Form):
	score = IntegerField("Score", [validators.data_required(message="You need to enter your score as a number")])
	date = DateField("Date")


def update_user_average(scores_l):
	# Gets number of quizzes completed and computes the new average

	# The new score has already been added, saves call to db
	curr_num_of_scores = len(scores_l)
	new_average = round(mean(scores_l), 2)

	return [new_average, curr_num_of_scores]


@app.route("/add/score", methods=['GET', 'POST'])
@is_logged_in
def add_score():
	form = ScoreForm(request.form)

	if request.method == "POST" and form.validate():

		score = form.score.data
		date = form.date.data

		# If date in future, retry
		if date > sys_date.today():
			flash("Date cannot be in the future!", "danger")
			return redirect(url_for("add_score"))

		# Don't need else as redirects if > today's date
		new_score = get_scores_for_update(score, session["username"])

		# below gives: list: [new_average, new_num_entries]
		new_entries = update_user_average(new_score)
		data = {
			"Average": new_entries[0],
			"Scores": new_score,
			"num_entries": new_entries[1]
		}

		# Update the scores
		firebase.put("/pubquiztracker/Scores", session["username"], data)
		flash("Score entered!", "success")

		return redirect(url_for("dashboard"))
	return render_template("add-score.html", form=form)


def all_average():
	score_result = get_required_data()
	average_lis = [v['Average'] for v in score_result.values()]
	return average_lis


@app.route(f"/<string:curr_user>_stats")
@is_logged_in
def stats(curr_user):
	score_result = get_required_data(user_name=curr_user)

	custom_colours_dict = get_required_data(parent_dir="Colours")

	scores_l = score_result['Scores']

	average = round(mean(scores_l), 2)

	# Don't want to return e.g 20.0, but do want to return e.g 20.5
	# So if the value is x.0, then just cast to int
	if isinstance(average, int):
		average = int(average)

	best = max(scores_l)
	worst = min(scores_l)

	s_stats = [average, best, worst]

	return render_template('curUserStats.html', scores_l=scores_l, colour=custom_colours_dict[curr_user],
						   curr_user=curr_user, score_stats=s_stats)


def pie_chart(graph_usernames, custom_colours, graph_scores):

	pie_img = BytesIO()

	fig1, ax1 = plt.subplots()

	# pie chart
	ax1.pie(graph_scores, labels=graph_usernames, startangle=90, colors=custom_colours)
	# Equal aspect ratio ensures that pie is drawn as a circle.
	ax1.axis('equal')

	plt.savefig(pie_img, format='png')
	plt.close()
	pie_img.seek(0)
	pie_url = b64encode(pie_img.getvalue()).decode('utf8')

	return pie_url


def barh_chart(graph_usernames, custom_colours, graph_scores):
	barh_img = BytesIO()

	# Horizontal bar chart
	plt.barh(graph_usernames, graph_scores, color=custom_colours)
	plt.savefig(barh_img, format='png')
	plt.close()
	barh_img.seek(0)

	return b64encode(barh_img.getvalue()).decode('utf8')


def barv_chart(graph_usernames, score_result):

	# Name plus average score
	labels = list(f"{i} ({score_result[i]['Average']})" for i in graph_usernames)

	# Gets the average score for each user
	all_avg_lis = all_average()
	avg_of_avg = round(mean(all_avg_lis), 2)

	return [labels, all_avg_lis, avg_of_avg]


def overall_avgs_chart(graph_usernames, score_result):
	x = 0
	dict_of_each_players_scores = {}

	for i in graph_usernames:
		# Needed for the x axis of graph
		x = max(x, score_result[i]['num_entries'])

		dict_of_each_players_scores[i] = score_result[i]['Scores']

	x = [f"{i + 1}" for i in range(x)]
	return dict_of_each_players_scores, x


@app.route(f"/overall/stats")
def overall_stats():
	# Data for the overall stats page
	score_result = get_required_data()
	usernames = list(score_result.keys())

	custom_colours_dict = get_required_data(parent_dir="Colours")
	cust_colours = list(custom_colours_dict[i] for i in custom_colours_dict)

	average_of_averages = round(mean([score_result[usernames[i]]['Average'] for i in range(len(usernames))]), 2)

	# Gets total scores for each user
	graph_scores = list(sum(i['Scores']) for i in score_result.values())

	# 0: Individual Average Scores with Names, 1: Just The Scores, 3: Average of Averages
	avg_with_names, avg_scores, avg_of_avg = barv_chart(usernames, score_result)

	line_img = overall_avgs_chart(usernames, score_result)

	line_graph_dict = {"score_dict": line_img[0], "x_axis": line_img[1]}

	return render_template('overallStats.html', b_avg_with_names=avg_with_names, b_avg_scores=avg_scores,
						   b_avg_of_avg=avg_of_avg, average_of_averages=average_of_averages, max=max(graph_scores),
						   labels=usernames, values=graph_scores, line_graph_dict=line_graph_dict, colours=cust_colours,
						   col_dict=custom_colours_dict)


@app.route('/<string:variable>/', methods=['POST'])
def get_js(variable):
	js_variable = variable
	firebase.put(f"/pubquiztracker/Colours", session['username'], f"#{js_variable}")
	flash("Score entered!", "success")
	return redirect(url_for("register"))


if __name__ == "__main__":
	app.run(debug=True)
