from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os
import qrcode
import urllib.parse

from controllers import (
    get_porteiro_by_email,
    create_porteiro,
    get_morador_by_unique,
    create_morador,
    search_moradores,
    list_moradores,
    create_encomenda,
    search_encomenda_by_uuid_prefix,
    finalize_retirada,
    confirm_retirada,
    get_historico,
    get_pendentes,
    get_morador_by_id,
)

bp = Blueprint("main", __name__)


def login_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "porteiro_id" not in session:
            return redirect(url_for("main.login"))
        return func(*args, **kwargs)

    return wrapper


@bp.route("/")
def index():
    return redirect(url_for("main.dashboard"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        porteiro = get_porteiro_by_email(email)
        from werkzeug.security import check_password_hash

        if porteiro and check_password_hash(porteiro.password_hash, password):
            session["porteiro_id"] = porteiro.id
            session["porteiro_nome"] = porteiro.nome
            return redirect(url_for("main.dashboard"))
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    pendentes = get_pendentes()
    return render_template("dashboard.html", pendentes=pendentes)


@bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar_encomenda():
    if request.method == "POST":
        cod = request.form.get("cod")
        empresa = request.form.get("empresa")
        empresa_outro = request.form.get("empresa_outro")
        if empresa == "Outro" and empresa_outro:
            empresa = empresa_outro
        entregador = request.form.get("entregador")
        morador_id = request.form.get("morador_id")
        morador = get_morador_by_id(morador_id) if morador_id else None
        package_uuid = create_encomenda(
            cod,
            empresa,
            entregador,
            session.get("porteiro_id"),
            morador.id if morador else None,
        )
        qr_dir = os.path.join(bp.root_path, "static", "qrcodes")
        os.makedirs(qr_dir, exist_ok=True)
        qr_url = url_for("main.confirmar_retirada", uuid=package_uuid, _external=True)
        qr_img = qrcode.make(qr_url)
        qr_path = os.path.join(qr_dir, f"{package_uuid}.png")
        qr_img.save(qr_path)
        shortened_id = package_uuid[:8]
        wa_link = None
        if morador and morador.whatsapp:
            phone = "".join(filter(str.isdigit, morador.whatsapp))
            message = (
                f"Sua encomenda foi registrada com o ID {shortened_id}. "
                f"Apresente este código ao porteiro para retirada."
            )
            wa_link = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
        if wa_link:
            flash(
                (
                    f"Encomenda registrada com ID {shortened_id}. "
                    f'<a href="{wa_link}" target="_blank">Enviar via WhatsApp</a>'
                ),
                "html",
            )
        else:
            flash(
                f"Encomenda registrada com ID {shortened_id}. Envie este ID ao morador."
            )
        return redirect(url_for("main.dashboard"))

    morador_id_param = request.args.get("morador_id")
    nome = request.args.get("nome")
    torre = request.args.get("torre")
    if torre:
        torre = torre.upper()
    ap = request.args.get("ap")
    moradores = None
    mensagem = None
    if morador_id_param:
        morador_obj = get_morador_by_id(morador_id_param)
        if morador_obj:
            moradores = [morador_obj]
        else:
            mensagem = "Morador não encontrado."
    elif nome:
        moradores = search_moradores(nome=nome)
        if not moradores:
            mensagem = "Nenhum morador encontrado com esse nome."
    elif torre and ap:
        moradores = search_moradores(torre=torre, ap=ap)
        if not moradores:
            mensagem = "Nenhum morador encontrado para esse bloco e apartamento."
    empresas = ["Correios", "Mercado Livre", "Amazon", "Shopee", "Outro"]
    return render_template(
        "registrar.html",
        moradores=moradores,
        empresas=empresas,
        nome=nome,
        torre=torre,
        ap=ap,
        mensagem=mensagem,
    )


@bp.route("/retirar", methods=["GET", "POST"])
@login_required
def retirar_encomenda():
    encomenda = None
    searched = False
    if request.method == "POST":
        searched = True
        search_uuid = request.form.get("uuid")
        encomenda = search_encomenda_by_uuid_prefix(search_uuid)
        if not encomenda:
            flash("Encomenda não encontrada.")
    return render_template("retirar.html", encomenda=encomenda, searched=searched)


@bp.route("/confirmar/<uuid:uuid>")
def confirmar_retirada(uuid):
    porteiro_id = session.get("porteiro_id") if "porteiro_id" in session else None
    result = confirm_retirada(str(uuid), porteiro_id)
    if result == "already":
        flash("Encomenda já retirada.")
    elif result == "ok":
        flash(f"Encomenda {str(uuid)[:8]} retirada com sucesso.")
    else:
        flash("Encomenda não encontrada.")
    return redirect(url_for("main.dashboard"))


@bp.route("/finalizar_retirada/<int:encomenda_id>", methods=["POST"])
@login_required
def finalizar_retirada_route(encomenda_id):
    morador_nome = request.form.get("morador_nome")
    result = finalize_retirada(encomenda_id, morador_nome, session.get("porteiro_id"))
    if result == "already":
        flash("Encomenda já retirada.")
    elif result is None:
        flash("Encomenda não encontrada.")
    else:
        flash("Retirada registrada com sucesso.")
    return redirect(url_for("main.dashboard"))


@bp.route("/historico")
@login_required
def historico():
    encomendas = get_historico()
    return render_template("historico.html", encomendas=encomendas)


@bp.route("/moradores")
@login_required
def listar_moradores():
    moradores = list_moradores()
    return render_template("lista_moradores.html", moradores=moradores)


@bp.route("/cadastrar_morador", methods=["GET", "POST"])
@login_required
def cadastrar_morador_route():
    if request.method == "POST":
        nome = request.form.get("nome")
        torre = request.form.get("torre")
        if torre:
            torre = torre.upper()
        ap = request.form.get("ap")
        whatsapp = request.form.get("whatsapp")
        existing = get_morador_by_unique(nome, torre, ap)
        if existing:
            flash("Já existe um morador com esse nome e apartamento.")
        else:
            create_morador(nome, torre, ap, whatsapp)
            flash("Morador cadastrado com sucesso.")
            return redirect(url_for("main.cadastrar_morador_route"))
    return render_template("cadastrar_morador.html")


@bp.route("/cadastrar_porteiro", methods=["GET", "POST"])
@login_required
def cadastrar_porteiro_route():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        password = request.form.get("password")
        if get_porteiro_by_email(email):
            flash("Já existe um porteiro com esse email.")
        else:
            create_porteiro(nome, email, password)
            flash("Porteiro cadastrado com sucesso.")
            return redirect(url_for("main.cadastrar_porteiro_route"))
    return render_template("cadastrar_porteiro.html")
