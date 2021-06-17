#!/usr/bin/python
# -*- coding: utf-8 -*-
import enum
from contextlib import contextmanager
from datetime import datetime, timedelta
from sqlalchemy import create_engine, desc, func, Column, Enum, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.sql.sqltypes import Float
import configs

# create engine
engine = create_engine(configs.database_uri, echo=configs.database_echo)

# 
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

# 
Base = declarative_base(bind=engine)
Base.query = Session.query_property()

class Privilegios(Base):
	__tablename__	= 'privilegios'
	id				= Column(Integer, primary_key=True)
	usuario_id		= Column(Integer, ForeignKey("usuario.id"), unique=True)
	alterar_usuarios= Column(Boolean, default=False)
	alterar_produtos= Column(Boolean, default=False)

class Usuario(Base):
	__tablename__	= 'usuario'
	id				= Column(Integer, primary_key=True)
	login			= Column(String, unique=True)
	senha		 	= Column(String, default=None)
	ativo			= Column(Boolean, default=True)
	privilegios		= relationship("Privilegios", uselist=False)

	@classmethod
	def obter(cls, login):
		return cls.query.filter(cls.login == login).first()

class ProdutoCategoria(enum.Enum):
	frutas = 1

class Produto(Base):
	__tablename__	= 'produto'
	id				= Column(Integer, primary_key=True)
	nome			= Column(String)
	preco			= Column(Float, default=1)
	quantidade_min	= Column(Integer, default=1)
	categoria		= Column(Enum(ProdutoCategoria))

	@classmethod
	def obter(cls, *args, **kwargs):
		return cls.query.filter_by(*args, **kwargs).first()

	def obter_quantidade(self):
		sessao = Session()
		return sessao.query(
			func.sum(Estoque.quantidade).label("total")
		).filter(
			Estoque.id_produto == self.id
		).first().total

class Estoque(Base):
	__tablename__	= 'estoque'
	id				= Column(Integer, primary_key=True)
	id_produto		= Column(Integer, ForeignKey("produto.id"))
	data			= Column(DateTime, default=datetime.utcnow)
	produto			= relationship("Produto", uselist=False)
	operacao		= Column(String)
	quantidade		= Column(Integer)

	@classmethod
	def add(cls, produto, operacao, quantidade):
		sessao = Session()
		try:
			sessao.add(Estoque(
				id_produto = produto,
				operacao = operacao,
				quantidade = quantidade,
			))
			sessao.commit()
			return True
		except Exception as error:
			sessao.rollback()
			return False

def criar_tabelas():
	return Base.metadata.create_all()

@contextmanager
def session_scope():
	"""Provide a transactional scope around a series of operations."""
	session = SessionFactory()
	try:
		yield session
		session.commit()
	except:
		session.rollback()
		raise
	finally:
		session.close()

def obter_sessao():
	return SessionFactory()

def update():
	Session.commit()

def rollback():
	Session.rollback()

def add_usuario(usuario):
	sessao = obter_sessao()
	sessao.add(usuario)
	sessao.commit()

def deletar_usuario(usuario):
	sessao = obter_sessao()
	sessao.delete(usuario)
	sessao.commit()

def authenticar(login, senha):
    # obter usuario no banco de dados
	usuario = Usuario.query.filter(Usuario.login == login).first()
	# validar usuario retornado do banco de dados
	if not usuario:
		return None, 'O usuário informado não existe.'
	# validar se o usuario esta ativo
	if not usuario.ativo:
		return None, 'O usuario está bloqueado de acessar o sistema.'
	# validar senha do usuario
	if usuario.senha != senha:
		return None, 'A senha informada não é valida.'
	# o usuario é valido	
	if usuario.ativo:
		return usuario, 'Logado com sucesso.'

if __name__ == "__main__":
	criar_tabelas()
	sessao = obter_sessao()
	abacaxi = Produto(
		nome = "Camisa Polo",
		categoria = ProdutoCategoria.frutas,
		preco = 10,
	)
	sessao.add(abacaxi)
	laranja = Produto(
		nome = "Calça Jeans",
		categoria = ProdutoCategoria.frutas,
		preco = 10,
	)
	sessao.add(laranja)
	#print("Adicionando estoque")
	sessao.add(Estoque(
		produto = laranja,
		operacao = 'Compra de Estoque',
		quantidade = 10
	))
	sessao.add(Estoque(
		produto = laranja,
		operacao = 'Compra de Estoque',
		quantidade = 20
	))
	sessao.add(Estoque(
		produto = abacaxi,
		operacao = 'Compra de Estoque',
		quantidade = 20
	))
	#print("Adicionando usuarios")
	sessao.add_all([
		Usuario(
			login="admin",
			senha="admin",
			privilegios = Privilegios(
				alterar_usuarios = True,
				alterar_produtos = True
			)
		),
	])
	sessao.commit()