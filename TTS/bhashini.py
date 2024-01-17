import requests

# Your API key (replace with your actual API key provided by Bhashini)
api_key = '39a54df509-d168-4ebc-9c64-e10957dea723'

# The API endpoint for Bhashini TTS
api_endpoint = 'https://tts.bhashini.ai/v1/synthesize'

# Headers to be sent with the request
headers = {
    'X-API-KEY': api_key,
    'Content-Type': 'application/json'
}

# Data payload with text, language ID, and voice ID
data = {
    "text": "Your text here",
    "languageId": "hi",  # Example for Hindi language
    "voiceId": 0         # Replace with the correct voice ID
}

# Send the POST request to the Bhashini TTS API
response = requests.post(api_endpoint, headers=headers, json=data)

# Check if the request was successful
if response.status_code == 200:
    # The API should return the audio content in the response body
    audio_content = response.content
    # You can save this as an
