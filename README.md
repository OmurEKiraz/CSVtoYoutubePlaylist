# 🎵 YouTube Playlist CSV Importer

YouTube Playlist CSV Importer is a Python desktop app with a simple GUI that lets you import songs from a CSV file directly into a YouTube playlist. Perfect for transferring playlists from Spotify or other sources to YouTube!

### Works seamlessly with CSVs from the [Spotify Playlist to CSV](https://github.com/OmurEKiraz/SpotifyPlaylistToCSV) exporter 

## 🚀 Features

Enter YouTube Playlist ID directly 🎯

Select Client Secret JSON and CSV file via file dialogs 📂

Install dependencies directly from the app 🐍

Start import with a single button ▶️

Progress bar shows import progress in real time ⏱️

Log panel displays successes, errors, and skipped songs 📋

Remembers your last-used playlist, CSV, and client secret paths automatically 💾

## 🛠 Requirements

Python 3.7+ 🐍

Google Cloud account with YouTube Data API v3 enabled 🌐

client_secrets.json file from Google Cloud Console 🔑


## 🔑 Getting Your Client Secret

To use this app, you need a client_secrets.json file from Google Cloud Console. Follow these steps:

Go to Google Cloud Console.

Create a new project or select an existing one.

In the left menu, go to APIs & Services → Library.

Search for YouTube Data API v3 and click Enable.

Go to APIs & Services → Credentials.

Click Create Credentials → OAuth Client ID.

If prompted, configure the OAuth consent screen (choose External, fill in app name, email, etc., then save).

Choose Desktop app as the application type and give it a name.

Click Create, then Download JSON.

Save this file as client_secrets.json somewhere accessible and use the Select Client Secret button in the app to load it.

⚠️ Keep your client_secrets.json safe and do not share it publicly.

## ⚙️ How to Use


Double Click the ui.pyw file

Click Install Dependencies (first time only)

In the app window:

Enter your Playlist ID

Click Select Client Secret and choose your client_secrets.json

Click Select CSV File and choose your CSV

Click Start Import ▶️

During import:

- Log panel shows each added song, skipped items, and errors 📋

After import:

- Remaining songs (if any) can be retried in the next run 🔄

Failed or skipped songs are logged for review 📄

## 📂 CSV Format

The CSV should have the following structure:

#### Track Name,Artists
#### Song Example 1,Artist 1
#### Song Example 2,Artist 2

## 📌 Notes

Only publicly searchable songs on YouTube are added 🔍

Respect YouTube API limits (~60–70 songs per run with free quota) ⏱️

OAuth token expires if unused for 5–7 days; delete youtube_token.pickle if needed 🔄

App remembers your last-used playlist, CSV, and client secret paths automatically 💾

## 📜 License

This project is licensed under the MIT License 📝
