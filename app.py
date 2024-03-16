import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, session, request
from flask_session import Session
import spotipy
from dotenv import dotenv_values

env = dotenv_values(".env")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
        auth_manager = spotipy_oauth(cache_handler)

        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect('/login')
        
        spotify = spotipy.Spotify(auth_manager=auth_manager)

        return func(spotify=spotify, *args, **kwargs)
    return wrapper


@app.route("/")
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


@app.route('/login')
def login():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy_oauth(cache_handler)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')
    
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect(auth_manager.get_authorize_url())
    
    return redirect('/')


@app.route('/callback')
def callback():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy_oauth(cache_handler)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')
    
    return "Error: No code provided."


def spotipy_oauth(cache_handler: spotipy.cache_handler.CacheHandler):
    return spotipy.oauth2.SpotifyOAuth(
        client_id=env['SPOTIFY_CLIENT_ID'],
        client_secret=env['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=env['SPOTIFY_REDIRECT_URI'],
        scope='playlist-read-collaborative,playlist-modify-private,playlist-modify-public,playlist-read-private,ugc-image-upload',
        cache_handler=cache_handler,
        show_dialog=True
    )

def is_logged_in():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy_oauth(cache_handler)
    return auth_manager.validate_token(cache_handler.get_cached_token())

if __name__ == '__main__':
	app.run(debug=True)