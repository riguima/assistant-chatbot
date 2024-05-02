from pathlib import Path

import telebot
from sqlalchemy import select

from audio_para_texto.config import config
from audio_para_texto.database import Session
from audio_para_texto.models import Configuration, TelegramMessage
from audio_para_texto.utils import ask_chat_gpt, transcribe_audio

with Session() as session:
    query = select(Configuration).where(Configuration.name == 'telegram_token')
    telegram_token = session.scalars(query).first()
    bot = telebot.TeleBot(telegram_token.value)
    bot.set_webhook()


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 'Envie qualquer pergunta em texto ou áudio'
    )


@bot.message_handler(content_types=['voice', 'audio'])
def on_audio(message):
    with Session() as session:
        query = select(TelegramMessage).where(
            TelegramMessage.user_id == str(message.chat.id)
        )
        message_model = session.scalars(query).first()
        thread_id = None if message_model is None else message_model.thread_id
    transcribing_message = bot.send_message(
        message.chat.id, 'Transcrevendo áudio...'
    )
    if message.voice:
        file_id = message.voice.file_id
    else:
        file_id = message.audio.file_id
    file_info = bot.get_file(file_id)
    file_path = Path('static') / 'audios' / file_info.file_path.split('/')[-1]
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)
    text = transcribe_audio(str(file_path))
    answer, thread_id = ask_chat_gpt(text, thread_id)
    bot.send_message(message.chat.id, answer)
    bot.delete_message(message.chat.id, transcribing_message.id)
    with Session() as session:
        telegram_message = TelegramMessage(
            audio_url=config['DOMAIN'] + f'/static/audios/{file_path.name}',
            text=text,
            answer=answer,
            user_id=str(message.chat.id),
            thread_id=thread_id,
        )
        session.add(telegram_message)
        session.commit()


@bot.message_handler(content_types=['text'])
def on_text(message):
    with Session() as session:
        query = select(TelegramMessage).where(
            TelegramMessage.user_id == str(message.chat.id)
        )
        message_model = session.scalars(query).first()
        thread_id = None if message_model is None else message_model.thread_id
    answer, thread_id = ask_chat_gpt(message.text, thread_id)
    bot.send_message(message.chat.id, answer)
    with Session() as session:
        telegram_message = TelegramMessage(
            text=message.text,
            answer=answer,
            user_id=str(message.chat.id),
            thread_id=thread_id,
        )
        session.add(telegram_message)
        session.commit()


if __name__ == '__main__':
    bot.infinity_polling()
