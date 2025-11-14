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
   TABS — style général "ronds"
   ============================ */

/* Tous les st.tabs ont ce style par défaut → ronds */
div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 0.6rem;
    padding-bottom: 0.25rem;
}

div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 0.45rem 1.3rem !important;
    background: #020617 !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    color: #9ca3af !important;
    font-weight: 600 !important;
}

/* Onglet sélectionné = pill verte douce */
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(34,197,94,0.18) !important;
    border-color: #22c55e !important;
    color: #e5e7eb !important;
}


/* ============================
   SOUS-TABS — style "barre" (dans .tm-subtabs)
   ============================ */

/* Conteneur des sous-tabs (Mes matchs, Maître de jeu) */
.tm-subtabs div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 1.2rem;
    border-bottom: 1px solid rgba(148,163,184,0.28);
    padding-bottom: 0;
    margin-top: 0.35rem;
}

/* Boutons de sous-tabs = texte simple */
.tm-subtabs div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 0 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.2rem 0 0.35rem 0 !important;
    color: #9ca3af !important;
    font-weight: 500 !important;
}

/* Sous-tab actif = barre + texte vert */
.tm-subtabs div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: transparent !important;
    color: #22c55e !important;
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
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "changeme")
DATABASE_URL = st.secrets.get("DATABASE_URL", "sqlite:///pronos.db")

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
    Column("timestamp_utc", String, nullable=False),
    UniqueConstraint("user_id", "match_id", name="uniq_user_match"),
)

category_rules = Table(
    "category_rules",
    meta,
    Column("category", String, primary_key=True),
    Column("points_result", Integer, nullable=False, server_default="2"),  # bon résultat
    Column("points_exact", Integer, nullable=False, server_default="4"),   # score exact
)

# 👉 NOUVELLE TABLE : points manuels (bonus/malus)
manual_points = Table(
    "manual_points",
    meta,
    Column("adjustment_id", String, primary_key=True),
    Column("user_id", String, ForeignKey("users.user_id"), nullable=False),
    Column("points", Integer, nullable=False),
    Column("reason", String, nullable=False),
    Column("created_at", String, nullable=False),  # "YYYY-MM-DD HH:MM:SS" UTC
)

# 👉 CRÉATION DES TABLES SI ELLES N'EXISTENT PAS (nouvelle base)
meta.create_all(engine)


def init_first_user():
    """Crée un premier user par défaut si la table est vide."""
    with engine.begin() as conn:
        count = conn.execute(
            select(func.count()).select_from(users)
        ).scalar()
        if count == 0:
            uid = str(uuid.uuid4())
            display_name = "Admin"
            pin_code = "0000"
            conn.execute(
                insert(users).values(
                    user_id=uid,
                    display_name=display_name,
                    pin_code=pin_code,
                    is_game_master=1,  # Admin = maître de jeu par défaut
                )
            )


init_first_user()

# -----------------------------
# AUTO-LOGIN VIA TOKEN DANS L'URL
# -----------------------------
def auto_login_from_token():
    # Si déjà connecté, ne rien faire
    if st.session_state.get("player") is not None:
        return

    params = st.query_params
    token_list = params.get("token")
    if not token_list:
        return

    # token_list peut être str ou list selon la version, on gère les deux
    if isinstance(token_list, list):
        token = token_list[0]
    else:
        token = token_list

    with engine.begin() as conn:
        row = conn.execute(
            select(users).where(users.c.login_token == token)
        ).mappings().first()

    if row:
        st.session_state["player"] = dict(row)
        st.session_state["collapse_sidebar"] = True


# 👉 On peut appeler la fonction maintenant que engine/users existent
auto_login_from_token()

# -----------------------------
# UTILS
# -----------------------------
def get_logo_base64():
    img_path = Path("ballon_maroc.jpg")  # ⚠️ mets le bon nom EXACT ici
    data = img_path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def now_maroc():
    return datetime.now(ZoneInfo("Africa/Casablanca"))
    
DAY_ABBR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
MONTH_ABBR = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"]

def format_dt_local(dt: datetime) -> str:
    """Formate un datetime en style 'Ven 14 nov 2025 — 20:45' en heure marocaine."""
    jour = DAY_ABBR[dt.weekday()]
    mois = MONTH_ABBR[dt.month - 1]
    return f"{jour} {dt.day:02d} {mois} {dt.year} — {dt:%H:%M}"


def is_editable(kickoff_paris_str: str) -> bool:
    """True si on peut encore modifier le prono (avant coup d'envoi)."""
    try:
        ko_local = datetime.strptime(
            kickoff_paris_str, "%Y-%m-%d %H:%M"
        ).replace(tzinfo=ZoneInfo("Africa/Casablanca"))
        return now_maroc() < ko_local
    except Exception:
        return False


def result_sign(h, a):
    h, a = int(h), int(a)
    return (h > a) - (h < a)  # 1/0/-1


def compute_points(ph, pa, fh, fa, pts_result=2, pts_exact=4):
    """
    pts_result  = points pour bon résultat (victoire/nul/défaite)
    pts_exact   = points pour score exact
    """
    try:
        if fh is None or fa is None:
            return 0
        ph, pa, fh, fa = int(ph), int(pa), int(fh), int(fa)
        if ph == fh and pa == fa:
            return pts_exact
        return pts_result if result_sign(ph, pa) == result_sign(fh, fa) else 0
    except Exception:
        return 0



@st.cache_data(ttl=10)
def load_df():
    with engine.begin() as conn:
        df_users = pd.read_sql(select(users), conn)
        df_matches = pd.read_sql(select(matches), conn)
        df_preds = pd.read_sql(select(predictions), conn)
    return df_users, df_matches, df_preds


@st.cache_data
def load_manual_points():
    """Charge les points manuels (bonus/malus)."""
    with engine.begin() as conn:
        try:
            df = pd.read_sql(select(manual_points), conn)
        except Exception:
            df = pd.DataFrame(columns=["adjustment_id", "user_id", "points", "reason", "created_at"])
    return df


def upsert_prediction(user_id: str, match_id: str, ph: int, pa: int):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with engine.begin() as conn:
        row = conn.execute(
            select(predictions)
            .where(predictions.c.user_id == user_id, predictions.c.match_id == match_id)
        ).mappings().first()
        if row:
            conn.execute(
                update(predictions)
                .where(predictions.c.prediction_id == row["prediction_id"])
                .values(ph=int(ph), pa=int(pa), timestamp_utc=ts)
            )
        else:
            conn.execute(
                insert(predictions).values(
                    prediction_id=str(uuid.uuid4()),
                    user_id=user_id,
                    match_id=match_id,
                    ph=int(ph),
                    pa=int(pa),
                    timestamp_utc=ts,
                )
            )
    st.cache_data.clear()


def add_match(home: str, away: str, kickoff_paris: str, category: str | None = None):
    """Ajoute un match. kickoff_paris = 'YYYY-MM-DD HH:MM' heure de Paris."""
    _ = datetime.strptime(kickoff_paris, "%Y-%m-%d %H:%M")  # validation simple

    if category is not None:
        category = category.strip()
        if category == "":
            category = None

    with engine.begin() as conn:
        conn.execute(insert(matches).values(
            match_id=str(uuid.uuid4()),
            home=home.strip(),
            away=away.strip(),
            kickoff_paris=kickoff_paris.strip(),
            final_home=None,
            final_away=None,
            category=category,
        ))
    st.cache_data.clear()


def set_final_score(match_id: str, fh: int, fa: int):
    with engine.begin() as conn:
        conn.execute(
            update(matches)
            .where(matches.c.match_id == match_id)
            .values(final_home=int(fh), final_away=int(fa))
        )
    st.cache_data.clear()


def create_player(display_name: str) -> str:
    """Crée un joueur avec un code à 4 chiffres et renvoie ce code."""
    display_name = display_name.strip()
    if not display_name:
        raise ValueError("Le nom du joueur est obligatoire.")

    pin = f"{random.randint(1000, 9999)}"  # code aléatoire 4 chiffres

    with engine.begin() as conn:
        row = conn.execute(
            select(users).where(users.c.display_name == display_name)
        ).mappings().first()
        if row:
            raise ValueError("Ce joueur existe déjà.")

        uid = str(uuid.uuid4())
        conn.execute(
            insert(users).values(
                user_id=uid,
                display_name=display_name,
                pin_code=pin,
                is_game_master=0,
            )
        )

    st.cache_data.clear()
    return pin


def update_pin_code(user_id: str, new_pin: str):
    """Permet à l'admin de modifier manuellement le code d'un joueur."""
    new_pin = new_pin.strip()
    if not new_pin or len(new_pin) != 4 or not new_pin.isdigit():
        raise ValueError("Le code doit contenir exactement 4 chiffres (0-9).")

    with engine.begin() as conn:
        conn.execute(
            update(users)
            .where(users.c.user_id == user_id)
            .values(pin_code=new_pin)
        )
    st.cache_data.clear()


def authenticate_player(display_name: str, pin_code: str):
    """Vérifie nom + code, renvoie le user ou None."""
    display_name = display_name.strip()
    pin_code = pin_code.strip()
    if not display_name or not pin_code:
        return None

    with engine.begin() as conn:
        row = conn.execute(
            select(users).where(
                users.c.display_name == display_name,
                users.c.pin_code == pin_code
            )
        ).mappings().first()
    return row  # dict-like ou None


def delete_match_and_predictions(match_id: str):
    """Supprime un match et tous les pronostics associés."""
    with engine.begin() as conn:
        conn.execute(delete(predictions).where(predictions.c.match_id == match_id))
        conn.execute(delete(matches).where(matches.c.match_id == match_id))
    st.cache_data.clear()


def set_game_master(user_id: str, is_gm: bool):
    """Active ou désactive le rôle maître de jeu pour un joueur."""
    with engine.begin() as conn:
        conn.execute(
            update(users)
            .where(users.c.user_id == user_id)
            .values(is_game_master=1 if is_gm else 0)
        )
    st.cache_data.clear()


def add_manual_points(user_id: str, points: int, reason: str):
    """
    Ajoute des points manuels (bonus ou malus) à un joueur avec une raison.
    """
    reason = reason.strip()
    if not reason:
        raise ValueError("La raison est obligatoire.")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with engine.begin() as conn:
        conn.execute(
            insert(manual_points).values(
                adjustment_id=str(uuid.uuid4()),
                user_id=user_id,
                points=int(points),
                reason=reason,
                created_at=ts,
            )
        )

    st.cache_data.clear()


@st.cache_data
def load_catalog():
    """Charge la liste des clubs et sélections depuis le CSV."""
    return pd.read_csv("teams_catalog.csv")


catalog = load_catalog()

@st.cache_data
def load_category_rules():
    with engine.begin() as conn:
        try:
            df = pd.read_sql(select(category_rules), conn)
        except Exception:
            df = pd.DataFrame(columns=["category", "points_result", "points_exact"])
    return df

def logo_for(team_name):
    """Retourne le lien du logo si disponible."""
    try:
        row = catalog.loc[catalog["name"] == team_name]
        if row.empty:
            return None
        url = row.iloc[0]["logo_url"]
        if isinstance(url, str) and len(url) > 0:
            return url
    except Exception:
        return None
    return None
    

def format_kickoff(paris_str: str) -> str:
    """
    'YYYY-MM-DD HH:MM' → 'Ven 14 nov 2025 — 20:45'
    """
    try:
        dt = datetime.strptime(paris_str, "%Y-%m-%d %H:%M")
    except Exception:
        return paris_str

    jour = DAY_ABBR[dt.weekday()]
    mois = MONTH_ABBR[dt.month - 1]
    return f"{jour} {dt.day:02d} {mois} {dt.year} — {dt:%H:%M}"

def edited_after_kickoff(timestamp_utc_str: str, kickoff_paris_str: str) -> bool:
    """
    True si le prono a été enregistré APRÈS le coup d’envoi (en heure marocaine).
    Donc forcément via le maître de jeu.
    """
    try:
        ts_utc = datetime.strptime(timestamp_utc_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        ts_ma = ts_utc.astimezone(ZoneInfo("Africa/Casablanca"))

        ko_ma = datetime.strptime(kickoff_paris_str, "%Y-%m-%d %H:%M").replace(
            tzinfo=ZoneInfo("Africa/Casablanca")
        )

        return ts_ma > ko_ma
    except Exception:
        return False

def format_time_ma(dt: datetime) -> str:
    """Retourne l'heure locale HH:MM en heure marocaine."""
    return dt.strftime("%H:%M")

def upsert_category_rule(category: str, pts_result: int, pts_exact: int):
    category = category.strip()
    if not category:
        return

    with engine.begin() as conn:
        row = conn.execute(
            select(category_rules).where(category_rules.c.category == category)
        ).mappings().first()

        if row:
            conn.execute(
                update(category_rules)
                .where(category_rules.c.category == category)
                .values(points_result=int(pts_result), points_exact=int(pts_exact))
            )
        else:
            conn.execute(
                insert(category_rules).values(
                    category=category,
                    points_result=int(pts_result),
                    points_exact=int(pts_exact),
                )
            )

    st.cache_data.clear()

def update_match_kickoff(match_id: str, kickoff_paris: str):
    """
    Modifie la date/heure d'un match.
    kickoff_paris doit être au format 'YYYY-MM-DD HH:MM'
    """
    # validation simple du format
    _ = datetime.strptime(kickoff_paris, "%Y-%m-%d %H:%M")

    with engine.begin() as conn:
        conn.execute(
            update(matches)
            .where(matches.c.match_id == match_id)
            .values(kickoff_paris=kickoff_paris)
        )
    st.cache_data.clear()

# -----------------------------
# UI - HEADER + SIDEBAR
# -----------------------------

# Overlay "lignes de terrain"
st.markdown('<div class="tm-pitch-overlay"></div>', unsafe_allow_html=True)
logo_b64 = get_logo_base64()

# On essaye de récupérer le joueur dans la session
current_player = st.session_state.get("player", None)
current_name = current_player["display_name"] if current_player else "Invité"

st.markdown(
    f"""
    <div class="tm-card" style="margin-bottom: 1.2rem; position: relative; overflow: hidden;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:1.3rem;">
            <div>
                <div class="tm-chip" style="padding:.45rem 1.1rem; border-radius:999px; display:inline-flex; align-items:center; gap:.5rem;">
                    <span class="tm-chip-dot" style="width:10px;height:10px;"></span>
                    <span style="
                        font-size:1.2rem;
                        font-weight:700;
                        letter-spacing:0.04em;
                    ">
                        {current_name}
                    </span>
                </div>
                <div style="font-size:2.3rem; font-weight:800; margin-top:0.6rem;">
                    Tachkila Mouchkila
                </div>
                <div style="margin-top:0.2rem; font-size:1rem; color:#cbd5f5;">
                    ITRI
                </div>
            </div>
            <div class="tm-logo-rounded">
                <img src="data:image/jpeg;base64,{logo_b64}" alt="Logo Tachkila Mouchkila">
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


with st.sidebar:
    # Connexion joueur
    st.header("Connexion joueur")

    if st.session_state["player"] is None:
        name_input = st.text_input("Nom du joueur")
        pin_input = st.text_input("Code à 4 chiffres", type="password", max_chars=4)

        if st.button("Se connecter"):
            user = authenticate_player(name_input, pin_input)
            if user is None:
                st.error("Nom ou code incorrect (demande à l'admin de vérifier ton code).")
            else:
                # Générer un token de session “persistant”
                token = str(uuid.uuid4())

                with engine.begin() as conn:
                    conn.execute(
                        update(users)
                        .where(users.c.user_id == user["user_id"])
                        .values(login_token=token)
                    )

                st.session_state["player"] = dict(user)
                st.session_state["collapse_sidebar"] = True

                # Mettre à jour les query params (remplace l'ancien experimental_set_query_params)
                st.query_params.clear()
                st.query_params["token"] = token

                st.rerun()

    else:
        player = st.session_state["player"]
        st.success(f"Connecté : {player['display_name']}")
        if st.button("Changer de joueur"):
            st.session_state["player"] = None
            # On enlève le token de l'URL
            st.query_params.clear()
            st.rerun()

    st.markdown("---")

    # Mode admin
    st.header("Mode administrateur")

    if not st.session_state["admin_authenticated"]:
        admin_pw_input = st.text_input("Mot de passe admin", type="password")
        if st.button("Activer le mode admin"):
            if admin_pw_input == ADMIN_PASSWORD:
                st.session_state["admin_authenticated"] = True
                st.success("Mode admin activé")
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
    else:
        st.success("Mode admin actif")
        if st.button("Désactiver le mode admin"):
            st.session_state["admin_authenticated"] = False
            st.rerun()


# -----------------------------
# CONTEXTE UTILISATEUR
# -----------------------------
player = st.session_state["player"]
admin_authenticated = st.session_state["admin_authenticated"]

if player is None:
    st.info("Commence par te connecter avec ton nom + code à 4 chiffres dans la colonne de gauche.")
    st.stop()

df_users, df_matches, df_preds = load_df()
user_id = player["user_id"]
display_name = player["display_name"]

# Rôle maître de jeu ?
row_me = df_users[df_users["user_id"] == user_id]
if not row_me.empty and "is_game_master" in row_me.columns:
    is_game_master = bool(row_me.iloc[0]["is_game_master"])
else:
    is_game_master = False

can_manage_matches = admin_authenticated or is_game_master

# -----------------------------
# TABS
# -----------------------------
tab_labels = ["Mes matchs", "Classement"]
tab_ids = ["pronos", "classement"]

# Onglet "Maître de jeu" visible pour admin OU maître de jeu
if can_manage_matches:
    tab_labels.append("Maître de jeu")
    tab_ids.append("maitre")

# Onglet "Admin" visible uniquement pour l'admin
if admin_authenticated:
    tab_labels.append("Admin")
    tab_ids.append("admin")

tabs = st.tabs(tab_labels)
tab_dict = dict(zip(tab_ids, tabs))

tab_pronos = tab_dict["pronos"]
tab_classement = tab_dict["classement"]
tab_maitre = tab_dict.get("maitre")
tab_admin = tab_dict.get("admin")

# -----------------------------
# TAB PRONOS
# -----------------------------
with tab_pronos:

    if df_matches.empty:
        st.info("Aucun match pour le moment.")
    else:
        # Copie + parsing de la date
        df_matches_work = df_matches.copy()
        try:
            df_matches_work["_ko"] = pd.to_datetime(
                df_matches_work["kickoff_paris"], format="%Y-%m-%d %H:%M"
            )
        except Exception:
            df_matches_work["_ko"] = pd.to_datetime(
                df_matches_work["kickoff_paris"], errors="coerce"
            )

        # Match terminé = score final saisi
        df_matches_work["res_known"] = (
            df_matches_work["final_home"].notna()
            & df_matches_work["final_away"].notna()
        )

        # Match commencé ou pas (en heure marocaine)
        now = now_maroc().replace(tzinfo=None)
        
        df_matches_work["has_started"] = df_matches_work["_ko"].apply(
            lambda x: (pd.notna(x) and x <= now)
        )

        # 🟢 Matchs à venir : pas commencé, pas de score final
        df_a_venir = df_matches_work[
            (~df_matches_work["res_known"]) & (~df_matches_work["has_started"])
        ].sort_values("_ko", ascending=True, na_position="last")

        # 🟠 Matchs en cours : commencé, pas de score final
        df_en_cours = df_matches_work[
            (~df_matches_work["res_known"]) & (df_matches_work["has_started"])
        ].sort_values("_ko", ascending=True, na_position="last")

        # ⚪ Matchs terminés : score final saisi
        df_termines = df_matches_work[
            df_matches_work["res_known"]
        ].sort_values("_ko", ascending=False, na_position="last")

        # Pronostics du joueur courant
        my_preds = df_preds[df_preds["user_id"] == user_id]

        # Sous-onglets
        tab_avenir, tab_cours, tab_done = st.tabs(
            ["Matchs à venir", "Matchs en cours", "Matchs terminés"]
        )

        # ==========================
        # 🟢 MATCHS À VENIR
        # ==========================
        with tab_avenir:
            if df_a_venir.empty:
                st.caption("Aucun match à venir pour le moment.")
            else:
                for _, m in df_a_venir.iterrows():
                    exp_label = f"{m['home']} vs {m['away']} — {format_kickoff(m['kickoff_paris'])}"
                    with st.expander(exp_label):
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                        # Infos match + logos
                        with c1:
                            l1, l2, l3 = st.columns([1, 2, 1])
                            with l1:
                                lg_home = logo_for(m["home"])
                                if lg_home:
                                    st.image(lg_home, width=40)
                            with l2:
                                st.markdown(f"**{m['home']} vs {m['away']}**")
                                st.caption(f"Coup d’envoi : {format_kickoff(m['kickoff_paris'])}")
                                if "category" in m.index and pd.notna(m["category"]):
                                    st.caption(f"Catégorie : {m['category']}")
                            with l3:
                                lg_away = logo_for(m["away"])
                                if lg_away:
                                    st.image(lg_away, width=40)

                        existing = my_preds[my_preds["match_id"] == m["match_id"]]
                        ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                        pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                        editable = True  # par définition, à venir = éditable

                        with c2:
                            ph = st.number_input(
                                f"{m['home']} (dom.)",
                                0, 20, ph0, 1,
                                key=f"ph_future_{m['match_id']}",
                                disabled=not editable
                            )
                        with c3:
                            pa = st.number_input(
                                f"{m['away']} (ext.)",
                                0, 20, pa0, 1,
                                key=f"pa_future_{m['match_id']}",
                                disabled=not editable
                            )
                        with c4:
                            if editable:
                                if st.button("💾 Enregistrer", key=f"save_future_{m['match_id']}"):
                                    upsert_prediction(user_id, m["match_id"], ph, pa)
                                    st.success("Pronostic enregistré ✅")

        # ==========================
        # 🟠 MATCHS EN COURS
        # ==========================
        with tab_cours:
            if df_en_cours.empty:
                st.caption("Aucun match en cours pour le moment.")
            else:
                for _, m in df_en_cours.iterrows():
                    exp_label = f"{m['home']} vs {m['away']} — {format_kickoff(m['kickoff_paris'])}"
                    with st.expander(exp_label):
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                        # Infos match + logos
                        with c1:
                            l1, l2, l3 = st.columns([1, 2, 1])
                            with l1:
                                lg_home = logo_for(m["home"])
                                if lg_home:
                                    st.image(lg_home, width=40)
                            with l2:
                                st.markdown(f"**{m['home']} vs {m['away']}**")
                                st.caption(f"Coup d’envoi : {format_kickoff(m['kickoff_paris'])}")
                                if "category" in m.index and pd.notna(m["category"]):
                                    st.caption(f"Catégorie : {m['category']}")
                            with l3:
                                lg_away = logo_for(m["away"])
                                if lg_away:
                                    st.image(lg_away, width=40)

                        existing = my_preds[my_preds["match_id"] == m["match_id"]]
                        ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                        pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                        editable = False  # match en cours = verrouillé pour le joueur

                        with c2:
                            st.number_input(
                                f"{m['home']} (dom.)",
                                0, 20, ph0, 1,
                                key=f"ph_live_{m['match_id']}",
                                disabled=not editable
                            )
                        with c3:
                            st.number_input(
                                f"{m['away']} (ext.)",
                                0, 20, pa0, 1,
                                key=f"pa_live_{m['match_id']}",
                                disabled=not editable
                            )
                        with c4:
                            st.info("⛔ Verrouillé (match commencé)")

        # ==========================
        # ⚪ MATCHS TERMINÉS
        # ==========================
        with tab_done:
            if df_termines.empty:
                st.caption("Aucun match terminé pour le moment.")
            else:
                for _, m in df_termines.iterrows():
                    exp_label = f"{m['home']} vs {m['away']} — {format_kickoff(m['kickoff_paris'])}"
                    with st.expander(exp_label):
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                        # Infos match + logos
                        with c1:
                            l1, l2, l3 = st.columns([1, 2, 1])
                            with l1:
                                lg_home = logo_for(m["home"])
                                if lg_home:
                                    st.image(lg_home, width=40)
                            with l2:
                                st.markdown(f"**{m['home']} vs {m['away']}**")
                                st.caption(f"Coup d’envoi : {format_kickoff(m['kickoff_paris'])}")
                                if "category" in m.index and pd.notna(m["category"]):
                                    st.caption(f"Catégorie : {m['category']}")
                                st.caption(
                                    f"Score final : {int(m['final_home'])} - {int(m['final_away'])}"
                                )
                            with l3:
                                lg_away = logo_for(m["away"])
                                if lg_away:
                                    st.image(lg_away, width=40)

                        existing = my_preds[my_preds["match_id"] == m["match_id"]]
                        ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                        pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                        # Toujours non éditable
                        with c2:
                            st.number_input(
                                f"{m['home']} (dom.)",
                                0, 20, ph0, 1,
                                key=f"ph_done_{m['match_id']}",
                                disabled=True
                            )
                        with c3:
                            st.number_input(
                                f"{m['away']} (ext.)",
                                0, 20, pa0, 1,
                                key=f"pa_done_{m['match_id']}",
                                disabled=True
                            )
                        with c4:
                            st.info("✅ Match terminé")


# -----------------------------
# TAB CLASSEMENT
# -----------------------------
with tab_classement:
    if df_preds.empty and load_manual_points().empty:
        st.info("Pas encore de pronostics ou de points manuels.")
    elif df_matches.empty and df_preds.empty:
        st.info("Pas encore de matches terminés ni de pronostics, mais il peut y avoir des points manuels.")
    else:
        df_manual = load_manual_points()

        # Jointure pronos + matches + joueurs
        merged = (
            df_preds
            .merge(df_matches, on="match_id", how="left")
            .merge(df_users, on="user_id", how="left")
        )

        # On enlève l'Admin du classement pour les pronos
        merged = merged[merged["display_name"] != "Admin"]

        # Charger les règles de catégories (2/4 par défaut si pas de règle)
        df_rules = load_category_rules()

        def points_for_row(r):
            pts_result = 2
            pts_exact = 4

            cat = r.get("category", None)
            if pd.notna(cat):
                rule = df_rules[df_rules["category"] == cat]
                if not rule.empty:
                    pts_result = int(rule.iloc[0]["points_result"])
                    pts_exact = int(rule.iloc[0]["points_exact"])

            return compute_points(
                r["ph"], r["pa"],
                r["final_home"], r["final_away"],
                pts_result, pts_exact,
            )

        if not merged.empty:
            merged["points"] = merged.apply(points_for_row, axis=1)
        else:
            merged["points"] = []

        # --------------------------
        # Agrégation points pronos
        # --------------------------
        if not merged.empty:
            leaderboard_pronos = (
                merged.groupby(["user_id", "display_name"], dropna=False)["points"]
                .sum()
                .reset_index()
            )
        else:
            leaderboard_pronos = pd.DataFrame(columns=["user_id", "display_name", "points"])

        # --------------------------
        # Agrégation points manuels
        # --------------------------
        if not df_manual.empty:
            df_manual_users = df_manual.merge(df_users, on="user_id", how="left")
            df_manual_users = df_manual_users[df_manual_users["display_name"] != "Admin"]
            manual_agg = (
                df_manual_users.groupby(["user_id", "display_name"], dropna=False)["points"]
                .sum()
                .reset_index()
            )
        else:
            manual_agg = pd.DataFrame(columns=["user_id", "display_name", "points"])

        # Fusion des deux sources de points
        leaderboard = pd.concat(
            [leaderboard_pronos, manual_agg],
            ignore_index=True,
        )

        if not leaderboard.empty:
            leaderboard = (
                leaderboard.groupby(["user_id", "display_name"], dropna=False)["points"]
                .sum()
                .reset_index()
            )

            # Tri
            leaderboard = leaderboard.sort_values(
                ["points", "display_name"], ascending=[False, True]
            )

        if leaderboard.empty:
            st.info("Les scores finaux ne sont pas encore saisis et aucun point manuel n'a été ajouté.")
        else:
            # ==========================
            # PODIUM
            # ==========================
            st.markdown("### Podium")

            top3 = leaderboard.head(3).reset_index(drop=True)
            cols = st.columns(3)
            
            medals = ["🥇", "🥈", "🥉"]
            colors = ["#ffd700", "#c0c0c0", "#cd7f32"]
            
            for i, row in top3.iterrows():
                with cols[i]:
                    pseudo = row["display_name"]
                    pts = row["points"]
                    medal = medals[i]
                    color = colors[i]
            
                    st.markdown(
                        f"""
                        <div style="
                            background:{color}22;
                            border:2px solid {color};
                            border-radius:20px;
                            padding:16px;
                            text-align:center;
                            box-shadow:0 4px 10px rgba(0,0,0,0.15);
                        ">
                            <div style="font-size:40px;">{medal}</div>
                            <div style="font-size:20px;font-weight:700;margin-top:4px;">{pseudo}</div>
                            <div style="font-size:16px;margin-top:8px;">{pts} points</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # ==========================
            # CLASSEMENT COMPLET
            # ==========================
            st.markdown("### Classement complet")

            lb = leaderboard.reset_index(drop=True)
            for idx, row in lb.iterrows():
                rank = idx + 1
                pseudo = row["display_name"]
                pts = row["points"]

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        align-items:center;
                        margin-bottom:6px;
                    ">
                        <div style="
                            width:32px;height:32px;
                            border-radius:50%;
                            background:#0f4c81;
                            color:white;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-weight:700;
                            margin-right:8px;
                        ">{rank}</div>
                        <div style="flex:1;">
                            <span style="font-weight:600;">{pseudo}</span>
                            <span style="color:#9ca3af;"> — {pts} pts</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # ==========================
            # DÉTAIL PAR MATCH (+ points manuels)
            # ==========================
            with st.expander("Détail par match et points manuels"):
                detail = merged.copy()

                # On s'assure que la colonne "manual_reason" existe
                if "manual_reason" not in detail.columns:
                    detail["manual_reason"] = ""

                # Ajout des lignes de points manuels dans le détail
                df_manual_all = load_manual_points()
                if not df_manual_all.empty:
                    df_manual_all = df_manual_all.merge(df_users, on="user_id", how="left")
                    df_manual_all = df_manual_all[df_manual_all["display_name"] != "Admin"]

                    if not df_manual_all.empty:
                        manual_detail = pd.DataFrame({
                            "user_id": df_manual_all["user_id"],
                            "display_name": df_manual_all["display_name"],
                            "ph": [None] * len(df_manual_all),
                            "pa": [None] * len(df_manual_all),
                            "final_home": [None] * len(df_manual_all),
                            "final_away": [None] * len(df_manual_all),
                            "points": df_manual_all["points"],
                            "kickoff_paris": df_manual_all["created_at"].str.slice(0, 16),  # "YYYY-MM-DD HH:MM"
                            "timestamp_utc": df_manual_all["created_at"],
                            "manual_reason": df_manual_all["reason"],
                            "home": [None] * len(df_manual_all),
                            "away": [None] * len(df_manual_all),
                            "match_id": [None] * len(df_manual_all),
                            "category": [None] * len(df_manual_all),
                        })

                        # union des colonnes
                        common_cols = list(set(detail.columns).union(manual_detail.columns))
                        detail = pd.concat(
                            [
                                detail.reindex(columns=common_cols),
                                manual_detail.reindex(columns=common_cols),
                            ],
                            ignore_index=True,
                        )

                # Date du match (ou date du point manuel) en datetime pour filtrer sur les 7 derniers jours
                try:
                    detail["_ko"] = pd.to_datetime(
                        detail["kickoff_paris"], format="%Y-%m-%d %H:%M", errors="coerce"
                    )
                except Exception:
                    detail["_ko"] = pd.to_datetime(detail["kickoff_paris"], errors="coerce")

                # Filtre : uniquement les 7 derniers jours (heure marocaine)
                today_ma = now_maroc().date()
                min_date = today_ma - timedelta(days=7)
                detail = detail[detail["_ko"].dt.date >= min_date]

                if detail.empty:
                    st.caption("Aucun match ou point manuel sur les 7 derniers jours.")
                else:
                    # Label lisible pour chaque ligne
                    def make_label(row):
                        mr = row.get("manual_reason", "")
                        if isinstance(mr, str) and mr.strip() != "":
                            return f"Points manuels — {mr}"
                        else:
                            return f"{row['home']} vs {row['away']} — {format_kickoff(row['kickoff_paris'])}"

                    detail["match_label"] = detail.apply(make_label, axis=1)

                    # Choix du type de filtre
                    filtre = st.radio("Filtrer par :", ["Aucun", "Match", "Joueur"], horizontal=True)

                    if filtre == "Match":
                        # Matchs triés du plus récent au plus ancien
                        df_match_opts = (
                            detail.groupby("match_label")["_ko"]
                            .max()
                            .reset_index()
                            .sort_values("_ko", ascending=False)
                        )
                        matchs_disp = df_match_opts["match_label"].tolist()
                        match_sel = st.selectbox("Choisir un match / une raison", matchs_disp)
                        detail = detail[detail["match_label"] == match_sel]

                    elif filtre == "Joueur":
                        joueurs_disp = sorted(detail["display_name"].unique())
                        joueur_sel = st.selectbox("Choisir un joueur", joueurs_disp)
                        detail = detail[detail["display_name"] == joueur_sel]

                    # Construction du tableau final
                    show = detail[
                        [
                            "display_name",
                            "match_label",
                            "manual_reason",
                            "ph", "pa",
                            "final_home", "final_away",
                            "points",
                            "kickoff_paris",
                            "timestamp_utc",
                        ]
                    ].copy()

                    # Colonne emoji si prono enregistré après le coup d’envoi
                    show["⚠️"] = show.apply(
                        lambda r: (
                            "⚠️"
                            if isinstance(r["timestamp_utc"], str)
                            and isinstance(r["kickoff_paris"], str)
                            and edited_after_kickoff(r["timestamp_utc"], r["kickoff_paris"])
                            else ""
                        ),
                        axis=1,
                    )

                    # Renommage colonnes
                    show = show.rename(
                        columns={
                            "display_name": "Joueur",
                            "match_label": "Match / Raison",
                            "ph": "Prono D",
                            "pa": "Prono E",
                            "final_home": "Final D",
                            "final_away": "Final E",
                            "points": "Pts",
                            "kickoff_paris": "Coup d’envoi",
                        }
                    )

                    # Format lisible de la date
                    show["Coup d’envoi"] = show["Coup d’envoi"].apply(format_kickoff)

                    # On n'affiche plus le timestamp brut
                    show = show.drop(columns=["timestamp_utc"])

                    # Ordre des colonnes
                    cols_order = [
                        "Joueur",
                        "Match / Raison",
                        "Prono D", "Prono E",
                        "Final D", "Final E",
                        "Pts",
                        "⚠️",
                    ]

                    st.dataframe(
                        show[cols_order],
                        use_container_width=True,
                        hide_index=True,
                    )

# -----------------------------
# TAB MAÎTRE DE JEU
# -----------------------------
if tab_maitre is not None:
    with tab_maitre:
        if not can_manage_matches:
            st.info("Réservé à l'administrateur ou aux maîtres de jeu.")
        else:
            # Bandeau d'info sur le rôle
            if admin_authenticated and is_game_master:
                st.success("Mode admin + maître de jeu actifs.")
            elif admin_authenticated:
                st.success("Mode admin actif.")
            elif is_game_master:
                st.success("Mode maître de jeu actif (gestion des matches et des pronos des joueurs).")

            tab_ajout, tab_resultats, tab_pronos_joueurs, tab_points = st.tabs(
                ["Ajouter un match", "Résultats", "Pronos joueurs", "Points bonus/malus"]
            )

            # ONGLET 1 : AJOUTER UN MATCH
            with tab_ajout:
                st.markdown("### ➕ Ajouter un match")

                # Charger les catégories existantes
                df_users_cat, df_matches_cat, _ = load_df()
                existing_categories: list[str] = []
                if "category" in df_matches_cat.columns:
                    existing_categories = sorted(
                        [
                            str(c).strip()
                            for c in df_matches_cat["category"].dropna().unique()
                            if str(c).strip() != ""
                        ]
                    )

                options = ["(Aucune catégorie)"]
                if existing_categories:
                    options += existing_categories
                options.append("➕ Nouvelle catégorie...")

                cat_choice = st.selectbox("Catégorie du match (optionnel)", options)

                new_cat = ""
                pts_result = None
                pts_exact = None
                
                if cat_choice == "➕ Nouvelle catégorie...":
                    new_cat = st.text_input(
                        "Nouvelle catégorie",
                        placeholder="Ex : Poules, Quart de finale, Match amical..."
                    )
                
                    st.markdown("#### Règle de points pour cette catégorie")
                    col_res, col_exact = st.columns(2)
                    with col_res:
                        pts_result = st.number_input(
                            "Points pour bon résultat",
                            min_value=0,
                            max_value=20,
                            value=2,
                            step=1,
                        )
                    with col_exact:
                        pts_exact = st.number_input(
                            "Points pour score exact",
                            min_value=0,
                            max_value=50,
                            value=4,
                            step=1,
                        )

                with st.form("form_add_match"):
                    c1, c2, c3, c4 = st.columns([3, 3, 3, 2])
                
                    # Équipe domicile
                    with c1:
                        home = st.selectbox(
                            "Équipe domicile",
                            options=catalog["name"].sort_values(),
                            index=None,
                            placeholder="Choisir une équipe..."
                        )
                        if home:
                            logo = logo_for(home)
                            if logo:
                                st.image(logo, width=64, caption=home)
                
                    # Équipe extérieur
                    with c2:
                        away = st.selectbox(
                            "Équipe extérieur",
                            options=catalog["name"].sort_values(),
                            index=None,
                            placeholder="Choisir une équipe..."
                        )
                        if away:
                            logo = logo_for(away)
                            if logo:
                                st.image(logo, width=64, caption=away)
                
                    # Date + Heure (HH:MM)
                    with c3:
                        # 📅 Date du match
                        date_match = st.date_input("📅 Date du match")
                    
                        # CSS pour rendre les selects étroites
                        st.markdown(
                            """
                            <style>
                            .narrow-select select {
                                width: 75px !important;
                                min-width: 75px !important;
                                max-width: 75px !important;
                                padding: 4px;
                                font-size: 15px;
                                text-align: center;
                            }
                            .time-sep {
                                font-size: 24px;
                                font-weight: 700;
                                text-align: center;
                                margin-top: 8px;
                            }
                            </style>
                            """,
                            unsafe_allow_html=True,
                        )
                    
                        # ⏰ Heure du match
                        st.markdown("⏰ Heure du match")
                    
                        h_col, sep_col, m_col = st.columns([1, 0.4, 1])
                    
                        with h_col:
                            heure_str = st.selectbox(
                                "",
                                options=[f"{i:02d}" for i in range(24)],
                                key="heure_match_h",
                                label_visibility="collapsed",
                                placeholder="HH",
                            )
                            st.markdown('<div class="narrow-select"></div>', unsafe_allow_html=True)
                    
                        with sep_col:
                            st.markdown('<div class="time-sep">:</div>', unsafe_allow_html=True)
                    
                        with m_col:
                            minute_str = st.selectbox(
                                "",
                                options=[f"{i:02d}" for i in range(60)],
                                key="heure_match_m",
                                label_visibility="collapsed",
                                placeholder="MM",
                            )
                            st.markdown('<div class="narrow-select"></div>', unsafe_allow_html=True)
                    
                        # Reconstruction de l'heure
                        heure_match = datetime.strptime(f"{heure_str}:{minute_str}", "%H:%M").time()
                        kickoff_dt = datetime.combine(date_match, heure_match)
                        kickoff = kickoff_dt.strftime("%Y-%m-%d %H:%M")

                    # Bouton de submit du formulaire ✅
                    with c4:
                        submit = st.form_submit_button("Ajouter")
                
                    # Traitement du submit
                    if submit:
                        if not home or not away:
                            st.warning("Sélectionne les deux équipes.")
                        elif home == away:
                            st.warning("L'équipe domicile et l'équipe extérieur doivent être différentes.")
                        else:
                            if new_cat.strip():
                                category = new_cat.strip()
                    
                                # si le maître du jeu a saisi des points, on enregistre la règle
                                if pts_result is not None and pts_exact is not None:
                                    upsert_category_rule(category, pts_result, pts_exact)
                    
                            elif cat_choice not in ["(Aucune catégorie)", "➕ Nouvelle catégorie..."]:
                                category = cat_choice
                            else:
                                category = None
                    
                            add_match(home, away, kickoff, category)
                            if category:
                                st.success(f"Match ajouté ✅ ({home} vs {away} — {kickoff}, catégorie : {category})")
                            else:
                                st.success(f"Match ajouté ✅ ({home} vs {away} — {kickoff})")
                            st.rerun()

            # ONGLET 2 : RÉSULTATS
            with tab_resultats:
                st.markdown("### 📝 Saisie et modification des résultats")

                df_users3, df_matches3, _ = load_df()
                if df_matches3.empty:
                    st.info("Aucun match pour le moment.")
                else:
                    try:
                        df_matches3["_ko"] = pd.to_datetime(
                            df_matches3["kickoff_paris"], format="%Y-%m-%d %H:%M"
                        )
                    except Exception:
                        df_matches3["_ko"] = pd.NaT

                    df_matches3 = df_matches3.sort_values(
                        "_ko", ascending=False, na_position="last"
                    ).drop(columns=["_ko"])

                    for _, m in df_matches3.iterrows():
                        match_id = m["match_id"]
                    
                        with st.expander(f"{m['home']} vs {m['away']} — {format_kickoff(m['kickoff_paris'])}"):
                            c1, c2 = st.columns([3, 2])
                    
                            # --- Infos match + logos ---
                            with c1:
                                st.markdown(f"**{m['home']} vs {m['away']}**")
                                st.caption(f"Coup d’envoi : {format_kickoff(m['kickoff_paris'])}")
                                if "category" in m.index and pd.notna(m["category"]):
                                    st.caption(f"Catégorie : {m['category']}")
                    
                                lc1, lc2 = st.columns(2)
                                with lc1:
                                    lg_home = logo_for(m["home"])
                                    if lg_home:
                                        st.image(lg_home, width=48, caption=m["home"])
                                with lc2:
                                    lg_away = logo_for(m["away"])
                                    if lg_away:
                                        st.image(lg_away, width=48, caption=m["away"])
                    
                            with c2:
                                if pd.notna(m["final_home"]) and pd.notna(m["final_away"]):
                                    st.markdown(
                                        f"**Score final actuel :** {int(m['final_home'])} - {int(m['final_away'])}"
                                    )
                                else:
                                    st.markdown("**Score final actuel :** non saisi")
                    
                            st.markdown("---")
                    
                            # --- Edition de la date / heure du match ---
                            # On parse la date/heure actuelle du match
                            try:
                                ko_dt = datetime.strptime(m["kickoff_paris"], "%Y-%m-%d %H:%M")
                            except Exception:
                                ko_dt = datetime.now()
                    
                            c_date, c_time, c_btn_time = st.columns([2, 2, 2])
                    
                            with c_date:
                                new_date = st.date_input(
                                    "📅 Date du match",
                                    value=ko_dt.date(),
                                    key=f"date_edit_{match_id}",
                                )
                    
                            with c_time:
                                new_time = st.time_input(
                                    "⏰ Heure du match",
                                    value=ko_dt.time(),
                                    key=f"time_edit_{match_id}",
                                )
                    
                            with c_btn_time:
                                if st.button("🕒 Mettre à jour date/heure", key=f"update_ko_{match_id}"):
                                    new_ko = datetime.combine(new_date, new_time)
                                    new_ko_str = new_ko.strftime("%Y-%m-%d %H:%M")
                                    update_match_kickoff(match_id, new_ko_str)
                                    st.success(f"Date/heure mises à jour : {format_kickoff(new_ko_str)} ✅")
                                    st.rerun()
                    
                            st.markdown("---")
                    
                            # --- Edition du score final ---
                            c3, c4, c5 = st.columns([2, 2, 2])
                    
                            default_fh = int(m["final_home"]) if pd.notna(m["final_home"]) else 0
                            default_fa = int(m["final_away"]) if pd.notna(m["final_away"]) else 0
                    
                            with c3:
                                new_fh = st.number_input(
                                    f"Score {m['home']}",
                                    min_value=0,
                                    max_value=50,
                                    step=1,
                                    value=default_fh,
                                    key=f"fh_admin_{match_id}"
                                )
                            with c4:
                                new_fa = st.number_input(
                                    f"Score {m['away']}",
                                    min_value=0,
                                    max_value=50,
                                    step=1,
                                    value=default_fa,
                                    key=f"fa_admin_{match_id}"
                                )
                    
                            with c5:
                                if st.button("💾 Sauvegarder le score", key=f"save_score_{match_id}"):
                                    set_final_score(match_id, new_fh, new_fa)
                                    st.success("Score final mis à jour ✅ (le classement sera recalculé)")
                                    st.rerun()
                    
                                if st.button("🗑️ Supprimer ce match", key=f"delete_match_{match_id}"):
                                    delete_match_and_predictions(match_id)
                                    st.warning("Match supprimé avec ses pronostics associés 🗑️")
                                    st.rerun()

            # ONGLET 3 : PRONOS DES JOUEURS
            with tab_pronos_joueurs:
                st.markdown("### ✍️ Saisir ou corriger les pronostics d'un joueur")

                joueurs = df_users.sort_values("display_name").reset_index(drop=True)
                if joueurs.empty:
                    st.info("Aucun joueur.")
                else:
                    choix_joueur = st.selectbox(
                        "Choisir un joueur :",
                        joueurs["display_name"].tolist(),
                        key="pronos_joueurs_select",
                    )
                    cible = joueurs[joueurs["display_name"] == choix_joueur].iloc[0]
                    target_user_id = cible["user_id"]

                    st.caption(f"Modification des pronostics pour : **{choix_joueur}**")

                    if df_matches.empty:
                        st.info("Aucun match pour le moment.")
                    else:
                        try:
                            df_matches_gm = df_matches.copy()
                            df_matches_gm["_ko"] = pd.to_datetime(
                                df_matches_gm["kickoff_paris"], format="%Y-%m-%d %H:%M"
                            )
                        except Exception:
                            df_matches_gm = df_matches.copy()
                            df_matches_gm["_ko"] = pd.NaT

                        df_matches_gm = df_matches_gm.sort_values(
                            "_ko", ascending=False, na_position="last"
                        ).drop(columns=["_ko"])

                        preds_cible = df_preds[df_preds["user_id"] == target_user_id]

                        for _, m in df_matches_gm.iterrows():
                            st.markdown("---")
                            c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                            with c1:
                                st.markdown(f"**{m['home']} vs {m['away']}**")
                                st.caption(f"Coup d’envoi : {format_kickoff(m['kickoff_paris'])}")
                                if "category" in m.index and pd.notna(m["category"]):
                                    st.caption(f"Catégorie : {m['category']}")

                            existing = preds_cible[preds_cible["match_id"] == m["match_id"]]
                            ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                            pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                            res_known = (pd.notna(m["final_home"]) and pd.notna(m["final_away"]))

                            with c2:
                                ph = st.number_input(
                                    f"{m['home']} (dom.)",
                                    0, 20, ph0, 1,
                                    key=f"gm_ph_{target_user_id}_{m['match_id']}",
                                    disabled=False,
                                )
                            with c3:
                                pa = st.number_input(
                                    f"{m['away']} (ext.)",
                                    0, 20, pa0, 1,
                                    key=f"gm_pa_{target_user_id}_{m['match_id']}",
                                    disabled=False,
                                )

                            with c4:
                                if st.button("💾 Enregistrer", key=f"gm_save_{target_user_id}_{m['match_id']}"):
                                    upsert_prediction(target_user_id, m["match_id"], ph, pa)
                                    st.success(f"Pronostic enregistré pour {choix_joueur} ✅")

                            if res_known:
                                st.caption(f"Score final : {int(m['final_home'])} - {int(m['final_away'])}")

            # ONGLET 4 : POINTS BONUS/MALUS
            with tab_points:
                st.markdown("### 🎯 Ajouter des points manuellement (bonus / malus)")

                df_users_points, _, _ = load_df()
                df_manual_points = load_manual_points()

                if df_users_points.empty:
                    st.info("Aucun joueur.")
                else:
                    # Choix du joueur
                    choix_joueur_pts = st.selectbox(
                        "Choisir un joueur :",
                        df_users_points["display_name"].sort_values().tolist(),
                        key="points_joueur_select",
                    )
                    cible_pts = df_users_points[df_users_points["display_name"] == choix_joueur_pts].iloc[0]
                    target_user_id_pts = cible_pts["user_id"]

                    # Raison existante ou nouvelle (comme les catégories)
                    existing_reasons = []
                    if not df_manual_points.empty:
                        existing_reasons = sorted(
                            [
                                str(r).strip()
                                for r in df_manual_points["reason"].dropna().unique()
                                if str(r).strip() != ""
                            ]
                        )

                    if existing_reasons:
                        options_reasons = ["(Nouvelle raison)"] + existing_reasons
                    else:
                        options_reasons = ["(Nouvelle raison)"]

                    reason_choice = st.selectbox(
                        "Raison :",
                        options_reasons,
                        key="points_reason_select",
                    )

                    if reason_choice == "(Nouvelle raison)":
                        reason_input = st.text_input(
                            "Saisir une nouvelle raison",
                            placeholder="Ex : Bonus fair-play, Retard, Pari spécial..."
                        )
                    else:
                        reason_input = reason_choice

                    pts_value = st.number_input(
                        "Points à ajouter (positif = bonus, négatif = malus)",
                        min_value=-100,
                        max_value=100,
                        step=1,
                        value=1,
                    )

                    if st.button("💾 Ajouter ces points", key="add_manual_points"):
                        try:
                            add_manual_points(target_user_id_pts, int(pts_value), reason_input)
                            signe = "+" if pts_value > 0 else ""
                            st.success(f"{signe}{pts_value} points ajoutés à {choix_joueur_pts} (raison : {reason_input}).")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

                    st.markdown("---")
                    st.markdown("#### Historique des points manuels (7 derniers jours)")

                    if df_manual_points.empty:
                        st.caption("Aucune entrée de points manuels pour le moment.")
                    else:
                        df_manual_points = df_manual_points.merge(df_users_points, on="user_id", how="left")

                        df_manual_points["_created"] = pd.to_datetime(df_manual_points["created_at"], errors="coerce")
                        today_ma = now_maroc().date()
                        min_date = today_ma - timedelta(days=7)
                        df_manual_points = df_manual_points[
                            df_manual_points["_created"].dt.date >= min_date
                        ]

                        if df_manual_points.empty:
                            st.caption("Aucune entrée sur les 7 derniers jours.")
                        else:
                            df_display = df_manual_points.sort_values("_created", ascending=False)
                            df_display["Date"] = df_display["_created"].dt.strftime("%d/%m/%Y %H:%M")
                            df_display = df_display.rename(
                                columns={
                                    "display_name": "Joueur",
                                    "points": "Points",
                                    "reason": "Raison",
                                }
                            )
                            st.dataframe(
                                df_display[["Date", "Joueur", "Points", "Raison"]],
                                use_container_width=True,
                                hide_index=True,
                            )

# -----------------------------
# TAB ADMIN (gestion joueurs & rôles)
# -----------------------------
if tab_admin is not None:
    with tab_admin:
        st.subheader("Administration des joueurs")

        if not admin_authenticated:
            st.info("Réservé à l'administrateur. Active le mode admin dans la barre latérale.")
        else:
            st.success("Mode admin actif")

            # Ajout joueur
            st.markdown("### Ajouter un nouveau joueur")

            with st.form("add_player"):
                new_player_name = st.text_input("Nom du joueur (ex: Karim)")
                submit_player = st.form_submit_button("Créer le joueur")

            if submit_player:
                try:
                    pin = create_player(new_player_name)
                    st.success(f"Joueur créé — Nom : {new_player_name} — Code : {pin}")
                    st.info("Note ce code et communique-le au joueur.")
                except ValueError as e:
                    st.error(str(e))

            st.markdown("---")

            # Liste joueurs + rôle + modification de code
            st.markdown("### Joueurs existants, rôles et codes")

            df_users4, _, _ = load_df()
            if df_users4.empty:
                st.write("Aucun joueur créé pour l'instant.")
            else:
                if "is_game_master" not in df_users4.columns:
                    df_users4["is_game_master"] = 0

                for _, row in df_users4.sort_values("display_name").iterrows():
                    user_id_row = row["user_id"]
                    name = row["display_name"]
                    pin = row["pin_code"]
                    is_gm = bool(row["is_game_master"])

                    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 3, 3])

                    with c1:
                        st.markdown(f"**{name}**")
                    with c2:
                        st.caption(f"Code actuel : `{pin}`")
                    with c3:
                        st.write("Maître de jeu :", "✅" if is_gm else "❌")
                    with c4:
                        if is_gm:
                            if st.button("Retirer maître de jeu", key=f"unset_gm_{user_id_row}"):
                                set_game_master(user_id_row, False)
                                st.success(f"{name} n'est plus maître de jeu.")
                                st.rerun()
                        else:
                            if st.button("Nommer maître de jeu", key=f"set_gm_{user_id_row}"):
                                set_game_master(user_id_row, True)
                                st.success(f"{name} est maintenant maître de jeu.")
                                st.rerun()
                    with c5:
                        new_pin_val = st.text_input(
                            "Nouveau code (4 chiffres)",
                            max_chars=4,
                            key=f"new_pin_{user_id_row}",
                            label_visibility="collapsed",
                            placeholder="1234",
                        )
                        if st.button("Mettre à jour le code", key=f"update_pin_{user_id_row}"):
                            try:
                                update_pin_code(user_id_row, new_pin_val)
                                st.success(f"Code mis à jour pour {name}.")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))
