# app_test.py
# Streamlit pronos — VERSION SANS RAMADAN
# - Mode TEST = SQLite (si DATABASE_URL commence par sqlite)
# - Verrouillage basé sur l'heure FR (Europe/Paris)
# - Affichage double heure FR + MA
# - Code en 1 fichier, DB auto-créée

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Pronostics", page_icon="⚽", layout="wide")

DATABASE_URL = st.secrets.get("DATABASE_URL", "sqlite:///local_test.db")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "test1234")  # mot de passe admin (pour actions admin)
ADMIN_PLAYER_NAME = st.secrets.get("ADMIN_PLAYER_NAME", "Admin")
ADMIN_PLAYER_PIN = st.secrets.get("ADMIN_PLAYER_PIN", "0000")

IS_LOCAL_SQLITE = str(DATABASE_URL).startswith("sqlite")

TZ_PARIS = ZoneInfo("Europe/Paris")
TZ_MA = ZoneInfo("Africa/Casablanca")

DAY_ABBR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
MONTH_ABBR = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]


# ----------------------------
# TIME HELPERS
# ----------------------------
def now_paris() -> datetime:
    return datetime.now(TZ_PARIS)


def parse_kickoff_paris(paris_str: str) -> datetime:
    # paris_str: "YYYY-MM-DD HH:MM"
    return datetime.strptime(paris_str, "%Y-%m-%d %H:%M").replace(tzinfo=TZ_PARIS)


def format_kickoff_dual(paris_str: str) -> str:
    dt_paris = parse_kickoff_paris(paris_str)
    dt_ma = dt_paris.astimezone(TZ_MA)

    jour = DAY_ABBR[dt_paris.weekday()]
    mois = MONTH_ABBR[dt_paris.month - 1]

    return f"{jour} {dt_paris.day:02d} {mois} {dt_paris.year} — {dt_paris:%H:%M} (FR) • {dt_ma:%H:%M} (MA)"


# ----------------------------
# DB
# ----------------------------
def get_engine() -> Engine:
    if str(DATABASE_URL).startswith("sqlite"):
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    return create_engine(DATABASE_URL)


def init_db(engine: Engine) -> None:
    with engine.begin() as conn:
        # players
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                pin TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """))

        # matches
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                kickoff_paris TEXT NOT NULL,   -- "YYYY-MM-DD HH:MM"
                status TEXT NOT NULL DEFAULT 'scheduled', -- scheduled | finished
                score_home INTEGER,
                score_away INTEGER,
                created_at TEXT NOT NULL
            )
        """))

        # predictions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                match_id INTEGER NOT NULL,
                pred_home INTEGER NOT NULL,
                pred_away INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(player_id, match_id),
                FOREIGN KEY(player_id) REFERENCES players(id),
                FOREIGN KEY(match_id) REFERENCES matches(id)
            )
        """))

        # seed admin
        conn.execute(text("""
            INSERT OR IGNORE INTO players (name, pin, is_admin, created_at)
            VALUES (:name, :pin, 1, :created_at)
        """), {
            "name": ADMIN_PLAYER_NAME,
            "pin": ADMIN_PLAYER_PIN,
            "created_at": now_paris().isoformat()
        })


def db_read_df(engine: Engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def db_exec(engine: Engine, sql: str, params: dict | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


# ----------------------------
# AUTH
# ----------------------------
def login_block(engine: Engine) -> None:
    st.subheader("Connexion")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        name = st.text_input("Nom joueur", value=st.session_state.get("login_name", "")).strip()
    with col2:
        pin = st.text_input("PIN", type="password", value=st.session_state.get("login_pin", "")).strip()
    with col3:
        st.write("")
        st.write("")
        do_login = st.button("Se connecter", use_container_width=True)

    if do_login:
        if not name or not pin:
            st.error("Nom et PIN requis.")
            return

        # check user exists
        df = db_read_df(engine, "SELECT * FROM players WHERE name = :name", {"name": name})
        if df.empty:
            # create new player
            db_exec(engine, """
                INSERT INTO players (name, pin, is_admin, created_at)
                VALUES (:name, :pin, 0, :created_at)
            """, {"name": name, "pin": pin, "created_at": now_paris().isoformat()})
            df = db_read_df(engine, "SELECT * FROM players WHERE name = :name", {"name": name})

        # verify pin
        row = df.iloc[0].to_dict()
        if str(row["pin"]) != str(pin):
            st.error("PIN incorrect.")
            return

        st.session_state["user"] = {
            "id": int(row["id"]),
            "name": row["name"],
            "is_admin": bool(int(row["is_admin"])),
        }
        st.session_state["login_name"] = name
        st.session_state["login_pin"] = pin
        st.success(f"Connecté: {row['name']}")
        st.rerun()


def require_user() -> bool:
    return bool(st.session_state.get("user"))


def logout_button():
    if st.sidebar.button("Se déconnecter"):
        st.session_state.pop("user", None)
        st.rerun()


# ----------------------------
# BUSINESS LOGIC
# ----------------------------
def compute_points(actual_h: int, actual_a: int, pred_h: int, pred_a: int) -> int:
    # 3 points score exact, 1 point bon résultat (1N2), sinon 0
    if actual_h is None or actual_a is None:
        return 0
    if pred_h == actual_h and pred_a == actual_a:
        return 3
    actual_outcome = (actual_h > actual_a) - (actual_h < actual_a)  # 1,0,-1
    pred_outcome = (pred_h > pred_a) - (pred_h < pred_a)
    return 1 if actual_outcome == pred_outcome else 0


def get_matches(engine: Engine) -> pd.DataFrame:
    df = db_read_df(engine, """
        SELECT id, competition, home_team, away_team, kickoff_paris, status, score_home, score_away
        FROM matches
        ORDER BY kickoff_paris ASC
    """)
    if df.empty:
        return df

    # lock based on FR time
    now_p = now_paris()
    df["_ko_paris"] = df["kickoff_paris"].apply(lambda s: parse_kickoff_paris(str(s)))
    df["has_started"] = df["_ko_paris"].apply(lambda x: x <= now_p)
    df["kickoff_display"] = df["kickoff_paris"].apply(lambda s: format_kickoff_dual(str(s)))
    return df


def get_predictions(engine: Engine) -> pd.DataFrame:
    return db_read_df(engine, """
        SELECT
          p.id,
          p.player_id,
          pl.name AS player_name,
          p.match_id,
          p.pred_home,
          p.pred_away,
          p.created_at
        FROM predictions p
        JOIN players pl ON pl.id = p.player_id
        ORDER BY p.created_at DESC
    """)


# ----------------------------
# UI: PRONOS
# ----------------------------
def page_pronos(engine: Engine):
    st.header("⚽ Pronostics")

    matches = get_matches(engine)
    if matches.empty:
        st.info("Aucun match pour le moment. (Admin: ajoute des matchs dans l’onglet Admin)")
        return

    user = st.session_state["user"]
    preds = db_read_df(engine, """
        SELECT match_id, pred_home, pred_away
        FROM predictions
        WHERE player_id = :pid
    """, {"pid": user["id"]})
    pred_map = {int(r["match_id"]): (int(r["pred_home"]), int(r["pred_away"])) for _, r in preds.iterrows()} if not preds.empty else {}

    # filtres
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        show_all = st.checkbox("Voir tous les matchs", value=True)
    with c2:
        show_locked = st.checkbox("Inclure matchs verrouillés", value=True)

    df = matches.copy()
    if not show_all:
        df = df[df["status"] != "finished"]

    if not show_locked:
        df = df[~df["has_started"]]

    for _, m in df.iterrows():
        mid = int(m["id"])
        locked = bool(m["has_started"])
        finished = str(m["status"]) == "finished"

        with st.container(border=True):
            top = st.columns([3, 2, 2])
            with top[0]:
                comp = (m["competition"] or "").strip()
                if comp:
                    st.caption(comp)
                st.markdown(f"### {m['home_team']}  vs  {m['away_team']}")
                st.caption(m["kickoff_display"])
            with top[1]:
                if finished and pd.notna(m["score_home"]) and pd.notna(m["score_away"]):
                    st.metric("Score final", f"{int(m['score_home'])} - {int(m['score_away'])}")
                elif locked:
                    st.warning("Verrouillé (match commencé)")
                else:
                    st.success("Ouvert")
            with top[2]:
                existing = pred_map.get(mid)

                # inputs
                colh, cola, colb = st.columns([1, 1, 2])
                with colh:
                    ph = st.number_input(
                        f"{m['home_team']} (prono)",
                        min_value=0, max_value=30,
                        value=int(existing[0]) if existing else 0,
                        disabled=locked,
                        key=f"ph_{mid}"
                    )
                with cola:
                    pa = st.number_input(
                        f"{m['away_team']} (prono)",
                        min_value=0, max_value=30,
                        value=int(existing[1]) if existing else 0,
                        disabled=locked,
                        key=f"pa_{mid}"
                    )
                with colb:
                    st.write("")
                    btn = st.button(
                        "Enregistrer" if not existing else "Mettre à jour",
                        disabled=locked,
                        use_container_width=True,
                        key=f"save_{mid}"
                    )

                if btn and not locked:
                    if existing:
                        db_exec(engine, """
                            UPDATE predictions
                            SET pred_home = :ph, pred_away = :pa, created_at = :ts
                            WHERE player_id = :pid AND match_id = :mid
                        """, {"ph": int(ph), "pa": int(pa), "ts": now_paris().isoformat(), "pid": user["id"], "mid": mid})
                        st.success("Prono mis à jour ✅")
                    else:
                        db_exec(engine, """
                            INSERT INTO predictions (player_id, match_id, pred_home, pred_away, created_at)
                            VALUES (:pid, :mid, :ph, :pa, :ts)
                        """, {"pid": user["id"], "mid": mid, "ph": int(ph), "pa": int(pa), "ts": now_paris().isoformat()})
                        st.success("Prono enregistré ✅")
                    st.rerun()


# ----------------------------
# UI: CLASSEMENT
# ----------------------------
def page_classement(engine: Engine):
    st.header("🏆 Classement")

    matches = db_read_df(engine, """
        SELECT id, score_home, score_away, status
        FROM matches
    """)
    preds = get_predictions(engine)

    if matches.empty or preds.empty:
        st.info("Pas assez de données pour calculer un classement.")
        return

    match_map = {
        int(r["id"]): {
            "status": r["status"],
            "sh": (None if pd.isna(r["score_home"]) else int(r["score_home"])),
            "sa": (None if pd.isna(r["score_away"]) else int(r["score_away"])),
        }
        for _, r in matches.iterrows()
    }

    # calc points
    rows = []
    for _, p in preds.iterrows():
        mid = int(p["match_id"])
        info = match_map.get(mid, {})
        if info.get("status") != "finished":
            pts = 0
        else:
            pts = compute_points(info.get("sh"), info.get("sa"), int(p["pred_home"]), int(p["pred_away"]))
        rows.append({
            "Joueur": p["player_name"],
            "MatchId": mid,
            "Prono": f"{int(p['pred_home'])}-{int(p['pred_away'])}",
            "Points": pts
        })

    dfp = pd.DataFrame(rows)
    board = dfp.groupby("Joueur", as_index=False)["Points"].sum().sort_values("Points", ascending=False)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Total")
        st.dataframe(board, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Détail (points par prono)")
        st.dataframe(dfp.sort_values(["Points", "Joueur"], ascending=[False, True]), use_container_width=True, hide_index=True)


# ----------------------------
# UI: ADMIN
# ----------------------------
def page_admin(engine: Engine):
    st.header("🛠️ Admin")

    st.caption("Accès protégé par mot de passe admin (ADMIN_PASSWORD).")
    admin_ok = st.session_state.get("admin_ok", False)

    if not admin_ok:
        pw = st.text_input("Mot de passe admin", type="password")
        if st.button("Déverrouiller"):
            if pw == ADMIN_PASSWORD:
                st.session_state["admin_ok"] = True
                st.success("Admin déverrouillé ✅")
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
        return

    # --- add match
    st.subheader("Ajouter un match")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        competition = st.text_input("Compétition (optionnel)", value="")
    with col2:
        home_team = st.text_input("Équipe domicile", value="")
    with col3:
        away_team = st.text_input("Équipe extérieur", value="")
    with col4:
        kickoff_paris = st.text_input("Kickoff Paris (YYYY-MM-DD HH:MM)", value="")

    if st.button("Ajouter", use_container_width=True):
        try:
            _ = parse_kickoff_paris(kickoff_paris.strip())
        except Exception:
            st.error("Format kickoff invalide. Exemple: 2026-02-15 20:45")
            return
        if not home_team.strip() or not away_team.strip():
            st.error("Home/Away requis.")
            return

        db_exec(engine, """
            INSERT INTO matches (competition, home_team, away_team, kickoff_paris, status, created_at)
            VALUES (:c, :h, :a, :k, 'scheduled', :ts)
        """, {
            "c": competition.strip(),
            "h": home_team.strip(),
            "a": away_team.strip(),
            "k": kickoff_paris.strip(),
            "ts": now_paris().isoformat()
        })
        st.success("Match ajouté ✅")
        st.rerun()

    st.divider()

    # --- list matches + set result
    st.subheader("Gérer les matchs")
    matches = get_matches(engine)
    if matches.empty:
        st.info("Aucun match.")
        return

    for _, m in matches.iterrows():
        mid = int(m["id"])
        with st.container(border=True):
            st.markdown(f"### #{mid} — {m['home_team']} vs {m['away_team']}")
            st.caption(m["kickoff_display"])

            c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 2])
            with c1:
                status = st.selectbox(
                    "Statut",
                    options=["scheduled", "finished"],
                    index=0 if m["status"] == "scheduled" else 1,
                    key=f"st_{mid}"
                )
            with c2:
                sh = st.number_input(
                    "Score dom.",
                    min_value=0, max_value=30,
                    value=int(m["score_home"]) if pd.notna(m["score_home"]) else 0,
                    key=f"sh_{mid}"
                )
            with c3:
                sa = st.number_input(
                    "Score ext.",
                    min_value=0, max_value=30,
                    value=int(m["score_away"]) if pd.notna(m["score_away"]) else 0,
                    key=f"sa_{mid}"
                )
            with c4:
                st.write("")
                save = st.button("Enregistrer", key=f"save_m_{mid}", use_container_width=True)
            with c5:
                st.write("")
                delete = st.button("Supprimer", key=f"del_m_{mid}", use_container_width=True)

            if save:
                if status == "finished":
                    db_exec(engine, """
                        UPDATE matches
                        SET status = 'finished', score_home = :sh, score_away = :sa
                        WHERE id = :mid
                    """, {"sh": int(sh), "sa": int(sa), "mid": mid})
                else:
                    db_exec(engine, """
                        UPDATE matches
                        SET status = 'scheduled', score_home = NULL, score_away = NULL
                        WHERE id = :mid
                    """, {"mid": mid})
                st.success("Match mis à jour ✅")
                st.rerun()

            if delete:
                # cascade manually
                db_exec(engine, "DELETE FROM predictions WHERE match_id = :mid", {"mid": mid})
                db_exec(engine, "DELETE FROM matches WHERE id = :mid", {"mid": mid})
                st.success("Match supprimé ✅")
                st.rerun()


# ----------------------------
# MAIN
# ----------------------------
engine = get_engine()
init_db(engine)

if IS_LOCAL_SQLITE:
    st.warning("🧪 MODE TEST — Base SQLite locale (aucun impact sur Supabase)")

st.sidebar.title("Menu")

if not require_user():
    login_block(engine)
    st.stop()

user = st.session_state["user"]
st.sidebar.success(f"Connecté: {user['name']}")

logout_button()

page = st.sidebar.radio(
    "Aller à",
    ["Pronostics", "Classement", "Admin"],
    index=0
)

if page == "Pronostics":
    page_pronos(engine)
elif page == "Classement":
    page_classement(engine)
else:
    page_admin(engine)
