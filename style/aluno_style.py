import streamlit as st

def aplicar_estilo_aluno():
    st.markdown("""
    <style>

        /* ==========================================================================
           🎨 CONFIGURAÇÃO GERAL E FUNDO
           ========================================================================== */
        .stApp {
            background-color: #000000 !important;
            color: #ffffff !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            text-shadow: 0 0 10px #f6b31e;
            font-family: 'Garamond', serif !important;
            text-transform: uppercase;
            font-weight: bold !important;
        }

        .stCaption, p, label, [data-testid="stWidgetLabel"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* ==========================================================================
           📦 FORMULÁRIO
           ========================================================================== */
        [data-testid="stForm"] {
            border: 2px solid #f6b31e !important;
            border-radius: 10px;
            padding: 20px;
            background-color: #000000 !important;
        }

        /* ==========================================================================
           ⌨️ INPUTS / SELECTBOX / TEXTAREA
           ========================================================================== */
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"],
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 5px !important;
            font-weight: 500 !important;
        }

        div[data-baseweb="select"] * {
            color: #ffffff !important;
            background-color: transparent !important;
        }

        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"] li {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
        }

        div[data-baseweb="popover"] * {
            color: #ffffff !important;
        }

        .stTextInput input:focus,
        .stSelectbox div[data-baseweb="select"]:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus {
            border-color: #f6b31e !important;
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            box-shadow: 0 0 10px rgba(246, 179, 30, 0.5) !important;
        }

        /* ==========================================================================
           🔘 BOTÕES PADRÃO
           ========================================================================== */
        .stButton > button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            margin-bottom: 10px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            opacity: 1 !important;
            transition: all 0.2s ease-in-out;
        }

        .stButton > button:hover,
        .stButton > button:active,
        .stButton > button:focus {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border-color: #f6b31e !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        /* ==========================================================================
           🚀 BOTÃO ENVIAR SOLICITAÇÃO (FORM SUBMIT)
           ========================================================================== */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            font-weight: bold !important;
            width: 100% !important;
            opacity: 1 !important;
            transition: all 0.2s ease-in-out !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        div[data-testid="stFormSubmitButton"] > button:focus,
        div[data-testid="stFormSubmitButton"] > button:active {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        /* ==========================================================================
           ⚠️ ALERTAS
           ========================================================================== */
        .stAlert {
            background-color: #1a1f2c !important;
            border: 2px solid #f6b31e !important;
            color: #ffffff !important;
        }

    </style>
    """, unsafe_allow_html=True)