import streamlit as st
import json
from sympy import sympify, simplify
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="FEA Math Solver", page_icon="🏗️", layout="wide")

# --- 1. CHARGEMENT DE LA BASE DE DONNÉES (JSON) ---
# On place ceci en haut pour que tout le reste du code y ait accès
@st.cache_data
def load_daily_problem(date_actuelle):
    try:
        # Assure-toi que le fichier database.json est dans le même dossier
        with open('database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
            
        reference_date = date(2024, 1, 1) # Date de lancement (à modifier si besoin)
        delta_days = (date_actuelle - reference_date).days
        index = delta_days % len(db)
        return db[index]
        
    except Exception as e:
        # Énigme de secours si le fichier JSON est introuvable
        return {"enonce": r"\lim_{x \to 0} \frac{\ln(1+x)}{x}", "solution": "1", "theme": "Secours (JSON non trouvé)"}

# On détermine le jour actuel et on charge l'énigme correspondante
today = date.today()
enigme_du_jour = load_daily_problem(today)

solution_attendue = enigme_du_jour["solution"]
enonce_affiche = enigme_du_jour["enonce"]
theme_affiche = enigme_du_jour.get("theme", "Analyse")

# --- 2. INITIALISATION DES VARIABLES ---
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'final_time' not in st.session_state:
    st.session_state.final_time = 0
if 'last_solved_date' not in st.session_state:
    st.session_state.last_solved_date = None
if 'message_retour' not in st.session_state:
    st.session_state.message_retour = None

# --- 3. LOGIQUE MATHÉMATIQUE (LORENZ) ---
@st.cache_data
def generate_lorenz(rho, num_steps=3000, dt=0.01):
    xs, ys, zs = np.empty(num_steps), np.empty(num_steps), np.empty(num_steps)
    xs[0], ys[0], zs[0] = (0.0, 1.0, 1.05)
    sigma, beta = 10.0, 2.667
    for i in range(num_steps - 1):
        xs[i + 1] = xs[i] + (sigma * (ys[i] - xs[i])) * dt
        ys[i + 1] = ys[i] + (xs[i] * (rho - zs[i]) - ys[i]) * dt
        zs[i + 1] = zs[i] + (xs[i] * ys[i] - beta * zs[i]) * dt
    return xs, ys, zs

# === 4. L'ARME SECRÈTE : LA FONCTION CALLBACK ===
def valider_calcul():
    reponse_user = st.session_state.input_reponse
    pilote_user = st.session_state.input_pilote
    
    try:
        val_user = sympify(reponse_user.replace(',', '.'))
        # NOUVEAU : On utilise la solution dynamique provenant du JSON !
        val_sol = sympify(solution_attendue) 
        
        if simplify(val_user - val_sol) == 0:
            st.session_state.final_time = round(time.time() - st.session_state.start_time, 2)
            st.session_state.last_solved_date = today
            st.session_state.leaderboard.append({"Pilote": pilote_user, "Temps (s)": st.session_state.final_time})
            st.session_state.message_retour = "succes"
        else:
            st.session_state.message_retour = "erreur_faux"
    except:
        st.session_state.message_retour = "erreur_syntaxe"

# --- 5. INTERFACE UTILISATEUR ---
has_solved_today = (st.session_state.last_solved_date == today)

with st.sidebar:
    st.title("📟 Job Monitor")
    st.text_input("User ID / Pilote :", "Romain", disabled=has_solved_today, key="input_pilote")
    st.markdown("---")
    st.subheader("📊 Global Ranking (Today)")
    if st.session_state.leaderboard:
        df = pd.DataFrame(st.session_state.leaderboard).sort_values(by="Temps (s)").reset_index(drop=True)
        st.table(df)
    st.caption("Créé par **Le stagiaire Romain**")

st.title("🛠️ Analyse de Structure Mathématique")
col_viz, col_input = st.columns([2, 1])

with col_input:
    st.subheader("Paramètres d'entrée")
    st.caption(f"Thème du jour : {theme_affiche}") # Petit bonus : on affiche le thème !
    
    if has_solved_today:
        st.success(f"🎯 ANALYSE TERMINÉE : {st.session_state.final_time}s")
        st.info("⏳ Machine en phase de refroidissement. Prochain Job disponible demain à minuit.")
        if st.session_state.message_retour == "succes":
            st.balloons()
            st.session_state.message_retour = None 
    else:
        st.text_input("Valeur de convergence (U) :", placeholder="Entrez le résultat...", key="input_reponse")
        st.button("RUN ANALYSIS", on_click=valider_calcul)
        
        if st.session_state.message_retour == "erreur_faux":
            st.error("❌ ERROR: Divergence détectée.")
            st.session_state.message_retour = None
        elif st.session_state.message_retour == "erreur_syntaxe":
            st.warning("⚠️ Erreur de syntaxe dans la saisie.")
            st.session_state.message_retour = None

with col_viz:
    if has_solved_today:
        rho_calcule = min(13 + (st.session_state.final_time * 0.5), 50.0)
        st.subheader(f"🌀 Visualisation du Chaos (ρ = {rho_calcule:.2f})")
        st.write(f"Niveau de chaos indexé sur votre temps : {st.session_state.final_time}s.")
        
        x, y, z = generate_lorenz(rho=rho_calcule)
        fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color=z, colorscale='Inferno', width=3))])
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor="rgba(0,0,0,0)", height=450,
                          scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⌛ En attente de convergence pour générer l'attracteur...")
        # NOUVEAU : On utilise l'énoncé dynamique provenant du JSON !
        st.latex(enonce_affiche)
        st.code("*STATUS : WAITING FOR INPUT...", language="text")
