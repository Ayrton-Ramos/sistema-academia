import sys
import os
# 🪛 GARANTIA LINUX: Força o Python a enxergar a raiz do projeto no Streamlit Cloud
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import psycopg2
from psycopg2 import extras
import bcrypt
import qrcode
import time
import threading
from datetime import datetime
from io import BytesIO

# IMPORTANDO AS TELAS E LOGICAS DOS MÓDULOS ISOLADOS (Caminhos em minúsculo)
from modulos.cadastro import exibir_tela_cadastro
from modulos.aluno_publico import exibir_formulario_aluno
from modulos.database import obtener_conexao, criar_tabela_alunos
from modulos.pagamento import exibir_tela_checkout_pix  # 🥋 Importação do novo módulo de checkout Pix

# IMPORTANDO OS DESIGNERS INJETÁVEIS DA PASTA STYLE
from style.auth_style import aplicar_estilo_auth
from style.cadastro_style import aplicar_estilo_cadastro
from style.aluno_style import aplicar_estilo_aluno

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E INICIALIZAÇÃO DA SESSÃO (TOPO ABSOLUTO)
# ==============================================================================
st.set_page_config(page_title="Sistema Lourenço Filho BJJ", page_icon="💪", layout="centered")

# Inicializa as variáveis de controle de login e dados do usuário na memória do Streamlit
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "email_usuario" not in st.session_state:
    st.session_state["email_usuario"] = ""
if "tipo_usuario" not in st.session_state:
    st.session_state["tipo_usuario"] = "" 
if "pagamento_status" not in st.session_state:
    st.session_state["pagamento_status"] = "OK"

# Cria e valida a estrutura das tabelas no banco de dados na inicialização do app
criar_tabela_alunos()

# ==============================================================================
# 2. 🤖 MOTOR DE COBRANÇA AUTOMÁTICA EM SEGUNDO PLANO (BACKGROUND THREAD)
# ==============================================================================
def enviar_email_automatico(nome, email):
    print(f"[MOTOR AUTOMÁTICO] E-mail de cobrança enviado para: {nome} <{email}>")
    return True

def rotina_cobranca_mensal(dia_alvo, hora_alvo, minuto_alvo):
    print("🤖 Monitor de cobrança automática da Lourenço Filho BJJ inicializado.")
    while True:
        agora = datetime.now()
        if agora.day == dia_alvo and agora.hour == hora_alvo and agora.minute == minuto_alvo:
            print(f"⏰ Horário alvo atingido ({agora.strftime('%d/%m/%Y %H:%M')}). Varrendo banco de dados por inadimplentes...")
            try:
                conn = obtener_conexao()
                cursor = conn.cursor()
                cursor.execute("SELECT nome, email FROM alunos WHERE pagamento_status = 'Não OK';")
                lista_devedores = cursor.fetchall()
                
                for nome, email in lista_devedores:
                    enviar_email_automatico(nome, email)
                    time.sleep(2)
                
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"[ERRO NO MOTOR AUTOMÁTICO]: {e}")
                
            time.sleep(65)
        time.sleep(30)

DIA_DO_DISPARO = 19
HORA_DO_DISPARO = 10
MINUTO_DO_DISPARO = 27

if not any(t.name == "ThreadCobrancaBJJ" for t in threading.enumerate()):
    motor_cobranca = threading.Thread(
        target=rotina_cobranca_mensal,
        args=(DIA_DO_DISPARO, HORA_DO_DISPARO, MINUTO_DO_DISPARO),
        name="ThreadCobrancaBJJ",
        daemon=True
    )
    motor_cobranca.start()

# ==============================================================================
# 3. FUNÇÕES DE AUTENTICAÇÃO (BUSCA ADICIONAL DO STATUS DE PAGAMENTO)
# ==============================================================================
def verificar_login_adm(email, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        query = "SELECT nome, senha_hash FROM usuarios_adm WHERE email = %s;"
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado:
            nome, hash_banco = resultado
            if bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, nome
        return False, "E-mail ou senha incorretos."
    except Exception as e:
        return False, f"Erro: {e}"

def verificar_login_aluno(email, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        # 💰 Captura também o pagamento_status direto no SELECT do login
        query = "SELECT nome, senha_hash, pagamento_status FROM alunos WHERE email = %s;"
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado:
            nome_aluno, hash_banco, status_pagto = resultado
            if hash_banco and bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, {"nome": nome_aluno, "status_pagto": status_pagto}
        return False, "E-mail ou senha incorretos ou não aprovados."
    except Exception as e:
        return False, f"Erro: {e}"

def cadastrar_usuario_adm(nome, email, senha):
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO usuarios_adm (nome, email, senha_hash) VALUES (%s, %s, %s);", (nome, email, senha_hash))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Administrador cadastrado!"
    except Exception:
        return False, "E-mail já cadastrado."

# ==============================================================================
# 4. FLUXO DE TELAS DO APLICATIVO (ROTEAMENTO DINÂMICO COM TRAVA PIX)
# ==============================================================================
if st.session_state["logado"]:
    aplicar_estilo_auth()
    
    try:
        st.sidebar.image("img/logo_bjj.png", use_container_width=True)
    except Exception:
        st.sidebar.write("### 🥋 LOURENÇO FILHO BJJ")
        
    st.sidebar.markdown(f"Guerreiro: **{st.session_state['nome_usuario']}**")
    st.sidebar.caption(f"Perfil: {st.session_state['tipo_usuario'].upper()}")
    st.sidebar.write("---")
    
    # LOGICA DE MENUS CONFORME O PERFIL LOGADO
    if st.session_state["tipo_usuario"] == "adm":
        st.sidebar.markdown("### 🥷 MENU PRINCIPAL")
        tela_selecionada = st.sidebar.radio("Ir para:", ["📋 Gestão de Alunos", "💪 Gestão de Treinos", "💰 Controle Financeiro"])
        st.sidebar.write("---")
    elif st.session_state["tipo_usuario"] == "aluno":
        tela_selecionada = "👤 Área do Aluno"

    st.sidebar.write("")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state["logado"] = False
        st.session_state["nome_usuario"] = ""
        st.session_state["email_usuario"] = ""
        st.session_state["tipo_usuario"] = ""
        st.session_state["pagamento_status"] = "OK"
        st.rerun()

    # RENDERIZAÇÃO DAS TELAS FILTRADAS
    if st.session_state["tipo_usuario"] == "adm":
        if tela_selecionada == "📋 Gestão de Alunos":
            st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
            aplicar_estilo_cadastro()
            exibir_tela_cadastro()
        elif tela_selecionada == "💪 Gestão de Treinos":
            st.title("💪 Fichas de Exercícios (BJJ)")
            st.info("Módulo em desenvolvimento.")
        elif tela_selecionada == "💰 Controle Financeiro":
            st.title("💰 Caixa e Mensalidades")
            st.info("Módulo em desenvolvimento.")
            
    elif st.session_state["tipo_usuario"] == "aluno":
        # 🥋 INTERCEPTADOR DE ADIMPLÊNCIA: Se o aluno estiver devedor, trava ele no checkout do Pix
        if st.session_state["pagamento_status"] == "Não OK":
            st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
            aplicar_estilo_aluno()
            exibir_tela_checkout_pix(st.session_state["nome_usuario"], st.session_state["email_usuario"], valor=150.00)
        else:
            # Se o status estiver perfeito ("OK"), libera o acesso aos treinos dele
            st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
            aplicar_estilo_aluno()
            exibir_formulario_aluno()

else:
    # --- FLUXO DO USUÁRIO DESLOGADO (LOGIN / NOVA MATRÍCULA) ---
    aplicar_estilo_auth()
    st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
    
    try:
        st.image("img/logo_bjj.png", use_container_width=True)
    except Exception:
        st.title("🥋 LOURENÇO FILHO BJJ")
        
    st.sidebar.title("Acesso Unificado")
    opcao = st.sidebar.radio("Escolha uma opção:", ["Login no Sistema", "Nova Matrícula (QR Code)", "Criar Conta ADM"])

    if opcao == "Nova Matrícula (QR Code)":
        aplicar_estilo_aluno()
        exibir_formulario_aluno()

    elif opcao == "Login no Sistema":
        st.title("🔐 Login Unificado")
        tipo_login = st.segmented_control("Entrar como:", options=["🥷 Administrador", "👤 Aluno"], default="🥷 Administrador")
        
        with st.form("form_login"):
            email_login = st.text_input("E-mail Cadastrado")
            senha_login = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar", use_container_width=True)
            
        if botao_login:
            if not email_login or not senha_login:
                st.warning("Preencha todos os campos!")
            else:
                with st.spinner("Autenticando..."):
                    email_limpo = email_login.lower().strip()
                    if tipo_login == "🥷 Administrador":
                        sucesso, info = verificar_login_adm(email_limpo, senha_login)
                        tipo_perfil = "adm"
                        status_p = "OK"
                        email_usuario_salvo = email_limpo
                    else:
                        sucesso, info = verificar_login_aluno(email_limpo, senha_login)
                        tipo_perfil = "aluno"
                        if sucesso:
                            email_usuario_salvo = email_limpo
                            status_p = info["status_pagto"]
                            info = info["nome"]
                        
                if sucesso:
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = info
                    st.session_state["email_usuario"] = email_usuario_salvo
                    st.session_state["tipo_usuario"] = tipo_perfil
                    st.session_state["pagamento_status"] = status_p
                    st.rerun()
                else:
                    st.error(info)
                    
    elif opcao == "Criar Conta ADM":
        st.title("🔐 Novo Administrator")
        with st.form("form_registro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            botao_registrar = st.form_submit_button("Cadastrar", use_container_width=True)
        if botao_registrar:
            sucesso, msg = cadastrar_usuario_adm(nome, email, senha)
            st.success(msg) if sucesso else st.error(msg)
            
    st.markdown('<div class="color-strip-bottom"></div>', unsafe_allow_html=True)