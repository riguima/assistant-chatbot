from pathlib import Path

import telebot

from audio_para_texto.config import config
from audio_para_texto.database import Session
from audio_para_texto.models import TelegramMessage
from audio_para_texto.utils import transcribe_audio

bot = telebot.TeleBot(config['BOT_TOKEN'])


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 'Envie qualquer áudio para transcrever para texto'
    )


@bot.message_handler(content_types=['voice', 'audio'])
def on_audio(message):
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
    bot.send_message(message.chat.id, text)
    bot.delete_message(message.chat.id, transcribing_message.id)
    with Session() as session:
        telegram_message = TelegramMessage(
            audio_url=config['DOMAIN'] + f'/static/audios/{file_path.name}',
            text=text,
            user_id=str(message.chat.id),
        )
        session.add(telegram_message)
        session.commit()


if __name__ == '__main__':
    bot.infinity_polling()
