#!/usr/bin/env python
import sys
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from utils.cleanup import cleanup
from utils.cleanup import cleanup_after_video_creation
import json
import ffmpeg
from utils.videos import save_data
from video_creation.final_video_resources import name_normalize
from utils import settings
from rich.console import Console
from utils import console
from utils.cleanup import cleanup
from utils.console import print_markdown, print_step
from video_creation.voices import save_text_to_mp3
from video_creation.background import (
    download_background_video,
    download_background_audio,
    chop_background,
    get_background_config,
)
from video_creation.final_video import make_final_video
from utils.ffmpeg_install import ffmpeg_install
from video_creation.poll_screenshot import take_poll_question_screenshot
from video_creation.poll_screenshot import take_poll_screenshot
from video_creation.comment_screenshot import take_comment_screenshot

import logging
logging.basicConfig(level=logging.DEBUG, filename='debug.log')

logging.debug('Starting application')

__VERSION__ = "3.2.1"

console = Console()

def video_exists(poll_id, videos_json_path='video_creation/data/videos.json'):
    try:
        with open(videos_json_path, 'r') as file:
            videos = json.load(file)
            for video in videos:
                if video['id'] == poll_id:
                    return True
    except FileNotFoundError:
        # If the videos.json file doesn't exist, return False
        return False
    return False

def main(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Group comments by poll
    polls = {}
    for item in data:
        poll_id = item['pollId']
        if poll_id not in polls:
            polls[poll_id] = {
                'pollId': poll_id,  # Add pollId here
                'slug': item['slug'],
                'question': item['question'],
                'comments': [],
                'category': item['categories']
            }
        polls[poll_id]['comments'].append({
            'commentId': item['commentId'],
            'comment': item['comment']
        })
        
    for poll_id, poll_data in polls.items():
        slug = poll_data['slug']
        poll_title = poll_data["question"]
        filename = f"{name_normalize(poll_title)[:251]}"
        poll_url = f"https://hunch.in/poll/{slug}"
        category = poll_data["category"]
        comments = poll_data['comments']

        if video_exists(poll_id):
            print(f"Video for poll ID {poll_id} already exists. Skipping...")
            continue

        # Create directories for poll
        poll_folder = Path(f"assets/temp/{poll_id}/png")
        audio_folder = Path(f"assets/temp/{poll_id}/mp3")
        poll_folder.mkdir(parents=True, exist_ok=True)
        audio_folder.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()

            # Take poll screenshot
            poll_question_screenshot_path = poll_folder/"poll"/"poll-question.png"
            take_poll_question_screenshot(page, poll_url, str(poll_question_screenshot_path))

            poll_screenshot_path = poll_folder/"poll"/"poll.png"
            take_poll_screenshot(page, poll_url, str(poll_screenshot_path))
            # Process text and audio for poll and comments
            poll_text = poll_data['question']
            # Save audio for poll
            print(f"Saving audio for poll...")
            poll_audio_filename = f"assets/temp/{poll_id}/mp3/poll.mp3"
            save_text_to_mp3(poll_text, poll_audio_filename, poll_id, is_poll=True)
            print(f"Poll Audio file created: {poll_audio_filename}")

            # Take comment screenshots and generate audio only for successful captures
            for i, comment in enumerate(comments):
                comment_id = comment['commentId']
                comment_url = f"https://hunch.in/comment/{slug}/{comment_id}"
                comment_screenshot_path = poll_folder/"comment"/f"comment{i}.png"
                comment_screenshot_success = take_comment_screenshot(page, comment_url, str(comment_screenshot_path))

                if comment_screenshot_success:
                    # Screenshot capture successful, save audio for the comment
                    comment_text = comment['comment']
                    comment_audio_filename = f"assets/temp/{poll_id}/mp3/comment{i}.mp3"
                    save_text_to_mp3(comment_text, comment_audio_filename, poll_id, is_poll=False)
                    print(f"Comment Audio file created: {comment_audio_filename}")
                else:
                    print(f"Failed to capture screenshot for comment {i} of poll: {poll_id}")

            browser.close()
            
        total_audio_length = 0.0

        poll_audio_path = f"assets/temp/{poll_id}/mp3/poll.mp3"
        if os.path.exists(poll_audio_path):
            total_audio_length += float(ffmpeg.probe(poll_audio_path)["format"]["duration"])

        for i in range(len(comments)):
            comment_audio_path = f"assets/temp/{poll_id}/mp3/comment{i}.mp3"
            if os.path.exists(comment_audio_path):
                total_audio_length += float(ffmpeg.probe(comment_audio_path)["format"]["duration"])
        
        # Add poll_audio.mp3 duration
        answered_poll_audio_path = f"assets/video-resources/poll_audio.mp3"
        if os.path.exists(answered_poll_audio_path):
            answered_poll_duration = float(ffmpeg.probe(answered_poll_audio_path)["format"]["duration"])
            total_audio_length += answered_poll_duration


        # Background video and audio processing
        print(f"Processing background audio and video...")
        bg_config = {
            "video": get_background_config("video"),
            "audio": get_background_config("audio"),
        }
        download_background_video(bg_config["video"])
        #download_background_audio(bg_config["audio"])

        # concatenated_audio_path = f"assets/temp/{poll_id}/audio.mp3"
        # total_audio_length = float(ffmpeg.probe(concatenated_audio_path)["format"]["duration"])

        # console.log(f"[bold blue] Total concatenated audio length: {total_audio_length} seconds")


        # Set video length dynamically
        length = total_audio_length
        console.log(f"[bold blue] Total audio length: {length} seconds")

        # Skip video generation if total audio length is less than 15 seconds
        if length < 15:
            console.log(f"[bold red] Total audio length for poll ID {poll_id} is less than 15 seconds. Skipping video generation for this poll.")
            subreddit = settings.config["reddit"]["thread"]["subreddit"]
            save_data(subreddit, filename + ".mp4", poll_title, poll_id, bg_config["video"][2])
            console.log(f"[bold red] Saved poll data in videos.json file.")
            console.log("Removing temporary files 🗑")
            cleanup_after_video_creation(poll_id, "hunch")
            cleanups = cleanup(poll_id)
            console.log(f"Removed {cleanups} temporary files 🗑")
            continue  # Skip the rest of the loop and move to the next poll ID

        number_of_screenshots = 1 + len(comments)

        chop_background(bg_config, length, poll_id)
        make_final_video(number_of_screenshots + 1, length, poll_data, bg_config)

        # Cleanup for this poll
        cleanup(poll_id)

if __name__ == "__main__":
    try:
        ffmpeg_install()
        directory = Path().absolute()
        config = settings.check_toml(
            f"{directory}/utils/.config.template.toml", f"{directory}/config.toml"
        )
        config is False and sys.exit()
        json_file_path = "assets/bigquery/top_US_voted_polls_and_top_comments_except_dating_category.json"  # Replace with actual JSON file path
        main(json_file_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise