from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session  # type: ignore # Flask-Session for persistent sessions
from datetime import timedelta
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
sess = Session()  # Initialize Flask-Session

def create_app():
    app = Flask(__name__)

    # 🔐 Secret Key & Security Configs
    app.config['SECRET_KEY'] = 'your-secret-key'  
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartspender.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 🛠 Session Configuration
    app.config['SESSION_TYPE'] = 'filesystem'  # Stores session data on the server
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_sessions')  # Custom session directory
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Keeps user logged in for 2 hours
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)  # Remember login for a week
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Security: Prevents JavaScript access to session cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protects against CSRF

    # 🔌 Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    sess.init_app(app)  # Enable Flask-Session

    # 🔄 Ensure Session Persists
    @app.before_request
    def make_session_permanent():
        session.permanent = True  

    # 💰 Custom Template Filter for Currency Formatting
    @app.template_filter('format_currency')
    def format_currency(value):
        return f"₹{value:,.2f}"

    # 🔗 Import & Register Blueprints
    from .routes import main
    app.register_blueprint(main)

    # 🔑 Load User for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    login_manager.login_view = 'main.login'  # Redirect unauthenticated users to login page

    return app
