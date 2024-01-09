import random
import requests
from requests.exceptions import JSONDecodeError
from utils import settings
from utils.voice import check_ratelimit

voices = [
    "Brian", "Emma", "Russell", "Joey", "Matthew",
    "Joanna", "Kimberly", "Amy", "Geraint", "Nicole",
    "Justin", "Ivy", "Kendra", "Salli", "Raveena",
]

class StreamlabsPolly:
    def __init__(self):
        self.url = "https://streamlabs.com/polly/speak"
        self.max_chars = 550
        self.voices = voices

    def run(self, text, filepath, random_voice: bool = False):
        default_voice = "Emma"  # Example default voice

        if random_voice:
            voice = self.randomvoice()
        else:
            voice = settings.config.get("settings", {}).get("tts", {}).get("streamlabs_polly_voice", default_voice)
            voice = str(voice).capitalize()

        body = {"voice": voice, "text": text, "service": "polly"}
        response = requests.post(self.url, data=body)
        if not check_ratelimit(response):
            self.run(text, filepath, random_voice)
        else:
            try:
                voice_data = requests.get(response.json()["speak_url"])
                with open(filepath, "wb") as f:
                    f.write(voice_data.content)
            except (KeyError, JSONDecodeError):
                try:
                    if response.json()["error"] == "No text specified!":
                        raise ValueError("Please specify a text to convert to speech.")
                except (KeyError, JSONDecodeError):
                    print("Error occurred calling Streamlabs Polly")

    def text_to_speech(self, text, filepath):
        try:
            self.run(text, filepath, random_voice=False)
        except Exception as e:
            print(f"An error occurred in text to speech conversion: {e}")

    def randomvoice(self):
        return random.choice(self.voices)
