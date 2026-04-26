import os
from flask import Flask
from datetime import datetime, timezone, timedelta

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
    if not get_porteiro_by_email("admin@receba.com"):
        create_porteiro("Porteiro padrão", "admin@receba.com", "admin")

app.register_blueprint(main_bp)


# Filtro para formatar datas em português
def format_date_br(date_obj):
    if date_obj is None or date_obj == "":
        return ""

    # Converter string para datetime se necessário
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return str(date_obj)

    # Interpretar a data armazenada como UTC e converter para hora local
    if date_obj.tzinfo is None:
        date_obj = date_obj.replace(tzinfo=timezone.utc).astimezone()
    else:
        date_obj = date_obj.astimezone()

    now_local = datetime.now(date_obj.tzinfo)
    date_local = date_obj.date()
    if date_local == now_local.date():
        return f"Hoje {date_obj.strftime('%H:%M')}"
    if date_local == (now_local.date() - timedelta(days=1)):
        return f"Ontem {date_obj.strftime('%H:%M')}"
    return date_obj.strftime("%d-%m-%Y %H:%M")


app.jinja_env.filters["format_date_br"] = format_date_br

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

# Para rodar localmente
# if __name__ == '__main__':
#     app.run(debug=True)
