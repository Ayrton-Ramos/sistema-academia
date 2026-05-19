import streamlit as st
import psycopg2
from modulos.database import obter_conexao

def enviar_pre_cadastro(nome, cpf, telefone, plano):
    try:
        conn = obter_conexao()
        cursor = conn.cursor()
        
        # Verifica se já não está na fila ou ativo
        query = "INSERT INTO pre_cadastro (nome, cpf, telefone, plano) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, (nome, cpf, telefone, plano))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Solicitação enviada com sucesso! Aguarde a aprovação na recepção."
    except psycopg2.errors.UniqueViolation:
        return False, "Este CPF já possui uma solicitação pendente ou já está cadastrado."
    except Exception as e:
        return False, f"Erro ao enviar: {e}"

def exibir_formulario_aluno():
    st.title("🏋️‍♂️ Ficha de Matrícula - Academia Lourenço")
    st.write("Insira seus dados abaixo para solicitar sua matrícula.")
    
    with st.form("form_aluno_externo", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        cpf = st.text_input("CPF (Apenas números)")
        telefone = st.text_input("WhatsApp")
        plano = st.selectbox("Escolha seu Plano", ["Mensal", "Trimestral", "Semestral", "Anual"])
        
        botao_enviar = st.form_submit_button("Solicitar Matrícula")
        
    if botao_enviar:
        if not nome or not cpf:
            st.warning("Nome e CPF são obrigatórios!")
        elif len(cpf) != 11 or not cpf.isdigit():
            st.error("CPF inválido. Digite os 11 números.")
        else:
            with st.spinner("Enviando dados..."):
                sucesso, msg = enviar_pre_cadastro(nome, cpf, telefone, plano)
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)