import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import base64
from pathlib import Path


from sqlalchemy import (
    create_engine, MetaData, Table, Column, String, Integer, ForeignKey,
    select, insert, update, UniqueConstraint, delete, func
)
from sqlalchemy.engine import Engine

import random



# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "player" not in st.session_state:
    st.session_state["player"] = None
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False
if "collapse_sidebar" not in st.session_state:
    st.session_state["collapse_sidebar"] = False

# -----------------------------
# CONFIG PAGE
# -----------------------------
sidebar_state = "expanded" if not st.session_state["collapse_sidebar"] else "collapsed"

st.set_page_config(
    page_title="Tachkila Mouchkila",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state=sidebar_state,
)


# -----------------------------
# THEME FOOTBALL (CSS visuel)
# -----------------------------
FOOTBALL_CSS = """
<style>

/* ---------------------------
   Import police stylée
----------------------------*/
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');

/* Appliquer Montserrat partout */
* {
    font-family: 'Montserrat', sans-serif !important;
}

/* Corps de la page = ambiance stade de nuit */
html, body {
    background:#020617 !important;
}
.stApp {
    background:
        radial-gradient(circle at 0% 0%, #22c55e22 0, #020617 50%, #01030a 100%),
        linear-gradient(135deg, #020617, #020617 40%, #0f3c2b 120%) !important;
}

/* Conteneur principal pour donner un look “app” */
.block-container {
    max-width: 1180px;
    padding-top: 1.5rem !important;
}

/* Sidebar sombre (desktop + mobile) */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020920) !important;
    border-right: 1px solid rgba(148,163,184,0.35);
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
/* =============================
   INPUTS SIDEBAR — BORDURE BLANCHE
   ============================= */

/* Conteneur des champs texte / mot de passe (BaseWeb input) */
[data-testid="stSidebar"] div[data-baseweb="input"] {
    border: 2px solid rgba(255,255,255,0.9) !important;
    border-radius: 10px !important;
    background-color: #020617 !important;
}

/* Quand le champ est actif (focus dans l’input) */
[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px #22c55e !important;
}

/* Champ type selectbox (BaseWeb select) */
[data-testid="stSidebar"] div[data-baseweb="select"] {
    border: 2px solid rgba(255,255,255,0.9) !important;
    border-radius: 10px !important;
    background-color: #020617 !important;
}

/* Focus sur un selectbox */
[data-testid="stSidebar"] div[data-baseweb="select"]:focus-within {
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px #22c55e !important;
}

/* Sidebar en mode drawer (mobile) */
[aria-label="Main menu"] + div [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020920) !important;
}

/* Bannière "Terrain" en haut */
.tm-pitch-overlay {
    position:absolute;
    top:0;
    left:0;
    right:0;
    height:180px;
    pointer-events:none;
    opacity:0.45;
    background-image:
        linear-gradient(to right, rgba(120,150,150,0.13) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(120,150,150,0.13) 1px, transparent 1px);
    background-size:36px 36px;
    mask-image: linear-gradient(to bottom, black, transparent);
}

/* Logo arrondi */
.tm-logo-rounded {
    width: 140px;
    height: 140px;
    border-radius: 22px;   
    overflow: hidden;
    border: 1px solid rgba(148,163,184,0.55);
    box-shadow: 0 12px 28px rgba(0,0,0,0.75);
    background: #0a0f1c;
}
.tm-logo-rounded img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Cartes élégantes */
.tm-card {
    background: radial-gradient(circle at 0 0, #22c55e22 0, #020617 70%);
    padding: 1.3rem;
    border-radius: 22px;
    border: 1px solid rgba(200,200,200,0.14);
    box-shadow: 0 18px 35px rgba(0,0,0,0.65);
}

/* Badge style tournoi */
.tm-chip {
    display:inline-flex;
    align-items:center;
    gap: .4rem;
    padding:.28rem .7rem;
    border-radius:999px;
    border:1px solid rgba(200,200,200,0.3);
    font-size:.75rem;
    text-transform:uppercase;
    letter-spacing:.05em;
    color:#e5e7eb;
}
.tm-chip-dot {
    width:7px;
    height:7px;
    border-radius:999px;
    background:#22c55e;
}

/* ============================
   TABS — Style par défaut pour TOUS les tabs
   ============================ */

/* Conteneur des tabs principaux */
div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 0.6rem;
    padding-bottom: 0.25rem;
    border-bottom: none !important;
}

/* Tous les tabs par défaut = style rond */
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 0.45rem 1.3rem !important;
    background: #020617 !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-bottom: 1px solid rgba(255,255,255,0.16) !important;
    color: #9ca3af !important;
    font-weight: 600 !important;
}

/* Tab sélectionné par défaut = pill verte (PAS de barre en dessous) */
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(34,197,94,0.18) !important;
    border-color: #22c55e !important;
    border-bottom: 1px solid #22c55e !important;
    color: #e5e7eb !important;
}

/* ============================
   SOUS-TABS — Override pour style "barre"
   Cible UNIQUEMENT les tabs imbriqués (niveau 2+)
   ============================ */

/* Conteneur des sous-tabs */
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 1.2rem !important;
    border-bottom: 1px solid rgba(148,163,184,0.28) !important;
    padding-bottom: 0 !important;
    margin-top: 0.35rem !important;
}

/* Boutons de sous-tabs = OVERRIDE du style par défaut */
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 0 !important;
    background: transparent !important;
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.2rem 0 0.35rem 0 !important;
    color: #9ca3af !important;
    font-weight: 500 !important;
}

/* Sous-tab actif = OVERRIDE complet */
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: transparent !important;
    color: #22c55e !important;
    border: none !important;
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-bottom: 2px solid #22c55e !important;
    font-weight: 600 !important;
}


/* Expanders = fiches match */
.streamlit-expanderHeader {
    background:#0f172a !important;
    border-radius:18px !important;
    padding:.75rem 1rem !important;
    border:1px solid rgba(255,255,255,0.12);
}

/* Dataframes stylés */
[data-testid="stDataFrame"] {
    border-radius:16px !important;
    overflow:hidden !important;
    border:1px solid rgba(255,255,255,0.15) !important;
    box-shadow:0 18px 28px rgba(0,0,0,0.6) !important;
}

</style>
"""

st.markdown(FOOTBALL_CSS, unsafe_allow_html=True)

# Secrets attendus

DATABASE_URL = st.secrets.get("DATABASE_URL", "sqlite:///pronos.db")
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
ADMIN_PLAYER_NAME = st.secrets["ADMIN_PLAYER_NAME"]
ADMIN_PLAYER_PIN = st.secrets["ADMIN_PLAYER_PIN"]

# -----------------------------
# DB INIT
# -----------------------------
engine: Engine = create_engine(DATABASE_URL, future=True)
meta = MetaData()

users = Table(
    "users", meta,
    Column("user_id", String, primary_key=True),
    Column("display_name", String, unique=True, nullable=False),
    Column("pin_code", String, nullable=False),
    Column("is_game_master", Integer, nullable=False, server_default="0"),
    Column("login_token", String, nullable=True),  # 👈 nouveau
)

matches = Table(
    "matches", meta,
    Column("match_id", String, primary_key=True),
    Column("home", String, nullable=False),
    Column("away", String, nullable=False),
    Column("kickoff_paris", String, nullable=False),  # "YYYY-MM-DD HH:MM" heure de Paris
    Column("final_home", Integer, nullable=True),
    Column("final_away", Integer, nullable=True),
    Column("category", String, nullable=True),  # colonne directement créée
)

predictions = Table(
    "predictions", meta,
    Column("prediction_id", String, primary_key=True),
    Column("user_id", String, ForeignKey("users.user_id"), nullable=False),
    Column("match_id", String, ForeignKey("matches.match_id"), nullable=False),
    Column("ph", Integer, nullable=False),
    Column("pa", Integer, nullable=False),
    Column("time
