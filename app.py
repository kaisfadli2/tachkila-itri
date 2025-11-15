            # RÉSULTATS
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

                        # 👉 Expander dépliable comme pour les matchs joueurs
                        exp_label = f"{m['home']} vs {m['away']} — {format_kickoff(m['kickoff_paris'])}"
                        with st.expander(exp_label):
                            c1, c2 = st.columns([3, 2])

                            with c1:
                                st.markdown(f"**{m['home']} vs {m['away']}**")
                                st.caption(f"Coup d’envoi : {format_kickoff(m['kickoff_paris'])}")
                                if "category" in m.index and pd.notna(m["category"]):
                                    st.caption(f"Catégorie : {m['category']}")

                            with c2:
                                if pd.notna(m["final_home"]) and pd.notna(m["final_away"]):
                                    st.markdown(
                                        f"**Score final actuel :** {int(m['final_home'])} - {int(m['final_away'])}"
                                    )
                                else:
                                    st.markdown("**Score final actuel :** non saisi")

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

                            edit_open = st.checkbox(
                                "🕒 Modifier la date / l'heure du match",
                                key=f"toggle_edit_{match_id}",
                            )

                            if edit_open:
                                try:
                                    ko_dt = datetime.strptime(m["kickoff_paris"], "%Y-%m-%d %H:%M")
                                except Exception:
                                    ko_dt = datetime.now()

                                c_date, c_time, c_actions = st.columns([2, 2, 2])

                                with c_date:
                                    new_date = st.date_input(
                                        "📅 Nouvelle date",
                                        value=ko_dt.date(),
                                        key=f"date_edit_{match_id}",
                                    )

                                with c_time:
                                    st.markdown("⏰ Nouvelle heure")
                                    h_col2, sep_col2, m_col2 = st.columns([1, 0.3, 1])

                                    with h_col2:
                                        heure_str2 = st.selectbox(
                                            "",
                                            options=[f"{i:02d}" for i in range(24)],
                                            index=ko_dt.hour,
                                            key=f"heure_edit_h_{match_id}",
                                            label_visibility="collapsed",
                                        )
                                    with sep_col2:
                                        st.markdown("**:**")
                                    with m_col2:
                                        minute_str2 = st.selectbox(
                                            "",
                                            options=[f"{i:02d}" for i in range(60)],
                                            index=ko_dt.minute,
                                            key=f"minute_edit_m_{match_id}",
                                            label_visibility="collapsed",
                                        )

                                    new_time = datetime.strptime(f"{heure_str2}:{minute_str2}", "%H:%M").time()

                                with c_actions:
                                    if st.button("🕒 Mettre à jour", key=f"update_ko_{match_id}"):
                                        new_ko = datetime.combine(new_date, new_time)
                                        new_ko_str = new_ko.strftime("%Y-%m-%d %H:%M")
                                        update_match_kickoff(match_id, new_ko_str)
                                        st.success(f"Date/heure mises à jour : {format_kickoff(new_ko_str)} ✅")
                                        st.rerun()
