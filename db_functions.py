import mysql.connector
from config import *

#ESTABELECE CONEXÃO COM O BANCO DE DADOS
def conectar_db():
    conexao = mysql.connector.connect (
        host = DB_HOST,
        user = DB_USER,
        password = DB_PASSWORD,
        database = DB_NAME
    )
     #ALTERA O CURSOR PARA DICIONÁRIO
    cursor = conexao.cursor(dictionary=True)
    return conexao, cursor

#ENCERRA A CONEXÃO COM O BANCO DE DADOS
def encerrar_db(cursor, conexao):
    cursor.close()
    conexao.close()

#LIMPA 
def limpar_input(campo):
    campolimpo = campo.replace(".","").replace("/","").replace("-","").replace(" ","").replace("(","").replace(")","").replace("R$","")
    return campolimpo