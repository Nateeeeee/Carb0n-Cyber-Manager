from database import db

class Computador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # livre, ocupado, pausado
    tempo_restante = db.Column(db.Integer, default=0)

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Float, nullable=False)
