from functools import wraps
from flask import redirect, url_for, session, request
import spotipy
from dotenv import dotenv_values

env = dotenv_values(".env")

def auth_required(is_login=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
            auth_manager = spotipy.oauth2.SpotifyOAuth(
            client_id=env['SPOTIFY_CLIENT_ID'],
            client_secret=env['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=env['SPOTIFY_REDIRECT_URI'],
            scope='playlist-read-collaborative,playlist-modify-private,playlist-modify-public,playlist-read-private,ugc-image-upload',
            cache_handler=cache_handler,
            show_dialog=True
        )

            if is_login:
                if request.args.get("code"):
                    auth_manager.get_access_token(request.args.get("code"))
                    return redirect('/')

            if not auth_manager.validate_token(cache_handler.get_cached_token()):
                return redirect(url_for('login'))
            
            spotify = spotipy.Spotify(auth_manager=auth_manager)

            return func(spotify=spotify, *args, **kwargs)
        return wrapper
    return decorator