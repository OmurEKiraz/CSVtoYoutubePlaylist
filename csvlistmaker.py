# csvlistmaker.py
import os
import pickle
import time
import csv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ------------------------------
# CONFIGURATION
# ------------------------------
# Google API scopes for YouTube Data API
SCOPES = ["https://www.googleapis.com/auth/youtube"]

# Local files to cache data, remaining songs, and failed/skipped logs
CACHE_FILE = "existing_videos.pickle"
REMAINING_FILE = "remaining_songs.pickle"
LOG_FILE = "failed_or_skipped.csv"

# Import batching and delay settings to respect YouTube API limits
BATCH_SIZE = 50
SEARCH_DELAY = 1  # seconds between searches
INSERT_DELAY = 1  # seconds between insertions

# ------------------------------
# LOGGING HELPER
# ------------------------------
def log(msg, gui=None, color="green"):
    """
    Print messages to console and optionally to GUI log panel.
    """
    print(msg)
    if gui:
        gui.log(msg, color)

# ------------------------------
# GOOGLE AUTHENTICATION
# ------------------------------
def get_authenticated_service(client_secret_path, gui=None):
    """
    Authenticate with Google using OAuth2 and return a YouTube service object.
    """
    creds = None
    token_pickle = "youtube_token.pickle"
    if os.path.exists(token_pickle):
        with open(token_pickle, "rb") as token:
            creds = pickle.load(token)
            log("Loaded existing credentials.", gui)
    if not creds:
        log("Starting Google OAuth flow...", gui)
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=8080, open_browser=True)
        with open(token_pickle, "wb") as token:
            pickle.dump(creds, token)
        log("Google authentication successful!", gui)
    return build("youtube", "v3", credentials=creds)

# ------------------------------
# FETCH EXISTING PLAYLIST VIDEOS
# ------------------------------
def get_existing_video_titles(youtube, playlist_id, gui=None):
    """
    Retrieve existing video titles from a playlist and cache them locally.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            log("Cache found. Using local cached video list.", gui)
            return pickle.load(f)

    log("Cache not found. Fetching playlist from YouTube...", gui)
    titles = set()
    next_page = None
    while True:
        try:
            response = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page
            ).execute()
        except HttpError as e:
            status = e.resp.status
            reason = ""
            try:
                reason = e.error_details[0]['reason'] if hasattr(e, 'error_details') else ""
            except:
                reason = str(e)

            if status == 403 and "quotaExceeded" in reason:
                log("❌ Quota exceeded: YouTube API limit reached! Cannot fetch playlist.", gui, "red")
            else:
                log(f"❌ YouTube API error (HTTP {status}): {reason}", gui, "red")
            return titles  # return empty or partial list

        for item in response.get("items", []):
            titles.add(item["snippet"]["title"].lower())
        next_page = response.get("nextPageToken")
        if not next_page:
            break

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(titles, f)
    log(f"{len(titles)} existing videos cached.", gui)
    return titles

# ------------------------------
# ADD VIDEO TO PLAYLIST
# ------------------------------
def add_video(youtube, playlist_id, video_id, gui=None, retries=3):
    """
    Add a video to a playlist, with retries for transient errors.
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
            status = e.resp.status
            reason = ""
            try:
                reason = e.error_details[0]['reason'] if hasattr(e, 'error_details') else ""
            except:
                reason = str(e)

            if status == 403 and "quotaExceeded" in reason:
                log("❌ Quota exceeded: YouTube API limit reached! Cannot add more videos.", gui, "red")
                return False
            else:
                log(f"❌ YouTube API error adding video (HTTP {status}): {reason}", gui, "red")
                if attempt < retries - 1:
                    time.sleep(3)
                else:
                    return False

# ------------------------------
# READ CSV SONGS
# ------------------------------
def read_csv_songs(csv_file, gui=None):
    """
    Read songs from CSV and return as a list of dictionaries with query, track, and artist.
    """
    songs = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = f"{row['Track Name']} {row['Artists']}".lower()
            songs.append({"query": query, "track": row['Track Name'], "artist": row['Artists']})
    log(f"{len(songs)} songs loaded from CSV.", gui)
    return songs

# ------------------------------
# MAIN IMPORT FUNCTION
# ------------------------------
def import_csv_to_youtube(playlist_id, csv_file, client_secret_path, gui=None):
    """
    Main function: imports CSV songs into a YouTube playlist, handles caching, failures, and logging.
    """
    youtube = get_authenticated_service(client_secret_path, gui)
    existing_titles = get_existing_video_titles(youtube, playlist_id, gui)
    log(f"{len(existing_titles)} videos already exist.", gui)

    # Load remaining songs from previous run if available
    if os.path.exists(REMAINING_FILE):
        with open(REMAINING_FILE, "rb") as f:
            remaining_songs = pickle.load(f)
        log(f"{len(remaining_songs)} remaining songs loaded.", gui)
    else:
        remaining_songs = read_csv_songs(csv_file, gui)

    failed_log = []
    added_count = 0

    while remaining_songs:
        song = remaining_songs.pop(0)
        query = song["query"]

        # Skip if already in playlist
        if query in existing_titles:
            failed_log.append({**song, "Reason": "Already added"})
            continue

        try:
            # Search YouTube for video
            search_resp = youtube.search().list(
                q=query,
                part="id",
                type="video",
                maxResults=1
            ).execute()
            time.sleep(SEARCH_DELAY)

            if search_resp["items"]:
                video_id = search_resp["items"][0]["id"]["videoId"]
                if add_video(youtube, playlist_id, video_id, gui):
                    existing_titles.add(query)
                    added_count += 1
                    log(f"Added: {song['track']} - {song['artist']}", gui, "green")
                else:
                    failed_log.append({**song, "Reason": "Failed to add or quota hit"})
                time.sleep(INSERT_DELAY)
            else:
                log(f"Video not found: {song['track']} - {song['artist']}", gui, "orange")
                failed_log.append({**song, "Reason": "Not found"})

            # Batch pause
            if added_count % BATCH_SIZE == 0 and added_count > 0:
                log(f"{added_count} songs processed. Pausing briefly...", gui)
                time.sleep(5)

        except HttpError as e:
            status = e.resp.status
            reason = ""
            try:
                reason = e.error_details[0]['reason'] if hasattr(e, 'error_details') else ""
            except:
                reason = str(e)

            if status == 403 and "quotaExceeded" in reason:
                log("❌ Quota exceeded: YouTube API limit reached! Stopping import.", gui, "red")
                failed_log.append({**song, "Reason": "Quota exceeded"})
                remaining_songs.insert(0, song)
                break
            else:
                log(f"❌ YouTube API error (HTTP {status}): {reason}", gui, "red")
                failed_log.append({**song, "Reason": reason})
                with open(REMAINING_FILE, "wb") as f:
                    pickle.dump([song] + remaining_songs, f)
                break

    # Save failed/skipped songs
    if failed_log:
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["track", "artist", "Reason", "query"])
            writer.writeheader()
            for entry in failed_log:
                writer.writerow(entry)
        log(f"Failed/skipped songs logged: {LOG_FILE}", gui)

    # Save remaining songs for next run
    if remaining_songs:
        with open(REMAINING_FILE, "wb") as f:
            pickle.dump(remaining_songs, f)
        log(f"{len(remaining_songs)} songs saved for next run.", gui)

    log("Import complete!", gui)
