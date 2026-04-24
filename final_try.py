import streamlit as st
import json
import os
from sympy import sympify, simplify
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="FEA Math Solver", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #2b2b2b; color: #e0e0e0; }
    .stTextInput>div>div>input { background-color: #3d3d3d; color: #00ff00; font-family: 'Courier New'; }
    .stButton>button { border: 1px solid #555; background-color: #444; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTION DU CLASSEMENT PERMANENT ---
FICHIER_SCORES = "scores.json"

def charger_scores():
    if os.path.exists(FICHIER_SCORES):
        with open(FICHIER_SCORES, "r", encoding='utf-8') as f:
            return json.load(f)
    return []

def sauvegarder_score(pilote, temps):
    scores = charger_scores()
    scores.append({
        "Pilote": pilote, 
        "Temps (s)": temps, 
        "Date": str(date.today())
    })
    with open(FICHIER_SCORES, "w", encoding='utf-8') as f:
        json.dump(scores, f, indent=4)

# --- 3. CHARGEMENT DE LA BASE DE DONNÉES (ÉNIGMES) ---
@st.cache_data
def load_daily_problem(date_actuelle):
    try:
        with open('database.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
        reference_date = date(2024, 1, 1) 
        delta_days = (date_actuelle - reference_date).days
        index = delta_days % len(db)
        return db[index]
    except Exception as e:
        return {"enonce": r"\lim_{x \to 0} \frac{\ln(1+x)}{x}", "solution": "1", "theme": "Secours (JSON introuvable)"}

# Initialisation du problème du jour
aujourd_hui = str(date.today())
enigme_du_jour = load_daily_problem(date.today())
solution_attendue = enigme_du_jour["solution"]
enonce_affiche = enigme_du_jour["enonce"]
theme_affiche = enigme_du_jour.get("theme", "Analyse")

# --- 4. INITIALISATION DE LA MÉMOIRE DE SESSION ---
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'message_retour' not in st.session_state:
    st.session_state.message_retour = None

# --- 5. LOGIQUE MATHÉMATIQUE (LORENZ) ---
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

# === 6. L'ARME SECRÈTE : LA FONCTION CALLBACK ===
def valider_calcul():
    reponse_user = st.session_state.input_reponse
    pilote_user = st.session_state.input_pilote
    
    try:
        val_user = sympify(reponse_user.replace(',', '.'))
        val_sol = sympify(solution_attendue) 
        
        if simplify(val_user - val_sol) == 0:
            temps_final = round(time.time() - st.session_state.start_time, 2)
            # SAUVEGARDE PERMANENTE
            sauvegarder_score(pilote_user, temps_final)
            st.session_state.message_retour = "succes"
        else:
            st.session_state.message_retour = "erreur_faux"
    except:
        st.session_state.message_retour = "erreur_syntaxe"

# --- 7. INTERFACE UTILISATEUR & VERROUILLAGE ---
scores_globaux = charger_scores()

with st.sidebar:
    st.title("📟 Job Monitor")
    
    # 1. On récupère le pseudo
    pseudo_actuel = st.text_input("User ID / Pilote :", "Romain", key="input_pilote")
    
    # 2. On vérifie si ce pseudo a déjà gagné aujourd'hui
    a_deja_joue = any(s["Pilote"] == pseudo_actuel and s["Date"] == aujourd_hui for s in scores_globaux)
    
    st.markdown("---")
    st.subheader("📊 Global Ranking (Today)")
    
    scores_du_jour = [s for s in scores_globaux if s["Date"] == aujourd_hui]
    
    if scores_du_jour:
        # On affiche le classement du jour
        df = pd.DataFrame(scores_du_jour)[["Pilote", "Temps (s)"]]
        df = df.sort_values(by="Temps (s)").reset_index(drop=True)
        st.table(df)
    else:
        st.caption("En attente de convergence... Soyez le premier !")
        
    st.caption("Abaqus-Style Math Engine")
    st.caption("Créé par **Romain**")

st.title("🛠️ Analyse de Structure Mathématique")
col_viz, col_input = st.columns([2, 1])

with col_input:
    st.subheader("Paramètres d'entrée")
    st.caption(f"Thème du jour : {theme_affiche}") 
    
    if a_deja_joue:
        # On retrouve son temps dans la base de données
        mon_score = next(s["Temps (s)"] for s in scores_globaux if s["Pilote"] == pseudo_actuel and s["Date"] == aujourd_hui)
        st.success(f"🎯 ANALYSE TERMINÉE : {mon_score}s")
        st.info("⏳ Vous avez déjà validé la mission du jour. Prochain Job disponible demain.")
        
        # Affichage des ballons une seule fois
        if st.session_state.message_retour == "succes":
            st.balloons()
            st.session_state.message_retour = None 
    else:
        # Champ de saisie lié au Callback
        st.text_input("Valeur de convergence (U) :", placeholder="Entrez le résultat...", key="input_reponse")
        st.button("RUN ANALYSIS", on_click=valider_calcul)
        
        # Gestion des erreurs
        if st.session_state.message_retour == "erreur_faux":
            st.error("❌ ERROR: Divergence détectée.")
            st.session_state.message_retour = None
        elif st.session_state.message_retour == "erreur_syntaxe":
            st.warning("⚠️ Erreur de syntaxe dans la saisie.")
            st.session_state.message_retour = None

with col_viz:
    if a_deja_joue:
        mon_score = next(s["Temps (s)"] for s in scores_globaux if s["Pilote"] == pseudo_actuel and s["Date"] == aujourd_hui)
        rho_calcule = min(13 + (mon_score * 0.5), 50.0)
        
        st.subheader(f"🌀 Visualisation du Chaos (ρ = {rho_calcule:.2f})")
        st.write(f"Niveau de chaos indexé sur votre temps : {mon_score}s.")
        
        x, y, z = generate_lorenz(rho=rho_calcule)
        fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color=z, colorscale='Inferno', width=3))])
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor="rgba(0,0,0,0)", height=450,
                          scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⌛ En attente de convergence pour générer l'attracteur...")
        st.latex(enonce_affiche)
        st.code("""
# NODE DEFINITION
*Node, nset=AllNodes
1, 0.0, 0.0, 0.0
...
*Step, name=Math_Analysis
*Static, LimitCalculation

*STATUS : WAITING FOR INPUT CONVERGENCE...
        """, language="text")
