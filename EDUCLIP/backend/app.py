import os
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import pickle
import requests
from pytube import YouTube
from transformers import pipeline
# from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
# CORS(app)



# Load trained Random Forest model and vectorizer
try:
    with open("model.pkl", "rb") as f:
        vectorizer, model = pickle.load(f)
except FileNotFoundError:
    print("Error: model.pkl file not found in 'backend' directory.")
    exit(1)

# API and Model Configurations
YOUTUBE_API_KEY = "YOUTUBE_API_KEY"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
DETAILS_URL = "https://www.googleapis.com/youtube/v3/videos"
genai.configure(api_key="genai.configure api_key")

RAPIDAPI_KEY = ""  # Replace with your RapidAPI key
RAPIDAPI_HOST = "microsoft-translator-text.p.rapidapi.com"  # API 


# Helper Functions
def get_video_id(youtube_url):
    """Extract video ID from YouTube URL."""
    if "youtube.com" in youtube_url:
        return youtube_url.split("v=")[-1].split("&")[0]
    elif "youtu.be" in youtube_url:
        return youtube_url.split("/")[-1]
    return None

def fetch_captions(video_id):
    """Fetch captions using YouTube Transcript API."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript])
        return full_text
    except Exception as e:
        raise Exception(f"Error fetching captions: {str(e)}")


def summarize_text(text):
    """Send the text to Google Gemini API for summarization."""
    try:
        model = genai.GenerativeModel("gemini-1.0-pro")
        response = model.generate_content(f"Summarize the following text:\n{text}")
        return response.text
    except Exception as e:
        raise Exception(f"Error summarizing text: {str(e)}")

def fetch_videos(query, page_token=None, max_results=10):
    """Fetch videos from YouTube API."""
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "pageToken": page_token,
    }
    response = requests.get(SEARCH_URL, params=params)
    return response.json() if response.status_code == 200 else {}

def fetch_video_details(video_ids):
    """Fetch detailed statistics for videos."""
    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }
    response = requests.get(DETAILS_URL, params=params)
    return response.json().get("items", []) if response.status_code == 200 else []

def translate_summary(text, target_language):
    """Translate text using Microsoft Translator API via RapidAPI."""
    url = "https://microsoft-translator-text.p.rapidapi.com/translate"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    querystring = {"to": target_language, "api-version": "3.0"}

    try:
        payload = [{"Text": text}]
        response = requests.post(url, headers=headers, params=querystring, json=payload)
        if response.status_code == 200:
            translation = response.json()
            translated_text = translation[0]["translations"][0]["text"]
            return translated_text
        else:
            raise Exception(f"Translation API Error: {response.status_code}, {response.text}")
    except Exception as e:
        raise Exception(f"Error during translation: {str(e)}")



# Flask Routes
@app.route("/")
def home():
    """Serve the homepage."""
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.json
        query = data.get("query")
        page_token = data.get("pageToken", None)

        if not query:
            return jsonify({"error": "Invalid input, 'query' key is required"}), 400

        # Fetch videos
        video_response = fetch_videos(query, page_token=page_token)
        videos = video_response.get("items", [])
        video_ids = [video['id']['videoId'] for video in videos]
        video_details = fetch_video_details(video_ids)

        results = []
        for video in video_details:
            title = video['snippet']['title'].lower()
            category_id = video['snippet'].get('categoryId', "")
            excluded_keywords = ["adult", "funny", "gaming", "music", "movie", "shorts", "entertainment"]
            excluded_categories = ["10", "20", "24"]

            if any(keyword in title for keyword in excluded_keywords) or category_id in excluded_categories:
                continue

            view_count = int(video['statistics'].get('viewCount', 0))
            if view_count < 50000:
                continue

            metadata = f"{video['snippet']['title']} {video['snippet']['description']}"
            vectorized_data = vectorizer.transform([metadata])
            prediction = model.predict(vectorized_data)

            if prediction[0] == 1:
                results.append({
                    "title": video['snippet']['title'],
                    "videoId": video['id'],
                    "channelName": video['snippet']['channelTitle'],
                    "channelLogo": video['snippet']['thumbnails']['default']['url'],
                })

        if not results:
            return jsonify({"error": "No educational content found for the search term."}), 400

        return jsonify({"results": results, "nextPageToken": video_response.get("nextPageToken")})
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



@app.route("/summarize", methods=["POST"])
def summarize():
    """Summarize captions of a YouTube video."""
    try:
        data = request.json
        video_url = data.get("videoLink")

        if not video_url:
            return jsonify({"error": "Please provide a valid YouTube video link."}), 400

        # Step 1: Extract video ID
        video_id = get_video_id(video_url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube video link."}), 400

        # Step 2: Fetch captions
        captions = fetch_captions(video_id)

        # Step 3: Summarize captions using Gemini API
        summary = summarize_text(captions)

        return jsonify({"summary": summary}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/translate", methods=["POST"])
def translate_summary_api():
    """Translate the summary into the selected language."""
    try:
        data = request.json
        summary = data.get("summary")
        target_language = data.get("language")

        if not summary or not target_language:
            return jsonify({"error": "Summary and target language are required."}), 400

        # Translate summary
        translated_text = translate_summary(summary, target_language)
        return jsonify({"translatedSummary": translated_text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)                                                                                                                              
