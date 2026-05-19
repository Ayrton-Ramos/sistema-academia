import streamlit as st

def aplicar_estilo_auth():
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

        .stCaption,
        p,
        label,
        [data-testid="stWidgetLabel"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
        }

        /* ==========================================================================
           🎛️ SIDEBAR
           ========================================================================== */
        [data-testid="stSidebar"] {
            background-color: #060911 !important;
            border-right: 3px solid #f6b31e;
        }

        [data-testid="stSidebar"] .stMarkdown p {
            color: #ffffff !important;
        }

        /* ==========================================================================
           📋 RADIO BUTTONS / MENU LATERAL
           ========================================================================== */
        div[role="radiogroup"] > label,
        div[data-testid="stSegmentedControl"] button {
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
            transition: all 0.2s ease-in-out !important;
        }

        div[role="radiogroup"] > label:hover,
        div[data-testid="stSegmentedControl"] button:hover {
            background-color: #1a1f2c !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        div[role="radiogroup"] label [data-testid="stTableCell"] {
            display: none !important;
        }
        
        /* ==========================================================================
        🔄 TROCA ENTRE ADMINISTRADOR / ALUNO
        ========================================================================== */

        /* Container do controle */
        div[role="radiogroup"] {
            gap: 10px !important;
        }

        /* Botões */
        div[role="radiogroup"] label {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            font-weight: bold !important;
            transition: all 0.2s ease-in-out !important;
        }

        /* Texto interno */
        div[role="radiogroup"] label p {
            color: #ffffff !important;
            font-weight: bold !important;
        }

        /* Item selecionado */
        div[role="radiogroup"] label[data-selected="true"] {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        /* Hover */
        div[role="radiogroup"] label:hover {
            background-color: #1a1f2c !important;
            box-shadow: 0 0 15px #f6b31e !important;
        }

        /* Remove fundo branco interno */
        div[role="radiogroup"] * {
            background-color: transparent !important;
            color: #ffffff !important;
        }

        /* Remove bolinha padrão */
        div[role="radiogroup"] input {
            display: none !important;
}
        /* ==========================================================================
           ⌨️ INPUTS / SELECTBOX
           ========================================================================== */
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"],
        .stTextArea textarea,
        .stNumberInput input {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 5px !important;
            font-weight: 500 !important;
        }

        .stTextInput input:focus,
        .stSelectbox div[data-baseweb="select"]:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {
            border-color: #f6b31e !important;
            background-color: #000000 !important;
            color: #ffffff !important;
            box-shadow: 0 0 12px #f6b31e !important;
        }

        /* ==========================================================================
           📦 FORMULÁRIOS
           ========================================================================== */
        [data-testid="stForm"] {
            border: 2px solid #f6b31e !important;
            border-radius: 10px;
            padding: 20px;
            background-color: #000000 !important;
        }

        /* ==========================================================================
           🔘 BOTÕES NORMAIS
           ========================================================================== */
        .stButton > button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            text-transform: uppercase !important;
            font-weight: bold !important;
            width: 100% !important;
            opacity: 1 !important;
            box-shadow: none !important;
            transition: all 0.2s ease-in-out !important;
        }

        .stButton > button:hover,
        .stButton > button:focus,
        .stButton > button:active {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border-color: #f6b31e !important;
            box-shadow: 0 0 20px #f6b31e !important;
        }

        /* ==========================================================================
           🚀 BOTÃO LOGIN / ENTRAR (FORM SUBMIT)
           ========================================================================== */
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #f6b31e !important;
            border-radius: 8px !important;
            padding: 10px 15px !important;
            text-transform: uppercase !important;
            font-weight: bold !important;
            width: 100% !important;
            opacity: 1 !important;
            box-shadow: none !important;
            transition: all 0.2s ease-in-out !important;
        }

        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:focus,
        div[data-testid="stFormSubmitButton"] > button:active {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border-color: #f6b31e !important;
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