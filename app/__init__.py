from flask import Flask
from .extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    # THIS LINE REGISTERS user_loader
    from . import login_manager
    

    from .routes import main
    app.register_blueprint(main)

    from .auth import auth
    app.register_blueprint(auth)

    return app
