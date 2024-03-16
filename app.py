from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
	cover = {'title': 'Melody Mix', 'url': ''}
	playlist = [{'title': 'fffff', 'artist': 'Anyone', 'url': ''}, 
			 {'title': 'ggggg', 'artist': 'Anyone', 'url': ''},]
	# return render_template("playlist.html", cover=cover, playlist=playlist)
	return render_template("index.html")
if __name__ == '__main__':
	app.run(debug=True)