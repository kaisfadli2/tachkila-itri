# app_test.py
# =============================================================================
# Tachkila Mouchkila — VERSION TEST (Option 2)
# ✅ AUCUN IMPACT SUR SUPABASE / PROD
# - Si DATABASE_URL n'est PAS dans st.secrets -> SQLite local (local_test.db)
# - Horaires : saisie maître de jeu = heure FRANCE (Paris)
# - Affichage joueur : FR + MA
# - Verrouillage : heure FRANCE
# =============================================================================

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import base64
from pathlib import Path
import random
from typing import Optional, Tuple

from sqlalchemy import (
    create_engine, MetaData, Table, Column, String, Integer, ForeignKey,
    select, insert, update, UniqueConstraint, delete, func
)
from sqlalchemy.engine import Engine


# =============================================================================
# SESSION STATE INIT
# =============================================================================
if "player" not in st.session_state:
    st.session_state["player"] = None
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False
if "collapse_sidebar" not in st.session_state:
    st.session_state["collapse_sidebar"] = False
if "confirm_reset_competition" not in st.session_state:
    st.session_state["confirm_reset_competition"] = False


# =============================================================================
# PAGE CONFIG
# =============================================================================
sidebar_state = "expanded" if not st.session_state["collapse_sidebar"] else "collapsed"

st.set_page_config(
    page_title="Tachkila Mouchkila (TEST)",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state=sidebar_state,
)


# =============================================================================
# THEME CSS (Football + Ramadan vibes light)
# =============================================================================
FOOTBALL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Montserrat', sans-serif !important; }
html, body { background:#020617 !important; }
.stApp {
    background:
        radial-gradient(circle at 0% 0%, rgba(245,158,11,0.10) 0, #020617 45%, #01030a 100%),
        radial-gradient(circle at 80% 15%, rgba(34,197,94,0.12) 0, transparent 45%),
        linear-gradient(135deg, #020617, #020617 40%, #0f3c2b 120%) !important;
}

/* étoiles */
.stApp:after{
  content:"";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.18;
  background-image: radial-gradient(rgba(255,255,255,0.75) 1px, transparent 1.5px);
  background-size: 34px 34px;
  mask-image: radial-gradient(circle at 50% 15%, black 0, transparent 65%);
}
.block-container, [data-testid="stSidebar"]{ position: relative; z-index: 1; }

.block-container { max-width: 1180px; padding-top: 1.4rem !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020920) !important;
    border-right: 1px solid rgba(245, 158, 11, 0.22);
}
[data-testid="stSidebar"] * { color: #e5e7eb !important; }

/* Inputs sidebar */
[data-testid="stSidebar"] div[data-baseweb="input"],
[data-testid="stSidebar"] div[data-baseweb="select"]{
    border: 2px solid rgba(255,255,255,0.9) !important;
    border-radius: 10px !important;
    background-color: #020617 !important;
}
[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within,
[data-testid="stSidebar"] div[data-baseweb="select"]:focus-within{
    border-color: #22c55e !important;
    box-shadow: 0 0 0 1px #22c55e !important;
}

/* Header overlay grid */
.tm-pitch-overlay {
    position:absolute;
    top:0; left:0; right:0;
    height:180px;
    pointer-events:none;
    opacity:0.35;
    background-image:
        linear-gradient(to right, rgba(120,150,150,0.13) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(120,150,150,0.13) 1px, transparent 1px);
    background-size:36px 36px;
    mask-image: linear-gradient(to bottom, black, transparent);
}

/* Ramadan card */
.rm-card {
  position: relative;
  overflow: hidden;
  border-radius: 26px;
  border: 1px solid rgba(245, 158, 11, 0.35);
  box-shadow: 0 18px 40px rgba(0,0,0,0.65);
  background:
    radial-gradient(circle at 0% 0%, rgba(245,158,11,0.18) 0, rgba(2,6,23,0.92) 60%),
    linear-gradient(135deg, rgba(2,6,23,0.92), rgba(15,23,42,0.92));
  padding: 1.15rem 1.15rem;
  margin-bottom: 1.15rem;
}
.rm-card:before{
  content:"";
  position:absolute;
  left:-20%;
  top:-55%;
  width:140%;
  height:120%;
  transform: rotate(8deg);
  background: linear-gradient(90deg, transparent, rgba(245,158,11,0.16), transparent);
  filter: blur(2px);
  opacity: .8;
}
.rm-badge {
  display: inline-flex;
  align-items: center;
  gap: .55rem;
  padding: .38rem .85rem;
  border-radius: 999px;
  border: 1px solid rgba(245,158,11,0.45);
  background: rgba(245,158,11,0.10);
  color: #fde68a;
  font-weight: 700;
  font-size: .78rem;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.rm-moon {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display:flex;
  align-items:center;
  justify-content:center;
  background: rgba(245,158,11,0.14);
  border: 1px solid rgba(245,158,11,0.35);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05);
}
.rm-title{
  margin-top:.55rem;
  font-size: 2.15rem;
  font-weight: 900;
  letter-spacing: .01em;
  color: #f8fafc;
}
.rm-sub{
  margin-top:.2rem;
  color: rgba(226,232,240,0.80);
  font-size: 1rem;
}
.rm-timehint{
  margin-top:.45rem;
  font-size:.85rem;
  color: rgba(226,232,240,0.75);
}
.rm-timehint b{ color:#fde68a; }

.rm-logo {
  width: 140px;
  height: 140px;
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(245, 158, 11, 0.50);
  box-shadow: 0 12px 30px rgba(0,0,0,0.75);
  background: rgba(2,6,23,0.75);
}
.rm-logo img { width:100%; height:100%; object-fit: cover; }

/* Tabs */
div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 0.6rem;
    padding-bottom: 0.25rem;
    border-bottom: none !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 0.45rem 1.3rem !important;
    background: #020617 !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-bottom: 1px solid rgba(255,255,255,0.16) !important;
    color: #9ca3af !important;
    font-weight: 600 !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(34,197,94,0.18) !important;
    border-color: #22c55e !important;
    border-bottom: 1px solid #22c55e !important;
    color: #e5e7eb !important;
}

/* Subtabs */
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 1.2rem !important;
    border-bottom: 1px solid rgba(148,163,184,0.28) !important;
    padding-bottom: 0 !important;
    margin-top: 0.35rem !important;
}
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stTabs"] button[data-baseweb="tab"] {
    border-radius: 0 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.2rem 0 0.35rem 0 !important;
    color: #9ca3af !important;
    font-weight: 500 !important;
}
div[data-testid="stTabs"] [role="tabpanel"] div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: transparent !important;
    color: #22c55e !important;
    border: none !important;
    border-bottom: 2px solid #22c55e !important;
    font-weight: 600 !important;
}

.streamlit-expanderHeader {
    background:#0f172a !important;
    border-radius:18px !important;
    padding:.75rem 1rem !important;
    border:1px solid rgba(255,255,255,0.12);
}
[data-testid="stDataFrame"] {
    border-radius:16px !important;
    overflow:hidden !important;
    border:1px solid rgba(255,255,255,0.15) !important;
    box-shadow:0 18px 28px rgba(0,0,0,0.6) !important;
}
</style>
"""
st.markdown(FOOTBALL_CSS, unsafe_allow_html=True)


# =============================================================================
# SECRETS / CONFIG (TEST SAFE)
# =============================================================================
# OPTION 2: si DATABASE_URL n'existe pas, on utilise SQLite local -> aucun impact prod
DATABASE_URL = st.secrets.get("DATABASE_URL", "sqlite:///local_test.db")

ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "test1234")
ADMIN_PLAYER_NAME = st.secrets.get("ADMIN_PLAYER_NAME", "Admin")
ADMIN_PLAYER_PIN = st.secrets.get("ADMIN_PLAYER_PIN", "0000")

IS_LOCAL_SQLITE = DATABASE_URL.startswith("sqlite")


# =============================================================================
# TIMEZONES — saisie/verrouillage FR, affichage FR+MA
# =============================================================================
TZ_PARIS = ZoneInfo("Europe/Paris")
TZ_MA = ZoneInfo("Africa/Casablanca")

DAY_ABBR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
MONTH_ABBR = ["jan", "fév", "mar", "avr", "mai", "jun", "jul", "aoû", "sep", "oct", "nov", "déc"]


def now_paris() -> datetime:
    return datetime.now(TZ_PARIS)


def now_maroc() -> datetime:
    return datetime.now(TZ_MA)


def format_dt_fr(dt: datetime) -> str:
    jour = DAY_ABBR[dt.weekday()]
    mois = MONTH_ABBR[dt.month - 1]
    return f"{jour} {dt.day:02d} {mois} {dt.year} — {dt:%H:%M}"


def parse_kickoff_paris(kickoff_paris_str: str) -> datetime:
    return datetime.strptime(kickoff_paris_str, "%Y-%m-%d %H:%M").replace(tzinfo=TZ_PARIS)


def format_kickoff_dual(kickoff_paris_str: str) -> str:
    try:
        dt_paris = parse_kickoff_paris(kickoff_paris_str)
        dt_ma = dt_paris.astimezone(TZ_MA)
        return f"{format_dt_fr(dt_paris)} (FR) • {dt_ma:%H:%M} (MA)"
    except Exception:
        return kickoff_paris_str


def is_editable_until_kickoff_paris(kickoff_paris_str: str) -> bool:
    try:
        return now_paris() < parse_kickoff_paris(kickoff_paris_str)
    except Exception:
        return False


def edited_after_kickoff(timestamp_utc_str: str, kickoff_paris_str: str) -> bool:
    try:
        ts_utc = datetime.strptime(timestamp_utc_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        ts_paris = ts_utc.astimezone(TZ_PARIS)
        ko_paris = parse_kickoff_paris(kickoff_paris_str)
        return ts_paris > ko_paris
    except Exception:
        return False


def result_sign(h, a) -> int:
    h, a = int(h), int(a)
    return (h > a) - (h < a)


def compute_points(ph, pa, fh, fa, pts_result=2, pts_exact=4) -> int:
    try:
        if fh is None or fa is None:
            return 0
        ph, pa, fh, fa = int(ph), int(pa), int(fh), int(fa)
        if ph == fh and pa == fa:
            return int(pts_exact)
        return int(pts_result) if result_sign(ph, pa) == result_sign(fh, fa) else 0
    except Exception:
        return 0


# =============================================================================
# DB INIT
# =============================================================================
@st.cache_resource
def get_engine() -> Engine:
    return create_engine(
        DATABASE_URL,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


engine: Engine = get_engine()
meta = MetaData()

users = Table(
    "users", meta,
    Column("user_id", String, primary_key=True),
    Column("display_name", String, unique=True, nullable=False),
    Column("pin_code", String, nullable=False),
    Column("is_game_master", Integer, nullable=False, server_default="0"),
    Column("login_token", String, nullable=True),
)

matches = Table(
    "matches", meta,
    Column("match_id", String, primary_key=True),
    Column("home", String, nullable=False),
    Column("away", String, nullable=False),
    Column("kickoff_paris", String, nullable=False),  # heure France "YYYY-MM-DD HH:MM"
    Column("final_home", Integer, nullable=True),
    Column("final_away", Integer, nullable=True),
    Column("category", String, nullable=True),
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
    Column("points_result", Integer, nullable=False, server_default="2"),
    Column("points_exact", Integer, nullable=False, server_default="4"),
)

manual_points = Table(
    "manual_points",
    meta,
    Column("adjustment_id", String, primary_key=True),
    Column("user_id", String, ForeignKey("users.user_id"), nullable=False),
    Column("points", Integer, nullable=False),
    Column("reason", String, nullable=False),
    Column("created_at", String, nullable=False),  # UTC "YYYY-MM-DD HH:MM:SS"
)

meta.create_all(engine)


def init_first_user() -> None:
    with engine.begin() as conn:
        count = conn.execute(select(func.count()).select_from(users)).scalar()
        if count == 0:
            conn.execute(
                insert(users).values(
                    user_id=str(uuid.uuid4()),
                    display_name=ADMIN_PLAYER_NAME,
                    pin_code=ADMIN_PLAYER_PIN,
                    is_game_master=1,
                )
            )


init_first_user()


# =============================================================================
# AUTO LOGIN VIA TOKEN
# =============================================================================
def auto_login_from_token() -> None:
    if st.session_state.get("player") is not None:
        return

    params = st.query_params
    token_val = params.get("token")
    if not token_val:
        return

    token = token_val[0] if isinstance(token_val, list) else token_val

    with engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.login_token == token)).mappings().first()

    if row:
        st.session_state["player"] = dict(row)
        st.session_state["collapse_sidebar"] = True


auto_login_from_token()


# =============================================================================
# ASSETS
# =============================================================================
@st.cache_resource
def get_logo_base64() -> str:
    # fallback: si image absente, on évite crash
    img_path = Path("ballon_maroc.jpg")
    if not img_path.exists():
        return ""
    data = img_path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


# =============================================================================
# LOADERS (cached)
# =============================================================================
@st.cache_data(ttl=60)
def load_users() -> pd.DataFrame:
    with engine.begin() as conn:
        return pd.read_sql(select(users), conn)


@st.cache_data(ttl=60)
def load_matches() -> pd.DataFrame:
    with engine.begin() as conn:
        return pd.read_sql(select(matches), conn)


@st.cache_data(ttl=60)
def load_predictions() -> pd.DataFrame:
    with engine.begin() as conn:
        return pd.read_sql(select(predictions), conn)


def load_df() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_users(), load_matches(), load_predictions()


@st.cache_data(ttl=60)
def load_manual_points() -> pd.DataFrame:
    with engine.begin() as conn:
        try:
            return pd.read_sql(select(manual_points), conn)
        except Exception:
            return pd.DataFrame(columns=["adjustment_id", "user_id", "points", "reason", "created_at"])


@st.cache_data(ttl=60)
def load_category_rules() -> pd.DataFrame:
    with engine.begin() as conn:
        try:
            return pd.read_sql(select(category_rules), conn)
        except Exception:
            return pd.DataFrame(columns=["category", "points_result", "points_exact"])


@st.cache_data(ttl=60)
def load_catalog() -> pd.DataFrame:
    try:
        return pd.read_csv("teams_catalog.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["name"])


# =============================================================================
# DB ACTIONS
# =============================================================================
def clear_cache() -> None:
    st.cache_data.clear()


def authenticate_player(display_name: str, pin_code: str):
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
    return row


def upsert_prediction(user_id: str, match_id: str, ph: int, pa: int) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with engine.begin() as conn:
        row = conn.execute(
            select(predictions).where(
                predictions.c.user_id == user_id,
                predictions.c.match_id == match_id,
            )
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
    clear_cache()


def add_match(home: str, away: str, kickoff_paris: str, category: Optional[str] = None) -> None:
    _ = datetime.strptime(kickoff_paris, "%Y-%m-%d %H:%M")  # validation

    category_clean = category.strip() if isinstance(category, str) else None
    if category_clean == "":
        category_clean = None

    with engine.begin() as conn:
        conn.execute(
            insert(matches).values(
                match_id=str(uuid.uuid4()),
                home=home.strip(),
                away=away.strip(),
                kickoff_paris=kickoff_paris.strip(),
                final_home=None,
                final_away=None,
                category=category_clean,
            )
        )
    clear_cache()


def set_final_score(match_id: str, fh: int, fa: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            update(matches)
            .where(matches.c.match_id == match_id)
            .values(final_home=int(fh), final_away=int(fa))
        )
    clear_cache()


def update_match_kickoff(match_id: str, kickoff_paris: str) -> None:
    _ = datetime.strptime(kickoff_paris, "%Y-%m-%d %H:%M")
    with engine.begin() as conn:
        conn.execute(
            update(matches)
            .where(matches.c.match_id == match_id)
            .values(kickoff_paris=kickoff_paris)
        )
    clear_cache()


def delete_match_and_predictions(match_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(delete(predictions).where(predictions.c.match_id == match_id))
        conn.execute(delete(matches).where(matches.c.match_id == match_id))
    clear_cache()


def create_player(display_name: str) -> str:
    display_name = display_name.strip()
    if not display_name:
        raise ValueError("Le nom du joueur est obligatoire.")

    pin = f"{random.randint(1000, 9999)}"
    with engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.display_name == display_name)).mappings().first()
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
    clear_cache()
    return pin


def update_pin_code(user_id: str, new_pin: str) -> None:
    new_pin = new_pin.strip()
    if not new_pin or len(new_pin) != 4 or not new_pin.isdigit():
        raise ValueError("Le code doit contenir exactement 4 chiffres (0-9).")

    with engine.begin() as conn:
        conn.execute(
            update(users)
            .where(users.c.user_id == user_id)
            .values(pin_code=new_pin)
        )
    clear_cache()


def set_game_master(user_id: str, is_gm: bool) -> None:
    with engine.begin() as conn:
        conn.execute(
            update(users)
            .where(users.c.user_id == user_id)
            .values(is_game_master=1 if is_gm else 0)
        )
    clear_cache()


def delete_player_and_data(user_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(delete(predictions).where(predictions.c.user_id == user_id))
        conn.execute(delete(manual_points).where(manual_points.c.user_id == user_id))
        conn.execute(delete(users).where(users.c.user_id == user_id))
    clear_cache()


def reset_competition() -> None:
    with engine.begin() as conn:
        conn.execute(delete(predictions))
        conn.execute(delete(manual_points))
        conn.execute(delete(matches))
    clear_cache()


def add_manual_points(user_id: str, points: int, reason: str) -> None:
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
    clear_cache()


def upsert_category_rule(category: str, pts_result: int, pts_exact: int) -> None:
    category = category.strip()
    if not category:
        return

    with engine.begin() as conn:
        row = conn.execute(select(category_rules).where(category_rules.c.category == category)).mappings().first()
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
    clear_cache()


def ensure_team_in_catalog(team_name: str) -> None:
    team_name = team_name.strip()
    if not team_name:
        return

    try:
        df = pd.read_csv("teams_catalog.csv")
    except FileNotFoundError:
        df = pd.DataFrame(columns=["name"])

    if "name" not in df.columns:
        df["name"] = []

    if team_name in df["name"].astype(str).tolist():
        return

    df = pd.concat([df, pd.DataFrame({"name": [team_name]})], ignore_index=True)
    df = df.drop_duplicates(subset=["name"]).sort_values("name")
    df.to_csv("teams_catalog.csv", index=False)
    clear_cache()


# =============================================================================
# EXPORT TABLES (classement + détail)
# =============================================================================
@st.cache_data(ttl=20)
def compute_export_tables() -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_users, df_matches, df_preds = load_df()
    df_manual = load_manual_points()
    df_rules = load_category_rules()

    # CLASSEMENT
    if df_preds.empty and df_manual.empty:
        leaderboard_export = pd.DataFrame(columns=["Joueur", "Points"])
    else:
        merged = (
            df_preds.merge(df_matches, on="match_id", how="left")
                   .merge(df_users, on="user_id", how="left")
        )
        merged = merged[merged["display_name"] != "Admin"]

        def points_for_row(r):
            pts_result = 2
            pts_exact = 4
            cat = r.get("category", None)
            if pd.notna(cat):
                rule = df_rules[df_rules["category"] == cat]
                if not rule.empty:
                    pts_result = int(rule.iloc[0]["points_result"])
                    pts_exact = int(rule.iloc[0]["points_exact"])
            return compute_points(r["ph"], r["pa"], r["final_home"], r["final_away"], pts_result, pts_exact)

        merged["points"] = merged.apply(points_for_row, axis=1) if not merged.empty else []

        leaderboard_pronos = (
            merged.groupby(["user_id", "display_name"], dropna=False)["points"].sum().reset_index()
        ) if not merged.empty else pd.DataFrame(columns=["user_id", "display_name", "points"])

        if not df_manual.empty:
            df_manual_users = df_manual.merge(df_users, on="user_id", how="left")
            df_manual_users = df_manual_users[df_manual_users["display_name"] != "Admin"]
            manual_agg = (
                df_manual_users.groupby(["user_id", "display_name"], dropna=False)["points"].sum().reset_index()
            )
        else:
            manual_agg = pd.DataFrame(columns=["user_id", "display_name", "points"])

        leaderboard = pd.concat([leaderboard_pronos, manual_agg], ignore_index=True)
        if not leaderboard.empty:
            leaderboard = (
                leaderboard.groupby(["user_id", "display_name"], dropna=False)["points"].sum().reset_index()
                .sort_values(["points", "display_name"], ascending=[False, True])
            )
            leaderboard_export = leaderboard.rename(columns={"display_name": "Joueur", "points": "Points"})[
                ["Joueur", "Points"]
            ].reset_index(drop=True)
        else:
            leaderboard_export = pd.DataFrame(columns=["Joueur", "Points"])

    # DETAIL
    if df_preds.empty and df_manual.empty:
        detail_export = pd.DataFrame(
            columns=["Joueur", "Match / Raison", "Prono D", "Prono E", "Final D", "Final E", "Pts", "⚠️", "Coup d’envoi"]
        )
        return leaderboard_export, detail_export

    merged2 = (
        df_preds.merge(df_matches, on="match_id", how="left")
               .merge(df_users, on="user_id", how="left")
    )
    merged2 = merged2[merged2["display_name"] != "Admin"]

    def points_for_row2(r):
        pts_result = 2
        pts_exact = 4
        cat = r.get("category", None)
        if pd.notna(cat):
            rule = df_rules[df_rules["category"] == cat]
            if not rule.empty:
                pts_result = int(rule.iloc[0]["points_result"])
                pts_exact = int(rule.iloc[0]["points_exact"])
        return compute_points(r["ph"], r["pa"], r["final_home"], r["final_away"], pts_result, pts_exact)

    merged2["points"] = merged2.apply(points_for_row2, axis=1) if not merged2.empty else []
    detail = merged2.copy()
    if "manual_reason" not in detail.columns:
        detail["manual_reason"] = ""

    # Ajout points manuels au détail
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
                "kickoff_paris": df_manual_all["created_at"].str.slice(0, 16),
                "timestamp_utc": df_manual_all["created_at"],
                "manual_reason": df_manual_all["reason"],
                "home": [None] * len(df_manual_all),
                "away": [None] * len(df_manual_all),
                "match_id": [None] * len(df_manual_all),
                "category": [None] * len(df_manual_all),
            })
            common_cols = list(set(detail.columns).union(manual_detail.columns))
            detail = pd.concat(
                [detail.reindex(columns=common_cols), manual_detail.reindex(columns=common_cols)],
                ignore_index=True,
            )

    # filtre 7 jours (Paris)
    def to_paris_dt(s: str):
        try:
            return parse_kickoff_paris(s)
        except Exception:
            return pd.NaT

    detail["_ko_paris"] = detail["kickoff_paris"].astype(str).apply(to_paris_dt)
    today_p = now_paris().date()
    min_date = today_p - timedelta(days=7)
    detail = detail[pd.notna(detail["_ko_paris"]) & (detail["_ko_paris"].dt.date >= min_date)]
    if detail.empty:
        detail_export = pd.DataFrame(
            columns=["Joueur", "Match / Raison", "Prono D", "Prono E", "Final D", "Final E", "Pts", "⚠️", "Coup d’envoi"]
        )
        return leaderboard_export, detail_export

    def make_label(row):
        mr = row.get("manual_reason", "")
        if isinstance(mr, str) and mr.strip():
            return f"Points manuels — {mr}"
        return f"{row['home']} vs {row['away']} — {format_kickoff_dual(row['kickoff_paris'])}"

    detail["match_label"] = detail.apply(make_label, axis=1)

    show = detail[[
        "display_name", "match_label",
        "ph", "pa",
        "final_home", "final_away",
        "points",
        "kickoff_paris",
        "timestamp_utc",
        "_ko_paris",
    ]].copy().sort_values("_ko_paris", ascending=False)

    show["⚠️"] = show.apply(
        lambda r: (
            "⚠️" if isinstance(r.get("timestamp_utc", None), str)
            and isinstance(r.get("kickoff_paris", None), str)
            and edited_after_kickoff(r["timestamp_utc"], r["kickoff_paris"])
            else ""
        ),
        axis=1,
    )

    show = show.rename(columns={
        "display_name": "Joueur",
        "match_label": "Match / Raison",
        "ph": "Prono D",
        "pa": "Prono E",
        "final_home": "Final D",
        "final_away": "Final E",
        "points": "Pts",
        "kickoff_paris": "Coup d’envoi",
    })

    show["Coup d’envoi"] = show["Coup d’envoi"].apply(format_kickoff_dual)
    show = show.drop(columns=["timestamp_utc", "_ko_paris"])

    cols_order = ["Match / Raison", "Joueur", "Pts", "Prono D", "Prono E", "Final D", "Final E", "⚠️", "Coup d’envoi"]
    detail_export = show[cols_order].reset_index(drop=True)
    return leaderboard_export, detail_export


# =============================================================================
# HEADER
# =============================================================================
st.markdown('<div class="tm-pitch-overlay"></div>', unsafe_allow_html=True)

logo_b64 = get_logo_base64()
current_player = st.session_state.get("player", None)
current_name = current_player["display_name"] if current_player else "Invité"

st.markdown(
    f"""
    <div class="rm-card">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:1.1rem;">
            <div style="min-width: 0;">
                <div class="rm-badge">
                    <span class="rm-moon">🌙</span>
                    <span>{current_name}</span>
                    <span style="opacity:.65;">•</span>
                    <span>Ramadan Kareem</span>
                </div>

                <div class="rm-title">Tachkila Mouchkila</div>
                <div class="rm-sub">ITRI — pronostics football</div>

                <div class="rm-timehint">
                    Horaires affichés : <b>France (Paris)</b> + <b>Maroc</b> • Verrouillage : <b>heure France</b>
                </div>

                {"<div class='rm-timehint'><b>🧪 MODE TEST</b> — Base SQLite locale (aucun impact sur Supabase)</div>" if IS_LOCAL_SQLITE else ""}
            </div>

            <div class="rm-logo">
                {f'<img src="data:image/jpeg;base64,{logo_b64}" alt="Logo">' if logo_b64 else '<div style="display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:#fde68a;font-weight:800;">LOGO</div>'}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =============================================================================
# SIDEBAR — LOGIN + ADMIN
# =============================================================================
with st.sidebar:
    st.header("Connexion joueur")

    if st.session_state["player"] is None:
        name_input = st.text_input("Nom du joueur")
        pin_input = st.text_input("Code à 4 chiffres", type="password", max_chars=4)

        if st.button("Se connecter"):
            user = authenticate_player(name_input, pin_input)
            if user is None:
                st.error("Nom ou code incorrect (demande à l'admin de vérifier ton code).")
            else:
                token = str(uuid.uuid4())
                with engine.begin() as conn:
                    conn.execute(
                        update(users)
                        .where(users.c.user_id == user["user_id"])
                        .values(login_token=token)
                    )

                st.session_state["player"] = dict(user)
                st.session_state["collapse_sidebar"] = True
                st.query_params.clear()
                st.query_params["token"] = token
                st.rerun()

    else:
        player_sidebar = st.session_state["player"]
        st.success(f"Connecté : {player_sidebar['display_name']}")
        if st.button("Changer de joueur"):
            st.session_state["player"] = None
            st.query_params.clear()
            st.rerun()

    st.markdown("---")
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


# =============================================================================
# CONTEXTE UTILISATEUR
# =============================================================================
player = st.session_state["player"]
admin_authenticated = st.session_state["admin_authenticated"]

if player is None:
    st.info("Commence par te connecter avec ton nom + code à 4 chiffres dans la colonne de gauche.")
    st.stop()

df_users, df_matches, df_preds = load_df()
user_id = player["user_id"]
display_name = player["display_name"]

row_me = df_users[df_users["user_id"] == user_id]
is_game_master = bool(row_me.iloc[0]["is_game_master"]) if (not row_me.empty and "is_game_master" in row_me.columns) else False
can_manage_matches = admin_authenticated or is_game_master

catalog = load_catalog()


# =============================================================================
# TABS
# =============================================================================
tab_labels = ["Mes matchs", "Classement"]
tab_ids = ["pronos", "classement"]

if can_manage_matches:
    tab_labels.append("Maître de jeu")
    tab_ids.append("maitre")

if admin_authenticated:
    tab_labels.append("Admin")
    tab_ids.append("admin")

tabs = st.tabs(tab_labels)
tab_dict = dict(zip(tab_ids, tabs))

tab_pronos = tab_dict["pronos"]
tab_classement = tab_dict["classement"]
tab_maitre = tab_dict.get("maitre")
tab_admin = tab_dict.get("admin")


# =============================================================================
# TAB PRONOS
# =============================================================================
with tab_pronos:
    if df_matches.empty:
        st.info("Aucun match pour le moment.")
    else:
        st.info(
            "📢 **Information pronostics**\n\n"
            "- Vous pouvez saisir vos pronostics dans l’onglet **A venir**.\n"
            "- Ils restent modifiables **jusqu’au début du match (heure France)**.\n"
            "- Une fois le match commencé, les pronostics sont **verrouillés**.\n"
            "- Horaires affichés : **France (Paris) + Maroc**.\n"
        )

        df_matches_work = df_matches.copy()
        df_matches_work["_ko_paris"] = df_matches_work["kickoff_paris"].astype(str).apply(
            lambda s: parse_kickoff_paris(s) if pd.notna(s) else pd.NaT
        )

        df_matches_work["res_known"] = (
            df_matches_work["final_home"].notna() & df_matches_work["final_away"].notna()
        )

        now_p = now_paris()
        df_matches_work["has_started"] = df_matches_work["_ko_paris"].apply(
            lambda x: (pd.notna(x) and x <= now_p)
        )

        df_a_venir = df_matches_work[(~df_matches_work["res_known"]) & (~df_matches_work["has_started"])].sort_values(
            "_ko_paris", ascending=True, na_position="last"
        )
        df_en_cours = df_matches_work[(~df_matches_work["res_known"]) & (df_matches_work["has_started"])].sort_values(
            "_ko_paris", ascending=True, na_position="last"
        )
        df_termines = df_matches_work[df_matches_work["res_known"]].sort_values(
            "_ko_paris", ascending=False, na_position="last"
        )

        my_preds = df_preds[df_preds["user_id"] == user_id]

        tab_avenir, tab_cours, tab_done = st.tabs(["A venir", "En cours", "Terminés"])

        # -------- A VENIR --------
        with tab_avenir:
            if df_a_venir.empty:
                st.caption("Aucun match à venir pour le moment.")
            else:
                for _, m in df_a_venir.iterrows():
                    exp_label = f"{m['home']} vs {m['away']} — {format_kickoff_dual(m['kickoff_paris'])}"
                    with st.expander(exp_label):
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                        with c1:
                            st.markdown(f"**{m['home']} vs {m['away']}**")
                            if "category" in m.index and pd.notna(m["category"]):
                                st.caption(f"Catégorie : {m['category']}")
                            st.caption(f"Coup d’envoi : {format_kickoff_dual(m['kickoff_paris'])}")

                        existing = my_preds[my_preds["match_id"] == m["match_id"]]
                        has_prono = not existing.empty
                        ph0 = int(existing.iloc[0]["ph"]) if has_prono else 0
                        pa0 = int(existing.iloc[0]["pa"]) if has_prono else 0

                        editable = is_editable_until_kickoff_paris(m["kickoff_paris"])

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
                                    st.rerun()
                            else:
                                st.info("⛔ Verrouillé (heure France)")

                        st.markdown("---")
                        if has_prono:
                            st.success(f"✅ Pronostic actuel : {ph0} - {pa0}")
                        else:
                            st.warning("⚠️ Prono pas encore fait pour ce match.")

        # -------- EN COURS --------
        with tab_cours:
            if df_en_cours.empty:
                st.caption("Aucun match en cours pour le moment.")
            else:
                for _, m in df_en_cours.iterrows():
                    exp_label = f"{m['home']} vs {m['away']} — {format_kickoff_dual(m['kickoff_paris'])}"
                    with st.expander(exp_label):
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                        with c1:
                            st.markdown(f"**{m['home']} vs {m['away']}**")
                            if "category" in m.index and pd.notna(m["category"]):
                                st.caption(f"Catégorie : {m['category']}")
                            st.caption(f"Coup d’envoi : {format_kickoff_dual(m['kickoff_paris'])}")

                        existing = my_preds[my_preds["match_id"] == m["match_id"]]
                        ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                        pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                        with c2:
                            st.number_input(f"{m['home']} (dom.)", 0, 20, ph0, 1, key=f"ph_live_{m['match_id']}", disabled=True)
                        with c3:
                            st.number_input(f"{m['away']} (ext.)", 0, 20, pa0, 1, key=f"pa_live_{m['match_id']}", disabled=True)
                        with c4:
                            st.info("⛔ Verrouillé (match commencé — heure France)")

        # -------- TERMINES --------
        with tab_done:
            if df_termines.empty:
                st.caption("Aucun match terminé pour le moment.")
            else:
                for _, m in df_termines.iterrows():
                    exp_label = f"{m['home']} vs {m['away']} — {format_kickoff_dual(m['kickoff_paris'])}"
                    with st.expander(exp_label):
                        c1, c2, c3, c4 = st.columns([3, 3, 3, 3])

                        with c1:
                            st.markdown(f"**{m['home']} vs {m['away']}**")
                            if "category" in m.index and pd.notna(m["category"]):
                                st.caption(f"Catégorie : {m['category']}")
                            st.caption(f"Coup d’envoi : {format_kickoff_dual(m['kickoff_paris'])}")
                            st.caption(f"Score final : {int(m['final_home'])} - {int(m['final_away'])}")

                        existing = my_preds[my_preds["match_id"] == m["match_id"]]
                        ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                        pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                        with c2:
                            st.number_input(f"Prono {m['home']} (dom.)", 0, 20, ph0, 1, key=f"ph_done_{m['match_id']}", disabled=True)
                        with c3:
                            st.number_input(f"Prono {m['away']} (ext.)", 0, 20, pa0, 1, key=f"pa_done_{m['match_id']}", disabled=True)

                        with c4:
                            if not existing.empty:
                                fh, fa = int(m["final_home"]), int(m["final_away"])
                                if ph0 == fh and pa0 == fa:
                                    st.success("🎉 Score exact !")
                                elif result_sign(ph0, pa0) == result_sign(fh, fa):
                                    st.info("👍 Bon résultat !")
                                else:
                                    st.warning("😌 Dommage")
                            else:
                                st.info("ℹ️ Aucun prono saisi pour ce match.")


# =============================================================================
# TAB CLASSEMENT
# =============================================================================
with tab_classement:
    df_manual = load_manual_points()

    if df_preds.empty and df_manual.empty:
        st.info("Pas encore de pronostics ou de points manuels.")
    else:
        merged = (
            df_preds.merge(df_matches, on="match_id", how="left")
                   .merge(df_users, on="user_id", how="left")
        )
        merged = merged[merged["display_name"] != "Admin"]
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
            return compute_points(r["ph"], r["pa"], r["final_home"], r["final_away"], pts_result, pts_exact)

        merged["points"] = merged.apply(points_for_row, axis=1) if not merged.empty else []

        leaderboard_pronos = (
            merged.groupby(["user_id", "display_name"], dropna=False)["points"].sum().reset_index()
        ) if not merged.empty else pd.DataFrame(columns=["user_id", "display_name", "points"])

        if not df_manual.empty:
            df_manual_users = df_manual.merge(df_users, on="user_id", how="left")
            df_manual_users = df_manual_users[df_manual_users["display_name"] != "Admin"]
            manual_agg = (
                df_manual_users.groupby(["user_id", "display_name"], dropna=False)["points"].sum().reset_index()
            )
        else:
            manual_agg = pd.DataFrame(columns=["user_id", "display_name", "points"])

        leaderboard = pd.concat([leaderboard_pronos, manual_agg], ignore_index=True)
        if not leaderboard.empty:
            leaderboard = (
                leaderboard.groupby(["user_id", "display_name"], dropna=False)["points"].sum().reset_index()
                .sort_values(["points", "display_name"], ascending=[False, True])
            )

        if leaderboard.empty:
            st.info("Les scores finaux ne sont pas encore saisis et aucun point manuel n'a été ajouté.")
        else:
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
                            border:1px solid {color};
                            border-radius:14px;
                            padding:8px 10px;
                            text-align:center;
                        ">
                            <div style="font-size:26px; line-height:1;">{medal}</div>
                            <div style="font-size:14px;font-weight:700;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                                {pseudo}
                            </div>
                            <div style="font-size:12px;margin-top:2px;">{pts} pts</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("### Classement complet")
            lb = leaderboard.reset_index(drop=True)
            for idx, row in lb.iterrows():
                rank = idx + 1
                pseudo = row["display_name"]
                pts = row["points"]
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;margin-bottom:6px;">
                        <div style="
                            width:32px;height:32px;border-radius:50%;
                            background:#0f4c81;color:white;display:flex;
                            align-items:center;justify-content:center;font-weight:700;
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

            with st.expander("Détail par match et points manuels"):
                detail = merged.copy()
                if "manual_reason" not in detail.columns:
                    detail["manual_reason"] = ""

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
                            "kickoff_paris": df_manual_all["created_at"].str.slice(0, 16),
                            "timestamp_utc": df_manual_all["created_at"],
                            "manual_reason": df_manual_all["reason"],
                            "home": [None] * len(df_manual_all),
                            "away": [None] * len(df_manual_all),
                            "match_id": [None] * len(df_manual_all),
                            "category": [None] * len(df_manual_all),
                        })
                        common_cols = list(set(detail.columns).union(manual_detail.columns))
                        detail = pd.concat(
                            [detail.reindex(columns=common_cols), manual_detail.reindex(columns=common_cols)],
                            ignore_index=True,
                        )

                def to_paris_dt(s: str):
                    try:
                        return parse_kickoff_paris(s)
                    except Exception:
                        return pd.NaT

                detail["_ko_paris"] = detail["kickoff_paris"].astype(str).apply(to_paris_dt)
                today_p = now_paris().date()
                min_date = today_p - timedelta(days=7)
                detail = detail[pd.notna(detail["_ko_paris"]) & (detail["_ko_paris"].dt.date >= min_date)]

                if detail.empty:
                    st.caption("Aucun match ou point manuel sur les 7 derniers jours.")
                else:
                    def make_label2(row):
                        mr = row.get("manual_reason", "")
                        if isinstance(mr, str) and mr.strip():
                            return f"Points manuels — {mr}"
                        return f"{row['home']} vs {row['away']} — {format_kickoff_dual(row['kickoff_paris'])}"

                    detail["match_label"] = detail.apply(make_label2, axis=1)

                    filtre = st.radio("Filtrer par :", ["Aucun", "Match", "Joueur"], horizontal=True)

                    if filtre == "Match":
                        df_match_opts = (
                            detail.groupby("match_label")["_ko_paris"].max().reset_index()
                            .sort_values("_ko_paris", ascending=False)
                        )
                        match_sel = st.selectbox("Choisir un match / une raison", df_match_opts["match_label"].tolist())
                        detail = detail[detail["match_label"] == match_sel]
                    elif filtre == "Joueur":
                        joueur_sel = st.selectbox("Choisir un joueur", sorted(detail["display_name"].unique()))
                        detail = detail[detail["display_name"] == joueur_sel]

                    show = detail[[
                        "display_name", "match_label",
                        "ph", "pa",
                        "final_home", "final_away",
                        "points",
                        "kickoff_paris",
                        "timestamp_utc",
                        "_ko_paris",
                    ]].copy().sort_values("_ko_paris", ascending=False)

                    show["⚠️"] = show.apply(
                        lambda r: (
                            "⚠️" if isinstance(r["timestamp_utc"], str)
                            and isinstance(r["kickoff_paris"], str)
                            and edited_after_kickoff(r["timestamp_utc"], r["kickoff_paris"])
                            else ""
                        ),
                        axis=1,
                    )

                    show = show.rename(columns={
                        "display_name": "Joueur",
                        "match_label": "Match / Raison",
                        "ph": "Prono D",
                        "pa": "Prono E",
                        "final_home": "Final D",
                        "final_away": "Final E",
                        "points": "Pts",
                        "kickoff_paris": "Coup d’envoi",
                    })

                    show["Coup d’envoi"] = show["Coup d’envoi"].apply(format_kickoff_dual)
                    show = show.drop(columns=["timestamp_utc", "_ko_paris"])

                    cols_order = ["Match / Raison", "Joueur", "Pts", "Prono D", "Prono E", "Final D", "Final E", "⚠️", "Coup d’envoi"]
                    st.dataframe(show[cols_order], use_container_width=True, hide_index=True)


# =============================================================================
# TAB MAÎTRE DE JEU
# =============================================================================
if tab_maitre is not None:
    with tab_maitre:
        if not can_manage_matches:
            st.info("Réservé à l'administrateur ou aux maîtres de jeu.")
        else:
            if admin_authenticated and is_game_master:
                st.success("Mode admin + maître de jeu actifs.")
            elif admin_authenticated:
                st.success("Mode admin actif.")
            elif is_game_master:
                st.success("Mode maître de jeu actif (gestion des matches et des pronos des joueurs).")

            tab_ajout, tab_resultats, tab_pronos_joueurs, tab_points, tab_export = st.tabs(
                ["Ajouter un match", "Résultats", "Pronos joueurs", "Points bonus/malus", "Export / sauvegarde"]
            )

            # -------- AJOUTER UN MATCH --------
            with tab_ajout:
                st.markdown("### ➕ Ajouter un match")
                st.caption("⏱️ Saisie **heure France (Paris)**. Verrouillage basé sur cette heure. Affichage joueurs FR+MA.")

                df_users_cat, df_matches_cat, _ = load_df()
                existing_categories: list[str] = []
                if "category" in df_matches_cat.columns:
                    existing_categories = sorted(
                        [str(c).strip() for c in df_matches_cat["category"].dropna().unique() if str(c).strip()]
                    )

                options = ["(Aucune catégorie)"] + existing_categories + ["➕ Nouvelle catégorie..."]
                cat_choice = st.selectbox("Catégorie du match (optionnel)", options)

                new_cat = ""
                pts_result = None
                pts_exact = None

                if cat_choice == "➕ Nouvelle catégorie...":
                    new_cat = st.text_input("Nouvelle catégorie", placeholder="Ex : Poules, Quart de finale, Match amical...")
                    st.markdown("#### Règle de points pour cette catégorie")
                    col_res, col_exact = st.columns(2)
                    with col_res:
                        pts_result = st.number_input("Points pour bon résultat", min_value=0, max_value=20, value=2, step=1)
                    with col_exact:
                        pts_exact = st.number_input("Points pour score exact", min_value=0, max_value=50, value=4, step=1)

                with st.form("form_add_match"):
                    c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                    team_options = sorted(catalog["name"].astype(str).dropna().unique().tolist()) if not catalog.empty else []

                    with c1:
                        st.markdown("**Équipe domicile**")
                        home_suggest = st.selectbox("Choisir dans la liste", options=team_options, key="home_team_select") if team_options else ""
                        if not team_options:
                            st.caption("Aucune équipe enregistrée, saisissez un nom ci-dessous.")
                        home_manual = st.text_input("Ou saisir une nouvelle équipe domicile", key="home_manual", placeholder="Nom de l'équipe domicile").strip()
                        home = home_manual or home_suggest

                    with c2:
                        st.markdown("**Équipe extérieur**")
                        away_suggest = st.selectbox("Choisir dans la liste", options=team_options, key="away_team_select") if team_options else ""
                        if not team_options:
                            st.caption("Aucune équipe enregistrée, saisissez un nom ci-dessous.")
                        away_manual = st.text_input("Ou saisir une nouvelle équipe extérieur", key="away_manual", placeholder="Nom de l'équipe extérieur").strip()
                        away = away_manual or away_suggest

                    with c3:
                        date_match = st.date_input("📅 Date du match (France)")
                        st.markdown("⏰ Heure du match (France / Paris)")
                        h_col, sep_col, m_col = st.columns([1, 0.3, 1])

                        with h_col:
                            heure_str = st.selectbox("", options=[f"{i:02d}" for i in range(24)], key="heure_match_h", label_visibility="collapsed")
                        with sep_col:
                            st.markdown("**:**")
                        with m_col:
                            minute_str = st.selectbox("", options=[f"{i:02d}" for i in range(60)], key="heure_match_m", label_visibility="collapsed")

                        heure_match = datetime.strptime(f"{heure_str}:{minute_str}", "%H:%M").time()
                        kickoff_dt = datetime.combine(date_match, heure_match)
                        kickoff = kickoff_dt.strftime("%Y-%m-%d %H:%M")  # stocké comme heure Paris

                    with c4:
                        submit = st.form_submit_button("Ajouter")

                    if submit:
                        if not home or not away:
                            st.warning("Sélectionne ou saisis les deux équipes.")
                        elif home == away:
                            st.warning("L'équipe domicile et l'équipe extérieur doivent être différentes.")
                        else:
                            ensure_team_in_catalog(home)
                            ensure_team_in_catalog(away)

                            if new_cat.strip():
                                category = new_cat.strip()
                                if pts_result is not None and pts_exact is not None:
                                    upsert_category_rule(category, pts_result, pts_exact)
                            elif cat_choice not in ["(Aucune catégorie)", "➕ Nouvelle catégorie..."]:
                                category = cat_choice
                            else:
                                category = None

                            add_match(home, away, kickoff, category)
                            msg = f"Match ajouté ✅ ({home} vs {away} — {format_kickoff_dual(kickoff)})"
                            if category:
                                msg += f" — catégorie : {category}"
                            st.success(msg)
                            st.rerun()

            # -------- RÉSULTATS --------
            with tab_resultats:
                st.markdown("### 📝 Saisie et modification des résultats (7 derniers jours)")
                df_users3, df_matches3, _ = load_df()

                if df_matches3.empty:
                    st.info("Aucun match pour le moment.")
                else:
                    df_matches3["_ko_paris"] = df_matches3["kickoff_paris"].astype(str).apply(
                        lambda s: parse_kickoff_paris(s) if pd.notna(s) else pd.NaT
                    )
                    today_p = now_paris().date()
                    min_date = today_p - timedelta(days=7)
                    df_matches3 = df_matches3[pd.notna(df_matches3["_ko_paris"]) & (df_matches3["_ko_paris"].dt.date >= min_date)]
                    if df_matches3.empty:
                        st.info("Aucun match récent (moins de 7 jours).")
                    else:
                        df_matches3 = df_matches3.sort_values("_ko_paris", ascending=False, na_position="last")

                        for _, m in df_matches3.iterrows():
                            match_id = m["match_id"]
                            exp_label = f"{m['home']} vs {m['away']} — {format_kickoff_dual(m['kickoff_paris'])}"
                            with st.expander(exp_label):
                                c1, c2 = st.columns([3, 2])

                                with c1:
                                    st.markdown(f"**{m['home']} vs {m['away']}**")
                                    if "category" in m.index and pd.notna(m["category"]):
                                        st.caption(f"Catégorie : {m['category']}")
                                    st.caption(f"Coup d’envoi : {format_kickoff_dual(m['kickoff_paris'])}")

                                with c2:
                                    if pd.notna(m["final_home"]) and pd.notna(m["final_away"]):
                                        st.markdown(f"**Score final actuel :** {int(m['final_home'])} - {int(m['final_away'])}")
                                    else:
                                        st.markdown("**Score final actuel :** non saisi")

                                c3, c4, c5 = st.columns([2, 2, 2])
                                default_fh = int(m["final_home"]) if pd.notna(m["final_home"]) else 0
                                default_fa = int(m["final_away"]) if pd.notna(m["final_away"]) else 0

                                with c3:
                                    new_fh = st.number_input(f"Score {m['home']}", min_value=0, max_value=50, step=1, value=default_fh, key=f"fh_admin_{match_id}")
                                with c4:
                                    new_fa = st.number_input(f"Score {m['away']}", min_value=0, max_value=50, step=1, value=default_fa, key=f"fa_admin_{match_id}")

                                with c5:
                                    if st.button("💾 Sauvegarder le score", key=f"save_score_{match_id}"):
                                        set_final_score(match_id, new_fh, new_fa)
                                        st.success("Score final mis à jour ✅")
                                        st.rerun()

                                    if st.button("🗑️ Supprimer ce match", key=f"delete_match_{match_id}"):
                                        delete_match_and_predictions(match_id)
                                        st.warning("Match supprimé 🗑️")
                                        st.rerun()

                                st.markdown("")
                                edit_open = st.checkbox("🕒 Modifier la date / l'heure (France)", key=f"toggle_edit_{match_id}")
                                if edit_open:
                                    try:
                                        ko_dt = datetime.strptime(m["kickoff_paris"], "%Y-%m-%d %H:%M")
                                    except Exception:
                                        ko_dt = now_paris().replace(tzinfo=None)

                                    c_date, c_time, c_actions = st.columns([2, 2, 2])

                                    with c_date:
                                        new_date = st.date_input("📅 Nouvelle date (France)", value=ko_dt.date(), key=f"date_edit_{match_id}")

                                    with c_time:
                                        st.markdown("⏰ Nouvelle heure (France)")
                                        h_col2, sep_col2, m_col2 = st.columns([1, 0.3, 1])
                                        with h_col2:
                                            heure_str2 = st.selectbox("", options=[f"{i:02d}" for i in range(24)], index=int(ko_dt.hour),
                                                                      key=f"heure_edit_h_{match_id}", label_visibility="collapsed")
                                        with sep_col2:
                                            st.markdown("**:**")
                                        with m_col2:
                                            minute_str2 = st.selectbox("", options=[f"{i:02d}" for i in range(60)], index=int(ko_dt.minute),
                                                                       key=f"minute_edit_m_{match_id}", label_visibility="collapsed")
                                        new_time = datetime.strptime(f"{heure_str2}:{minute_str2}", "%H:%M").time()

                                    with c_actions:
                                        if st.button("🕒 Mettre à jour", key=f"update_ko_{match_id}"):
                                            new_ko = datetime.combine(new_date, new_time)
                                            new_ko_str = new_ko.strftime("%Y-%m-%d %H:%M")
                                            update_match_kickoff(match_id, new_ko_str)
                                            st.success(f"Date/heure mises à jour : {format_kickoff_dual(new_ko_str)} ✅")
                                            st.rerun()

            # -------- PRONOS DES JOUEURS --------
            with tab_pronos_joueurs:
                st.markdown("### ✍️ Saisir ou corriger les pronostics d'un joueur (7 derniers jours)")
                joueurs = df_users.sort_values("display_name").reset_index(drop=True)

                if joueurs.empty:
                    st.info("Aucun joueur.")
                else:
                    choix_joueur = st.selectbox("Choisir un joueur :", joueurs["display_name"].tolist())
                    cible = joueurs[joueurs["display_name"] == choix_joueur].iloc[0]
                    target_user_id = cible["user_id"]

                    st.caption(f"Modification des pronostics pour : **{choix_joueur}**")

                    if df_matches.empty:
                        st.info("Aucun match pour le moment.")
                    else:
                        df_matches_gm = df_matches.copy()
                        df_matches_gm["_ko_paris"] = df_matches_gm["kickoff_paris"].astype(str).apply(
                            lambda s: parse_kickoff_paris(s) if pd.notna(s) else pd.NaT
                        )
                        today_p = now_paris().date()
                        min_date = today_p - timedelta(days=7)
                        df_matches_gm = df_matches_gm[pd.notna(df_matches_gm["_ko_paris"]) & (df_matches_gm["_ko_paris"].dt.date >= min_date)]
                        if df_matches_gm.empty:
                            st.info("Aucun match récent (moins de 7 jours).")
                        else:
                            df_matches_gm = df_matches_gm.sort_values("_ko_paris", ascending=False, na_position="last")
                            preds_cible = df_preds[df_preds["user_id"] == target_user_id]

                            for _, m in df_matches_gm.iterrows():
                                match_id = m["match_id"]
                                exp_label = f"{m['home']} vs {m['away']} — {format_kickoff_dual(m['kickoff_paris'])}"

                                with st.expander(exp_label):
                                    c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

                                    with c1:
                                        st.markdown(f"**{m['home']} vs {m['away']}**")
                                        if "category" in m.index and pd.notna(m["category"]):
                                            st.caption(f"Catégorie : {m['category']}")
                                        st.caption(f"Coup d’envoi : {format_kickoff_dual(m['kickoff_paris'])}")

                                    existing = preds_cible[preds_cible["match_id"] == match_id]
                                    ph0 = int(existing.iloc[0]["ph"]) if not existing.empty else 0
                                    pa0 = int(existing.iloc[0]["pa"]) if not existing.empty else 0

                                    with c2:
                                        ph = st.number_input(f"{m['home']} (dom.)", 0, 20, ph0, 1, key=f"gm_ph_{target_user_id}_{match_id}")
                                    with c3:
                                        pa = st.number_input(f"{m['away']} (ext.)", 0, 20, pa0, 1, key=f"gm_pa_{target_user_id}_{match_id}")

                                    with c4:
                                        if st.button("💾 Enregistrer", key=f"gm_save_{target_user_id}_{match_id}"):
                                            upsert_prediction(target_user_id, match_id, ph, pa)
                                            st.success("Pronostic enregistré ✅")
                                            st.rerun()

                                    if pd.notna(m["final_home"]) and pd.notna(m["final_away"]):
                                        st.caption(f"Score final : {int(m['final_home'])} - {int(m['final_away'])}")

            # -------- POINTS BONUS/MALUS --------
            with tab_points:
                st.markdown("### 🎯 Ajouter des points manuellement (bonus / malus)")
                df_users_points, _, _ = load_df()
                df_manual_points_df = load_manual_points()

                if df_users_points.empty:
                    st.info("Aucun joueur.")
                else:
                    choix_joueur_pts = st.selectbox(
                        "Choisir un joueur :",
                        df_users_points["display_name"].sort_values().tolist(),
                        key="points_joueur_select",
                    )
                    cible_pts = df_users_points[df_users_points["display_name"] == choix_joueur_pts].iloc[0]
                    target_user_id_pts = cible_pts["user_id"]

                    existing_reasons = []
                    if not df_manual_points_df.empty:
                        existing_reasons = sorted(
                            [str(r).strip() for r in df_manual_points_df["reason"].dropna().unique() if str(r).strip()]
                        )

                    options_reasons = ["(Nouvelle raison)"] + existing_reasons if existing_reasons else ["(Nouvelle raison)"]
                    reason_choice = st.selectbox("Raison :", options_reasons, key="points_reason_select")
                    reason_input = (
                        st.text_input("Saisir une nouvelle raison", placeholder="Ex : Bonus fair-play, Retard, Pari spécial...")
                        if reason_choice == "(Nouvelle raison)"
                        else reason_choice
                    )

                    pts_value = st.number_input(
                        "Points à ajouter (positif = bonus, négatif = malus)",
                        min_value=-100, max_value=100, step=1, value=1,
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

                    if df_manual_points_df.empty:
                        st.caption("Aucune entrée de points manuels pour le moment.")
                    else:
                        df_manual_points_df = df_manual_points_df.merge(df_users_points, on="user_id", how="left")
                        df_manual_points_df["_created"] = pd.to_datetime(df_manual_points_df["created_at"], errors="coerce", utc=True)

                        now_utc = datetime.now(timezone.utc)
                        min_dt_utc = now_utc - timedelta(days=7)
                        df_manual_points_df = df_manual_points_df[
                            pd.notna(df_manual_points_df["_created"]) & (df_manual_points_df["_created"] >= min_dt_utc)
                        ]

                        if df_manual_points_df.empty:
                            st.caption("Aucune entrée sur les 7 derniers jours.")
                        else:
                            df_display = df_manual_points_df.sort_values("_created", ascending=False).copy()
                            df_display["Date"] = df_display["_created"].dt.tz_convert(TZ_PARIS).dt.strftime("%d/%m/%Y %H:%M") + " (FR)"
                            df_display = df_display.rename(columns={"display_name": "Joueur", "points": "Points", "reason": "Raison"})
                            st.dataframe(df_display[["Date", "Joueur", "Points", "Raison"]], use_container_width=True, hide_index=True)

            # -------- EXPORT / SAUVEGARDE --------
            with tab_export:
                st.markdown("### 💾 Export du classement et des détails")
                st.write(
                    "Tu peux télécharger :\n"
                    "- le **classement complet**\n"
                    "- le **détail par match** (7 derniers jours)\n"
                )

                leaderboard_export, detail_export = compute_export_tables()

                if leaderboard_export.empty and detail_export.empty:
                    st.warning("Il n'y a pas encore de données à exporter.")
                else:
                    c1, c2 = st.columns(2)

                    with c1:
                        st.markdown("#### Classement (aperçu)")
                        if leaderboard_export.empty:
                            st.caption("Aucun classement disponible.")
                        else:
                            st.dataframe(leaderboard_export, use_container_width=True, hide_index=True)
                            csv_lb = leaderboard_export.to_csv(index=False, sep=";").encode("utf-8")
                            st.download_button(
                                label="📥 Télécharger le classement (CSV)",
                                data=csv_lb,
                                file_name=f"classement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                            )

                    with c2:
                        st.markdown("#### Détail par match (aperçu)")
                        if detail_export.empty:
                            st.caption("Aucun détail sur les 7 derniers jours.")
                        else:
                            st.dataframe(detail_export, use_container_width=True, hide_index=True)
                            csv_detail = detail_export.to_csv(index=False, sep=";").encode("utf-8")
                            st.download_button(
                                label="📥 Télécharger les détails (CSV)",
                                data=csv_detail,
                                file_name=f"details_matchs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                            )


# =============================================================================
# TAB ADMIN
# =============================================================================
if tab_admin is not None:
    with tab_admin:
        st.subheader("Administration des joueurs")

        if not admin_authenticated:
            st.info("Réservé à l'administrateur. Active le mode admin dans la barre latérale.")
        else:
            st.success("Mode admin actif")

            st.markdown("### Ajouter un nouveau joueur")
            with st.form("add_player"):
                new_player_name = st.text_input("Nom du joueur (ex: Karim)")
                submit_player = st.form_submit_button("Créer le joueur")

            if submit_player:
                try:
                    pin = create_player(new_player_name)
                    st.success(f"Joueur créé — Nom : {new_player_name} — Code : {pin}")
                    st.info("Note ce code et communique-le au joueur.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

            st.markdown("---")
            st.markdown("### Joueurs existants, rôles et actions")

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
                    is_gm_row = bool(row["is_game_master"])

                    c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 3, 3, 3])

                    with c1:
                        st.markdown(f"**{name}**")

                    with c2:
                        st.caption(f"Code actuel : `{pin}`")

                    with c3:
                        st.write("Maître de jeu :", "✅" if is_gm_row else "❌")

                    with c4:
                        if is_gm_row:
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

                    with c6:
                        if name == ADMIN_PLAYER_NAME:
                            st.caption("🔒 Joueur admin")
                        else:
                            if st.button("🗑️ Supprimer le joueur", key=f"delete_player_{user_id_row}"):
                                delete_player_and_data(user_id_row)
                                st.warning(f"Joueur '{name}' supprimé avec ses données.")
                                st.rerun()

                    st.markdown("<hr style='border:0.5px solid rgba(255,255,255,0.18); margin:0.9rem 0;'>", unsafe_allow_html=True)

            # Zone dangereuse
            st.markdown("---")
            st.markdown("### ⚠️ Zone dangereuse : remise à zéro de la compétition")

            if st.button("🚨 Remettre tous les compteurs à zéro", key="btn_reset_all"):
                st.session_state["confirm_reset_competition"] = True

            if st.session_state["confirm_reset_competition"]:
                st.warning(
                    "Êtes-vous sûr de vouloir **supprimer tous les matchs, tous les pronostics et tous les points manuels** ? "
                    "Cette action est **irréversible**."
                )

                col_ok, col_cancel = st.columns(2)

                with col_ok:
                    if st.button("✅ Oui, tout remettre à zéro", key="btn_reset_all_confirm"):
                        reset_competition()
                        st.session_state["confirm_reset_competition"] = False
                        st.success("Tous les matchs, pronostics et points manuels ont été supprimés. Les joueurs sont conservés.")
                        st.rerun()

                with col_cancel:
                    if st.button("❌ Annuler", key="btn_reset_all_cancel"):
                        st.session_state["confirm_reset_competition"] = False
                        st.info("Remise à zéro annulée.")
