from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import os

from controllers import (
    get_porteiro_by_email,
    create_porteiro,
    get_morador_by_unique,
    create_morador,
    search_moradores,
    create_encomenda,
    cod_pendente_existe,
    search_encomenda_by_uuid_prefix,
    finalize_retirada,
    confirm_retirada,
    get_historico,
    get_pendentes,
    get_morador_by_id,
    get_morador_by_whatsapp,
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

        if not morador_id:
            nome = request.form.get("nome")
            torre = request.form.get("torre")
            if torre:
                torre = torre.upper()
            ap = request.form.get("ap")
            if nome and torre and ap:
                morador = get_morador_by_unique(nome, torre, ap)
                if not morador:
                    create_morador(nome, torre, ap, None)
                    morador = get_morador_by_unique(nome, torre, ap)
                if morador:
                    morador_id = morador.id
            elif nome:
                moradores = search_moradores(nome=nome)
                if len(moradores) == 1:
                    morador_id = moradores[0].id

        if cod and cod_pendente_existe(cod):
            flash("Já existe uma encomenda pendente com esse código.", "danger")
            if morador_id:
                return redirect(
                    url_for("main.registrar_encomenda", morador_id=morador_id)
                )
            return redirect(
                url_for(
                    "main.registrar_encomenda",
                    nome=request.form.get("nome", ""),
                    torre=request.form.get("torre", ""),
                    ap=request.form.get("ap", ""),
                )
            )

        morador = get_morador_by_id(morador_id) if morador_id else None
        porteiro_id = session.get("porteiro_id")
        if not porteiro_id:
            flash(
                "É necessário estar logado como porteiro para registrar uma encomenda."
            )
            return redirect(url_for("main.login"))
        create_encomenda(
            cod,
            empresa,
            entregador,
            porteiro_id,
            morador.id if morador else None,
        )
        flash("Encomenda registrada com sucesso!")
        return redirect(url_for("main.dashboard"))

    morador_id_param = request.args.get("morador_id")
    nome = request.args.get("nome")
    torre = request.args.get("torre")
    if torre:
        torre = torre.upper()
    ap = request.args.get("ap")
    moradores = None
    morador_found = None
    mensagem = None

    if morador_id_param:
        morador_obj = get_morador_by_id(morador_id_param)
        if morador_obj:
            morador_found = morador_obj
            moradores = [morador_obj]
            nome = morador_obj.nome
            torre = morador_obj.torre
            ap = morador_obj.ap
        else:
            mensagem = "Morador não encontrado."
    elif nome:
        moradores = search_moradores(nome=nome)
        if not moradores:
            mensagem = "Nenhum morador encontrado com esse nome."
        elif len(moradores) == 1:
            morador_found = moradores[0]
            nome = morador_found.nome
            torre = morador_found.torre
            ap = morador_found.ap
    elif torre and ap:
        moradores = search_moradores(torre=torre, ap=ap)
        if not moradores:
            mensagem = "Nenhum morador encontrado para esse bloco e apartamento."
        elif len(moradores) == 1:
            morador_found = moradores[0]
            nome = morador_found.nome
            torre = morador_found.torre
            ap = morador_found.ap

    empresas = ["Correios", "Mercado Livre", "Amazon", "Shopee", "Outro"]
    return render_template(
        "registrar.html",
        moradores=moradores,
        morador_found=morador_found,
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
    moradores_endereco = None
    searched = False
    search_uuid = None

    if request.method == "POST":
        searched = True
        search_uuid = request.form.get("uuid")
    else:
        search_uuid = request.args.get("uuid")
        if search_uuid:
            searched = True

    if search_uuid:
        encomenda = search_encomenda_by_uuid_prefix(search_uuid)
        if encomenda:
            if getattr(encomenda, "torre", None) and getattr(encomenda, "ap", None):
                moradores_endereco = search_moradores(
                    torre=encomenda.torre, ap=encomenda.ap
                )
        else:
            flash("Encomenda não encontrada.")

    return render_template(
        "retirar.html",
        encomenda=encomenda,
        searched=searched,
        moradores_endereco=moradores_endereco,
    )


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
        flash("Encomenda retirada com sucesso.")
    return redirect(url_for("main.dashboard"))


@bp.route("/historico")
@login_required
def historico():
    encomendas = get_historico()
    return render_template("historico.html", encomendas=encomendas)


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
        elif whatsapp and get_morador_by_whatsapp(whatsapp):
            flash("Já existe um morador com esse número de telefone.", "danger")
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
