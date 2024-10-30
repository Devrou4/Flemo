from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_mail import Mail


app = Flask(__name__)
app.config['SECRET_KEY'] = 'c05c5ad21a274a97267a1fbe0b243a64'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['CKEDITOR_PKG_TYPE'] = 'basic'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
ckeditor = CKEditor(app)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] =
# app.config['MAIL_PASSWORD'] =
mail = Mail()

from flemo import routes
