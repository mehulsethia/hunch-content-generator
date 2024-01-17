import ffmpeg
import subprocess
import cv2
from PIL import Image, ImageSequence
import numpy as np
from rich.console import Console

console = Console()

def extract_audio(video_path, output_path):
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-q:a', '0',
            '-map', 'a',
            output_path,
            '-y'
        ]
        subprocess.run(command, check=True)
        console.log(f"[bold green] Audio extracted successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")

def overlay_gif_on_video(video_path, gif_path, output_path):
    try:
        # Open the video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video file.")
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Open the GIF
        gif = Image.open(gif_path)
        frames = [frame.copy() for frame in ImageSequence.Iterator(gif)]

        print("Starting video processing...")
        # Video processing loop
        gif_length = len(frames)
        frame_index = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert video frame to PIL Image
            video_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # Overlay GIF frame
            gif_frame = frames[frame_index % gif_length].convert("RGBA")
            gif_width, gif_height = gif_frame.size
            x = width - gif_width - 10  # Position at the top right
            y = 10  # Small margin from the top
            video_frame.paste(gif_frame, (x, y), gif_frame)

            # Convert back to OpenCV format and write frame
            frame = cv2.cvtColor(np.array(video_frame), cv2.COLOR_RGB2BGR)
            out.write(frame)

            frame_index += 1

        cap.release()
        out.release()
        console.log("[bold green] Video processing completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

def combine_video_audio(video_path, audio_path, output_path):
    try:
        command = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-map', '0:v:0',
            '-map', '1:a:0',
            output_path,
            '-y'
        ]
        subprocess.run(command, check=True)
        console.log(f"[bold green] Video and audio combined successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error combining video and audio: {e}")


def reencode_video(input_path, output_path, resolution="1080x1920", fps=59.94):
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-s', resolution,  # Set resolution
            '-r', str(fps),  # Set frame rate
            '-c:v', 'libx264',  # Video codec
            '-c:a', 'aac',  # Audio codec
            '-b:a', '192k',  # Audio bitrate
            '-strict', 'experimental',
            '-y',  # Overwrite output file without asking
            output_path
        ]
        subprocess.run(command, check=True)
        console.log(f"[bold green] Video re-encoded successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error re-encoding video: {e}")
        
def concatenate_videos(video1_path, video2_path, output_path):
    try:
        command = [
            'ffmpeg',
            '-i', video1_path,
            '-i', video2_path,
            '-filter_complex', 
            "[0:v][1:v]concat=n=2:v=1:a=0[outv];[0:a][1:a]concat=n=2:v=0:a=1[outa]",
            '-map', '[outv]',
            '-map', '[outa]',
            output_path
        ]
        subprocess.run(command, check=True)
        console.log(f"[bold green] Videos concatenated successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during concatenation: {e}")


def check_audio_stream(video_path):
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False  # Don't raise an error for non-zero exit status
        )
        output = result.stderr.decode()
        return "Audio:" in output
    except Exception as e:
        print(f"Error checking audio stream: {e}")
        return False


# Assuming properties of the main video
main_video_width = 1080
main_video_height = 1920
main_video_fps = 30  # Replace with actual FPS of main video
        

# # Replace with the path to your test video and logo image
# audio_path = "/Users/mehul/Desktop/extracted_audio.aac"
# processed_video_path = "/Users/mehul/Desktop/processed_video.mp4"

# video_path = "/Users/mehul/Desktop/RedditVideoMakerBot/assets/testvideo/testvideo.mp4"
# logo_path = "/Users/mehul/Desktop/RedditVideoMakerBot/assets/logo/logo_animation_1.gif"
# outro_path = "/Users/mehul/Desktop/RedditVideoMakerBot/assets/outro/outro.mp4"
# output_path = "/Users/mehul/Desktop/finalvideo.mp4"

# reencoded_main_video = "/Users/mehul/Desktop/reencoded_main_video.mp4"
# reencoded_outro_video = "/Users/mehul/Desktop/reencoded_outro_video.mp4"
# intermediate_output = "/Users/mehul/Desktop/intermediate_video.mp4"
# final_output = "/Users/mehul/Desktop/finalvideo.mp4"

# # Extract audio from the original video
# extract_audio(video_path, audio_path)

# # Process the video frames (overlay GIF)
# overlay_gif_on_video(video_path, logo_path, processed_video_path)

# # Combine the processed video with the extracted audio
# combine_video_audio(processed_video_path, audio_path, output_path)

# # Re-encode the videos to match main video properties
# reencode_video(output_path, reencoded_main_video)
# reencode_video(outro_path, reencoded_outro_video)
# concatenate_videos(intermediate_output, reencoded_outro_video, final_output)
