from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from audio_para_texto.database import db


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    password: Mapped[str]
    authenticated: Mapped[Optional[bool]] = mapped_column(default=False)
    is_admin: Mapped[Optional[bool]] = mapped_column(default=False)

    @property
    def is_authenticated(self):
        return self.authenticated

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class TelegramMessage(Base):
    __tablename__ = 'telegram-mensagens'
    id: Mapped[int] = mapped_column(primary_key=True)
    audio_url: Mapped[str]
    text: Mapped[str]
    user_id: Mapped[str]


class WhatsappMessage(Base):
    __tablename__ = 'whatsapp-mensagens'
    id: Mapped[int] = mapped_column(primary_key=True)
    audio_url: Mapped[str]
    text: Mapped[str]
    phone_number: Mapped[str]


Base.metadata.create_all(db)
