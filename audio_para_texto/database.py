from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from audio_para_texto.config import config

db = create_engine(config['DATABASE_URI'])
Session = sessionmaker(db)
