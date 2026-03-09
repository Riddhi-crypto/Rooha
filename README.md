# 🎵 Rooha — AI-Powered Emotion-Based Music Recommendation

> *Rooha (रूह) means "soul" in Hindi/Urdu — because music touches the soul.*

Rooha is an intelligent web application that detects your emotional state through **facial expressions** or **written text**, then curates a personalised playlist from **Spotify** that matches exactly how you feel.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red?logo=opencv)
![Spotify](https://img.shields.io/badge/Spotify-API-1DB954?logo=spotify)

---

## ✨ Features

### Dual-Input Emotion Detection
- **📸 Facial Expression Analysis** — Real-time webcam capture → Haar Cascade face detection → CNN-based emotion classification across 7 categories
- **✏️ Text Sentiment Analysis** — Custom NLP engine with keyword matching, polarity scoring, intensity detection, and negation handling

### Spotify-Powered Music
- Detected emotions are mapped to **mood profiles** (valence + energy ranges + genre seeds)
- Live queries to **Spotify Web API** return real tracks with artwork, previews, and direct play links
- Fallback playlist system when API keys are not configured

### Full-Stack Application
- 🎨 Immersive dark UI with glassmorphism, ambient mood-reactive backgrounds, and fluid animations
- 👤 User authentication (register/login) with session persistence
- 📊 History tracking — view all past emotion detection sessions
- 📱 Fully responsive — works on desktop, tablet, and mobile

---

## 🏗️ Architecture

```
User Input ──→ Emotion Detection ──→ Mood Translation ──→ Spotify Query ──→ Playlist
   │                  │                     │                   │              │
   ├─ Camera     ├─ Face Pipeline      ├─ Emotion→Mood     ├─ Genre      ├─ 12 tracks
   └─ Text       │  (OpenCV+CNN)       │  Lookup Table     │  Seeds      ├─ Artwork
                  └─ Text Pipeline      └─ Valence+Energy   └─ Web API   └─ Previews
                     (NLP Engine)          Ranges
```

### Emotion → Mood → Genre Mapping

| Emotion   | Mood        | Genres                        |
|-----------|-------------|-------------------------------|
| 😊 Happy   | Joyful      | pop, dance, happy, summer     |
| 😢 Sad     | Melancholic | acoustic, sad, indie, piano   |
| 😤 Angry   | Intense     | rock, metal, punk, hard-rock  |
| 😰 Fear    | Tense       | ambient, soundtrack, classical|
| 😲 Surprise| Energetic   | edm, electro, party, dance   |
| 🤢 Disgust | Brooding    | blues, grunge, alternative   |
| 😐 Neutral | Calm        | chill, lo-fi, jazz, r-n-b    |

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.8+
- Spotify Developer Account (optional but recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rooha.git
cd rooha

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up Spotify API keys
cp .env.example .env
# Edit .env with your Spotify Client ID and Secret
```

### Get Spotify API Keys

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy the **Client ID** and **Client Secret**
4. Add `http://localhost:5000/callback` as a Redirect URI
5. Set them as environment variables or in `.env` file

### Run

```bash
# Set environment variables (or use .env file)
export SPOTIFY_CLIENT_ID=your_client_id
export SPOTIFY_CLIENT_SECRET=your_client_secret

# Start the server
python app.py
```

Open **http://localhost:5000** in your browser.

> **Note:** The app works without Spotify keys too — it will use fallback playlists instead of live Spotify results.

---

## 📁 Project Structure

```
rooha/
├── app.py                      # Flask backend + API routes
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore
├── README.md
├── database/
│   └── rooha.db               # SQLite database (auto-created)
├── templates/
│   └── index.html              # Main HTML template (SPA)
└── static/
    ├── css/
    │   └── style.css           # Complete stylesheet
    └── js/
        └── app.js              # Frontend JavaScript (SPA logic)
```

---

## 🔌 API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | `/`                   | Serve the main application               |
| POST   | `/api/analyze/text`   | Analyze text input for emotion           |
| POST   | `/api/analyze/face`   | Analyze facial image for emotion         |
| POST   | `/api/feedback`       | Submit feedback on recommendation        |
| GET    | `/api/history`        | Get detection history                    |
| GET    | `/api/stats`          | Get aggregate statistics                 |
| POST   | `/api/auth/register`  | Create new user account                  |
| POST   | `/api/auth/login`     | User login                               |
| POST   | `/api/auth/logout`    | User logout                              |
| GET    | `/api/auth/status`    | Check authentication status              |

---

## 🧠 Technical Details

### Text Sentiment Engine (Custom NLP)
- **Keyword matching** — 50+ emotion-specific keywords per category
- **Polarity scoring** — Positive/negative word weights with aggregation
- **Intensity modifiers** — "very", "extremely", "really" amplify scores by 1.5x
- **Negation handling** — "not happy" correctly flips polarity
- **Multi-category output** — Scores across all 7 emotions, selects highest

### Face Emotion Pipeline
- **Haar Cascade** detector for face localization
- **48×48 grayscale** normalization
- Feature extraction (brightness, contrast, symmetry, region analysis)
- **7-class classification** with confidence scoring

### Spotify Integration
- **Client Credentials** OAuth2 flow (no user login required)
- Mood-to-genre seed mapping with randomized queries for variety
- Returns track name, artist, album, artwork, preview URL, Spotify link
- Automatic fallback to curated playlists if API is unavailable

---

## 🛠️ Tech Stack

| Layer           | Technology                    |
|-----------------|-------------------------------|
| Backend         | Python 3.10 + Flask 3.0       |
| Face Detection  | OpenCV 4.9 + Haar Cascades    |
| NLP Engine      | Custom sentiment analyzer     |
| Music API       | Spotify Web API (Spotipy)     |
| Database        | SQLite with WAL mode          |
| Frontend        | HTML5 + CSS3 + Vanilla JS     |
| UI Design       | Glassmorphism + Dark Theme    |
| Typography      | Playfair Display + Outfit     |
| Icons           | Google Material Icons         |

---
## Output Screenshots
<img width="1908" height="896" alt="Screenshot 2026-03-09 210146" src="https://github.com/user-attachments/assets/736a508a-660a-4420-8914-c030d3950b3f" />

<img width="1908" height="896" alt="Screenshot 2026-03-09 210146" src="https://github.com/user-attachments/assets<img width="1899" height="873" alt="Screenshot 2026-03-09 210202" src="https://github.com/user-attachments/assets/4bd453fc-5fdf-4655-8ab2-329b3fbc529b" />
/95<img width="1912" height="801" alt="Screenshot 2026-03-09 210232" src="https://github.com/user-attachments/assets/24fc3a41-8058-44e7-8572-b2576181e7dd" />
e2da00-1d8b-4bed-<img width="1900" height="899" alt="Screenshot 2026-03-09 210302" src="https://github.com/user-attachments/assets/6a9c9586-c283-4aa5-875a-f29fcb00b9c9" />
9df1-176d<img width="1914" height="910" alt="Screenshot 2026-03-09 210454" src="https://github.com/user-attachments/assets/b2d022a4-64d5-4f2c-889e-8c9f610891c7" />
420aec6b" />

## 🔮 Future Enhancements

- [ ] Pre-trained CNN model (FER2013) for higher facial accuracy
- [ ] Transformer-based text emotion classifier (BERT/RoBERTa)
- [ ] User preference learning (collaborative filtering)
- [ ] Physiological signal integration (wearables)
- [ ] Multi-language text support
- [ ] Playlist saving to user's Spotify account

---

## 📄 License



---

built by Riddhi Sahu
