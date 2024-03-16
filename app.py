from flask import Flask, render_template, request, jsonify
import json
from ai import chat_session_id, client
from prompt import prompt_text, playlist_prompt
from spotipy import Spotify

app = Flask(__name__)

spotify: Spotify

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    input_text = request.form["input_text"]
    with client.connect(chat_session_id) as session:
        reply = session.query(
            prompt_text + input_text,
            timeout=60,
        )
        reply.content = reply.content.replace('\\', '')

    with client.connect(chat_session_id) as session:
        playlist_name_reply = session.query(
            playlist_prompt + input_text,
            timeout=60,
        )
        
        response = json.loads(reply.content)
        playlist_name = playlist_name_reply.content

        print(response)
        print(playlist_name)


        if "seed_artists" in response:
            seed_artists = response["seed_artists"]
            seed_artists = seed_artists.split(",")
            for i in range(len(seed_artists)):
                artist_id = spotify.search(q=seed_artists[i], type="artist")["artists"]["items"][0]["id"]
                seed_artists[i] = artist_id
            response["seed_artists"] = str(",".join(seed_artists))
        if "seed_tracks" in response:
            seed_tracks = response["seed_tracks"]
            seed_tracks = seed_tracks.split(",")
            for i in range(len(seed_tracks)):
                track_id = spotify.search(q=seed_tracks[i], type="track")["tracks"]["items"][0]["id"]
                seed_tracks[i] = track_id
            response["seed_tracks"] = str(",".join(seed_tracks))
        
        recommendations = spotify.recommendations(limit=50, **response)
        # id, name, artist, url (album image)
        songs = []
        for track in recommendations["tracks"]:
            song = {
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "url": track["images"][0]["url"]
            }
            songs.append(song)
        
        cover = {
            "title": playlist_name,
            "url": songs[0]["url"]
        }

        return render_template("playlist.html", playlist = songs, cover = cover)



if __name__ == '__main__':
    app.run(debug=True)