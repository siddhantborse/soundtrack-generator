import os
import cv2
import shutil
import base64
import gradio as gr
from PIL import Image
from dotenv import load_dotenv
from google import genai
from moviepy.editor import VideoFileClip, AudioFileClip, afx

# STEP 1 — Load the API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    client = None
else:
    client = genai.Client(api_key=api_key)

# STEP 2 — Frame extractor function
def extract_frames(video_path, interval_seconds=5):
    """Extracts frames from a video at a specified interval."""
    if not os.path.exists("temp_frames"):
        os.makedirs("temp_frames")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    frame_paths = []
    current_seconds = 0
    while current_seconds < duration:
        frame_id = int(current_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_path = f"temp_frames/frame_{current_seconds}.jpg"
        cv2.imwrite(frame_path, frame)
        frame_paths.append(frame_path)
        current_seconds += interval_seconds
        
    cap.release()
    return frame_paths, duration

# STEP 3 — Scene analyser function
def analyse_video_scenes(frame_paths):
    """Analyses video frames using Gemini to generate a music prompt."""
    descriptions = []
    prompt_single = "Analyse this video frame and return a short music description for it. Focus on: mood (calm/tense/joyful/melancholic/energetic/dramatic), energy level (low/medium/high), and setting (nature/urban/indoor/action/romantic). Return only 1-2 sentences describing what kind of music would suit this scene. Be specific about instruments and tempo."
    
    for path in frame_paths:
        img = Image.open(path)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt_single, img]
        )
        descriptions.append(response.text)
    
    combined_descriptions = "\n".join(descriptions)
    prompt_summary = f"Here are music descriptions for different scenes of a video: {combined_descriptions}. Summarise these into a single cohesive music prompt of 2-3 sentences that would work as a background soundtrack for the whole video. Mention specific instruments, mood, tempo, and energy."
    
    summary_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt_summary
    )
    return summary_response.text

# STEP 4 — Music generator function
def generate_music(music_prompt, duration_seconds):
    """Generates a soundtrack using Lyria 3 Pro based on the prompt."""
    full_prompt = f"{music_prompt} Instrumental only, no vocals. Duration approximately {duration_seconds} seconds."
    
    response = client.models.generate_content(
        model="lyria-3-pro-preview",
        contents=full_prompt
    )
    
    audio_path = "outputs/generated_music.mp3"
    audio_bytes = None
    
    # Iterate through candidates and parts to find audio data
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.inline_data:
                audio_bytes = part.inline_data.data
                break
        if audio_bytes:
            break
            
    if not audio_bytes:
        raise Exception("No audio data found in Lyria response.")
        
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    
    return audio_path

# STEP 5 — Video merger function
def merge_audio_video(video_path, audio_path):
    """Merges the generated audio with the original video using moviepy."""
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    
    if audio.duration > video.duration:
        audio = audio.subclip(0, video.duration)
    elif audio.duration < video.duration:
        audio = afx.audio_loop(audio, duration=video.duration)
        
    final_video = video.set_audio(audio)
    output_path = "outputs/final_video_with_music.mp4"
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    video.close()
    audio.close()
    return output_path

# STEP 6 — Gradio interface
def process_video(video_file, interval, show_desc):
    """Main processing function for the Gradio interface."""
    if not client:
        return None, "Error", "Please add your GEMINI_API_KEY to the .env file"
    
    if video_file is None:
        return None, "", "Could not read the video file. Please try a different format."
    
    try:
        print("Extracting frames from video...")
        frame_paths, duration = extract_frames(video_file, interval)
        
        print("Analysing scenes with Gemini Vision...")
        music_description = analyse_video_scenes(frame_paths)
        
        print("Generating soundtrack with Lyria 3 Pro...")
        audio_path = generate_music(music_description, duration)
        
        print("Merging audio and video...")
        final_video_path = merge_audio_video(video_file, audio_path)
        
        status = "Done! Your video with soundtrack is ready."
        return final_video_path, music_description if show_desc else "", status
        
    except Exception as e:
        print(f"Error: {e}")
        if "Gemini" in str(e):
            return None, "", "Scene analysis failed. Check your API key and internet connection."
        elif "Lyria" in str(e):
            return None, "", "Music generation failed. The Lyria 3 Pro model may be temporarily unavailable."
        return None, "", f"An unexpected error occurred: {e}"
    finally:
        if os.path.exists("temp_frames"):
            shutil.rmtree("temp_frames")

with gr.Blocks(title="🎵 Soundtrack Generator — Lyria") as demo:
    gr.Markdown("# 🎵 Soundtrack Generator — Lyria")
    gr.Markdown("Upload a video and AI will generate a custom music soundtrack for it using Google's Lyria 3 Pro.")
    
    with gr.Row():
        with gr.Column():
            video_input = gr.Video(label="Upload your video", sources=["upload"])
            interval_slider = gr.Slider(label="Frame analysis interval (seconds)", minimum=3, maximum=10, value=5, step=1)
            desc_checkbox = gr.Checkbox(label="Show generated music description", value=True)
            submit_btn = gr.Button("Generate Soundtrack")
            
        with gr.Column():
            video_output = gr.Video(label="Final video with music")
            desc_output = gr.Textbox(label="Music Description")
            status_output = gr.Textbox(label="Status")
            
    submit_btn.click(
        fn=process_video,
        inputs=[video_input, interval_slider, desc_checkbox],
        outputs=[video_output, desc_output, status_output]
    )

if __name__ == "__main__":
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    demo.launch()
