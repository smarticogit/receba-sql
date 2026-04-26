import os
from flask import Flask
from datetime import datetime

from models import db
from controllers import get_porteiro_by_email, create_porteiro
from routes import bp as main_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = "change_this_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///receba.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    if not get_porteiro_by_email("admin@exemplo.com"):
        create_porteiro("Porteiro padrão", "admin@exemplo.com", "admin")

app.register_blueprint(main_bp)


# Filtro para formatar datas em português
def format_date_br(date_obj):
    if date_obj is None or date_obj == "":
        return ""

    # Converter string para datetime se necessário
    if isinstance(date_obj, str):
        try:
            # Tenta com microsegundos primeiro
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                # Tenta sem microsegundos
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return str(date_obj)

    return date_obj.strftime("%d-%m-%Y %H:%M")


app.jinja_env.filters["format_date_br"] = format_date_br

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

# Para rodar localmente
# if __name__ == '__main__':
#     app.run(debug=True)
