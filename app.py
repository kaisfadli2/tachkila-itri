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

/* Quand le champ est actif (focus dans l’in*
