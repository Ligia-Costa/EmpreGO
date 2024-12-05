from flask import Flask, render_template, request, redirect, session, send_from_directory
from mysql.connector import Error
from config import * #config.py
from db_functions import * #funções DB
import os
import time

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config['UPLOAD_FOLDER'] = 'uploads/'  # é a pastinha upload que irá receber os arquivos enviados pelo usuário

#ROTA DA PÁGINA INICIAL (TODOS ACESSAM)
@app.route('/')
def index():
    if session:
        if 'adm' in session:
            login = 'adm'
        else:
            login = 'empresa'
    else:
        login = False

    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa 
        FROM vaga 
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa
        WHERE vaga.status = 'ativa'
        ORDER BY vaga.id_vaga DESC;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL)
        vagas = cursor.fetchall()
        return render_template('index.html', vagas=vagas, login=login)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

# ROTA DA PÁGINA DE LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session:
        if 'adm' in session:
            return redirect('/adm')
        else:
            return redirect('/empresa')

    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        if not email or not senha:  # Corrigi aqui para verificar ambos os campos corretamente
            erro = "Os campos precisam estar preenchidos!"
            return render_template('login.html', msg_erro=erro)

        if email == MASTER_EMAIL and senha == MASTER_PASSWORD:
            session['adm'] = True
            return redirect('/adm')

        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE email = %s AND senha = %s'
            cursor.execute(comandoSQL, (email, senha))
            empresa = cursor.fetchone()

            if not empresa:
                return render_template('login.html', msgerro='E-mail e/ou senha estão errados!')

            # Acessar os dados como dicionário
            if empresa['status'] == 'inativa':
                return render_template('login.html', msgerro='Empresa desativada! Procure o administrador!')

            session['id_empresa'] = empresa['id_empresa']
            session['nome_empresa'] = empresa['nome_empresa']
            return redirect('/empresa')
        
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA DA PÁGINA DO ADMIN
@app.route('/adm')
def adm():
    #Se não houver sessão ativa
    if not session:
        return redirect('/login')
    #Se não for o administrador
    if not 'adm' in session:
        return redirect('/empresa')
  
    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM Empresa WHERE status = "ativa"'
        cursor.execute(comandoSQL)
        empresas_ativas = cursor.fetchall()

        comandoSQL = 'SELECT * FROM Empresa WHERE status = "inativa"'
        cursor.execute(comandoSQL)
        empresas_inativas = cursor.fetchall()

        return render_template('adm.html', empresas_ativas=empresas_ativas, empresas_inativas=empresas_inativas)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

#ROTA PARA ABRIR E RECEBER AS INFORMAÇÕES DE UMA NOVA EMPRESA
@app.route('/cadastrar_empresa', methods=['POST', 'GET'])
def cadastrar_empresa():
    #Verificar se tem uma sessão/login
    if not session:
        return redirect('/login')
    
    #Se não for o ADM -- Irá para login
    if not 'adm' in session:
        return redirect('/empresa')
    
    #Acesso ao formulário de cadastro
    if request.method == 'GET':
        return render_template('cadastrar_empresa.html')
    
    #Tratando os dados vindo do formulário
    if request.method == 'POST':
        nome_empresa = request.form['nome_empresa']
        cnpj = limpar_input(request.form['cnpj'])
        telefone = limpar_input(request.form['telefone'])
        email = request.form['email']
        senha = request.form['senha']

    #Verificar se os campos estão preenchidos
        if not nome_empresa or not cnpj or not telefone or not email or not senha:
            return render_template('cadastrar_empresa.html', msg_erro="Todos os campos são obrigatórios!")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'INSERT INTO empresa (nome_empresa, cnpj, telefone, email, senha) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(comandoSQL, (nome_empresa, cnpj, telefone, email, senha))
            conexao.commit() #Para comandos DML
            return redirect('/adm')
        except Error as erro:
            if erro.errno == 1062: #Errno = erro número
                return render_template('cadastrar_empresa', msg_erro="Esse e-mail já existe!")
            else:
                return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA PARA EDITAR UMA EMPRESA
@app.route('/editar_empresa/<int:id_empresa>', methods=['GET', 'POST'])
def editar_empresa(id_empresa):
    if not session:
        return redirect('/login')
    
    if not session['adm']:
        return redirect('/login')
    
    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM empresa WHERE id_empresa = %s'  
            cursor.execute(comandoSQL, (id_empresa,))
            empresa = cursor.fetchone()
            return render_template('editar_empresa.html', empresa=empresa)
        except Error as erro:
            return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

        #Tratando os dados vindo do formulário
    if request.method == 'POST':
        nome_empresa = request.form['nome_empresa']
        cnpj = limpar_input(request.form['cnpj'])
        telefone = limpar_input(request.form['telefone'])
        email = request.form['email']
        senha = request.form['senha']

    #Verificar se os campos estão preenchidos
        if not nome_empresa or not cnpj or not telefone or not email or not senha:
            return render_template('editar_empresa.html', msg_erro="Todos os campos são obrigatórios!")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            UPDATE empresa
            SET nome_empresa=%s, cnpj=%s, telefone=%s, email=%s, senha=%s
            WHERE id_empresa = %s; 
            '''
            cursor.execute(comandoSQL, (nome_empresa, cnpj, telefone, email, senha, id_empresa))
            conexao.commit() #Para comandos DML
            return redirect('/adm')
        except Error as erro:
            if erro.errno == 1062: #Errno = erro número
                return render_template('editar_empresa', msg_erro="Esse e-mail já existe!")
            else:
                return f"Erro de BD: {erro}"
        except Exception as erro:
            return f"Erro de BackEnd: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA PARA ATIVAR OU DESATIVAR A EMPRESA
@app.route('/status_empresa/<int:id_empresa>')
def status(id_empresa):
    if not session:
        return redirect('/login')
    
    if not session['adm']:
        return redirect('/login')
    
    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM empresa WHERE id_empresa = %s'  
        cursor.execute(comandoSQL, (id_empresa,))
        status_empresa = cursor.fetchone()

        if status_empresa['status'] == 'ativa':
            novo_status = 'inativa'
        else:
            novo_status = 'ativa'

        comandoSQL = 'UPDATE empresa SET status=%s WHERE id_empresa=%s'
        cursor.execute(comandoSQL, (novo_status, id_empresa))
        conexao.commit()

        #Se a empresa estiver sendo desativada, as vagas também serão
        if novo_status == 'inativa':
            comandoSQL = 'UPDATE vaga SET status = %s WHERE id_empresa = %s'
            cursor.execute(comandoSQL, (novo_status, id_empresa))
            conexao.commit()
        return redirect('/adm')
    except Error as erro: #Mostra os erros
            return f"Erro de BD: {erro}"
    except Exception as erro:
            return f"Erro de BackEnd: {erro}"
    finally:
            encerrar_db(cursor, conexao)

#ROTA PARA EXCLUIR UMA EMPRESA
@app.route('/excluir_empresa/<int:id_empresa>')
def excluir_empresa(id_empresa):
    if not session:
        return redirect('/login')
    
    if not session['adm']:
        return redirect('/login')
    
    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        DELETE candidato
        FROM candidato
        JOIN vaga ON candidato.id_vaga = vaga.id_vaga
        WHERE vaga.id_empresa = %s
        '''
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()


        #Excluindo as vagas relacionadas na empresa
        comandoSQL= 'DELETE FROM vaga WHERE id_empresa = %s'
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()

        #Excluindo a empresa
        comandoSQL= 'DELETE FROM empresa WHERE id_empresa = %s'
        cursor.execute(comandoSQL, (id_empresa,))
        conexao.commit()
        return redirect('/adm')
    
    except Error as erro: #Mostra os erros
            return f"Erro de BD: {erro}"
    except Exception as erro:
            return f"Erro de BackEnd: {erro}"
    finally:
            encerrar_db(cursor, conexao)

#ROTA DA PÁGINA DE GESTÃO DAS EMPRESAS
@app.route('/empresa')
def empresa():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    id_empresa = session['id_empresa']
    nome_empresa = session['nome_empresa']

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT * FROM vaga WHERE id_empresa = %s AND status = "ativa" ORDER BY id_vaga DESC'
        cursor.execute(comandoSQL, (id_empresa,))
        vagas_ativas = cursor.fetchall()

        comandoSQL = 'SELECT * FROM vaga WHERE id_empresa = %s AND status = "inativa" ORDER BY id_vaga DESC'
        cursor.execute(comandoSQL, (id_empresa,))
        vagas_inativas = cursor.fetchall()

        return render_template('empresa.html', nome_empresa=nome_empresa, vagas_ativas=vagas_ativas, vagas_inativas=vagas_inativas)         
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

#ROTA PARA EDITAR A VAGA
@app.route('/editar_vaga/<int:id_vaga>', methods=['GET','POST'])
def editar_vaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    if request.method == 'GET':
        try:
            conexao, cursor = conectar_db()
            comandoSQL = 'SELECT * FROM vaga WHERE id_vaga = %s;'
            cursor.execute(comandoSQL, (id_vaga,))
            vaga = cursor.fetchone()
            return render_template('editar_vaga.html', vaga=vaga)
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = request.form['local']
        salario = limpar_input(request.form['salario'])

        if not titulo or not descricao or not formato or not tipo:
            return redirect('/empresa')
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            UPDATE vaga SET titulo=%s, descricao=%s, formato=%s, tipo=%s, local=%s, salario=%s
            WHERE id_vaga = %s;
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, id_vaga))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA PARA ALTERAR O STATUS DA VAGA
@app.route("/status_vaga/<int:id_vaga>")
def status_vaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'SELECT status FROM vaga WHERE id_vaga = %s;'
        cursor.execute(comandoSQL, (id_vaga,))
        vaga = cursor.fetchone()
        if vaga['status'] == 'ativa':
            status = 'inativa'
        else:
            status = 'ativa'

        comandoSQL = 'UPDATE vaga SET status = %s WHERE id_vaga = %s'
        cursor.execute(comandoSQL, (status, id_vaga))
        conexao.commit()
        return redirect('/empresa')
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

#ROTA PARA EXCLUIR VAGA
@app.route("/excluir_vaga/<int:id_vaga>")
def excluir_vaga(id_vaga):
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')

    try:
        conexao, cursor = conectar_db()
        comandoSQL = 'DELETE FROM candidato WHERE id_vaga = %s'
        cursor.execute(comandoSQL, (id_vaga,))
        conexao.commit()
        comandoSQL = 'DELETE FROM vaga WHERE id_vaga = %s AND status = "inativa"'
        cursor.execute(comandoSQL, (id_vaga,))
        conexao.commit()
        return redirect('/empresa')
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)

@app.route('/cadastrar_vaga', methods=['POST','GET'])
def cadastrar_vaga():
    #Verifica se não tem sessão ativa
    if not session:
        return redirect('/login')
    #Verifica se o adm está tentando acessar indevidamente
    if 'adm' in session:
        return redirect('/adm')
    
    if request.method == 'GET':
        return render_template('cadastrar_vaga.html')
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        formato = request.form['formato']
        tipo = request.form['tipo']
        local = ''
        local = request.form['local']
        salario = ''
        salario = limpar_input(request.form['salario'])
        id_empresa = session['id_empresa']

        if not titulo or not descricao or not formato or not tipo:
            return render_template('cadastrar_vaga.html', msg_erro="Os campos obrigatório precisam estar preenchidos!")
        
        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            INSERT INTO Vaga (titulo, descricao, formato, tipo, local, salario, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(comandoSQL, (titulo, descricao, formato, tipo, local, salario, id_empresa))
            conexao.commit()
            return redirect('/empresa')
        except Error as erro:
            return f"ERRO! Erro de Banco de Dados: {erro}"
        except Exception as erro:
            return f"ERRO! Outros erros: {erro}"
        finally:
            encerrar_db(cursor, conexao)

#ROTA PARA VER DETALHES DA VAGA
@app.route('/sobre_vaga/<int:id_vaga>')
def sobre_vaga(id_vaga):
    try:
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa 
        FROM vaga 
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa 
        WHERE vaga.id_vaga = %s;
        '''
        conexao, cursor = conectar_db()
        cursor.execute(comandoSQL, (id_vaga,))
        vaga = cursor.fetchone()
        
        if not vaga:
            return redirect('/')
        
        return render_template('sobre_vaga.html', vaga=vaga)
    except Error as erro:
        return f"ERRO! Erro de Banco de Dados: {erro}"
    except Exception as erro:
        return f"ERRO! Outros erros: {erro}"
    finally:
        encerrar_db(cursor, conexao)     

#ROTA PARA SE CANDIDATAR NA VAGA
@app.route('/candidatar/<int:id_vaga>', methods=['POST','GET'])
def candidatar(id_vaga):
    #Verifica se não tem sessão ativa
    if 'empresa' in session:
        return redirect('/')
    if 'adm' in session:
        return redirect('/')

    if request.method == 'GET':
        return render_template('Candidatar.html',id_vaga=id_vaga)
        
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = limpar_input(request.form['telefone'])
        senha = request.form['senha']
        curriculo = request.files['file']

    if not nome or not email or not telefone or not senha or not curriculo.filename:
        return render_template('candidatar.html', msg_erro="Todos os campos são obrigatórios")

    try:
        timestamp = int(time.time())
        nome_curriculo = f"{timestamp}_{curriculo.filename}"
        curriculo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_curriculo))
        conexao, cursor = conectar_db()
        comandoSQL = '''
        INSERT INTO candidato (nome, telefone, email, curriculo, senha, id_vaga)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(comandoSQL, (nome, telefone, email, nome_curriculo, senha, id_vaga))
        conexao.commit()
        return render_template('retorno.html', feedback=True)
    except Exception as erro:
        return render_template('retorno.html', feedback=False)
    finally:
        encerrar_db(cursor, conexao)

#ROTA PESQUISAR POR PALAVRA CHAVE
@app.route('/pesquisar', methods=['GET'])
def pesquisar():
    palavra_chave = request.args.get('q', '')
    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa
        FROM vaga
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa
        WHERE vaga.status = 'ativa' AND (
            vaga.titulo LIKE %s OR
            vaga.descricao LIKE %s
        )
        '''
        cursor.execute(comandoSQL, (f'%{palavra_chave}%', f'%{palavra_chave}%'))
        vagas = cursor.fetchall()
        return render_template('resultados_pesquisa.html', vagas=vagas, palavra_chave=palavra_chave)
    except Error as erro:
        return f"ERRO! {erro}"
    finally:
        encerrar_db(cursor, conexao)

# ROTA PARA VISUALIZAR CANDIDATOS
@app.route('/visualizar_candidatos/<int:id_vaga>', methods=['GET', 'POST'])
def visualizar_candidatos(id_vaga):
    if not session:
        return redirect('/login')
    if 'adm' in session:
        return redirect('/adm')
    
    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''SELECT * FROM candidato WHERE id_vaga = %s'''
        cursor.execute(comandoSQL, (id_vaga,))
        candidatos = cursor.fetchall()
        return render_template('candidatos.html', candidatos=candidatos)
    
    except mysql.connector.Error as erro:
        return f"Erro de Banco de dados: {erro}"  
    except Exception as erro:  
        return f"Erro de Back-end: {erro}"
    finally:
        encerrar_db(conexao, cursor)

#ROTA PARA UPLOAD
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    if request.method == 'POST':
        
        #recebe o arquivo do FORM
        file = request.files['file']
        #Validação 1 - Não tem o arquivo
        if file.filename == '':
            msg = "Nenhum arquivo enviado!"
            return render_template('upload.html', msg=msg)
        
        try:
            timestamp = int(time.time()) #Gera um código
            nome_arquivo = f"{timestamp}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)) #Salva o arquivo em uma pasta (nuvem)
            conexao, cursor = conectar_db()
            comandoSQL = "INSERT INTO arquivo (nome_arquivo) VALUES (%s)"
            cursor.execute(comandoSQL, (nome_arquivo,))
            conexao.commit()
            return redirect('/')
        except mysql.connector.Error as erro:
            return render_template ('upload.html', msg=f"Erro de BD {erro}")
        except Exception as erro:
            return render_template('upload.html', msg=f"Erro de Back-end {erro}")
        finally:
            encerrar_db(cursor, conexao)

#ROTA PARA DELETAR O ARQUIVO
@app.route('/delete/<filename>/<int:id_vaga>')
def delete_file(filename, id_vaga):
    # try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(file_path)  # Exclui o arquivo

        conexao, cursor = conectar_db()
        comandoSQL = "DELETE FROM candidato WHERE curriculo = %s"
        cursor.execute(comandoSQL, (filename,))
        conexao.commit()

        return redirect(f'/visualizar_candidatos/{id_vaga}')
    # except mysql.connector.Error as erro:
    #     return f"Erro de banco de Dados: {erro}"
    # except Exception as erro:
    #     return f"Erro de back-end: {erro}"
    # finally:
    #     encerrar_db(conexao, cursor)

#Rota de Login para Candidatos
@app.route('/login_candidato', methods=['GET', 'POST'])
def login_candidato():
    if session.get('candidato_id'):
        return redirect('/vagas_interesse')

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        try:
            conexao, cursor = conectar_db()
            comandoSQL = '''
            SELECT * FROM candidato WHERE email = %s AND senha = %s
            '''
            cursor.execute(comandoSQL, (email, senha))
            candidato = cursor.fetchone()

            if candidato:
                session['candidato_id'] = candidato['id_candidato']
                session['nome_candidato'] = candidato['nome']
                return redirect('/vagas_interesse')
            else:
                return render_template('login_candidato.html', msg_erro="Email ou senha incorretos")
        except Exception as erro:
            return f"Erro: {erro}"
        finally:
            encerrar_db(cursor, conexao)

    return render_template('login_candidato.html')

#Rota para Visualizar Vagas de Interesse    
@app.route('/vagas_interesse')
def vagas_interesse():
    if not session.get('candidato_id'):
        return redirect('/login_candidato')

    candidato_id = session['candidato_id']

    try:
        conexao, cursor = conectar_db()
        comandoSQL = '''
        SELECT vaga.*, empresa.nome_empresa
        FROM vaga
        JOIN candidato ON vaga.id_vaga = candidato.id_vaga
        JOIN empresa ON vaga.id_empresa = empresa.id_empresa
        WHERE candidato.id_candidato = %s
        '''
        cursor.execute(comandoSQL, (candidato_id,))
        vagas = cursor.fetchall()
        return render_template('vagas_interesse.html', vagas=vagas)
    except Exception as erro:
        return f"Erro: {erro}"
    finally:
        encerrar_db(cursor, conexao)

#ROTA PARA ABRIR O ARQUIVO -- FAZER DOWNLOAD
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

#ROTA TRATA O ERRO 404 - Página não encontrada
@app.errorhandler(404)
def not_found(error):
    return render_template('erro404.html'), 404

#ROTA PARA CONTATO
@app.route('/contato')
def contato():
    return render_template('contato.html')

#ROTA PARA PÁGINA SOBRE
@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

#ROTA DE LOGOUT - ENCERRA AS SESSÕES
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#FINAL DO CÓDIGO
if __name__ == '__main__':
    app.run(debug=True)