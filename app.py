from flask import Flask, render_template, flash, redirect, url_for, session, request
from firebase import firebase
from datetime import date as sys_date
from wtforms import Form, IntegerField, PasswordField, StringField, validators
from wtforms.fields import EmailField, DateField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_cors import CORS
from statistics import mean
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '>\xcdN\x9f\xcc\x0f<\xec\xb0x\x8em~\xc6\x16\xae~?&\xc2\x81\xa9\xa1&'
CORS(app)

firebase = firebase.FirebaseApplication("https://pubquiztracker.firebaseio.com/", None)
current_year = str(datetime.today().year)


@app.route('/')
def index():
	return render_template('home.html')


@app.route('/about')
def about():
	return render_template('about.html')


def get_required_data(parent_dir="Scores", user_name="", endpoint="", year=""):
	return firebase.get(f"/pubquiztracker/{year}/{parent_dir}/{user_name}", endpoint)


@app.route("/leaderboard")
def leaderboard():
	score_result = get_required_data(year=current_year)

	scores_list = []
	min_number_needed_rows = 0

	for k, v in score_result.items():
		# Makes list of lists of each users scores
		individual_user_scores = score_result[k]
		scores_list.append(individual_user_scores['Scores'])

		# If 1 person has done 10 quizzes but another only 9 we still need 10 rows
		min_number_needed_rows = max(min_number_needed_rows, v['num_entries'])

	# Use of dictionary for better integrity
	user_d = {k: v for k, v in enumerate(list(score_result.keys()))}

	# For total scores row
	t_scores = [sum(i) for i in scores_list]

	return render_template("leaderboards/leaderboard_2022.html", current_year=current_year, num_users=user_d, num_rows=min_number_needed_rows, scores=scores_list, tot_scores=t_scores)


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
	user_email = request.form['email']
	user_db_call_result = get_required_data(parent_dir="Users", year=current_year)
	# Todo: make this better
	for user, user_data in user_db_call_result.items():
		candidate_user = user_data["Email"]
		if candidate_user == user_email:
			return user_data['Username'], user_data['Password']


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		password_candidate = request.form['password']
		credentials = check_user()
		if credentials:
			username = credentials[0]
			password_to_check = credentials[1]

			if sha256_crypt.verify(password_candidate, password_to_check):
				#  Passed
				session['logged_in'] = True
				session['username'] = username

				flash("You are now logged in!", 'success')
				return redirect(url_for('dashboard'))
			else:
				error_msg = "Invalid login, please check your username and password"
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
def dashboard(message=None):
	if message:
		flash(message, 'success')
	return render_template("dashboard.html")


def get_scores_for_update(new_score, u_name):
	try:
		# Gets all scores list for current user
		user_list = get_required_data(year=current_year, user_name=u_name)['Scores']
		# Adds new score
		user_list.append(new_score)
	except TypeError:
		flash("Something went wrong, tell Ben and give him the values you put in for score and date!", "danger")
		return redirect(url_for("add_score"))

	return user_list


class ScoreForm(Form):
	score = IntegerField("Score", [validators.data_required(message="You need to enter your score as a number")])
	date = DateField("Date")

def update_user_average(scores_list):
	# Gets number of quizzes completed and computes the new average

	# The new score has already been added, saves call to db
	current_num_of_scores = len(scores_list)
	new_average = round(mean(scores_list), 2)

	return [new_average, current_num_of_scores]


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
		firebase.put(f"/pubquiztracker/{current_year}/Scores", session["username"], data)
		flash("Score entered!", "success")

		return redirect(url_for("dashboard"))
	return render_template("add-score.html", form=form)


def all_average():
	score_result = get_required_data(year=current_year)
	average_lis = [v['Average'] for v in score_result.values()]
	return average_lis


@app.route(f"/<string:curr_user>/statistics")
@is_logged_in
def stats(curr_user):
	score_result = get_required_data(year=current_year, user_name=curr_user)
	last_year_results = get_required_data(year=str(int(current_year)-1), user_name=curr_user)

	custom_colours_dict = get_required_data(parent_dir="Colours")

	scores_list = score_result['Scores']
	last_year_scores_to_use = last_year_results['Scores'][:len(scores_list)]

	player_average = round(mean(scores_list), 2)

	# Don't want to return e.g 20.0, but do want to return e.g 20.5
	# So if the value is x.0, then just cast to int
	if isinstance(player_average, int):
		player_average = int(player_average)

	best = max(scores_list)
	worst = min(scores_list)

	s_stats = [player_average, best, worst]

	return render_template('curUserStats.html', scores_list=scores_list, colour=custom_colours_dict[curr_user],
						   curr_user=curr_user, score_stats=s_stats, last_year_scores_to_use=last_year_scores_to_use)

def barv_chart(graph_usernames, score_result):

	# Name plus average score
	labels = list(f"{i} ({score_result[i]['Average']})" for i in graph_usernames)

	# Gets the average score for each user
	all_averages_list = all_average()
	average_of_average = round(mean(all_averages_list), 2)

	return [labels, all_averages_list, average_of_average]


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
	score_result = get_required_data(year=current_year)
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

@app.route("/alter/score", methods=["GET", "POST"])
def alter_scores():
	if request.method == "POST":
		return craig_function_delete_score()

	if request.method == "GET":
		curr_user = session['username']
		score_result = get_required_data(year=current_year, user_name=curr_user)

		score_to_delete = score_result['Scores'][-1]

		return render_template("alterScore.html", num_rows=1, curr_user=curr_user, score_to_delete=score_to_delete)

def craig_function(user_JSON):
	user_JSON_updated = user_JSON
	user_JSON_updated['Scores'] = user_JSON['Scores'][:-1]
	user_JSON_updated['Average'] =  round(mean(user_JSON['Scores']), 2)
	user_JSON_updated['num_entries'] = len(user_JSON['Scores'])

	return user_JSON_updated

def craig_function_delete_score():
	user_JSON = get_required_data(year=current_year, user_name=session['username'])
	user_JSON_updated = craig_function(user_JSON)


	firebase.put(f"/pubquiztracker/{current_year}/Scores", session["username"], user_JSON_updated)

	# firebase.put(f"/pubquiztracker/{current_year}/Scores", session['username'], result)
	return dashboard("Score deleted!")

if __name__ == "__main__":
	app.run(debug=True)
