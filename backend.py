from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

app = Flask(__name__)
app.secret_key = b'\x9c\x029#\x05\xf1\xf5\x00\xa6\x8a\xff\x15\xc4\xfa9O\x81C\x0ep\x17\x92\xd5O'

class register_form(Form):
    name = StringField('Name', [validators.data_required(), validators.Length(min=2, max=25)])
    email = StringField('Email', [validators.data_required(), validators.Length(min=6, max=40)])
    # password = PasswordField('Password', [
    #     validators.data_required(),
    #     validators.EqualTo('confirm', message='Passwords do not match.')
    # ])
    # confirm = PasswordField('Confirm password')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('PubQuizIndex.html')

@app.route('/register', methods=['GET', 'POST'])
def reg():
    form = register_form(request.form)
    # Test for now
    if request.method == 'POST' and form.validate():
        name = request.form['name']
        email = request.form['email']
        print(name, email)
        flash("Registration successful!", 'success')
        return redirect(url_for('index'))
    else:
        if form.errors:
            print("You've got errors!")
            flash('You have some errors')
            print(session['_flashes'])
    return render_template('PubQuizRegister.html')

if __name__ == '__main__':
    app.run(debug=True)
