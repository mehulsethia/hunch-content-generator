import multiprocessing
import os
import re
from rich.console import Console
from tqdm import tqdm
from os.path import exists  # Needs to be imported specifically
from typing import Final
from typing import Tuple, Any, Dict

import ffmpeg
import translators
from PIL import Image
from rich.console import Console
from rich.progress import track

from utils.cleanup import cleanup
from utils.console import print_step, print_substep
from utils.thumbnail import create_thumbnail
from utils.videos import save_data
from utils import settings


import tempfile
import threading
import time

from video_creation.logo_outro import *

console = Console()

class ProgressFfmpeg(threading.Thread):
    def __init__(self, vid_duration_seconds, progress_update_callback):
        threading.Thread.__init__(self, name="ProgressFfmpeg")
        self.stop_event = threading.Event()
        self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.vid_duration_seconds = vid_duration_seconds
        self.progress_update_callback = progress_update_callback

    def run(self):  
        while not self.stop_event.is_set():
            latest_progress = self.get_latest_ms_progress()
            if latest_progress is not None:
                completed_percent = latest_progress / self.vid_duration_seconds
                self.progress_update_callback(completed_percent)
            time.sleep(1)

    def get_latest_ms_progress(self):
        lines = self.output_file.readlines()

        if lines:
            for line in lines:
                if "out_time_ms" in line:
                    out_time_ms_str = line.split("=")[1].strip()
                    if out_time_ms_str.isnumeric():
                        return float(out_time_ms_str) / 1000000.0
                    else:
                        # Handle the case when "N/A" is encountered
                        return None
        return None

    def stop(self):
        self.stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()


def name_normalize(name: str) -> str:
    name = re.sub(r'[?\\"%*:|<>]', "", name)
    name = re.sub(r"( [w,W]\s?\/\s?[o,O,0])", r" without", name)
    name = re.sub(r"( [w,W]\s?\/)", r" with", name)
    name = re.sub(r"(\d+)\s?\/\s?(\d+)", r"\1 of \2", name)
    name = re.sub(r"(\w+)\s?\/\s?(\w+)", r"\1 or \2", name)
    name = re.sub(r"\/", r"", name)

    lang = settings.config["reddit"]["thread"]["post_lang"]
    if lang:
        print_substep("Translating filename...")
        translated_name = translators.translate_text(name, translator="google", to_language=lang)
        return translated_name
    else:
        return name


def prepare_background(poll_id: str, W: int, H: int) -> str:
    output_path = f"assets/temp/{poll_id}/background_noaudio.mp4"
    output = (
        ffmpeg.input(f"assets/temp/{poll_id}/background.mp4")
        .filter("crop", f"ih*({W}/{H})", "ih")
        .output(
            output_path,
            an=None,
            **{
                "c:v": "h264",
                "b:v": "20M",
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
            },
        )
        .overwrite_output()
    )
    try:
        output.run(quiet=True)
    except ffmpeg.Error as e:
        print(e.stderr.decode("utf8"))
        exit(1)
    return output_path

        
def merge_background_audio(audio: ffmpeg, poll_id: str):
    """Gather an audio and merge with assets/backgrounds/background.mp3
    Args:
        audio (ffmpeg): The TTS final audio but without background.
        reddit_id (str): The ID of subreddit
    """
    background_audio_volume = settings.config["settings"]["background"]["background_audio_volume"]
    console.log(f"[bold blue] Background Audio Volumne: {background_audio_volume}")

    if background_audio_volume == 0:
        return audio  # Return the original audio
    else:
        # # sets volume to config
        # bg_audio = ffmpeg.input(f"assets/temp/{poll_id}/background.mp3").filter(
        #     "volume",
        #     background_audio_volume,
        # )
        # # Merges audio and background_audio
        # merged_audio = ffmpeg.filter([audio, bg_audio], "amix", duration="longest")
        # return merged_audio  # Return merged audio

        # Load the original background audio file
        bg_audio = ffmpeg.input(f"assets/temp/{poll_id}/background.mp3")

        # Apply the volume setting to the background audio
        adjusted_bg_audio = bg_audio.filter("volume", volume=background_audio_volume)

        # Save the adjusted background audio to a temporary file
        adjusted_bg_audio_path = f"assets/temp/{poll_id}/adjusted_background.mp3"
        ffmpeg.output(adjusted_bg_audio, adjusted_bg_audio_path).overwrite_output().run()

        # Load the adjusted background audio for merging
        adjusted_bg_audio = ffmpeg.input(adjusted_bg_audio_path)

        # Merge the TTS audio and the adjusted background audio
        merged_audio = ffmpeg.filter([audio, adjusted_bg_audio], "amix", duration="longest")

        return merged_audio  # Return the merged audio

