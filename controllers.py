import uuid
from datetime import datetime
from types import SimpleNamespace
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

from models import db


def row_to_obj(row):
    if row is None:
        return None
    return SimpleNamespace(**dict(row._mapping))


def get_porteiro_by_email(email):
    result = db.session.execute(
        text("SELECT * FROM porteiros WHERE email = :email"), {"email": email}
    ).fetchone()
    return row_to_obj(result)


def create_porteiro(nome, email, senha):
    hashed = generate_password_hash(senha)
    db.session.execute(
        text(
            "INSERT INTO porteiros (nome, email, password_hash) VALUES (:nome, :email, :pwd)"
        ),
        {"nome": nome, "email": email, "pwd": hashed},
    )
    db.session.commit()


def get_morador_by_unique(nome, torre, ap):
    result = db.session.execute(
        text(
            "SELECT * FROM moradores WHERE nome = :nome AND torre = :torre AND ap = :ap"
        ),
        {"nome": nome, "torre": torre, "ap": ap},
    ).fetchone()
    return row_to_obj(result)


def create_morador(nome, torre, ap, whatsapp):
    db.session.execute(
        text(
            "INSERT INTO moradores (nome, torre, ap, whatsapp) VALUES (:nome, :torre, :ap, :whatsapp)"
        ),
        {"nome": nome, "torre": torre, "ap": ap, "whatsapp": whatsapp},
    )
    db.session.commit()


def search_moradores(nome=None, torre=None, ap=None):
    query = "SELECT * FROM moradores WHERE 1=1"
    params = {}
    if nome:
        query += " AND nome LIKE :nome"
        params["nome"] = f"%{nome}%"
    if torre:
        query += " AND torre = :torre"
        params["torre"] = torre
    if ap:
        query += " AND ap = :ap"
        params["ap"] = ap
    results = db.session.execute(text(query), params).fetchall()
    return [row_to_obj(r) for r in results]


def list_moradores():
    results = db.session.execute(
        text("SELECT * FROM moradores ORDER BY nome")
    ).fetchall()
    return [row_to_obj(r) for r in results]


def get_morador_by_id(morador_id):
    result = db.session.execute(
        text("SELECT * FROM moradores WHERE id = :id"), {"id": morador_id}
    ).fetchone()
    return row_to_obj(result)


def create_encomenda(cod, empresa, entregador, porteiro_id, morador_id):
    package_uuid = str(uuid.uuid4())
    now = datetime.utcnow()
    db.session.execute(
        text(
            "INSERT INTO encomendas (uuid, cod, empresa, entregador, porteiro_id, morador_id, status, data_registro) "
            "VALUES (:uuid, :cod, :empresa, :entregador, :porteiro_id, :morador_id, :status, :data_registro)"
        ),
        {
            "uuid": package_uuid,
            "cod": cod,
            "empresa": empresa,
            "entregador": entregador,
            "porteiro_id": porteiro_id,
            "morador_id": morador_id,
            "status": "pendente",
            "data_registro": now,
        },
    )
    db.session.commit()
    return package_uuid


def search_encomenda_by_uuid_prefix(prefix):
    query = (
        "SELECT e.*, p.nome AS porteiro_nome, m.nome AS morador_nome, rp.nome AS retirada_porteiro_nome "
        "FROM encomendas e "
        "LEFT JOIN porteiros p ON p.id = e.porteiro_id "
        "LEFT JOIN moradores m ON m.id = e.morador_id "
        "LEFT JOIN porteiros rp ON rp.id = e.retirada_porteiro_id "
        "WHERE e.uuid LIKE :prefix LIMIT 1"
    )
    result = db.session.execute(text(query), {"prefix": f"{prefix}%"}).fetchone()
    return row_to_obj(result)


def finalize_retirada(encomenda_id, morador_nome, porteiro_id):
    encomenda = db.session.execute(
        text("SELECT * FROM encomendas WHERE id = :id"), {"id": encomenda_id}
    ).fetchone()
    if not encomenda:
        return None
    encomenda_obj = row_to_obj(encomenda)
    if encomenda_obj.status == "retirada":
        return "already"
    morador = db.session.execute(
        text("SELECT * FROM moradores WHERE nome = :nome LIMIT 1"),
        {"nome": morador_nome},
    ).fetchone()
    if morador:
        morador_id = morador.id
    else:
        db.session.execute(
            text("INSERT INTO moradores (nome) VALUES (:nome)"), {"nome": morador_nome}
        )
        db.session.commit()
        morador_id = db.session.execute(text("SELECT last_insert_rowid()")).fetchone()[
            0
        ]
    now = datetime.utcnow()
    db.session.execute(
        text(
            "UPDATE encomendas SET status = :status, data_retirada = :data_retirada, "
            "morador_id = :morador_id, retirada_porteiro_id = :retirada_porteiro_id WHERE id = :id"
        ),
        {
            "status": "retirada",
            "data_retirada": now,
            "morador_id": morador_id,
            "retirada_porteiro_id": porteiro_id,
            "id": encomenda_id,
        },
    )
    db.session.commit()
    return "ok"


def confirm_retirada(uuid_code, porteiro_id=None):
    encomenda = db.session.execute(
        text("SELECT * FROM encomendas WHERE uuid = :uuid"), {"uuid": uuid_code}
    ).fetchone()
    if not encomenda:
        return None
    encomenda_obj = row_to_obj(encomenda)
    if encomenda_obj.status == "retirada":
        return "already"
    now = datetime.utcnow()
    db.session.execute(
        text(
            "UPDATE encomendas SET status = :status, data_retirada = :data_retirada, "
            "retirada_porteiro_id = :retirada_porteiro_id WHERE uuid = :uuid"
        ),
        {
            "status": "retirada",
            "data_retirada": now,
            "retirada_porteiro_id": porteiro_id,
            "uuid": uuid_code,
        },
    )
    db.session.commit()
    return "ok"


def get_historico():
    query = (
        "SELECT e.*, p.nome AS porteiro_nome, m.nome AS morador_nome, rp.nome AS retirada_porteiro_nome "
        "FROM encomendas e "
        "LEFT JOIN porteiros p ON p.id = e.porteiro_id "
        "LEFT JOIN moradores m ON m.id = e.morador_id "
        "LEFT JOIN porteiros rp ON rp.id = e.retirada_porteiro_id "
        "ORDER BY e.data_registro DESC"
    )
    results = db.session.execute(text(query)).fetchall()
    return [row_to_obj(r) for r in results]


def get_pendentes():
    query = (
        "SELECT e.*, p.nome AS porteiro_nome, m.nome AS morador_nome "
        "FROM encomendas e "
        "LEFT JOIN porteiros p ON p.id = e.porteiro_id "
        "LEFT JOIN moradores m ON m.id = e.morador_id "
        "WHERE e.status = :status"
    )
    results = db.session.execute(text(query), {"status": "pendente"}).fetchall()
    return [row_to_obj(r) for r in results]
