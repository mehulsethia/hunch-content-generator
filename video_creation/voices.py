from typing import Tuple
import os
from rich.console import Console
from TTS.GTTS import GTTS
from TTS.TikTok import TikTok
from TTS.aws_polly import AWSPolly
from TTS.engine_wrapper import TTSEngine
from TTS.pyttsx import pyttsx
from TTS.elevenlabs import elevenlabs
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
    "ElevenLabs": elevenlabs,
}


# def save_text_to_mp3(reddit_obj) -> Tuple[int, int]:
#     """Saves text to MP3 files.

#     Args:
#         reddit_obj (): Reddit object received from reddit API in reddit/subreddit.py

#     Returns:
#         tuple[int,int]: (total length of the audio, the number of comments audio was generated for)
#     """

#     voice = settings.config["settings"]["tts"]["voice_choice"]
#     if str(voice).casefold() in map(lambda _: _.casefold(), TTSProviders):
#         text_to_mp3 = TTSEngine(get_case_insensitive_key_value(TTSProviders, voice), reddit_obj)
#     else:
#         while True:
#             print_step("Please choose one of the following TTS providers: ")
#             print_table(TTSProviders)
#             choice = input("\n")
#             if choice.casefold() in map(lambda _: _.casefold(), TTSProviders):
#                 break
#             print("Unknown Choice")
#         text_to_mp3 = TTSEngine(get_case_insensitive_key_value(TTSProviders, choice), reddit_obj)
#     return text_to_mp3.run()

def save_text_to_mp3(text, filename, poll_id, is_poll):
    console.print(f"Starting audio generation for {('poll' if is_poll else 'comment')} with text: {text}")
    console.print("Is Poll?: ", is_poll)

    try:
        voice_choice = "streamlabspolly"
        tts_provider = get_case_insensitive_key_value(TTSProviders, voice_choice)

        if tts_provider is None:
            console.print("No matching TTS provider found.")
            return False

        key = "question" if is_poll else "comment"
        hunch_object = {"pollId": poll_id, key: text}
        console.print("Hunch Object: ", hunch_object)

        tts_engine = TTSEngine(tts_provider, hunch_object)
        success = tts_engine.run()

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
