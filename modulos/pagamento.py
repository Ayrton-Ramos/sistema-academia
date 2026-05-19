import streamlit as st
import mercadopago
import time
import base64
from modulos.database import obtener_conexao

# ==============================================================================
# 🔑 CREDENCIAIS OFICIAIS DO MERCADO PAGO (PRODUÇÃO)
# ==============================================================================
MERCADOPAGO_TOKEN = "APP_USR-2717776949160930-051912-399fff3c441e1500df20aadf262c4ac4-3412918000"

def gerar_pix_mensalidade(nome_aluno, email_aluno, valor=150.00):
    """Conecta com a API do Mercado Pago e gera o Pix oficial com QR Code e Copia e Cola"""
    try:
        sdk = mercadopago.SDK(MERCADOPAGO_TOKEN)
        
        # Estrutura os dados do pagamento conforme exigido pela API
        payment_data = {
            "transaction_amount": float(valor),
            "description": f"Mensalidade - Lourenço Filho BJJ ({nome_aluno})",
            "payment_method_id": "pix",
            "payer": {
                "email": email_aluno,
                "first_name": nome_aluno.split()[0],
                "last_name": nome_aluno.split()[-1] if len(nome_aluno.split()) > 1 else ""
            }
        }
        
        payment_response = sdk.payment().create(payment_data)
        pagamento = payment_response["response"]
        
        # Tratamento de erro caso o token seja rejeitado pelo servidor do Mercado Pago
        if "status" in pagamento and pagamento["status"] == 401:
            st.error("⚠️ Erro de Autenticação com o Mercado Pago. Verifique as credenciais.")
            return None, None, None
            
        id_pagamento = pagamento["id"]
        qr_code_copia_cola = pagamento["point_of_interaction"]["transaction_data"]["qr_code"]
        qr_code_base64 = pagamento["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        
        return id_pagamento, qr_code_copia_cola, qr_code_base64
    except Exception as e:
        st.error(f"Erro técnico ao conectar com a API de pagamentos: {e}")
        return None, None, None

def verificar_status_pagamento(id_pagamento):
    """Consulta o servidor do Mercado Pago para checar se o Pix foi pago"""
    try:
        sdk = mercadopago.SDK(MERCADOPAGO_TOKEN)
        payment_response = sdk.payment().get(id_pagamento)
        return payment_response["response"]["status"]  # Retorna 'approved', 'pending', etc.
    except Exception:
        return "pending"

def atualizar_status_aluno_banco(email_aluno):
    """Muda de forma definitiva o status do aluno de 'Não OK' para 'OK' no PostgreSQL"""
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alunos SET pagamento_status = 'OK' WHERE email = %s;",
            (email_aluno,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status no banco de dados: {e}")
        return False

def exibir_tela_checkout_pix(nome_aluno, email_aluno, valor=150.00):
    """Gera a interface visual do checkout Pix e gerencia o loop de aprovação automática"""
    st.markdown("<h2 style='text-align: center; color: #D4AF37;'>🥋 Pendência Financeira Detectada</h2>", unsafe_allow_html=True)
    st.write(f"Olá, **{nome_aluno}**. Identificamos que sua mensalidade atual está em aberto no sistema.")
    st.write(f"Para liberar seu acesso aos treinos e conteúdos, efetue o pagamento do plano de **R$ {valor:.2f}** abaixo:")
    
    st.write("---")

    # Garante que o Pix só será gerado uma única vez por sessão do aluno
    if "id_pix" not in st.session_state:
        with st.spinner("Gerando chave Pix dinâmica com o banco..."):
            id_pag, copia_cola, qr_base64 = gerar_pix_mensalidade(nome_aluno, email_aluno, valor)
            if id_pag:
                st.session_state["id_pix"] = id_pag
                st.session_state["copia_cola_pix"] = copia_cola
                st.session_state["qr_base64_pix"] = qr_base64
            else:
                return

    # Renderiza o QR Code convertendo os dados em string Base64 da API em imagem física
    try:
        col_img, col_info = st.columns([1, 1.5])
        with col_img:
            qr_img = base64.b64decode(st.session_state["qr_base64_pix"])
            st.image(qr_img, width=220)
        with col_info:
            st.write("")
            st.markdown("### **Instruções:**")
            st.write("1. Abra o aplicativo do seu banco.")
            st.write("2. Escolha a opção **Pagar com Pix > QR Code**.")
            st.write("3. Escaneie a imagem ao lado.")
    except Exception:
        st.error("Erro ao processar imagem gráfica do QR Code.")

    # Caixa com o código Copia e Cola para quem estiver fazendo pelo celular
    st.text_input("Pix Copia e Cola (Clique para copiar):", value=st.session_state["copia_cola_pix"], disabled=True)
    
    # Marcador de status que avisa o aluno que o sistema está monitorando
    status_placeholder = st.empty()
    status_placeholder.warning("⏳ Aguardando confirmação do pagamento do Pix... (A tela atualizará sozinha após o pagamento)")

    # 🔄 LOOP DE VALIDAÇÃO (Polling automático em background)
    status = verificar_status_pagamento(st.session_state["id_pix"])
    
    if status == "approved":
        status_placeholder.empty()
        st.success("🎉 ¡PAGAMENTO RECONHECIDO COM SUCESSO! Seu acesso está liberado.")
        
        # Efetua a alteração na tabela de alunos
        atualizar_status_aluno_banco(email_aluno)
        
        # Atualiza a memória de sessão do app_auth na mesma hora para abrir o painel do aluno
        st.session_state["pagamento_status"] = "OK"
        
        # Limpa o cache da transação finalizada
        del st.session_state["id_pix"]
        del st.session_state["copia_cola_pix"]
        del st.session_state["qr_base64_pix"]
        
        time.sleep(2)
        st.rerun()