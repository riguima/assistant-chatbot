from flask import redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select
from pathlib import Path
from httpx import get, post

from audio_para_texto.database import Session
from audio_para_texto.forms import LoginForm
from audio_para_texto.models import User, WhatsappMessage
from audio_para_texto.config import config
from audio_para_texto.utils import transcribe_audio


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

    @app.route('/', methods=['GET', 'POST'])
    def test_whatsapp():
        if request.method == 'GET' and request.args.get('hub.challenge') and request.args.get('hub.verify_token') == config['WHATSAPP_API_TOKEN']:
            return str(request.args['hub.challenge'])
        message = request.json['entry'][0]['changes'][0]['value']['messages'][0]
        if message['type'] == 'audio':
            audio_id = message['audio']['id']
            url = get(f'https://graph.facebook.com/v19.0/{audio_id}', headers={
                'Authorization': f'Bearer {config["WHATSAPP_API_ACCESS_TOKEN"]}'
            }).json()['url']
            audio_path = Path('static') / 'audios' / f'{audio_id}.mp3'
            with open(audio_path, 'wb') as f:
                response = get(url, headers={
                    'Authorization': f'Bearer {config["WHATSAPP_API_ACCESS_TOKEN"]}'
                })
                f.write(response.content)
            result_text = transcribe_audio(str(audio_path))
            response = post(f'https://graph.facebook.com/v19.0/{config["WHATSAPP_API_ACCOUNT_ID"]}/messages', headers={
                'Authorization': f'Bearer {config["WHATSAPP_API_ACCESS_TOKEN"]}'
            }, json={
                'messaging_product': 'whatsapp',
                'context': {
                    'message_id': message['id'],
                },
                'to': message['from'],
                'type': 'text',
                'text': {
                    'preview_url': False,
                    'body': result_text,
                }
            })
            with Session() as session:
                whatsapp_message = WhatsappMessage(
                    audio_url=config['DOMAIN'] + f'/static/audios/{audio_id}.mp3',
                    text=result_text,
                    phone_number=message['from'],
                )
                session.add(whatsapp_message)
                session.commit()
        return jsonify({'status': 'ok'})
