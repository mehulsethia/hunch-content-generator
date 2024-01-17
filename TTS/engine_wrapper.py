import os
from pathlib import Path
from typing import Tuple
from moviepy.editor import AudioFileClip
from pydub import AudioSegment
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

    def run(self, speed: float = 1.0) -> Tuple[int, int]:
        idx = -1
        if self.hunch_object.get("question"):
            self.call_tts(self.hunch_object["question"], speed=speed)
        for idx, comment in enumerate(self.hunch_object.get("comments", [])):
            if self.length > self.max_length:
                break
            self.call_tts(f"comment{idx}", comment["comment"], speed=speed)
        return self.length, idx + 1

    def call_tts(self, text: str, speed: float = 1.0):
        try:
            self.tts_module.run(text, filepath=self.filename)
            
            # Load the audio using pydub
            audio = AudioSegment.from_mp3(self.filename)

            if len(audio) > 0:
            
                # Adjust the speed using pydub
                modified_audio = audio.speedup(playback_speed=speed)
                
                # Save the modified audio
                modified_audio.export(self.filename, format="mp3")

                # clip = AudioFileClip(self.filename)
                # self.length += clip.duration
                # Get the duration of the modified audio
                self.length += len(modified_audio) / 1000.0
            else:
                print(f"Error: Loaded audio has zero length for {self.filename}")
    
        except Exception as e:
            print(f"Error generating TTS for {self.filename}: {e}")
        finally:
            # Ensure that the modified_audio is closed
            modified_audio.close() if 'modified_audio' in locals() else None

def process_text(text: str, clean: bool = True):
    return sanitize_text(text) if clean else text
