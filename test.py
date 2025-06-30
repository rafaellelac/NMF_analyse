import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ------------------------------------------------------------
# PARAMÈTRES À ADAPTER
# ------------------------------------------------------------
EXCEL_PATH  = "NMF_vs_Etoile_Lavalloise.xlsx"
SHEET_NAME  = "Nantes Métropole Futsal (À domi"
HEATMAP_ON  = "origin"          # "origin"  ou  "destination"
SUCCESS_ONLY = True             # True : passes réussies uniquement

# ------------------------------------------------------------
# 1. Charger et remettre à plat la feuille
# ------------------------------------------------------------
def load_passes(xls_path=EXCEL_PATH, sheet_name=SHEET_NAME, success_only=True):
    """Retourne un DataFrame (une ligne = une passe)."""
    df_raw = pd.read_excel(xls_path, sheet_name=sheet_name, header=None)
    df_raw = df_raw.dropna(how="all").dropna(axis=1, how="all")  # lignes/colonnes vides

    attrib_block = df_raw.iloc[1:12]           # lignes contenant les attributs
    raw_attrs    = attrib_block.iloc[:, 0]     # 1ère colonne = noms bruts

    # Noms nettoyés
    terrain_labels = ["FieldXfrom", "FieldYfrom", "FieldXto", "FieldYto"]
    rename_map = {
        "Passe": "PassID", "Temps": "Time", "Démarrer": "Start",
        "Arrêter": "Stop", "Joueurs": "Player",
        "Nombre joueuses éliminées": "PlayersEliminated",
        "Résultat": "Result"
    }
    clean_names, t_i = [], 0
    for val in raw_attrs:
        v = "" if pd.isna(val) else str(val).strip()
        if v == "Position sur le terrain":
            clean_names.append(terrain_labels[t_i])
            t_i += 1
        elif v in rename_map:
            clean_names.append(rename_map[v])
        else:
            clean_names.append(v if v else f"Unknown_{len(clean_names)}")

    # Transposer → colonnes = attributs
    df = attrib_block.iloc[:, 1:]
    df.index = clean_names
    df = df.T.reset_index(drop=True)

    # Filtre passes réussies
    if success_only:
        df = df[df["Result"].astype(str).str.strip().eq("Succès")]

    # Convertir coordonnées en float
    for c in terrain_labels:
        df[c] = df[c].astype(float)

    return df

df = load_passes()

# ------------------------------------------------------------
# 2. Carte des passes réussies
# ------------------------------------------------------------
fig_passmap = go.Figure()

# demi‑terrain normalisé
fig_passmap.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1,
                      line=dict(color="black", width=2), layer="below")

for player, part in df.groupby("Player"):
    xs, ys, hover = [], [], []
    for _, r in part.iterrows():
        xs += [r.FieldXfrom, r.FieldXto, None]
        ys += [r.FieldYfrom, r.FieldYto, None]
        hover += [f"{player}<br>{r.Time}", "", ""]
    fig_passmap.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", name=player,
        text=hover, hoverinfo="text",
        line=dict(width=2)
    ))

fig_passmap.update_layout(
    title="Carte des passes réussies – Nantes Métropole Futsal",
    xaxis=dict(range=[0, 1], visible=False),
    yaxis=dict(range=[0, 1], visible=False),
    width=850, height=500,
    legend_title="Joueurs (cliquer pour filtrer)",
    plot_bgcolor="white"
)

# ------------------------------------------------------------
# 3. Heatmap origines ou destinations
# ------------------------------------------------------------
if HEATMAP_ON == "origin":
    x, y = df["FieldXfrom"], df["FieldYfrom"]
    title_hm = "Heatmap des ORIGINES de passes"
else:
    x, y = df["FieldXto"], df["FieldYto"]
    title_hm = "Heatmap des DESTINATIONS de passes"

fig_heat = px.density_heatmap(
    df, x=x, y=y, nbinsx=30, nbinsy=30,
    title=title_hm, labels={"x": "", "y": ""},
    range_x=[0, 1], range_y=[0, 1]
)
fig_heat.update_layout(width=850, height=500, xaxis_visible=False, yaxis_visible=False)

# ------------------------------------------------------------
# 4. Histogramme passes / joueur
# ------------------------------------------------------------
pass_counts = df["Player"].value_counts().reset_index()
pass_counts.columns = ["Player", "Passes"]

fig_hist = px.bar(pass_counts, x="Player", y="Passes",
                  title="Nombre de passes par joueur",
                  labels={"Player": "Joueur", "Passes": "Passes réussies"})
fig_hist.update_layout(width=850, height=400)

# ------------------------------------------------------------
# 5. Afficher les trois figures
# ------------------------------------------------------------
fig_passmap.show()   # carte des passes
fig_heat.show()      # heatmap
fig_hist.show()      # histogramme
