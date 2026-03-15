

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Porteiro(db.Model):

    __tablename__ = 'porteiros'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    encomendas = db.relationship(
        'Encomenda',
        foreign_keys='Encomenda.porteiro_id',
        backref='porteiro',
        lazy=True
    )
    retiradas = db.relationship(
        'Encomenda',
        foreign_keys='Encomenda.retirada_porteiro_id',
        backref='retirada_porteiro',
        lazy=True
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Morador(db.Model):

    __tablename__ = 'moradores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    torre = db.Column(db.String(50), nullable=True)
    ap = db.Column(db.String(50), nullable=True)
    whatsapp = db.Column(db.String(50), nullable=True)

    encomendas = db.relationship('Encomenda', backref='morador', lazy=True)


class Encomenda(db.Model):

    __tablename__ = 'encomendas'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    cod = db.Column(db.String(50), nullable=False)
    empresa = db.Column(db.String(100), nullable=False)
    entregador = db.Column(db.String(100), nullable=True)

    porteiro_id = db.Column(db.Integer, db.ForeignKey('porteiros.id'), nullable=False)
    morador_id = db.Column(db.Integer, db.ForeignKey('moradores.id'), nullable=True)

    status = db.Column(db.String(20), default='pendente')
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    data_retirada = db.Column(db.DateTime, nullable=True)

    retirada_porteiro_id = db.Column(db.Integer, db.ForeignKey('porteiros.id'), nullable=True)

    def __repr__(self) -> str:
        return f"<Encomenda {self.uuid[:8]}...>"