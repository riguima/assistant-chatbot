from importlib import import_module

from flask import Flask

from audio_para_texto.config import config


def load_extensions(app):
    for extension in config['EXTENSIONS']:
        extension_module = import_module(extension)
        extension_module.init_app(app)


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.update({
        'SECRET_KEY': config['SECRET_KEY'],
    })
    load_extensions(app)
    return app
