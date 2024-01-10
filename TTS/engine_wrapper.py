import os
from pathlib import Path
from typing import Tuple
from moviepy.editor import AudioFileClip
from utils.voice import sanitize_text

DEFAULT_MAX_LENGTH = 50

class TTSEngine:
    def __init__(self, tts_module, hunch_object: dict, filename: str, path: str = "assets/temp/", max_length: int = DEFAULT_MAX_LENGTH):
        self.filename = filename  # Add this line
        self.tts_module = tts_module() if callable(tts_module) else tts_module
        if "pollId" not in hunch_object:
            raise ValueError("Invalid hunch_object structure. Expected a dictionary with a 'pollId' key.")
        self.poll_id = hunch_object["pollId"]
        self.hunch_object = hunch_object
        self.path = f"{path}{self.poll_id}/mp3"
        Path(self.path).mkdir(parents=True, exist_ok=True)
        self.max_length = max_length
        self.length = 0

    def run(self) -> Tuple[int, int]:
        idx = -1
        if self.hunch_object.get("question"):
            self.call_tts(self.hunch_object["question"])
        for idx, comment in enumerate(self.hunch_object.get("comments", [])):
            if self.length > self.max_length:
                break
            self.call_tts(f"comment{idx}", comment["comment"])
        return self.length, idx + 1

    def call_tts(self, text: str):
        try:
            self.tts_module.run(text, filepath=self.filename)
            clip = AudioFileClip(self.filename)
            self.length += clip.duration
        except Exception as e:
            print(f"Error generating TTS for {self.filename}: {e}")
        finally:
            clip.close() if 'clip' in locals() else None

def process_text(text: str, clean: bool = True):
    return sanitize_text(text) if clean else text
