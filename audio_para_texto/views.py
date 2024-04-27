from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select

from audio_para_texto.database import Session
from audio_para_texto.forms import LoginForm
from audio_para_texto.models import User


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
                print(user_model)
                if user_model and user_model.password == request.form['password']:
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
