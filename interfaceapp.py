import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox
import pygubu
import pygubu.builder.tkstdwidgets
import pygubu.builder.ttkstdwidgets
import database as db
import sqlalchemy
import sqlalchemy.sql.default_comparator
import sqlalchemy.ext.baked

#PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
#PROJECT_UI = os.path.join(PROJECT_PATH, "Interface.ui")

class JanelaLogin(tk.Tk):
	''' Janela de Login'''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_login')
		janela.__class__ = cls
		janela.app = app
		# obter elementos da janela
		janela.campo_usuario = app.builder.get_object('e_usuario')
		janela.campo_senha = app.builder.get_object('e_senha')
		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", app.sair)
		# retornar janela
		return janela

	def botao_entrar(self):
		try:
			# obter dados cadastrais
			login = self.campo_usuario.get()
			senha = self.campo_senha.get()
			# authenticar usuario
			self.app.usuario, erro = db.authenticar(login, senha)
			if self.app.usuario:
				self.withdraw()
				self.app.principal.deiconify()
			else:
				tkinter.messagebox.showerror('Erro', erro)
		finally:
			# self.campo_usuario.delete(0, 'end')
			self.campo_senha.delete(0, 'end')

class JanelaPrincipal(tk.Tk):
	''' Janela Principal '''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_main')
		janela.__class__ = cls
		janela.app = app
		# definir estado padrão como invisivel
		janela.withdraw()
		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", app.sair)
		# retornar janela
		return janela

	def botao_vendas(self):
		# verificar acesso do usuario
		if not self.app.usuario.privilegios.alterar_usuarios:
			return tkinter.messagebox.showerror(
				f'{self.app.usuario.login}',
				f'Você não tem privilégios suficientes para acessar esta seção'
			)
		# exibir janela vendas
		self.app.vendas.atualizar()
		self.app.vendas.deiconify()

	def botao_controle(self):
		# exibir janela controle de estoque
		self.app.controle.atualizar_produtos()
		self.app.controle.deiconify()

	def botao_compras(self):
		# verificar acesso do usuario
		if not self.app.usuario.privilegios.alterar_produtos:
			return tkinter.messagebox.showerror(
				f'{self.app.usuario.login}',
				f'Você não tem privilégios suficientes para acessar esta seção!'
			)
		# exibir janela gerenciamento de produtos
		self.app.produtos.deiconify()
		
	def botao_usuarios(self):
		# verificar acesso do usuario
		if not self.app.usuario.privilegios.alterar_usuarios:
			return tkinter.messagebox.showerror(
				f'{self.app.usuario.login}',
				f'Você não tem privilégios suficientes para acessar esta seção!'
			)
		# exibir janela gerenciamento de usuarios
		self.app.usuarios.deiconify()
		self.app.usuarios.atualizar()
	
	def botao_relatorios(self):
		self.app.relatorios.deiconify()

	def botao_desconectar(self):
		self.app.usuario = None
		self.app.revalidar_usuario()

class JanelaUsuarios(tk.Tk):
	''' Janela Gerenciamento de Usuarios '''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_usuarios')
		janela.__class__ = cls
		janela.app = app
		# definir estado padrão como invisivel
		janela.withdraw()
		# obter elementos da janela
		janela.lista = app.builder.get_object('list_usuarios')
		janela.usuario = app.builder.get_object('e_usuario2')
		janela.senha = app.builder.get_object('e_senha2')
		janela.ativo = app.builder.get_variable('cb_v_ativo')
		janela.alterar_usuarios = app.builder.get_variable('cb_v_alterar_usuarios')
		janela.alterar_produtos = app.builder.get_variable('cb_v_alterar_produtos')
		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", janela.withdraw)
		janela.lista.bind("<<ListboxSelect>>", janela.evento_selecionar)
		# retornar janela
		return janela

	def atualizar(self):
		# limpar lista de usuarios
		self.lista.delete(0, 'end')
		# adicionar usuarios na lista
		for usuario in db.Usuario.query.all():
			self.lista.insert(0, usuario.login)

	def limpar(self):
		self.usuario.delete(0, 'end')
		self.senha.delete(0, 'end')
		self.ativo.set(False)
		self.alterar_usuarios.set(False)
		self.alterar_produtos.set(False)
	
	def evento_selecionar(self, evento):
		# obter seleções na lista
		if selecionados := evento.widget.curselection():
			# obter primeiro da lista de selecao ( bloqueado na interface single )
			usuario_selecionado = evento.widget.get(selecionados[0])
			# obter usuario no banco de dados
			usuario = db.Usuario.obter(usuario_selecionado)
			# verificar se o usuario é valido
			if not usuario:
				self.atualizar()
				return tkinter.messagebox.showerror(
					f'Erro',
					f'O usuário selecionado parece não existir mais!'
				)
			# preencher dados do usuario
			self.limpar()
			self.usuario.insert(0, usuario.login)
			self.senha.insert(0, usuario.senha)
			self.ativo.set(usuario.ativo)
			self.alterar_usuarios.set(usuario.privilegios.alterar_usuarios)
			self.alterar_produtos.set(usuario.privilegios.alterar_produtos)

	def salvar(self):
		# obter usuario da listbox
		usuario_selecionado = self.lista.get(tk.ACTIVE)
		# obter usuario no banco de dados
		usuario = db.Usuario.obter(usuario_selecionado)
		# verificar se o usuario é valido
		if not usuario:
			self.atualizar()
			return tkinter.messagebox.showerror(
				f'Erro',
				f'O usuário selecionado parece não existir mais!'
			)
		# preencher novas informacoes
		usuario.login = self.usuario.get()
		usuario.senha = self.senha.get()
		usuario.ativo = self.ativo.get()
		usuario.privilegios.alterar_usuarios = self.alterar_usuarios.get()
		usuario.privilegios.alterar_produtos = self.alterar_produtos.get()
		# salvar dados no banco de dados
		db.update()
		# atualizar usuario da sessao
		if usuario_selecionado == self.app.usuario.login:
			self.app.usuario = usuario
			self.app.revalidar_usuario()
		# atualizar a interface
		self.atualizar()
		self.limpar()

	def adicionar(self):
		# obter uma nova sessão no banco de dados
		sessao = db.SessionFactory()
		try:
			# adicionar usuario
			sessao.add(db.Usuario(
				login=self.usuario.get(),
				senha=self.senha.get(),
				privilegios = db.Privilegios(
					alterar_usuarios = self.alterar_usuarios.get(),
					alterar_produtos = self.alterar_produtos.get()
				)
			))
			# confirmar todas alteraçoes feitas nesta sessão
			sessao.commit()
			# limpar campos
			self.limpar()
		except sqlalchemy.exc.IntegrityError as error:
			# cancelar todas alterações feitas nesta sessão
			sessao.rollback()
			# exibir mensagem de erro
			tkinter.messagebox.showerror(
				f'Erro',
				f'[ {error.code} ]: {error.args[0]}'
			)
		finally:
			# fechar sessao
			sessao.close()
			# atualizar a interface
			self.atualizar()

	def deletar(self):
		# obter usuario da listbox
		usuario_selecionado = self.lista.get(tk.ACTIVE)
		# deletar usuario
		sessao = db.SessionFactory()
		try:
			# deletar o usuario selecionado
			sessao.query(db.Usuario).filter_by(login=usuario_selecionado).delete()
			# confirmar todas alteraçoes feitas nesta sessão
			sessao.commit()
		except sqlalchemy.exc.IntegrityError as error:
			# cancelar todas alterações feitas nesta sessão
			sessao.rollback()
			# exibir mensagem de erro
			tkinter.messagebox.showerror(
				f'Erro',
				f'[ {error.code} ]: {error.args[0]}'
			)
		finally:
			# fechar sessao
			sessao.close()
		# atualizar a interface
		self.atualizar()
		# revalidar meu usuario
		if usuario_selecionado == self.app.usuario.login:
			self.app.usuario = None
			self.app.revalidar_usuario()

class JanelaControle(tk.Tk):
	''' Janela Controle de Estoque '''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_controle')
		janela.__class__ = cls
		janela.app = app
		# definir estado padrão como invisivel
		janela.withdraw()
		# obter elementos da janela
		janela.produtos = app.builder.get_object('tree_produtos')
		janela.filtro = app.builder.get_object('e_produto_filtro')
		janela.estoque = app.builder.get_object('list_produto_estoque')
		janela.unidades = app.builder.get_object('l_unidades')
		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", janela.withdraw)
		janela.filtro.bind('<Key-Return>', janela.filtrar_produtos)
		janela.produtos.bind('<<TreeviewSelect>>', janela.selecionar_produto)
		# retornar janela
		return janela

	def atualizar_produtos(self, filtro = None):
		# não filtrar produtos
		if filtro in [None, '']:
			filtro = '%'
		# limpar produtos
		for item in self.produtos.get_children():
			self.produtos.delete(item)
		# atualizar produtos
		for produto in db.Produto.query.filter(db.Produto.nome.like(filtro)).all():
			self.produtos.insert('', 'end', produto.id, text=produto.nome, values=(produto.id))

	def filtrar_produtos(self, widget):
		self.atualizar_produtos(self.filtro.get())

	def selecionar_produto(self, widget):
		# obter lista de seleção
		if selecionados := self.produtos.selection():
			# obter primeiro na lista de seleção
			produto_item = self.produtos.item(selecionados[0])
			produto_id, = produto_item['values']
			# obter produto no banco
			produto = db.Produto.obter(id=produto_id)
			# limpar lista de usuarios
			self.estoque.delete(0, 'end')
			# adicionar usuarios na lista
			for estoque in db.Estoque.query.filter_by(id_produto=produto.id).all():
				data = estoque.data.strftime('%d/%m/%Y %H:%M:%S')

				if estoque.operacao == 'Compra de Estoque':
					self.estoque.insert(0, f'[ {data}  ] Operação: {estoque.operacao}, Quantidade: {estoque.quantidade}, Preço de Compra: {estoque.produto.preco:.2f}')

				else:
					self.estoque.insert(0, f'[ {data}  ] Operação: {estoque.operacao}, Quantidade: {abs(estoque.quantidade)}')
			#
			self.unidades.config(text = produto.obter_quantidade())

class JanelaVendas(tk.Tk):
	''' Janela de Vendas '''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_vendas')
		janela.__class__ = cls
		janela.app = app
		# definir estado padrão como invisivel
		janela.withdraw()
		# obter elementos da janela
		janela.estoque = app.builder.get_object('tree_estoque')
		janela.carrinho = app.builder.get_object('tree_carrinho')
		janela.spin_add = app.builder.get_variable('spin_v_add')
		janela.spin_del = app.builder.get_variable('spin_v_del')
		# configurar titulo das treeviews
		janela.estoque['columns'] = janela.carrinho['columns'] = (
			'Produto', 'Und'
		)
		for tree in [janela.estoque, janela.carrinho]:
			tree.column('#0', width=0, stretch='no')
			tree.column('Produto', anchor='center', width=130)
			tree.column('Und', anchor='center', width=80)
			tree.heading('#0', text='Id')
			tree.heading('Produto', text='Produto')
			tree.heading('Und', text='Und')
		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", janela.withdraw)
		# retornar janela
		return janela
	
	def atualizar(self):
		# limpar estoque
		for item in self.estoque.get_children():
			self.estoque.delete(item)
		# limpar carrinho
		for item in self.carrinho.get_children():
			self.carrinho.delete(item)
		# adicionar produtos
		for produto in db.Produto.query.all():
			self.estoque.insert(parent='', index=0, iid=produto.id, values=(produto.nome, produto.obter_quantidade()))
		# limpar spins
		self.spin_add.set(0)
		self.spin_del.set(0)

	def botao_add(self):
		# obter produto selecionado
		if focus := self.estoque.focus():
			# obter estoque
			produto = db.Produto.obter(id=focus)
			# obter unidades
			unidades_no_estoque = produto.obter_quantidade()
			unidades_atual = int(self.carrinho.set(focus, 1) if self.carrinho.exists(focus) else 0)
			unidades_a_adicionar = self.spin_add.get()
			unidades_a_definir = unidades_a_adicionar + unidades_atual
			# validar quantidade
			if unidades_a_adicionar == 0:
				return None
			elif unidades_a_definir > unidades_no_estoque:
				self.spin_add.set(0)
				return tkinter.messagebox.showerror(
					f'Erro',
					f'Desculpe, mas você não pode vender {unidades_a_definir} unidades pois só existem {unidades_no_estoque} unidades no estoque.'
				)
			# adicionar ou substituir no carrinho
			if unidades_atual > 0:
				self.carrinho.set(focus, 1, unidades_a_definir)
			else:
				self.carrinho.insert(
					parent='',
					index=0,
					iid=focus,
					text=focus,
					values=(produto.nome, unidades_a_definir)
				)
			# atualizar quantidade
			self.estoque.set(focus, 1, unidades_no_estoque - unidades_a_definir)
			# limpar spin
			self.spin_add.set(0)
		
	def botao_remover(self):
		# obter produto selecionado
		if focus := self.carrinho.focus():
			# obter unidades
			estoque_und = int(self.estoque.set(focus, 1))
			carrinho_und = int(self.carrinho.set(focus, 1))
			unidades_a_remover = min(self.spin_del.get(), carrinho_und)
			unidades_a_definir = carrinho_und - unidades_a_remover
			#
			if unidades_a_remover >= carrinho_und:
				self.carrinho.delete(focus)
			else:
				self.carrinho.set(focus, 1, unidades_a_definir)
			# atualizar estoque
			self.estoque.set(focus, 1, estoque_und + unidades_a_remover)
			# limpar spin
			self.spin_del.set(0)

	def botao_finalizar(self):
		# listar produtos
		for produto_id in self.carrinho.get_children():
			quantidade = -int(self.carrinho.set(produto_id, 1))
			db.Estoque.add(produto_id, 'Vendido', quantidade)
		# atualizar tela
		self.atualizar()
		self.app.controle.selecionar_produto(None)

class JanelaProdutos(tk.Tk):
	''' Janela Controle de Estoque '''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_produtos')
		janela.__class__ = cls
		janela.app = app
		# definir estado padrão como invisivel
		janela.withdraw()
		# obter elementos da janela
		janela.produto = app.builder.get_object('e_produto')
		janela.qtd_produto = app.builder.get_variable('spin_v_qtd_produto')
		janela.preco_compra = app.builder.get_object('e_preco_compra')

		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", janela.withdraw)

		# retornar janela
		return janela

	def limpar(self):
		self.produto.delete(0, 'end')
		self.preco_compra.delete(0, 'end')
		self.qtd_produto.set(0)

	def botao_registrar(self):
		# obter produto da caixa de texto
		produto_nome = self.produto.get()
		if not produto_nome or produto_nome == "":
			return tkinter.messagebox.showerror(
				f'Erro',
				'Preencha o campo de nome do produto!'
			)
		# obter quantidade a adicionar da caixa de texto
		produto_qtd = self.qtd_produto.get()
		# verificar se a quantidade de produtos a adicionar é maior do que 0
		if produto_qtd <= 0:
			return tkinter.messagebox.showerror(
				f'Erro',
				'A quantidade de produtos deve ser maior do que 0!'
			)
		# obter preço de compra
		preco_compra_string = self.preco_compra.get()
		# verificar se o preço de compra é valido
		if not preco_compra_string or preco_compra_string == "":
			return tkinter.messagebox.showerror(
				f'Erro',
				'Preencha o campo de preço de compra!'
			)
		
		try:
			preco_compra = round(float(preco_compra_string), 2)
		except:
			return tkinter.messagebox.showerror(
				f'Erro',
				'Preço de compra inválido! Exemplo de preço válido: 10.25'
			)

		if preco_compra <= 0:
			return tkinter.messagebox.showerror(
				f'Erro',
				'Preço de compra deve ser maior do que 0!'
			)
		
		# obter uma nova sessão no banco de dados
		sessao = db.Session
		try:
			# obter produto no banco de dados
			produto = db.Produto.obter(nome=produto_nome)
			# adicionar produto ao estoque
			sessao.add(db.Estoque(
				produto = db.Produto(
					nome = produto_nome,
					categoria = db.ProdutoCategoria.frutas,
					preco = preco_compra,
				) if not produto else produto,
				operacao = 'Compra de Estoque',
				quantidade = produto_qtd
			))
			# confirmar todas alteraçoes feitas nesta sessão
			sessao.commit()
			# limpar campos
			self.limpar()
			# atualizar janela de controle
			self.app.controle.atualizar_produtos()
		except sqlalchemy.exc.IntegrityError as error:
			# exibir mensagem de erro
			tkinter.messagebox.showerror(
				f'Erro',
				f'[ {error.code} ]: {error.args[0]}'
			)

class JanelaRelatorios(tk.Tk):
	''' Janela de Relatorios '''

	@classmethod
	def setup(cls, app):
		# obter instancia da janela
		janela = app.builder.get_object('window_relatorios')
		janela.__class__ = cls
		janela.app = app
		# definir estado padrão como invisivel
		janela.withdraw()
		# obter elementos da janela
		janela.combo_relatorio = app.builder.get_object('cb_relatorio')
		janela.relatorio = app.builder.get_object('list_relatorio')
		janela.modelo = app.builder.get_variable('cb_v_relatorio')
		# definir modelos de relatorio
		janela.combo_relatorio['values'] = (
			'Todas as vendas',
			'Menos vendidos nos últimos 30 dias',
		)
		# definir eventos da janela
		janela.protocol("WM_DELETE_WINDOW", janela.withdraw)
		janela.combo_relatorio.bind("<<ComboboxSelected>>", janela.evento_selecionar_relatorio)
		# retornar janela
		return janela

	def evento_selecionar_relatorio(self, widget):
		# Todas as vendas
		if self.modelo.get() == self.combo_relatorio['values'][0]:
			# limpar relatorio
			self.relatorio.delete(0, 'end')
			# relatorio
			for estoque in db.Estoque.query.filter_by(operacao='Vendido').order_by(db.Estoque.data.desc()).all():
				data = estoque.data.strftime('%d/%m/%Y %H:%M:%S')
				self.relatorio.insert('end', f'[{data}] Produto: {estoque.produto.nome}, Unidades: {abs(estoque.quantidade)}')
		# Menos vendidos
		elif self.modelo.get() == self.combo_relatorio['values'][1]:
			# extrair produtos no banco de dados, com filtros e grupos
			operacoes = db.Session.query(
				db.Estoque,
				db.func.sum(db.Estoque.quantidade).label("total")
			).join(
				'produto'
			).filter(
				db.Estoque.operacao=='Vendido',
				db.Estoque.data >= db.datetime.today() - db.timedelta(days = 30)
			).group_by(
				db.Estoque.id_produto
			).order_by(
				db.desc('total')
			).all()
			# limpar relatorio
			self.relatorio.delete(0, 'end')
			# iterar produtos
			for estoque, total in operacoes:
				data = estoque.data.strftime('%d/%m/%Y %H:%M:%S')
				self.relatorio.insert('end', f'[{data}] Produto: {estoque.produto.nome}, Unidades: {abs(total)}')

class InterfaceApp:
	''' '''

	def __init__(self, master=None):
		# iniciar builder
		self.builder = pygubu.Builder()

		try:
			approot = os.path.dirname(os.path.abspath(__file__))
		except NameError:
			approot = os.path.dirname(os.path.abspath(sys.argv[0]))

		appui = os.path.join(approot, "Interface.ui")
		appicon = os.path.join(approot, "icone.ico")

		self.builder.add_resource_path(approot)
		self.builder.add_from_file(appui)

		# iniciar membros do sistema
		self.usuario = None
		# iniciar janelas
		self.login = JanelaLogin.setup(self)
		self.principal = JanelaPrincipal.setup(self)
		self.usuarios = JanelaUsuarios.setup(self)
		self.controle = JanelaControle.setup(self)
		self.vendas = JanelaVendas.setup(self)
		self.produtos = JanelaProdutos.setup(self)
		self.relatorios = JanelaRelatorios.setup(self)
		# atribuir callbacks nos elementos
		self.builder.connect_callbacks({
			# login
			'botao_entrar': self.login.botao_entrar,
			# principal
			'botao_vendas': self.principal.botao_vendas,
			'botao_controle': self.principal.botao_controle,
			'botao_compras': self.principal.botao_compras,
			'botao_usuarios': self.principal.botao_usuarios,
			'botao_relatorios': self.principal.botao_relatorios,
			'botao_desconectar': self.principal.botao_desconectar,
			# vendas
			'botao_add': self.vendas.botao_add,
			'botao_remover': self.vendas.botao_remover,
			'botao_finalizar': self.vendas.botao_finalizar,
			# produtos
			'botao_registrar': self.produtos.botao_registrar,
			# usuarios
			'botao_salvar': self.usuarios.salvar,
			'botao_adicionar': self.usuarios.adicionar,
			'botao_deletar': self.usuarios.deletar
		})

		# definir icone para cada janela
		self.login.iconbitmap(appicon)
		self.principal.iconbitmap(appicon)
		self.usuarios.iconbitmap(appicon)
		self.controle.iconbitmap(appicon)
		self.vendas.iconbitmap(appicon)
		self.produtos.iconbitmap(appicon)
		self.relatorios.iconbitmap(appicon)

	def revalidar_usuario(self):
		# validar sessão
		if self.usuario is None or not self.usuario.ativo:
			self.principal.withdraw()
			self.usuarios.withdraw()
			self.controle.withdraw()
			self.vendas.withdraw()
			self.relatorios.withdraw()
			self.produtos.withdraw()
			self.login.deiconify()

		else:
			# validar permissões de alterar usuários
			if not self.usuario.privilegios.alterar_usuarios:
				self.usuarios.withdraw()
			# validar permissões de alterar produtos
			if not self.usuario.privilegios.alterar_produtos:
				self.produtos.withdraw()


	def iniciar(self):
		self.login.mainloop()

	def sair(self):
		self.login.destroy()

if __name__ == '__main__':
	app = InterfaceApp()
	app.iniciar()