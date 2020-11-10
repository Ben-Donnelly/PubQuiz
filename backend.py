from flask import Flask, render_template, request

app = Flask(__name__)
app.secret_key = ''

@app.route('/', methods=['GET', 'POST'])
def index():
    # Test for now
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        print(name, email)
    return render_template('PubQuizIndex.html')


if __name__ == '__main__':
    app.run(debug=True)
