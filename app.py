from flask import Flask, render_template, request, jsonify
import requests
import base64
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
from dotenv import load_dotenv, dotenv_values
import os

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Spotify API credentials

CLIENT_ID = '52b7189ddc004efcbb47d974ec6c4ca2'
CLIENT_SECRET = '9ed6fbc80eec4ec687afeceb1062eb85'

# Function to obtain Spotify access token
def get_spotify_token(client_id, client_secret):
    client_credentials = f"{client_id}:{client_secret}"
    client_credentials_base64 = base64.b64encode(client_credentials.encode()).decode()

    token_url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': f'Basic {client_credentials_base64}'}
    data = {'grant_type': 'client_credentials'}

    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("Error obtaining Spotify access token")

# Function to fetch trending playlist data
def get_trending_playlist_data(playlist_id, access_token):
    sp = spotipy.Spotify(auth=access_token)
    music_data = []
    offset = 0
    limit = 50

    
    playlist_tracks = sp.playlist_tracks(playlist_id,offset = offset,limit = limit,fields='items(track(id, name, artists, album(id, name, release_date),external_urls))')
    while len(music_data) < limit:
        #playlist_tracks = sp.playlist_tracks(playlist_id, fields='items(track(id, name, artists, album(id, name, release_date),external_urls))')
        for track_info in playlist_tracks['items']:
            track = track_info['track']
            track_data = extract_track_data(track, sp)
            music_data.append(track_data)
        
    return pd.DataFrame(music_data)

# Helper function to extract track data
def extract_track_data(track, sp):
    track_name = track['name']
    artists = ', '.join([artist['name'] for artist in track['artists']])
    album_name = track['album']['name']
    album_id = track['album']['id']
    track_id = track['id']
    track_url = track['external_urls']['spotify']

    audio_features = sp.audio_features(track_id)[0] if track_id else None
    release_date, popularity = fetch_additional_track_info(track, sp, album_id, track_id)

    return {
        'Track Name': track_name,
        'Artists': artists,
        'Album Name': album_name,
        'Album ID': album_id,
        'Track ID': track_id,
        'Track URL': track_url,
        'Spotify Embed ID': track_url.split('/')[-1],  # Extract Spotify track ID
        'Popularity': popularity,
        'Release Date': release_date,
        'Danceability': audio_features['danceability'] if audio_features else None,
        'Energy': audio_features['energy'] if audio_features else None,
        'Loudness': audio_features['loudness'] if audio_features else None,
        'Valence': audio_features['valence'] if audio_features else None,
        'Tempo': audio_features['tempo'] if audio_features else None,
    }

# Function to fetch additional information about the track
def fetch_additional_track_info(track, sp, album_id, track_id):
    album_info = sp.album(album_id) if album_id else None
    release_date = album_info['release_date'] if album_info else None

    track_info = sp.track(track_id) if track_id else None
    popularity = track_info['popularity'] if track_info else None

    return release_date, popularity

# Function to normalize features
def normalize_features(df):
    scaler = MinMaxScaler()
    features = df[['Danceability', 'Energy', 'Loudness', 'Valence', 'Tempo']].values
    return scaler.fit_transform(features)

# Function for content-based recommendations
def content_based_recommendations(df, input_song_index, scaled_features, num_recommendations=5):
    similarity_scores = cosine_similarity([scaled_features[input_song_index]], scaled_features)
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]
    return df.iloc[similar_song_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Track URL','Track ID']]

# Routes
@app.route('/')
def song():
    access_token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)
    playlist_id = '5ABHKGoOzxkaa28ttQV9sE'
    global music_df
    music_df = get_trending_playlist_data(playlist_id, access_token)
    return render_template('songs.html', songs=music_df.to_dict(orient='records'))

@app.route('/recom')
def index():
    access_token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)
    playlist_id = '5ABHKGoOzxkaa28ttQV9sE'
    global music_df
    music_df = get_trending_playlist_data(playlist_id, access_token)
    global scaled_features
    scaled_features = normalize_features(music_df)
    return render_template('index.html', songs=music_df.to_dict(orient='records'))

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    print("Recieved data:",data)
    selected_song_index = int(request.json.get('song_index'))
    recommendations = content_based_recommendations(music_df, selected_song_index, scaled_features)
    return jsonify(recommendations.to_dict(orient='records'))


if __name__ == '__main__':
    app.run(debug=True)
