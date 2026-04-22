# Soundtrack Generator - Lyria

A simple Python web application that takes a video file as input, analyses the scenes using Gemini Vision AI, and generates a matching music soundtrack using Google's Lyria 3 Pro API.

## Prerequisites
- Python 3.10 or higher

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the environment variables:**
   - Get a Gemini API key from [Google AI Studio](https://aistudio.google.com).
   - Copy `.env.example` to `.env`.
   - Add your `GEMINI_API_KEY` to the `.env` file.

4. **Run the app:**
   ```bash
   python app.py
   ```

## How it Works
1. **Frame Extraction**: The app extracts frames from your uploaded video at set intervals.
2. **Scene Analysis**: Gemini Vision AI (Gemini 2.0 Flash) analyzes each frame to describe the mood, setting, and energy.
3. **Soundtrack Synthesis**: The individual scene descriptions are summarized into a cohesive music prompt.
4. **Music Generation**: Google's Lyria 3 Pro generates an instrumental soundtrack based on the prompt.
5. **Video Merging**: The generated audio is merged with the original video using MoviePy.
6. **Download**: You can preview and download the final video with the custom soundtrack.
