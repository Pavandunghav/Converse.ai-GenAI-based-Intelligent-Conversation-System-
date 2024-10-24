import assemblyai as aai

# Replace with your API key
aai.settings.api_key = "8d0cb4aeed33448d9398f1d34c0d5b44"

# URL of the file to transcribe
FILE_URL = "C:/Users/Aniket/Desktop/Abhishek Python/personal/django_tutorials/NPN/chatapp_v2/audio/recorded_audio.wav"

# You can also transcribe a local file by passing in a file path
# FILE_URL = './path/to/file.mp3'

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(FILE_URL)
print(transcript.text)