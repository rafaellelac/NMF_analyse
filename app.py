import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# --- Configuration ---
longueur = 40
largeur = 20

# Liste des fichiers Excel disponibles
def liste_matchs():
    fichiers = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    matchs = [(f.replace('.xlsx', '').replace('_vs_', ' vs ').replace('_', ' '), f) for f in fichiers]
    return matchs

def charger_match(fichier):
    return pd.read_excel(fichier)

# --- Création du layout ---
app.layout = html.Div([
    html.H1("Analyse des actions futsal"),

    html.Label("Match"),
    dcc.Dropdown(
        id='match-dropdown',
        options=[{'label': nom, 'value': f} for nom, f in liste_matchs()],
        value=liste_matchs()[0][1] if liste_matchs() else None
    ),

    html.Label("Équipe"),
    dcc.Dropdown(id='equipe-dropdown'),

    html.Label("Type d'analyse"),
    dcc.RadioItems(
        id='type-analyse-radio',
        options=[
            {'label': 'Collective', 'value': 'collectif'},
            {'label': 'Individuelle', 'value': 'individuel'}
        ],
        value='collectif'
    ),

    html.Div(id='selection-joueurs-container'),

    html.Label("Critère d'analyse"),
    dcc.Dropdown(
        id='critere-dropdown',
        options=[
            {'label': c, 'value': c.lower()} for c in ['Passe', 'Tir', 'Attaque', 'Défense', 'Gardien']
        ],
        value='passe'
    ),

    html.Label("Filtre"),
    dcc.Dropdown(id='filtre-dropdown', multi=True),

    dcc.Graph(id='graph-analyse')
])

# --- Callbacks dynamiques ---
@app.callback(
    Output('equipe-dropdown', 'options'),
    Output('equipe-dropdown', 'value'),
    Input('match-dropdown', 'value')
)

def update_equipes(match_file):
    if match_file is None:
        return [], None
    # Extraire les équipes depuis le nom du fichier
    base = os.path.basename(match_file).replace('.xlsx', '')
    if '_vs_' in base:
        equipes = base.split('_vs_')
    elif ' vs ' in base:
        equipes = base.split(' vs ')
    else:
        equipes = [base]
    equipes = [eq.replace('_', ' ').strip() for eq in equipes]
    options = [{'label': eq, 'value': eq} for eq in equipes]
    return options, options[0]['value'] if options else None

@app.callback(
    Output('selection-joueurs-container', 'children'),
    Input('match-dropdown', 'value'),
    Input('equipe-dropdown', 'value'),
    Input('type-analyse-radio', 'value')
)
def update_joueur_choix(match_file, equipe, type_analyse):
    if match_file is None or equipe is None:
        return html.Div()
    df = charger_match(match_file)
    joueurs = sorted(df[df['equipe'] == equipe]['joueur'].dropna().unique())

    if type_analyse == 'collectif':
        return html.Div([
            html.Label("Joueurs (laisser vide pour toute l'équipe)"),
            dcc.Dropdown(id='joueurs-dropdown', options=[{'label': j, 'value': j} for j in joueurs], multi=True)
        ])
    else:
        return html.Div([
            html.Label("Joueur"),
            dcc.Dropdown(id='joueur-dropdown', options=[{'label': j, 'value': j} for j in joueurs], value=joueurs[0] if joueurs else None),
            html.Label("Inclure le gardien ?"),
            dcc.Checklist(id='gardien-checklist', options=[{'label': 'Oui', 'value': 'gardien'}], value=[])
        ])

@app.callback(
    Output('filtre-dropdown', 'options'),
    Output('filtre-dropdown', 'value'),
    Input('critere-dropdown', 'value'),
    Input('type-analyse-radio', 'value')
)
def update_filtres(critere, type_analyse):
    filtres = {
        'passe': ['succès', 'manquée', 'interceptée', '0', '1', '2', '+2'],
        'attaque': ['joueurs franchis', 'faute provoquée', 'perte de balle', 'possession conséquente'],
        'défense': ['récupération avec ballon', 'récupération provoquée', 'interception', 'interception manquée',
                    'faute subie', 'faute provoquée', 'action défensive sans rec', 'duel perdu'],
        'tir': ['but', 'cadré', 'contré', 'non cadré', 'poteau', 'bar'],
        'gardien': ['arrêt avec récupération', 'arrêt avec possession adverse', 'ballon capté',
                    'but encaissé', 'sortie avec interception', 'sortie manquée']
    }
    if critere in filtres:
        return [{'label': f, 'value': f} for f in filtres[critere]], []
    else:
        return [], []

# --- Callback pour affichage du graphe complet (tous critères) ---
@app.callback(
    Output('graph-analyse', 'figure'),
    Input('match-dropdown', 'value'),
    Input('equipe-dropdown', 'value'),
    Input('type-analyse-radio', 'value'),
    Input('joueurs-dropdown', 'value'),
    Input('joueur-dropdown', 'value'),
    Input('gardien-checklist', 'value'),
    Input('critere-dropdown', 'value'),
    Input('filtre-dropdown', 'value')
)
def afficher_analyse(match_file, equipe, type_analyse, joueurs_collectif, joueur_indiv, gardien, critere, filtres):
    if match_file is None or equipe is None:
        return go.Figure()

    df = charger_match(match_file)
    df = df[df['equipe'] == equipe]
    fig = go.Figure()

    # Ajoute l'image du terrain en fond
    fig.update_layout(
        images=[dict(
            source="Fond terrain NMF/BLEU BLANC OR VERTICAL.jpg",  # Mets ici l'URL ou le chemin local de ton image
            xref="x", yref="y",
            x=0, y=largeur, sizex=longueur, sizey=largeur,
            sizing="stretch", opacity=0.5, layer="below"
        )],
        title=f"Analyse {critere.capitalize()}",
        xaxis=dict(range=[0, longueur], showgrid=False, zeroline=False),
        yaxis=dict(range=[0, largeur], scaleanchor='x', showgrid=False, zeroline=False)
    )
# ...existing code...

    # Sélection des joueurs
    if type_analyse == 'collectif':
        if joueurs_collectif:
            df = df[df['joueur'].isin(joueurs_collectif)]
    else:
        if joueur_indiv:
            joueurs = [joueur_indiv]
            if 'gardien' in gardien:
                df_gardien = df[df['joueur'] == 'gardien']
                df = pd.concat([df[df['joueur'].isin(joueurs)], df_gardien])
            else:
                df = df[df['joueur'].isin(joueurs)]

    # Analyse selon le critère
    if critere == 'passe':
        if filtres:
            statut_passe = ['succès', 'manquée', 'interceptée']
            nb_elim = [f for f in filtres if f not in statut_passe]
            if any(f in statut_passe for f in filtres):
                df = df[df['statut_passe'].isin(filtres)]
            if nb_elim:
                df = df[df['nb_joueurs_elimines'].astype(str).isin(nb_elim) |
                        ((df['nb_joueurs_elimines'] >= 3) & ('+2' in nb_elim))]
        for _, row in df.iterrows():
            x0, y0 = row['FieldXfrom'] * longueur, row['FieldYfrom'] * largeur
            x1, y1 = row['FieldXto'] * longueur, row['FieldYto'] * largeur
            distance = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1],
                mode='lines+markers',
                line=dict(width=2, color='blue'),
                marker=dict(size=6),
                customdata=[[row['joueur'], row['statut_passe'], distance]],
                hovertemplate=(
                    "Joueur: %{customdata[0]}<br>"
                    "Statut: %{customdata[1]}<br>"
                    "Distance: %{customdata[2]:.2f} m<br>"
                    "<extra></extra>"
                ),
                showlegend=False
            ))
            # Ajout d'une flèche (annotation) pour la pointe
            fig.add_annotation(
                x=x1, y=y1, ax=x0, ay=y0,
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=2, arrowcolor='blue',
                opacity=0.7
            )


    elif critere == 'tir':
        if filtres:
            df = df[df['statut_tir'].isin(filtres)]
        for _, row in df.iterrows():
            x, y = row['FieldXfrom'] * longueur, row['FieldYfrom'] * largeur
            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers',
                                     marker=dict(size=10, color='red'),
                                     text=f"{row['joueur']} - {row['statut_tir']}",
                                     hoverinfo='text'))

    elif critere == 'attaque':
        if filtres:
            df = df[df['type_attaque'].isin(filtres)]
        for _, row in df.iterrows():
            x, y = row['FieldXfrom'] * longueur, row['FieldYfrom'] * largeur
            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers',
                                     marker=dict(size=10, color='orange'),
                                     text=f"{row['joueur']} - {row['type_attaque']}",
                                     hoverinfo='text'))

    elif critere == 'défense':
        if filtres:
            df = df[df['type_defense'].isin(filtres)]
        for _, row in df.iterrows():
            x, y = row['FieldXfrom'] * longueur, row['FieldYfrom'] * largeur
            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers',
                                     marker=dict(size=10, color='green'),
                                     text=f"{row['joueur']} - {row['type_defense']}",
                                     hoverinfo='text'))

    elif critere == 'gardien':
        if filtres:
            df = df[df['statut_gardien'].isin(filtres)]
        for _, row in df.iterrows():
            x, y = row['FieldXfrom'] * longueur, row['FieldYfrom'] * largeur
            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers',
                                     marker=dict(size=10, color='purple'),
                                     text=f"{row['joueur']} - {row['statut_gardien']}",
                                     hoverinfo='text'))

    fig.update_layout(title=f"Analyse {critere.capitalize()}",
                      xaxis=dict(range=[0, longueur]),
                      yaxis=dict(range=[0, largeur], scaleanchor='x'))
    return fig

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)

