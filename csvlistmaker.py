# YouTube CSV Importer
# This script reads a CSV of songs (from Spotify or elsewhere)
# and adds them to a YouTube playlist. It uses OAuth for authentication
# and keeps track of already added videos using cache files.


import csv
import os
import pickle
import time

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# -----------------------------
# OAuth and API configuration
# -----------------------------
# Scopes define permissions the app has
SCOPES = ["https://www.googleapis.com/auth/youtube"]

# File path to your Google API client secrets JSON
CLIENT_SECRETS_FILE = "client_secrets.json"

# Token file to store OAuth credentials
TOKEN_PICKLE = "youtube_token.pickle"

# -----------------------------
# Playlist and CSV configuration
# -----------------------------
# Fill in your target YouTube playlist ID here
PLAYLIST_ID = ""  # e.g., 'PLRuQPcnVAn9Tj1RkmL2wJ9fv0vftW7rt4'

# CSV file containing songs to upload
CSV_FILE = "my_playlists.csv"

# Files for caching and logging
CACHE_FILE = "existing_videos.pickle"
REMAINING_FILE = "remaining_songs.pickle"
LOG_FILE = "failed_or_skipped.csv"

# Batch and delay settings
BATCH_SIZE = 50       # Number of videos processed before short delay
SEARCH_DELAY = 1      # Delay between YouTube search requests (seconds)
INSERT_DELAY = 1      # Delay between adding videos (seconds)

# -----------------------------
# YouTube OAuth Authentication
# -----------------------------
def get_authenticated_service():
    """
    Authenticate and return a YouTube service object.
    Uses OAuth2 and stores credentials in a pickle file.
    """
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

# -----------------------------
# Retrieve existing videos from the playlist
# -----------------------------
def get_existing_video_titles(youtube, playlist_id):
    """
    Returns a set of all video titles already in the playlist.
    Uses cache if available to reduce API calls.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            print("Cache found, using local cache.")
            return pickle.load(f)

    print("Cache not found, fetching playlist from YouTube...")
    titles = set()
    next_page = None
    while True:
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page
        ).execute()
        for item in response.get("items", []):
            titles.add(item["snippet"]["title"].lower())
        next_page = response.get("nextPageToken")
        if not next_page:
            break

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(titles, f)
    return titles

# -----------------------------
# Add a video to the playlist with retry support
# -----------------------------
def add_video(youtube, playlist_id, video_id, retries=3):
    """
    Attempts to add a video to the playlist, retrying if it fails.
    Returns True if successful, False otherwise.
    """
    for attempt in range(retries):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            ).execute()
            return True
        except HttpError as e:
            print(f"Error adding video: {e}")
            if attempt < retries - 1:
                time.sleep(3)
            else:
                return False

# -----------------------------
# Read songs from CSV
# -----------------------------
def read_csv_songs(csv_file):
    """
    Reads a CSV of songs and returns a list of dictionaries
    with track name, artist, and search query.
    """
    songs = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = f"{row['Track Name']} {row['Artists']}".lower()
            songs.append({"query": query, "track": row['Track Name'], "artist": row['Artists']})
    return songs

# -----------------------------
# Main import process
# -----------------------------
def import_csv_to_youtube(youtube, playlist_id):
    """
    Imports all songs from the CSV to the YouTube playlist.
    Handles caching, failed logs, and retrying failed additions.
    """
    existing_titles = get_existing_video_titles(youtube, playlist_id)
    print(f"{len(existing_titles)} videos already exist in the playlist.")

    # Load remaining songs from previous run if available
    if os.path.exists(REMAINING_FILE):
        with open(REMAINING_FILE, "rb") as f:
            remaining_songs = pickle.load(f)
        print(f"Resuming upload of {len(remaining_songs)} songs...")
    else:
        remaining_songs = read_csv_songs(CSV_FILE)

    failed_log = []
    added_count = 0

    while remaining_songs:
        song = remaining_songs.pop(0)
        query = song["query"]

        if query in existing_titles:
            failed_log.append({**song, "Reason": "Already added"})
            continue

        try:
            # Search YouTube
            search_resp = youtube.search().list(
                q=query,
                part="id",
                type="video",
                maxResults=1
            ).execute()
            time.sleep(SEARCH_DELAY)

            if search_resp["items"]:
                video_id = search_resp["items"][0]["id"]["videoId"]
                if add_video(youtube, playlist_id, video_id):
                    existing_titles.add(query)
                    added_count += 1
                    print(f"Added: {song['track']} - {song['artist']}")
                else:
                    failed_log.append({**song, "Reason": "Failed to add"})
                time.sleep(INSERT_DELAY)
            else:
                print(f"Video not found: {song['track']} - {song['artist']}")
                failed_log.append({**song, "Reason": "Not found"})

            # Short batch delay
            if added_count % BATCH_SIZE == 0 and added_count > 0:
                print(f"{added_count} songs processed, taking a short break...")
                time.sleep(5)

        except HttpError as e:
            print(f"An error occurred: {e}")
            failed_log.append({**song, "Reason": str(e)})
            # Save remaining songs to pickle for retry
            with open(REMAINING_FILE, "wb") as f:
                pickle.dump([song] + remaining_songs, f)
            break  # Stop if quota or other error occurs

    # Save failed or skipped songs to log CSV
    if failed_log:
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["track", "artist", "Reason", "query"])
            writer.writeheader()
            for entry in failed_log:
                writer.writerow(entry)
        print(f"Failed or skipped songs logged in {LOG_FILE}")

    # Save remaining songs for next run
    if remaining_songs:
        with open(REMAINING_FILE, "wb") as f:
            pickle.dump(remaining_songs, f)
        print(f"{len(remaining_songs)} songs saved for next run.")

# -----------------------------
# Program entry point
# -----------------------------
if __name__ == "__main__":
    youtube = get_authenticated_service()
    import_csv_to_youtube(youtube, PLAYLIST_ID)
    print("All songs have been processed!")
