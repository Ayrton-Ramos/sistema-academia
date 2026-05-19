import streamlit as st
from psycopg2 import extras
import bcrypt
import qrcode
import time
import threading
from datetime import datetime
from io import BytesIO

# IMPORTANDO AS TELAS E LOGICAS DOS MÓDULOS ISOLADOS
from Modulos.cadastro import exibir_tela_cadastro
from Modulos.aluno_publico import exibir_formulario_aluno
from Modulos.database import obtener_conexao, criar_tabela_alunos

# IMPORTANDO OS DESIGNERS INJETÁVEIS DA PASTA STYLE
from style.auth_style import aplicar_estilo_auth
from style.cadastro_style import aplicar_estilo_cadastro
from style.aluno_style import aplicar_estilo_aluno

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E INICIALIZAÇÃO DA SESSÃO (TOPO ABSOLUTO)
# ==============================================================================
# Define o título da aba do navegador, o ícone e centraliza o layout na tela
st.set_page_config(page_title="Sistema Lourenço Filho BJJ", page_icon="💪", layout="centered")

# Inicializa as variáveis de controle de login na memória global do Streamlit
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "tipo_usuario" not in st.session_state:
    st.session_state["tipo_usuario"] = "" 

# Cria e valida a estrutura das tabelas no banco de dados na inicialização do app
criar_tabela_alunos()

# ==============================================================================
# 2. 🤖 MOTOR DE COBRANÇA AUTOMÁTICA EM SEGUNDO PLANO (BACKGROUND THREAD)
# ==============================================================================
def enviar_email_automatico(nome, email):
    """
    Função interna do servidor para disparar o e-mail automático.
    Espaço reservado para sua integração SMTP (smtplib).
    """
    print(f"[MOTOR AUTOMÁTICO] E-mail de cobrança enviado para: {nome} <{email}>")
    return True

def rotina_cobranca_mensal(dia_alvo, hora_alvo, minuto_alvo):
    """
    Loop perpétuo executado diretamente no núcleo do servidor.
    Monitora o relógio silenciosamente sem travar a interface do site.
    """
    print("🤖 Monitor de cobrança automática da Lourenço Filho BJJ inicializado.")
    while True:
        agora = datetime.now()
        
        # VALIDADOR DE TEMPO: Só executa se bater o Dia, a Hora e o Minuto exatos configurados
        if agora.day == dia_alvo and agora.hour == hora_alvo and agora.minute == minuto_alvo:
            print(f"⏰ Horário alvo atingido ({agora.strftime('%d/%m/%Y %H:%M')}). Varrendo banco de dados por inadimplentes...")
            try:
                conn = obtener_conexao()
                cursor = conn.cursor()
                
                # Coleta o nome e e-mail dos alunos cujo pagamento_status está como 'Não OK'
                cursor.execute("SELECT nome, email FROM alunos WHERE pagamento_status = 'Não OK';")
                lista_devedores = cursor.fetchall()
                
                for nome, email in lista_devedores:
                    enviar_email_automatico(nome, email)
                    time.sleep(2) # Pausa de 2 segundos entre e-mails para evitar bloqueios por SPAM
                
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"[ERRO NO MOTOR AUTOMÁTICO]: {e}")
                
            # Dorme por 65 segundos para o relógio virar e não reexecutar no mesmo minuto
            time.sleep(65)
            
        time.sleep(30) # Avalia o relógio do servidor a cada 30 segundos para manter precisão

# --- SEU PEDIDO: CONFIGURAÇÃO DO AGENDAMENTO PARA TODO DIA 19 ÀS 10:11 DA MANHÃ ---
DIA_DO_DISPARO = 19
HORA_DO_DISPARO = 10
MINUTO_DO_DISPARO = 27

# Inicializa a Thread em background de forma segura, evitando duplicações no servidor
if not any(t.name == "ThreadCobrancaBJJ" for t in threading.enumerate()):
    motor_cobranca = threading.Thread(
        target=rotina_cobranca_mensal,
        args=(DIA_DO_DISPARO, HORA_DO_DISPARO, MINUTO_DO_DISPARO),
        name="ThreadCobrancaBJJ",
        daemon=True # A Thread encerra suas atividades automaticamente se o Streamlit for desligado
    )
    motor_cobranca.start()

# ==============================================================================
# 3. FUNÇÕES DE AUTENTICAÇÃO (BANCO DE DADOS)
# ==============================================================================
def verificar_login_adm(email, senha):
    """Valida as credenciais dos administradores na tabela usuarios_adm utilizando Bcrypt"""
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
            # Compara a senha digitada com o hash criptografado salvo no banco
            if bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, nome
        return False, "E-mail ou senha incorretos."
    except Exception as e:
        return False, f"Erro: {e}"

def verificar_login_aluno(email, senha):
    """Valida as credenciais dos alunos ativos na tabela alunos"""
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        query = "SELECT nome, senha_hash FROM alunos WHERE email = %s;"
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado:
            nome_aluno, hash_banco = resultado
            if hash_banco and bcrypt.checkpw(senha.encode('utf-8'), hash_banco.encode('utf-8')):
                return True, nome_aluno
        return False, "E-mail ou senha incorretos ou não aprovados."
    except Exception as e:
        return False, f"Erro: {e}"

def cadastrar_usuario_adm(nome, email, senha):
    """Gera o hash Bcrypt e insere um novo administrador no banco de dados"""
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        # Criptografa a senha antes de enviar para o banco de dados
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO usuarios_adm (nome, email, senha_hash) VALUES (%s, %s, %s);", (nome, email, senha_hash))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Administrador cadastrado!"
    except Exception:
        return False, "E-mail já cadastrado."

# ==============================================================================
# 4. FLUXO DE TELAS DO APLICATIVO (ROTEAMENTO DINÂMICO)
# ==============================================================================
if st.session_state["logado"]:
    # --- FLUXO DO USUÁRIO CONECTADO / AUTENTICADO ---
    aplicar_estilo_auth() # Carrega as regras da barra lateral escura
    
    try:
        st.sidebar.image("img/logo_bjj.png", use_container_width=True)
    except Exception:
        st.sidebar.write("### 🥋 LOURENÇO FILHO BJJ")
        
    st.sidebar.markdown(f"Guerreiro: **{st.session_state['nome_usuario']}**")
    st.sidebar.caption(f"Perfil: {st.session_state['tipo_usuario'].upper()}")
    st.sidebar.write("---")
    
    # Renderização do menu lateral exclusivo do Administrador
    if st.session_state["tipo_usuario"] == "adm":
        st.sidebar.markdown("### 🥷 MENU PRINCIPAL")
        tela_selecionada = st.sidebar.radio("Ir para:", ["📋 Gestão de Alunos", "💪 Gestão de Treinos", "💰 Controle Financeiro"])
        st.sidebar.write("---")
            
    elif st.session_state["tipo_usuario"] == "aluno":
        tela_selecionada = "👤 Área do Aluno"

    st.sidebar.write("")
    # Botão de Logout: Limpa a sessão e recarrega o app no estado deslogado
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state["logado"] = False
        st.session_state["nome_usuario"] = ""
        st.session_state["tipo_usuario"] = ""
        st.rerun()

    # Redirecionamento cirúrgico de telas com injeção isolada de CSS
    if st.session_state["tipo_usuario"] == "adm":
        if tela_selecionada == "📋 Gestão de Alunos":
            st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True) # Faixa decorativa superior
            aplicar_estilo_cadastro() # Injeta o CSS focado em tabelas e listas
            exibir_tela_cadastro()   # Abre o módulo de gerenciamento
        elif tela_selecionada == "💪 Gestão de Treinos":
            st.title("💪 Fichas de Exercícios (BJJ)")
            st.info("Módulo em desenvolvimento.")
        elif tela_selecionada == "💰 Controle Financeiro":
            st.title("💰 Caixa e Mensalidades")
            st.info("Módulo em desenvolvimento.")
    elif st.session_state["tipo_usuario"] == "aluno":
        aplicar_estilo_aluno() # Injeta o CSS focado nos inputs escuros e dourados do aluno
        exibir_formulario_aluno()

else:
    # --- FLUXO DO USUÁRIO DESLOGADO (LOGIN / NOVA MATRÍCULA) ---
    aplicar_estilo_auth() # Carrega os inputs pretos e botão entrar com luz na borda
    st.markdown('<div class="color-strip-top"></div>', unsafe_allow_html=True)
    
    try:
        st.image("img/logo_bjj.png", use_container_width=True)
    except Exception:
        st.title("🥋 LOURENÇO FILHO BJJ")
        
    st.sidebar.title("Acesso Unificado")
    opcao = st.sidebar.radio("Escolha uma opção:", ["Login no Sistema", "Nova Matrícula (QR Code)", "Criar Conta ADM"])

    if opcao == "Nova Matrícula (QR Code)":
        aplicar_estilo_aluno() # Muda o layout para o formulário de matrícula
        exibir_formulario_aluno()

    elif opcao == "Login no Sistema":
        st.title("🔐 Login Unificado")
        # Seletor estilizado para definir o tipo de conta antes de submeter o formulário
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
                    if tipo_login == "🥷 Administrador":
                        sucesso, info = verificar_login_adm(email_login.lower().strip(), senha_login)
                        tipo_perfil = "adm"
                    else:
                        sucesso, info = verificar_login_aluno(email_login.lower().strip(), senha_login)
                        tipo_perfil = "aluno"
                        
                if sucesso:
                    # Trava o estado de login na memória e atualiza a tela para entrar no painel
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = info
                    st.session_state["tipo_usuario"] = tipo_perfil
                    st.rerun()
                else:
                    st.error(info)
                    
    elif opcao == "Criar Conta ADM":
        st.title("🔐 Novo Administrador")
        with st.form("form_registro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            botao_registrar = st.form_submit_button("Cadastrar", use_container_width=True)
        if botao_registrar:
            sucesso, msg = cadastrar_usuario_adm(nome, email, senha)
            st.success(msg) if sucesso else st.error(msg)
            
    st.markdown('<div class="color-strip-bottom"></div>', unsafe_allow_html=True) # Faixa decorativa inferior