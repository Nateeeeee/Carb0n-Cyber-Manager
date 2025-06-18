from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db
from models import Computador, Config
import threading
import time

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cybercafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# Iniciando banco e dados padrão
with app.app_context():
    db.create_all()

    # PCs padrão
    pcs = ['PC01', 'PC02', 'PC03', 'PC04', 'PC05']
    for nome in pcs:
        if not Computador.query.filter_by(nome=nome).first():
            pc = Computador(nome=nome, status='livre', tempo_restante=0)
            db.session.add(pc)

    # Configs padrão
    if not Config.query.filter_by(chave="preco_hora").first():
        db.session.add(Config(chave="preco_hora", valor=5.0))
    if not Config.query.filter_by(chave="preco_impressao").first():
        db.session.add(Config(chave="preco_impressao", valor=1.0))

    db.session.commit()


    # PCs padrão
    pcs = ['PC01', 'PC02', 'PC03', 'PC04', 'PC05']
    for nome in pcs:
        if not Computador.query.filter_by(nome=nome).first():
            pc = Computador(nome=nome, status='livre', tempo_restante=0)
            db.session.add(pc)

    # Configurações padrão
    if not Config.query.filter_by(chave="preco_hora").first():
        db.session.add(Config(chave="preco_hora", valor=5.0))
    if not Config.query.filter_by(chave="preco_impressao").first():
        db.session.add(Config(chave="preco_impressao", valor=1.0))

    db.session.commit()

# Thread para descontar tempo dos PCs em uso
def tempo_descontar():
    with app.app_context():
        while True:
            pcs = Computador.query.filter(Computador.status == 'ocupado').all()
            for pc in pcs:
                if pc.tempo_restante > 0:
                    pc.tempo_restante -= 1
                    if pc.tempo_restante <= 0:
                        pc.status = 'livre'
                        pc.tempo_restante = 0
                db.session.commit()
            time.sleep(60)  # a cada 1 minuto

threading.Thread(target=tempo_descontar, daemon=True).start()

# Rotas do servidor

@app.route('/status', methods=['GET'])
def status():
    pcs = Computador.query.all()
    return jsonify([
        {'pc': pc.nome, 'status': pc.status, 'tempo_restante': pc.tempo_restante * 60  # converte minutos → segundos
} for pc in pcs
    ])

@app.route('/iniciar', methods=['POST'])
def iniciar():
    data = request.json
    nome = data.get('pc')
    tempo = data.get('tempo_minutos')

    pc = Computador.query.filter_by(nome=nome.upper()).first()
    if not pc:
        return jsonify({'erro': 'PC não encontrado'}), 404
    if pc.status == 'ocupado':
        return jsonify({'erro': 'PC já está em uso'}), 400

    pc.status = 'ocupado'
    pc.tempo_restante = tempo
    db.session.commit()

    return jsonify({'msg': f'{nome} iniciado por {tempo} minutos'})

@app.route('/pausar', methods=['POST'])
def pausar():
    data = request.json
    nome = data.get('pc')

    pc = Computador.query.filter_by(nome=nome).first()
    if not pc:
        return jsonify({'erro': 'PC não encontrado'}), 404
    if pc.status != 'ocupado':
        return jsonify({'erro': 'PC não está em uso'}), 400

    pc.status = 'pausado'
    db.session.commit()
    return jsonify({'msg': f'{nome} pausado'})

@app.route('/encerrar', methods=['POST'])
def encerrar():
    data = request.json
    nome = data['pc'].upper()

    pc = Computador.query.filter_by(nome=nome).first()
    if pc:
        pc.status = 'livre'
        pc.tempo_restante = 0
        db.session.commit()
        return jsonify({"message": f"{nome} encerrado"}), 200
    return jsonify({"error": "PC não encontrado"}), 404


@app.route('/encerrar_todos', methods=['POST'])
def encerrar_todos():
    pcs = Computador.query.all()
    for pc in pcs:
        pc.status = 'livre'
        pc.tempo_restante = 0
    db.session.commit()
    return jsonify({'msg': 'Todas as sessões encerradas'})

@app.route('/precos', methods=['GET'])
def get_precos():
    precos = Config.query.all()
    return jsonify({p.chave: p.valor for p in precos})

@app.route('/precos', methods=['POST'])
def set_preco():
    data = request.json
    chave = data.get('chave')
    valor = data.get('valor')

    config = Config.query.filter_by(chave=chave).first()
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404

    config.valor = valor
    db.session.commit()

    return jsonify({'msg': f'{chave} atualizado para {valor}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
