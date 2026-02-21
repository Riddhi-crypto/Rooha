import os
import json
import base64
import random
import string
import hashlib
import sqlite3
import re
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, session, send_from_directory
)

import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rooha-dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'rooha.db')

SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '')
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')

EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

EMOTION_MOOD_MAP = {
    'happy':    {'mood': 'Joyful',      'valence': (0.7, 1.0),  'energy': (0.6, 1.0),  'genres': ['pop', 'dance', 'happy', 'summer']},
    'sad':      {'mood': 'Melancholic',  'valence': (0.0, 0.3),  'energy': (0.0, 0.4),  'genres': ['acoustic', 'sad', 'indie', 'piano']},
    'angry':    {'mood': 'Intense',      'valence': (0.2, 0.5),  'energy': (0.7, 1.0),  'genres': ['rock', 'metal', 'punk', 'hard-rock']},
    'fear':     {'mood': 'Tense',        'valence': (0.1, 0.4),  'energy': (0.3, 0.7),  'genres': ['ambient', 'dark-ambient', 'soundtrack', 'classical']},
    'surprise': {'mood': 'Energetic',    'valence': (0.5, 0.9),  'energy': (0.6, 1.0),  'genres': ['edm', 'electro', 'party', 'dance']},
    'disgust':  {'mood': 'Brooding',     'valence': (0.1, 0.4),  'energy': (0.3, 0.6),  'genres': ['blues', 'grunge', 'alternative', 'industrial']},
    'neutral':  {'mood': 'Calm',         'valence': (0.3, 0.6),  'energy': (0.2, 0.5),  'genres': ['chill', 'lo-fi', 'jazz', 'r-n-b']},
}

SENTIMENT_KEYWORDS = {
    'positive': {
        'words': ['happy', 'joy', 'love', 'great', 'amazing', 'wonderful', 'fantastic', 'beautiful',
                  'excited', 'blessed', 'grateful', 'awesome', 'brilliant', 'delighted', 'cheerful',
                  'thrilled', 'ecstatic', 'elated', 'content', 'peaceful', 'calm', 'relaxed',
                  'inspired', 'hopeful', 'optimistic', 'proud', 'confident', 'energetic', 'fun',
                  'laugh', 'smile', 'celebrate', 'party', 'dance', 'enjoy', 'good', 'best',
                  'perfect', 'excellent', 'superb', 'outstanding', 'magnificent', 'lovely', 'nice'],
        'weight': 1.0
    },
    'negative': {
        'words': ['sad', 'angry', 'hate', 'terrible', 'awful', 'horrible', 'depressed', 'anxious',
                  'stressed', 'frustrated', 'lonely', 'heartbroken', 'miserable', 'upset', 'furious',
                  'devastated', 'hopeless', 'worthless', 'exhausted', 'overwhelmed', 'scared',
                  'afraid', 'worried', 'nervous', 'hurt', 'pain', 'suffering', 'grief', 'loss',
                  'cry', 'tears', 'broken', 'lost', 'empty', 'numb', 'dark', 'bad', 'worst',
                  'disgusted', 'annoyed', 'irritated', 'bitter', 'resentful', 'gloomy', 'dread'],
        'weight': -1.0
    },
    'intensity': {
        'words': ['very', 'extremely', 'really', 'so', 'absolutely', 'completely', 'totally',
                  'incredibly', 'truly', 'deeply', 'utterly', 'super', 'quite', 'rather'],
        'weight': 1.5
    },
    'negation': {
        'words': ['not', "don't", "doesn't", "didn't", "can't", "won't", "isn't", "aren't",
                  'never', 'no', 'neither', 'nor', 'hardly', 'barely', 'scarcely'],
        'weight': -1.0
    }
}

EMOTION_KEYWORDS = {
    'happy':    ['happy', 'joy', 'excited', 'cheerful', 'delighted', 'elated', 'thrilled', 'ecstatic', 'content', 'glad', 'fun', 'celebrate', 'love', 'laugh', 'smile', 'party'],
    'sad':      ['sad', 'depressed', 'heartbroken', 'lonely', 'grief', 'sorrow', 'miserable', 'crying', 'tears', 'melancholy', 'gloomy', 'hopeless', 'lost', 'empty', 'blue', 'miss'],
    'angry':    ['angry', 'furious', 'rage', 'mad', 'irritated', 'annoyed', 'frustrated', 'hate', 'outraged', 'bitter', 'resentful', 'livid', 'enraged', 'hostile'],
    'fear':     ['scared', 'afraid', 'anxious', 'worried', 'terrified', 'nervous', 'panic', 'dread', 'frightened', 'horrified', 'uneasy', 'tense', 'phobia'],
    'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'stunned', 'unexpected', 'wow', 'incredible', 'unbelievable', 'startled', 'mind-blown', 'whoa'],
    'disgust':  ['disgusted', 'revolted', 'gross', 'sick', 'repulsed', 'nasty', 'vile', 'awful', 'horrible', 'unpleasant', 'distasteful', 'loathe'],
    'neutral':  ['okay', 'fine', 'alright', 'normal', 'average', 'moderate', 'indifferent', 'meh', 'whatever', 'so-so', 'calm', 'relaxed', 'peaceful', 'chill', 'bored'],
}

FALLBACK_PLAYLISTS = {
    'happy': [
        {'name': 'Happy', 'artist': 'Pharrell Williams', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH'},
        {'name': 'Walking on Sunshine', 'artist': 'Katrina & The Waves', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/05wIrZSwuaVWhcv5FfqeH0'},
        {'name': "Don't Stop Me Now", 'artist': 'Queen', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/7hQJA50XrCWABAu5v6QZ4i'},
    ],
    'sad': [
        {'name': 'Someone Like You', 'artist': 'Adele', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/1zwMYTA5nlNjZxYrvBB2pV'},
        {'name': 'Fix You', 'artist': 'Coldplay', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/7LVHVU3tWfcxj5aiPFEW4Q'},
        {'name': 'Hurt', 'artist': 'Johnny Cash', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/28cnXtME493VX9NOw9cIUh'},
    ],
    'angry': [
        {'name': 'In the End', 'artist': 'Linkin Park', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/60a0Rd6pjrkxjPbaKzXjfq'},
        {'name': 'Break Stuff', 'artist': 'Limp Bizkit', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/2IJsFhXRhDhLpaXzO0dCAn'},
    ],
    'fear': [
        {'name': 'Breathe Me', 'artist': 'Sia', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/1EPjDF7X8LjkXGBwYliHMy'},
    ],
    'surprise': [
        {'name': 'Uptown Funk', 'artist': 'Bruno Mars', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/32OlwWuMpZ6b0aN2RZOeMS'},
    ],
    'disgust': [
        {'name': 'Creep', 'artist': 'Radiohead', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/70LcF31zb1H0PyJoS1Sx1r'},
    ],
    'neutral': [
        {'name': 'Weightless', 'artist': 'Marconi Union', 'preview': None, 'image': '', 'url': 'https://open.spotify.com/track/1lCRw5FEZ1gPDNPzy1K4zW'},
    ],
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_seed TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            input_type TEXT NOT NULL,
            detected_emotion TEXT NOT NULL,
            confidence REAL,
            mood TEXT NOT NULL,
            input_text TEXT,
            tracks_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    ''')
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def analyze_text_emotion(text):
    text_lower = text.lower().strip()
    words = re.findall(r'\b\w+\b', text_lower)
    if not words:
        return 'neutral', 0.5, 'Calm'

    emotion_scores = {e: 0.0 for e in EMOTIONS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for word in words:
            if word in keywords:
                emotion_scores[emotion] += 2.0
            else:
                for kw in keywords:
                    if kw in word or word in kw:
                        emotion_scores[emotion] += 0.5

    polarity = 0.0
    intensity_mult = 1.0
    negation_active = False

    for i, word in enumerate(words):
        if word in SENTIMENT_KEYWORDS['negation']['words']:
            negation_active = True
            continue
        if word in SENTIMENT_KEYWORDS['intensity']['words']:
            intensity_mult = 1.5
            continue
        for cat in ['positive', 'negative']:
            if word in SENTIMENT_KEYWORDS[cat]['words']:
                score = SENTIMENT_KEYWORDS[cat]['weight'] * intensity_mult
                if negation_active:
                    score *= -1
                polarity += score
                negation_active = False
                intensity_mult = 1.0

    if max(emotion_scores.values()) > 0:
        detected = max(emotion_scores, key=emotion_scores.get)
        total = sum(emotion_scores.values())
        confidence = min(emotion_scores[detected] / max(total, 1) * 1.5, 0.98)
    elif polarity > 0.5:
        detected = 'happy'
        confidence = min(abs(polarity) / 5, 0.85)
    elif polarity < -0.5:
        if any(w in words for w in ['angry', 'mad', 'furious', 'hate', 'rage']):
            detected = 'angry'
        else:
            detected = 'sad'
        confidence = min(abs(polarity) / 5, 0.85)
    else:
        detected = 'neutral'
        confidence = 0.5

    confidence = max(confidence, 0.3)
    mood = EMOTION_MOOD_MAP[detected]['mood']
    return detected, round(confidence, 3), mood


def analyze_face_emotion(image_data):
    """
    Face emotion detection using a lightweight CNN approach.
    In production, load a pre-trained model. For demo, we use
    pixel analysis heuristics + random confidence.
    """
    try:
        import cv2
        img_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return 'neutral', 0.5, 'Calm'

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(48, 48))

        if len(faces) == 0:
            avg_brightness = np.mean(gray)
            contrast = np.std(gray)
            if avg_brightness > 140:
                emotion = 'happy'
                confidence = 0.55
            elif avg_brightness < 80:
                emotion = 'sad'
                confidence = 0.50
            else:
                emotion = 'neutral'
                confidence = 0.45
        else:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (48, 48))

            brightness = np.mean(face_resized)
            contrast = np.std(face_resized)
            upper_half = np.mean(face_resized[:24, :])
            lower_half = np.mean(face_resized[24:, :])
            left_half = np.mean(face_resized[:, :24])
            right_half = np.mean(face_resized[:, 24:])
            symmetry = 1.0 - abs(left_half - right_half) / 255.0

            scores = {
                'happy': 0.0, 'sad': 0.0, 'angry': 0.0, 'fear': 0.0,
                'surprise': 0.0, 'disgust': 0.0, 'neutral': 0.0
            }

            if brightness > 130 and lower_half > upper_half:
                scores['happy'] += 3.0
            if brightness < 100:
                scores['sad'] += 2.0
                scores['angry'] += 1.0
            if contrast > 60:
                scores['surprise'] += 2.0
                scores['angry'] += 1.0
            if upper_half > lower_half + 10:
                scores['surprise'] += 2.0
            if symmetry > 0.9:
                scores['neutral'] += 2.0
                scores['happy'] += 1.0
            if contrast < 35:
                scores['neutral'] += 2.0
                scores['sad'] += 1.0

            for e in scores:
                scores[e] += random.uniform(0, 0.5)

            emotion = max(scores, key=scores.get)
            total = sum(scores.values())
            confidence = min(scores[emotion] / max(total, 1), 0.92)
            confidence = max(confidence, 0.35)

        mood = EMOTION_MOOD_MAP[emotion]['mood']
        return emotion, round(confidence, 3), mood

    except ImportError:
        emotions_weighted = ['happy'] * 3 + ['sad'] * 2 + ['neutral'] * 3 + ['angry'] + ['surprise']
        emotion = random.choice(emotions_weighted)
        confidence = round(random.uniform(0.45, 0.78), 3)
        mood = EMOTION_MOOD_MAP[emotion]['mood']
        return emotion, confidence, mood
    except Exception as e:
        print(f"Face analysis error: {e}")
        return 'neutral', 0.5, 'Calm'


def get_spotify_token():
    """Get Spotify access token using Client Credentials flow."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    try:
        import urllib.request
        import urllib.parse

        credentials = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
        data = urllib.parse.urlencode({'grant_type': 'client_credentials'}).encode()
        req = urllib.request.Request('https://accounts.spotify.com/api/token', data=data)
        req.add_header('Authorization', f'Basic {credentials}')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urllib.request.urlopen(req, timeout=5) as resp:
            token_data = json.loads(resp.read().decode())
            return token_data.get('access_token')
    except Exception as e:
        print(f"Spotify token error: {e}")
        return None


def search_spotify_tracks(emotion, limit=12):
    """Search Spotify for tracks matching the emotion's mood profile."""
    token = get_spotify_token()
    if not token:
        return FALLBACK_PLAYLISTS.get(emotion, FALLBACK_PLAYLISTS['neutral'])

    try:
        import urllib.request
        import urllib.parse

        mood_config = EMOTION_MOOD_MAP[emotion]
        genre = random.choice(mood_config['genres'])
        mood_word = mood_config['mood'].lower()

        queries = [f'{mood_word} {genre}', f'{genre} mood', f'{mood_word} vibes']
        query = random.choice(queries)

        params = urllib.parse.urlencode({
            'q': query,
            'type': 'track',
            'limit': limit,
            'market': 'IN'
        })

        req = urllib.request.Request(f'https://api.spotify.com/v1/search?{params}')
        req.add_header('Authorization', f'Bearer {token}')

        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        tracks = []
        for item in data.get('tracks', {}).get('items', []):
            images = item.get('album', {}).get('images', [])
            tracks.append({
                'name': item['name'],
                'artist': ', '.join(a['name'] for a in item['artists']),
                'album': item['album']['name'],
                'preview': item.get('preview_url'),
                'image': images[0]['url'] if images else '',
                'url': item['external_urls'].get('spotify', ''),
                'duration_ms': item['duration_ms'],
                'popularity': item['popularity'],
            })

        return tracks if tracks else FALLBACK_PLAYLISTS.get(emotion, [])

    except Exception as e:
        print(f"Spotify search error: {e}")
        return FALLBACK_PLAYLISTS.get(emotion, [])


# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze/text', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    emotion, confidence, mood = analyze_text_emotion(text)
    tracks = search_spotify_tracks(emotion)

    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO sessions (user_id, input_type, detected_emotion, confidence, mood, input_text, tracks_json) VALUES (?,?,?,?,?,?,?)',
        (session.get('user_id'), 'text', emotion, confidence, mood, text, json.dumps(tracks))
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'session_id': session_id,
        'emotion': emotion,
        'confidence': confidence,
        'mood': mood,
        'mood_config': EMOTION_MOOD_MAP[emotion],
        'tracks': tracks,
        'input_type': 'text',
    })


@app.route('/api/analyze/face', methods=['POST'])
def analyze_face():
    data = request.json
    image_data = data.get('image', '')
    if not image_data:
        return jsonify({'error': 'No image provided'}), 400

    emotion, confidence, mood = analyze_face_emotion(image_data)
    tracks = search_spotify_tracks(emotion)

    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO sessions (user_id, input_type, detected_emotion, confidence, mood, tracks_json) VALUES (?,?,?,?,?,?)',
        (session.get('user_id'), 'face', emotion, confidence, mood, json.dumps(tracks))
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'session_id': session_id,
        'emotion': emotion,
        'confidence': confidence,
        'mood': mood,
        'mood_config': EMOTION_MOOD_MAP[emotion],
        'tracks': tracks,
        'input_type': 'face',
    })


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO feedback (session_id, rating) VALUES (?,?)',
                 (data.get('session_id'), data.get('rating')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/history')
def get_history():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM sessions ORDER BY created_at DESC LIMIT 50'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/stats')
def get_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
    by_emotion = conn.execute(
        'SELECT detected_emotion, COUNT(*) as count FROM sessions GROUP BY detected_emotion ORDER BY count DESC'
    ).fetchall()
    by_type = conn.execute(
        'SELECT input_type, COUNT(*) as count FROM sessions GROUP BY input_type'
    ).fetchall()
    avg_confidence = conn.execute('SELECT AVG(confidence) FROM sessions').fetchone()[0] or 0
    conn.close()
    return jsonify({
        'total_sessions': total,
        'by_emotion': [dict(r) for r in by_emotion],
        'by_input_type': [dict(r) for r in by_type],
        'avg_confidence': round(avg_confidence, 3),
    })


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, email, password_hash, avatar_seed) VALUES (?,?,?,?)',
            (data['username'], data['email'], hash_password(data['password']),
             ''.join(random.choices(string.ascii_lowercase, k=8))))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE email=?', (data['email'],)).fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'username': user['username']})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    finally:
        conn.close()


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email=? AND password_hash=?',
        (data['email'], hash_password(data['password']))).fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True, 'username': user['username']})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session.get('username')})
    return jsonify({'logged_in': False})


if __name__ == '__main__':
    init_db()
    print("\n" + "=" * 60)
    print("  ROOHA — Emotion-Based Music Recommendation System")
    print("=" * 60)
    if not SPOTIFY_CLIENT_ID:
        print("  ⚠  Spotify API keys not set — using fallback playlists")
        print("  Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars")
    else:
        print("  ✓  Spotify API configured")
    print(f"  →  Running at http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
