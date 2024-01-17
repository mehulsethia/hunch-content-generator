from typing import Tuple
import os
import json
import re
from rich.console import Console
from TTS.GTTS import GTTS
from TTS.TikTok import TikTok
from TTS.aws_polly import AWSPolly
from TTS.engine_wrapper import TTSEngine
from TTS.pyttsx import pyttsx
# from TTS.elevenlabs import elevenlabs
from TTS.streamlabs_polly import StreamlabsPolly
from utils import settings
from utils.console import print_table, print_step

console = Console()

TTSProviders = {
    "GoogleTranslate": GTTS,
    "AWSPolly": AWSPolly,
    "StreamlabsPolly": StreamlabsPolly,
    "TikTok": TikTok,
    "pyttsx": pyttsx,
    # "ElevenLabs": elevenlabs,
}

def remove_emojis(text):
    # Emoji patterns
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def load_abbreviations(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def expand_abbreviations(text, abbreviations_dict):
    for abbr, expansion in abbreviations_dict.items():
        text = text.replace(abbr, expansion)
    return text

def save_text_to_mp3(text, filename, poll_id, is_poll):
    console.print(f"Starting audio generation for {('poll' if is_poll else 'comment')} with text: {text}")
    console.print("Is Poll?: ", is_poll)

    try:

        # Load abbreviations and expand the text
        # abbreviations_file = '/Users/mehul/Desktop/hunch-content-generator/utils/abbreviations.json'
        # abbreviations_dict = load_abbreviations(abbreviations_file)
        # expanded_text = expand_abbreviations(text, abbreviations_dict)
        # clean_text = remove_emojis(expanded_text)

        # Remove emojis from the text
        clean_text = remove_emojis(text)

        voice_choice = "streamlabspolly"
        tts_provider = get_case_insensitive_key_value(TTSProviders, voice_choice)

        if tts_provider is None:
            console.print("No matching TTS provider found.")
            return False

        key = "question" if is_poll else "comment"
        hunch_object = {"pollId": poll_id, key: clean_text}
        console.print("Hunch Object: ", hunch_object)
        hunch_object['question']=hunch_object[key]

        tts_engine = TTSEngine(tts_provider, hunch_object, filename)
        success = tts_engine.run()
        console.print("Filename: ",filename)
        console.print("SUCCESS: ",success)

        if success and os.path.exists(filename):
            console.print(f"Audio file successfully created: {filename}")
            return True
        else:
            console.print(f"Failed to create audio file: {filename}")
            return False

    except Exception as e:
        console.print(f"Error during audio file generation: {e}")
        return False

def get_case_insensitive_key_value(input_dict, key):
    return next(
        (value for dict_key, value in input_dict.items() if dict_key.lower() == key.lower()),
        None,
    )
