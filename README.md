# 📄 CSV List Maker

csvlistmaker.py is a Python utility that reads a CSV file containing tracks and artists, tracks existing videos in a YouTube playlist, and prepares the playlist for importing new songs. This tool is ideal for transferring playlists from Spotify or other sources to YouTube. 🎵➡️📺

### [CSV files from the Spotify Playlist to CSV exporter](https://github.com/OmurEKiraz/SpotifyPlaylistToCSV) would work fine

## 🚀 Features

Reads CSV files with Track Name and Artists columns 🎶

Tracks videos already present in the playlist to avoid duplicates ✅

Retries automatically if a video insertion fails 🔁

Logs failed or skipped songs for review 📋

Supports batch processing and delays to comply with YouTube API limits ⏱️

## 🛠 Requirements

Python 3.7+ 🐍

Google Cloud Console account with YouTube Data API enabled 🌐

client_secrets.json file from Google Cloud Console 🔑

Python packages: google-auth-oauthlib, google-api-python-client

## ⚙️ Setup

Enable YouTube Data API on Google Cloud:

Access Google Cloud Console

Create a new project or use an existing one

Enable YouTube Data API v3

Create OAuth 2.0 Client IDs

Download client_secrets.json and place it in the same folder as csvlistmaker.py 📂

Install Python dependencies:

Install google-auth-oauthlib and google-api-python-client using pip

Prepare CSV file:

Name the CSV file my_playlists.csv (or another name, then update CSV_FILE in the script)

Include the columns: Track Name, Artists

Configure the script:

Set PLAYLIST_ID to the target YouTube playlist ID 🎯

Optionally adjust caching, batch, and delay settings (CACHE_FILE, BATCH_SIZE, SEARCH_DELAY, INSERT_DELAY)

## ▶️ Usage

Run the script using Python.

On the first run:

A browser window opens to authorize access to your Google account 🌐

OAuth credentials are saved in youtube_token.pickle for future runs 🔒

The script performs the following:

Reads all songs from the CSV

Checks which videos already exist in the playlist (using cache) ✅

Searches YouTube and adds new videos ➕

Logs any failed or skipped songs in failed_or_skipped.csv 📋

Saves remaining songs for subsequent runs in remaining_songs.pickle 💾

Because of the google APIs free quota limit you can add maximum of 60 to 70 song in one run for free

## 📂 CSV Format

The CSV should have the following structure:

Track Name | Artists
Song Example 1 | Artist 1
Song Example 2 | Artist 2


## 📌 Notes

Works only for publicly searchable songs on YouTube 🔍

Cache avoids duplicates and reduces API calls 💾

Adjust delays and batch size to manage YouTube quota limits ⏱️

Failed entries are logged for review and easy retry 🔄

📜 License

This project is licensed under the MIT License 📝
