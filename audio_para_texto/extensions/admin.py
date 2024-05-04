from flask import redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from audio_para_texto.database import Session
from audio_para_texto.models import (Configuration, TelegramMessage,
                                     WhatsappMessage)


class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class TelegramModelView(AdminModelView):
    column_searchable_list = ['user_id']


class WhatsappModelView(AdminModelView):
    column_searchable_list = ['phone_number']


def init_app(app):
    admin = Admin(app, name='admin')
    session = Session()
    admin.add_view(AdminModelView(Configuration, session))
    admin.add_view(TelegramModelView(TelegramMessage, session))
    admin.add_view(WhatsappModelView(WhatsappMessage, session))
