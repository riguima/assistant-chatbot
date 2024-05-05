from pathlib import Path

from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from httpx import get, post
from sqlalchemy import select

from audio_para_texto.config import config
from audio_para_texto.database import Session
from audio_para_texto.forms import LoginForm
from audio_para_texto.models import Configuration, User, WhatsappMessage
from audio_para_texto.utils import ask_chat_gpt, transcribe_audio


def init_app(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            with Session() as session:
                query = (
                    select(User)
                    .where(User.name == request.form['name'])
                    .where(User.is_admin == True)
                )
                user_model = session.scalars(query).first()
                if (
                    user_model
                    and user_model.password == request.form['password']
                    and user_model.is_admin
                ):
                    user_model.authenticated = True
                    session.commit()
                    login_user(user_model)
                    return redirect('/admin')
                else:
                    return redirect(
                        url_for(
                            'login',
                            error_message='Usuário ou Senha inválidos!',
                        )
                    )
        return render_template(
            'login.html',
            error_message=request.args.get('error_message'),
            form=form,
        )

    @app.get('/logout')
    def logout():
        try:
            with Session() as session:
                query = select(User).where(User.name == current_user.name)
                user_model = session.scalars(query).first()
                if user_model:
                    user_model.authenticated = False
                    session.commit()
        except AttributeError:
            pass
        logout_user()
        return redirect(url_for('login'))

    @app.route('/whatsapp-webhook', methods=['GET', 'POST'])
    def whatsapp_webhook():
        with Session() as session:
            query = select(Configuration).where(
                Configuration.name == 'whatsapp_token'
            )
            whatsapp_token = session.scalars(query).first()
            query = select(Configuration).where(
                Configuration.name == 'whatsapp_access_token'
            )
            whatsapp_access_token = session.scalars(query).first()
            query = select(Configuration).where(
                Configuration.name == 'whatsapp_account_id'
            )
            whatsapp_account_id = session.scalars(query).first()
        whatsapp_headers = {
            'Authorization': f'Bearer {whatsapp_access_token.value}'
        }
        if (
            request.method == 'GET'
            and request.args.get('hub.challenge')
            and request.args.get('hub.verify_token') == whatsapp_token.value
        ):
            return str(request.args['hub.challenge'])
        if request.json['entry'][0]['changes'][0]['value'].get('messages'):
            message = request.json['entry'][0]['changes'][0]['value'][
                'messages'
            ][0]
        else:
            return jsonify({'status': 'ok'})
        answer = None
        with Session() as session:
            query = select(WhatsappMessage).where(
                WhatsappMessage.phone_number == message['from']
            )
            message_model = session.scalars(query).first()
        if message['type'] == 'audio':
            audio_id = message['audio']['id']
            url = get(
                f'https://graph.facebook.com/v19.0/{audio_id}',
                headers=whatsapp_headers,
            ).json()['url']
            audio_path = Path('static') / 'audios' / f'{audio_id}.mp3'
            with open(audio_path, 'wb') as f:
                response = get(url, headers=whatsapp_headers)
                f.write(response.content)
            text = transcribe_audio(str(audio_path))
            answer, thread_id, assistant_id = ask_chat_gpt(text, message_model)
            with Session() as session:
                whatsapp_message = WhatsappMessage(
                    audio_url=config['DOMAIN']
                    + f'/static/audios/{audio_id}.mp3',
                    answer=answer,
                    text=text,
                    phone_number=message['from'],
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                )
                session.add(whatsapp_message)
                session.commit()
        elif message['type'] == 'text':
            answer, thread_id, assistant_id = ask_chat_gpt(
                message['text']['body'], message_model
            )
            with Session() as session:
                whatsapp_message = WhatsappMessage(
                    answer=answer,
                    text=message['text']['body'],
                    phone_number=message['from'],
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                )
                session.add(whatsapp_message)
                session.commit()
        if answer:
            post(
                f'https://graph.facebook.com/v19.0/{whatsapp_account_id.value}/messages',
                headers=whatsapp_headers,
                json={
                    'messaging_product': 'whatsapp',
                    'context': {
                        'message_id': message['id'],
                    },
                    'to': message['from'],
                    'type': 'text',
                    'text': {
                        'preview_url': False,
                        'body': answer,
                    },
                },
            )
        return jsonify({'status': 'ok'})
