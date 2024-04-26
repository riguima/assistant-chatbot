import os
from pathlib import Path

import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence


def transcribe_audio_chunk(path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data, language='pt-BR')


def transcribe_audio(path):
    sound = AudioSegment.from_file(path)
    chunks = split_on_silence(
        sound,
        min_silence_len=500,
        silence_thresh=sound.dBFS - 14,
        keep_silence=500,
    )
    chunk_folder = 'audio-chunks'
    os.makedirs(chunk_folder, exist_ok=True)
    result = ''
    for i, audio_chunk in enumerate(chunks, start=1):
        chunk_filename = Path(chunk_folder) / f'chunk{i}.wav'
        audio_chunk.export(str(chunk_filename), format='wav')
        text = transcribe_audio_chunk(str(chunk_filename))
        result += f'{text.capitalize()}. '
        os.remove(Path(chunk_folder) / chunk_filename.name)
    return result.strip()
