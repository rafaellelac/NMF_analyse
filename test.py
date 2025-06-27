# -------------------------------------------
# 1. Prérequis : installer Plotly (une fois)
# -------------------------------------------
# !pip install plotly pandas openpyxl

import pandas as pd
import plotly.graph_objects as go

# -------------------------------------------------------------
# 2. Charger et nettoyer la feuille « Nantes Métropole Futsal »
# -------------------------------------------------------------
excel_path = "NMF_vs_Etoile_Lavalloise.xlsx"   # adapte si besoin
sheet_name  = "Nantes Métropole Futsal (À domi"

# a) lire la feuille
df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

# b) la première ligne contient les vrais noms de colonnes
df_raw.columns = df_raw.iloc[0]
df = df_raw.drop(index=0).reset_index(drop=True)

print(df.head(3).T)  # transpose pour voir les noms de colonnes verticalement


# c) ne garder que les passes réussies + colonnes utiles
# Nettoyage général des noms de colonnes
df.columns = df.columns.str.strip()  # supprime les espaces en début/fin
df.columns = df.columns.str.replace('\n', '')  # supprime les retours à la ligne éventuels
print(df.columns.tolist())  # pour vérifier les noms propres

# Filtrage après nettoyage
df = df[df["Résultat"].str.strip() == "Succès"]


cols = ["Joueurs", "FieldXfrom", "FieldYfrom", "FieldXto", "FieldYto"]
df = df[cols].dropna()

# d) convertir les coordonnées en float (elles sont souvent stockées en str)
for c in cols[1:]:
    df[c] = df[c].astype(float)

# -----------------------------------------------------------------
# 3. Créer une figure Plotly avec un demi-terrain + flèches de passe
# -----------------------------------------------------------------
fig = go.Figure()

# a) dessiner le demi-terrain (normalisé 0-1)
# cadre
fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1,
              line=dict(color="black", width=2), layer="below")

# point de penalty (facultatif)
fig.add_shape(type="circle", x0=0.47, y0=0.47, x1=0.53, y1=0.53,
              line=dict(color="black"), fillcolor="black", layer="below")

# b) ajouter les passes, une trace par joueur pour gérer l’interactivité
for joueur, passes in df.groupby("Joueurs"):
    # pour chaque passe -> deux points (départ & arrivée) reliés par une ligne
    x = []
    y = []
    for _, row in passes.iterrows():
        x += [row["FieldXfrom"], row["FieldXto"], None]  # None = coupure du tracé
        y += [row["FieldYfrom"], row["FieldYto"], None]

    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        name=joueur,
        hoverinfo="text",
        text=[f"{joueur}<br>({row.FieldXfrom:.2f}, {row.FieldYfrom:.2f}) → "
              f"({row.FieldXto:.2f}, {row.FieldYto:.2f})"
              for _, row in passes.iterrows() for _ in (0,1,2)],
        line=dict(width=2)
    ))

# c) mise en forme
fig.update_layout(
    title="Carte interactive des passes réussies – Nantes Métropole Futsal",
    xaxis=dict(range=[0,1], showgrid=False, zeroline=False, visible=False),
    yaxis=dict(range=[0,1], showgrid=False, zeroline=False, visible=False),
    width=900, height=550,
    legend_title_text="Joueurs (cliquer pour masquer/afficher)",
    plot_bgcolor="white",
)

# d) afficher
fig.show()
