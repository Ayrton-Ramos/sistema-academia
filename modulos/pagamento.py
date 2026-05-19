import streamlit as st
import mercadopago
import time
import base64
from modulos.database import obtener_conexao

# ==============================================================================
# 🔑 CREDENCIAIS DO MERCADO PAGO - MODO PRODUÇÃO REAL (CHECKOUT TRANSPARENTE)
# ==============================================================================
MERCADOPAGO_TOKEN = "APP_USR-2597006826328144-051912-03fd709092d511dcff5c04e5798d803e-167356627"

def gerar_pix_mensalidade(nome_aluno, email_aluno, valor=2.00):
    """Conecta com a API de Produção do Mercado Pago e gera o Pix real de R$ 2,00"""
    try:
        sdk = mercadopago.SDK(MERCADOPAGO_TOKEN)
        
        payment_data = {
            "transaction_amount": float(valor),
            "description": f"Mensalidade Real - Lourenço Filho BJJ ({nome_aluno})",
            "payment_method_id": "pix",
            "payer": {
                "email": email_aluno,
                "first_name": nome_aluno.split()[0],
                "last_name": nome_aluno.split()[-1] if len(nome_aluno.split()) > 1 else "Silva"
            }
        }
        
        payment_response = sdk.payment().create(payment_data)
        pagamento = payment_response["response"]
        
        if "status" in pagamento and pagamento["status"] == 401:
            st.error("⚠️ Erro de Autenticação. O token de produção precisa ser verificado no painel.")
            return None, None, None
            
        if "id" not in pagamento:
            st.error(f"Erro da API do Mercado Pago: {pagamento.get('message', 'Erro desconhecido')}")
            return None, None, None
            
        id_pagamento = pagamento["id"]
        qr_code_copia_cola = pagamento["point_of_interaction"]["transaction_data"]["qr_code"]
        qr_code_base64 = pagamento["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        
        return id_pagamento, qr_code_copia_cola, qr_code_base64
    except Exception as e:
        st.error(f"Erro técnico ao conectar com a API de produção: {e}")
        return None, None, None

def verificar_status_pagamento(id_pagamento):
    """Consulta o Mercado Pago em tempo real para ver se o Pix real já foi pago"""
    try:
        sdk = mercadopago.SDK(MERCADOPAGO_TOKEN)
        payment_response = sdk.payment().get(id_pagamento)
        return payment_response["response"]["status"]  # Retorna 'approved' quando o dinheiro cai
    except Exception:
        return "pending"

def atualizar_status_aluno_banco(email_aluno):
    """Muda o status do aluno para 'Pago' no PostgreSQL após a aprovação real"""
    try:
        conn = obtener_conexao()
        cursor = conn.cursor()
        # 🎯 AJUSTADO: Agora salva como 'Pago' direto na tabela do banco
        cursor.execute(
            "UPDATE alunos SET pagamento_status = 'Pago' WHERE email = %s;",
            (email_aluno,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status no banco de dados: {e}")
        return False

def exibir_tela_checkout_pix(nome_aluno, email_aluno, valor=2.00):
    """Gera a interface visual do checkout Pix com monitoramento de aprovação automática"""
    st.markdown("<h2 style='text-align: center; color: #D4AF37;'>🥋 Liberação de Acesso via Pix Real</h2>", unsafe_allow_html=True)
    st.write(f"Olá, **{nome_aluno}**. Identificamos uma mensalidade em aberto no valor de **R$ {valor:.2f}**.")
    st.write("Efetue o pagamento abaixo. O sistema identificará a transferência e liberará seu acesso na hora.")
    
    st.write("---")

    if "id_pix" not in st.session_state:
        with st.spinner("Gerando QR Code Pix oficial no Mercado Pago..."):
            id_pag, copia_cola, qr_base64 = gerar_pix_mensalidade(nome_aluno, email_aluno, valor)
            if id_pag:
                st.session_state["id_pix"] = id_pag
                st.session_state["copia_cola_pix"] = copia_cola
                st.session_state["qr_base64_pix"] = qr_base64
            else:
                return

    try:
        col_img, col_info = st.columns([1, 1.5])
        with col_img:
            qr_img = base64.b64decode(st.session_state["qr_base64_pix"])
            st.image(qr_img, width=220)
        with col_info:
            st.write("")
            st.markdown("### **Instruções para o Teste Real:**")
            st.write("1. Abra o aplicativo do seu banco no celular.")
            st.write("2. Escolha **Pagar com Pix > Copiar e Colar** ou aponte a câmera para o QR Code.")
            st.write("3. Confirme o valor de **R$ 2,00** e faça o envio.")
    except Exception:
        st.error("Erro ao processar imagem gráfica do QR Code.")

    st.text_input("Pix Copia e Cola Oficial (Clique e segure para copiar):", value=st.session_state["copia_cola_pix"], disabled=True)
    
    status_placeholder = st.empty()
    status_placeholder.warning("⏳ Aguardando confirmação do banco... Assim que você pagar, essa tela vai atualizar sozinha!")

    # 🔄 LOOP DE VALIDAÇÃO AUTOMÁTICA REAL
    status = verificar_status_pagamento(st.session_state["id_pix"])
    
    if status == "approved":
        status_placeholder.empty()
        st.success("🎉 ¡PAGAMENTO REAL RECONHECIDO COM SUCESSO! Seu acesso está liberado.")
        
        # Altera na tabela do PostgreSQL para 'Pago'
        atualizar_status_aluno_banco(email_aluno)
        
        # Seta na sessão atual como 'Pago' para liberar a trava do app_auth na mesma hora
        st.session_state["pagamento_status"] = "Pago"
        
        del st.session_state["id_pix"]
        del st.session_state["copia_cola_pix"]
        del st.session_state["qr_base64_pix"]
        
        time.sleep(2)
        st.rerun()