
from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string
from flask import Flask, request, render_template, jsonify, redirect, url_for, session
from functools import wraps
from flask_migrate import Migrate
import os
import re
from werkzeug.utils import secure_filename
from flask import request, render_template, redirect
import requests
from bs4 import BeautifulSoup

DOMINIOS_FALSOS = {
    "youtube": ["youtube.c0m.lat", "y0utube.com.br", "you-tube.video"],
    "facebook": ["faceb00k.page", "facebooke.live", "f4cebook.com"],
    "instagram": ["1nstagram.store", "insta-gram.pics"],
    "tiktok": ["t1kt0k.video", "tik-tok.click"],
    "kwai": ["kwaii.link", "kwai-br.fun"],
    "whatsapp": ["whatszap.click", "wpp.me-confirma.live"],
    "mercado_pago": ["mpago.site", "mercado-br.online"],
    "nubank": ["nub4nk.app", "nubanq.link"],
    "maps": ["maps-google.place", "g0oglemaps.live"]
}

CAMINHOS_FALSOS = {
    "youtube": ["/watch?v={slug}", "/live/{slug}"],
    "facebook": ["/profile.php?id={slug}", "/story.php?story_fbid={slug}"],
    "instagram": ["/p/{slug}", "/reel/{slug}"],
    "tiktok": ["/@user/video/{slug}", "/v/{slug}"],
    "kwai": ["/video/{slug}", "/share/{slug}"],
    "whatsapp": ["/chat/{slug}", "/group/join/{slug}"],
    "mercado_pago": ["/cobranca/{slug}", "/pagamento/{slug}"],
    "nubank": ["/boleto/{slug}", "/pix/{slug}"],
    "maps": ["/place/{slug}", "/dir/?api=1&destination={slug}"]
}

def gerar_link_falso(slug, plataforma="youtube"):
    dominio = random.choice(DOMINIOS_FALSOS.get(plataforma, DOMINIOS_FALSOS["youtube"]))
    caminho = random.choice(CAMINHOS_FALSOS.get(plataforma, [f"/{slug}"]))
    return f"https://{dominio}{caminho}"


app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'P@licia1080#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'dados.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔧 Garante que a pasta existe (essencial no Render)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def imagem_permitida(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_imagem", methods=["POST"])
def upload_imagem():
    if 'imagem' not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada"}), 400
    
    imagem = request.files['imagem']
    
    if imagem.filename == '':
        return jsonify({"erro": "Nome de arquivo inválido"}), 400
    
    if imagem and imagem_permitida(imagem.filename):
        filename = secure_filename(imagem.filename)
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagem.save(caminho)

        # Gera URL pública
        url_imagem = url_for('static', filename=f'uploads/{filename}', _external=True)
        return jsonify({"url": url_imagem})
    
    return jsonify({"erro": "Formato de imagem não permitido"}), 400

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Cria a pasta, se não existir (isso resolve o erro no Render)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

class IPInicial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255))
    ip = db.Column(db.String(50))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    
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
    
# Tabela de acessos
class RegistroAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), db.ForeignKey('link.slug'))
    link = db.relationship('Link', backref='acessos')
    ip = db.Column(db.String(100))
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    foto_base64 = db.Column(db.Text)
    sistema = db.Column(db.String(100))
    navegador = db.Column(db.String(200))
    idioma = db.Column(db.String(50))
    fuso_horario = db.Column(db.String(100))
    conexao = db.Column(db.String(100))
    largura_tela = db.Column(db.String(20))
    altura_tela = db.Column(db.String(20))
    tempo_segundos = db.Column(db.Integer)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)

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
    slug = db.Column(db.String(100), db.ForeignKey('link.slug'))  # ✅ chave estrangeira
    link = db.relationship('Link', backref='registros')           # ✅ relação
with app.app_context():
    db.create_all()

# Página de criação de links
@app.route("/criar_link", methods=["GET", "POST"])
@login_requerido
def criar_link():
    if request.method == "POST":
        nome_investigado = request.form["nome_investigado"]
        destino = request.form["destino"]
        slug = request.form["slug"] or gerar_slug()
        plataforma = request.form["plataforma"]
        og_title = request.form["og_title"]
        og_description = request.form["og_description"]
        og_image = request.form["og_image"]

        if Link.query.filter_by(slug=slug).first():
            return "Slug já existe! Escolha outro.", 400

        novo_link = Link(
            slug=slug,
            destino=destino,
            nome_investigado=nome_investigado,
            plataforma=plataforma,
            og_title=og_title,
            og_description=og_description,
            og_image=og_image
        )
        db.session.add(novo_link)
        db.session.commit()

        if "127.0.0.1" in request.host_url or "localhost" in request.host_url:
            link_disfarcado = f"{request.host_url}link/{slug}"
        else:
            link_disfarcado = gerar_link_falso(slug, plataforma)

        return render_template("link_gerado.html", link=link_disfarcado)

    return render_template("criar_link.html")


# Gera slugs aleatórios
def gerar_slug(tamanho=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=tamanho))

# Acessa o link disfarçado
@app.route("/link/<slug>")
def rastrear_link(slug):
    link = Link.query.filter_by(slug=slug).first_or_404()

    user_agent = request.headers.get("User-Agent", "").lower()
    bots = ["facebookexternalhit", "twitterbot", "linkedinbot", "whatsapp", "slackbot", "telegrambot"]

    if any(bot in user_agent for bot in bots):
        try:
            # Tenta buscar os metadados reais do site de destino
            resposta = requests.get(link.destino, timeout=5)
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
            # Se der erro, usa um fallback padrão
            return render_template("preview_fallback.html", url_destino=link.destino)

    # Se não for bot, registra o acesso normalmente
    visitor_ip = request.remote_addr
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    novo = Registro(
        ip=visitor_ip,
        user_agent=request.headers.get("User-Agent"),
        timestamp=timestamp,
        slug=slug
    )
    db.session.add(novo)
    db.session.commit()

    return render_template("index.html", slug=slug, destino=link.destino, link=link)

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

    novo_registro = RegistroAcesso(
        slug=dados.get("slug"),
        ip=request.headers.get('X-Forwarded-For', request.remote_addr),
        latitude=dados.get("latitude"),
        longitude=dados.get("longitude"),
        foto_base64=dados.get("foto_base64"),
        sistema=dados.get("plataforma"),
        navegador=dados.get("userAgent"),
        idioma=dados.get("idioma"),
        fuso_horario=dados.get("fusoHorario"),
        conexao=dados.get("conexao"),
        largura_tela=dados.get("larguraTela"),
        altura_tela=dados.get("alturaTela"),
        tempo_segundos=dados.get("tempoSegundos")
    )

    db.session.add(novo_registro)
    db.session.commit()

    return jsonify({ "status": "ok", "destino": buscar_destino_por_slug(dados.get("slug")) })



@app.route("/coletar_ip_inicial", methods=["POST"])
def coletar_ip_inicial():
    dados = request.get_json()
    slug = dados.get("slug")
    ip = dados.get("ip")

    novo_ip = IPInicial(slug=slug, ip=ip)
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
