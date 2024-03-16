import os
import json
from functools import wraps
from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_session import Session
import spotipy
from dotenv import dotenv_values
from ai import chat_session_id, client
from prompt import prompt_text, playlist_prompt, available_genres

env = dotenv_values(".env")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

user_reccomendations = {}


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
    # print(get_user_token())
	# cover = {'title': 'Melody Mix', 'url': ''}
	# playlist = [{'name': 'fffff', 'artist': 'Anyone', 'url': ''}, 
	# 		 {'name': 'ggggg', 'artist': 'Anyone', 'url': ''},]
	# return render_template("playlist.html", cover=cover, playlist=playlist, spotify_url="")
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
    
    flash("You are already logged in.")
    return redirect('/')


@app.route('/logout')
def logout():
    session.pop('token_info', None)
    flash("You have successfully logged out.")
    return redirect('/')


@app.route('/callback')
def callback():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy_oauth(cache_handler)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        flash("You have successfully logged in.")
        return redirect('/')
    
    return "Error: No code provided."


def spotipy_oauth(cache_handler: spotipy.cache_handler.CacheHandler):
    return spotipy.oauth2.SpotifyOAuth(
        client_id=env['SPOTIFY_CLIENT_ID'],
        client_secret=env['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=env['SPOTIFY_REDIRECT_URI'],
        scope='user-top-read,playlist-read-collaborative,playlist-modify-private,playlist-modify-public,playlist-read-private,ugc-image-upload',
        cache_handler=cache_handler,
        show_dialog=True
    )

@app.template_test()
def is_logged_in():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy_oauth(cache_handler)
    return not auth_manager.validate_token(cache_handler.get_cached_token())


def get_user_token():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    return cache_handler.get_cached_token()


@app.route("/generate", methods=["POST"])
@auth_required
def query(spotify: spotipy.Spotify):
    input_text = request.form["input_text"]
    history_value = int(request.form["history"]) // 50
    print("History: ", history_value)
    # return ""
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
        print(reply.content)
        start_i = reply.content.find('{')
        end_i = reply.content.rfind('}')
        response = json.loads(reply.content[start_i:end_i+1])
        playlist_name = playlist_name_reply.content

    # print(response)
    print(playlist_name)


    if "seed_artists" in response:
        seed_artists = response["seed_artists"]
        seed_artists = seed_artists.split(", ")
        for i in range(len(seed_artists)):
            artist_id = spotify.search(q=seed_artists[i], type="artist")["artists"]["items"][0]["id"]
            seed_artists[i] = artist_id
        response["seed_artists"] = seed_artists
    if "seed_tracks" in response:
        seed_tracks = response["seed_tracks"]
        seed_tracks = seed_tracks.split(", ")
        for i in range(len(seed_tracks)):
            track_id = spotify.search(q=seed_tracks[i], type="track")["tracks"]["items"][0]["id"]
            seed_tracks[i] = track_id
        response["seed_tracks"] = seed_tracks
    if "seed_genres" in response:
        seed_genres = response["seed_genres"]
        seed_genres = seed_genres.split(", ")
        # filter out invalid genres
        seed_genres = [genre for genre in seed_genres if genre in available_genres]
        response["seed_genres"] = seed_genres
        
    top_artists = spotify.current_user_top_artists(limit=2*history_value)
    
    top_artists_ids = [artist["id"] for artist in top_artists["items"]]

    if "seed_artists" in response:
        response["seed_artists"] = response["seed_artists"] + top_artists_ids[: 4 - len(response["seed_artists"])]
    else:
        response["seed_artists"] = top_artists_ids[:4]

    print(response)

    genre_n = len(response["seed_genres"])
    artist_n = len(response["seed_artists"]) if 'seed_artists' in response else 0
    track_n = len(response["seed_tracks"]) if 'seed_tracks' in response else 0

    # to limit the number of seeds to 5
    if genre_n + artist_n + track_n > 5:
        k = genre_n + artist_n + track_n - 5
        if genre_n - k < 1:
            response["seed_genres"] = response["seed_genres"][:1]
        else:
            response["seed_genres"] = response["seed_genres"][:genre_n - k]
    if genre_n + artist_n + track_n > 5 and 'seed_artists' in response:
        k = genre_n + artist_n + track_n - 5
        if artist_n - k < 1:
            response["seed_artists"] = response["seed_artists"][:1]
        else:
            response["seed_artists"] = response["seed_artists"][:artist_n - k]
    if genre_n + artist_n + track_n > 5 and 'seed_tracks' in response:
        k = genre_n + artist_n + track_n - 5
        if track_n - k < 1:
            response["seed_tracks"] = response["seed_tracks"][:1]
        else:
            response["seed_tracks"] = response["seed_tracks"][:track_n - k]
    
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

    user_token = get_user_token()["access_token"]
    user_reccomendations[user_token] = {
        "title": playlist_name,
        "songs": songs
    }

    return render_template("playlist.html", playlist = songs, cover = cover, spotify_url="")


@app.route("/save")
@auth_required
def save(spotify: spotipy.Spotify):
    user_token = get_user_token()["access_token"]
    if user_token not in user_reccomendations:
        return redirect("/")
    playlist = user_reccomendations[user_token]
    playlist_name = playlist["title"]
    songs = playlist["songs"]
    playlist_id = spotify.user_playlist_create(
        user=spotify.me()["id"],
        name=playlist_name,
        public=False
    )["id"]
    song_ids = [song["id"] for song in songs]
    spotify.playlist_add_items(playlist_id, song_ids)
    cover = {
        "title": playlist_name,
        "url": spotify.playlist_cover_image(playlist_id)[0]["url"]
    }
    spotify_url = f"https://open.spotify.com/playlist/{playlist_id}"
    return render_template("playlist.html", playlist = songs, cover = cover, spotify_url=spotify_url)


app.jinja_env.globals.update(is_logged_in=is_logged_in)

if __name__ == '__main__':
    app.run(debug=True)