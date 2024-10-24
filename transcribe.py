from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import librosa

def transcribe(speech_file):

        ##Speech file should be in wav format 
        processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
        model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

        audio_input, _ = librosa.load(speech_file, sr=16000)
        input_values = processor(audio_input, return_tensors="pt", sampling_rate=16000).input_values

        logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)

        transcription = processor.decode(predicted_ids[0])
        return transcription


# speech_file=r"C:/Users/Aniket/Desktop/Abhishek Python/personal/django_tutorials/NPN/chatapp_v2/audio/recorded_audio.wav"

# print(transcribe(speech_file))