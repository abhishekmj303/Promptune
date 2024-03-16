import os
import json
from functools import wraps
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from flask_session import Session
import spotipy
from dotenv import dotenv_values
from ai import chat_session_id, client
from prompt import prompt_text, playlist_prompt, available_genres
from playlist_image import create_image

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
	# cover = {'title': 'Melody Mix', 'url': ''}
	# playlist = [{'name': 'fffff', 'artist': 'Anyone', 'url': ''}, 
	# 		 {'name': 'ggggg', 'artist': 'Anyone', 'url': ''},]
	# return render_template("playlist.html", cover=cover, playlist=playlist)
	return render_template("index.html")


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


@app.route("/query", methods=["POST"])
@auth_required
def query(spotify: spotipy.Spotify):
    input_text = request.form["input_text"]
    with client.connect(chat_session_id) as session:
        reply = session.query(
            prompt_text + input_text,
            timeout=60,
        )
        
        playlist_name_reply = session.query(
            playlist_prompt + input_text,
            timeout=60,
        )
        
        reply.content = reply.content.replace('\\', '')
        response = json.loads(reply.content)
        playlist_response = playlist_name_reply.content

    print(response)
    # print(playlist_name)
    print(playlist_response)

    # plalist_name has the playlist name and colors seperated by commas
    playlist_response = playlist_response.split(", ")
    playlist_name = playlist_response[0]
    colors = playlist_response[1:]

    print(playlist_name)
    print(colors)
    create_image(colors, playlist_name)



    if "seed_artists" in response:
        seed_artists = response["seed_artists"]
        seed_artists = seed_artists.split(",")
        for i in range(len(seed_artists)):
            artist_id = spotify.search(q=seed_artists[i], type="artist")["artists"]["items"][0]["id"]
            seed_artists[i] = artist_id
        response["seed_artists"] = seed_artists
    if "seed_tracks" in response:
        seed_tracks = response["seed_tracks"]
        seed_tracks = seed_tracks.split(",")
        for i in range(len(seed_tracks)):
            track_id = spotify.search(q=seed_tracks[i], type="track")["tracks"]["items"][0]["id"]
            seed_tracks[i] = track_id
        response["seed_tracks"] = seed_tracks
    if "seed_genres" in response:
        seed_genres = response["seed_genres"]
        seed_genres = seed_genres.split(",")
        # filter out invalid genres
        seed_genres = [genre for genre in seed_genres if genre in available_genres]
        response["seed_genres"] = seed_genres

    print(response)
    
    recommendations = spotify.recommendations(limit=50, **response)
    # id, name, artist, url (album image)
    songs = []
    for track in recommendations["tracks"]:
        song = {
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "url": track["album"]["images"][0]["url"]
        }
        songs.append(song)
    
    cover = {
        "title": playlist_name,
        "url": songs[0]["url"]
    }

    return render_template("playlist.html", playlist = songs, cover = cover)


if __name__ == '__main__':
    app.run(debug=True)