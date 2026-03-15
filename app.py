from flask import Flask

from models import db
from controllers import get_porteiro_by_username, create_porteiro

from routes import bp as main_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///receba.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if not get_porteiro_by_username('admin'):
        create_porteiro('Porteiro padrão', 'admin', 'admin')

app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True)