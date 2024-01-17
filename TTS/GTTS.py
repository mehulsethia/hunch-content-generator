import random

from gtts import gTTS

from utils import settings


class GTTS:
    def __init__(self):
        self.max_chars = 5000
        self.voices = []
        self.tld = 'com.in'

    def run(self, text, filepath):
        tts = gTTS(
            text=text,
            lang=settings.config["reddit"]["thread"]["post_lang"] or "en",
            tld=self.tld,
                
        )
        tts.save(filepath)

    def randomvoice(self):
        return random.choice(self.voices)
