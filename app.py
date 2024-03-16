from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
	cover = {'title': 'Melody Mix', 'url': ''}
	playlist = [{'name': 'fffff', 'artist': 'Anyone', 'url': ''}, 
			 {'name': 'ggggg', 'artist': 'Anyone', 'url': ''},]
	return render_template("playlist.html", cover=cover, playlist=playlist)
	# return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
	return render_template('login.html')

@app.route('/query', methods=['POST'])
def query():
	return render_template('query.html')

if __name__ == '__main__':
	app.run(debug=True)