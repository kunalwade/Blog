from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'



# % Database instance
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

MIGRATIONS_DIR = "migrations"

Migrate(app,db, MIGRATIONS_DIR)
login_manager= LoginManager(app)
login_manager.login_view = 'login'

#~%Bootstrap method 'info' to add blue style to display message for account-decorator-@login required
login_manager.login_message_category='info'
# with app.app_context():
    # db.create_all()


# @app.shell_context_processor
# def make_shell_context():
#     return {'db': db, 'User': User}

from flaskblog import routes 

