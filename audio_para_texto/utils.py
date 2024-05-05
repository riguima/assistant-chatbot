import os
from pathlib import Path

import speech_recognition as sr
from openai import OpenAI
from pydub import AudioSegment
from pydub.silence import split_on_silence
from speech_recognition.exceptions import UnknownValueError
from sqlalchemy import select

from audio_para_texto.database import Session
from audio_para_texto.models import Configuration


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
        try:
            text = transcribe_audio_chunk(str(chunk_filename))
            result += f'{text.capitalize()}. '
        except UnknownValueError:
            continue
        os.remove(Path(chunk_folder) / chunk_filename.name)
    return result.strip()


def ask_chat_gpt(question, thread_id):
    with Session() as session:
        query = select(Configuration).where(
            Configuration.name == 'openai_token'
        )
        openai_token = session.scalars(query).first()
        if openai_token:
            client = OpenAI(api_key=openai_token.value)
            with Session() as session:
                query = select(Configuration).where(
                    Configuration.name == 'assistant_id'
                )
                assistant_model = session.scalars(query).first()
                if assistant_model:
                    assistant = client.beta.assistants.retrieve(assistant_model.value)
                    if thread_id is None:
                        thread = client.beta.threads.create()
                        thread_id = thread.id
                    client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role='user',
                        content=question,
                    )
                    run = client.beta.threads.runs.create_and_poll(
                        thread_id=thread_id,
                        assistant_id=assistant.id,
                    )
                    messages = client.beta.threads.messages.list(
                        thread_id=thread_id
                    )
                    return messages.data[0].content[0].text.value, thread_id
        else:
            return '', thread_id
