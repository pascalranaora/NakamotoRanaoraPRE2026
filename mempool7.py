# import requests
# import pandas as pd
# import matplotlib.pyplot as plt
# import os
# import time
# from tqdm import tqdm

# # --- PARAMÈTRES ---
# HALVING_BLOCK = 840000  
# EPOCH = 2016            

# # Le DAA (ajustement de difficulté) n'est pas tombé exactement sur le Halving.
# # Il est tombé au multiple de 2016 suivant :
# DAA_BLOCK = HALVING_BLOCK + (EPOCH - (HALVING_BLOCK % EPOCH)) # Bloc 840672

# BLOCKS_BEFORE = EPOCH   # 1 époque avant
# BLOCKS_AFTER = 1500     # Assez de blocs après le DAA pour voir la relaxation

# START_BLOCK = HALVING_BLOCK - BLOCKS_BEFORE
# END_BLOCK = DAA_BLOCK + BLOCKS_AFTER
# CSV_FILENAME = "halving_840000_data.csv"

# API_URL = "https://mempool.space/api/v1/blocks/"

# def fetch_blocks(start_height, end_height):
#     print(f"Extraction via API des blocs {start_height} à {end_height}...")
#     blocks_data = []
#     current_height = end_height
#     pbar = tqdm(total=(end_height - start_height))
    
#     while current_height >= start_height:
#         try:
#             response = requests.get(f"{API_URL}{current_height}")
#             response.raise_for_status()
#             batch = response.json()
            
#             for block in batch:
#                 if start_height <= block['height'] <= end_height:
#                     blocks_data.append({
#                         'height': block['height'],
#                         'timestamp': block['timestamp'],
#                         'difficulty': block['difficulty']
#                     })
            
#             current_height = batch[-1]['height'] - 1
#             pbar.update(len(batch))
#             time.sleep(0.5) 
            
#         except Exception as e:
#             print(f"Erreur à {current_height}: {e}. Nouvel essai...")
#             time.sleep(2) 
            
#     pbar.close()
#     return blocks_data

# # --- CHARGEMENT OU EXTRACTION DES DONNÉES ---
# if os.path.exists(CSV_FILENAME):
#     print(f"Chargement instantané des données depuis {CSV_FILENAME}...")
#     df = pd.read_csv(CSV_FILENAME)
# else:
#     data = fetch_blocks(START_BLOCK, END_BLOCK)
#     df = pd.DataFrame(data)
#     df = df.sort_values('height').reset_index(drop=True)
    
#     # Calcul du Delta t
#     df['delta_t'] = df['timestamp'].diff()
#     df['delta_t'] = df['delta_t'].clip(lower=0)
    
#     # Sauvegarde locale
#     df.to_csv(CSV_FILENAME, index=False)
#     print(f"Données sauvegardées dans {CSV_FILENAME}.")

# # --- CALCUL DES STATISTIQUES POUR LE MODÈLE ---
# # Suppression du premier NaN dû au .diff()
# df_clean = df.dropna(subset=['delta_t'])

# phase1 = df_clean[df_clean['height'] < HALVING_BLOCK]['delta_t']
# phase2 = df_clean[(df_clean['height'] >= HALVING_BLOCK) & (df_clean['height'] < DAA_BLOCK)]['delta_t']
# phase3 = df_clean[df_clean['height'] >= DAA_BLOCK]['delta_t']

# print("\n" + "="*60)
# print(" RÉSULTATS STATISTIQUES POUR VALIDATION DU MODÈLE (COPIEZ CECI)")
# print("="*60)
# print(f"PHASE 1 : Équilibre Métastable (Avant Halving, Blocs {START_BLOCK} - {HALVING_BLOCK-1})")
# print(f"  -> Moyenne <Delta t> : {phase1.mean():.2f} secondes")
# print(f"  -> Variance sigma^2  : {phase1.var():.2f} s^2")

# print(f"\nPHASE 2 : La Trempe (Halving -> Thermostat DAA, Blocs {HALVING_BLOCK} - {DAA_BLOCK-1})")
# print(f"  -> Moyenne <Delta t> : {phase2.mean():.2f} secondes")
# print(f"  -> Variance sigma^2  : {phase2.var():.2f} s^2")
# print(f"  [!] Variation du Bruit Actif : +{((phase2.var() - phase1.var()) / phase1.var() * 100):.1f}% par rapport à l'équilibre")

# print(f"\nPHASE 3 : Relaxation (Après Thermostat DAA, Blocs {DAA_BLOCK} - {END_BLOCK})")
# print(f"  -> Moyenne <Delta t> : {phase3.mean():.2f} secondes")
# print(f"  -> Variance sigma^2  : {phase3.var():.2f} s^2")
# print("="*60 + "\n")

# # --- GRAPHIQUE (Optionnel, juste pour la visualisation locale) ---
# window = 144
# df['mean_delta_t'] = df['delta_t'].rolling(window=window, center=True).mean()
# df['var_delta_t'] = df['delta_t'].rolling(window=window, center=True).var()

# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# ax1.plot(df['height'], df['mean_delta_t'], color='blue')
# ax1.axvline(HALVING_BLOCK, color='red', linestyle='--', label='Halving (Trempe)')
# ax1.axvline(DAA_BLOCK, color='green', linestyle='--', label='DAA (Thermostat)')
# ax1.set_title('Temps d\'attente moyen (Moyenne Mobile 144 blocs)')
# ax1.legend()

# ax2.plot(df['height'], df['var_delta_t'], color='purple')
# ax2.axvline(HALVING_BLOCK, color='red', linestyle='--')
# ax2.axvline(DAA_BLOCK, color='green', linestyle='--')
# ax2.set_title('Variance / Bruit Actif (Moyenne Mobile 144 blocs)')

# plt.tight_layout()
# plt.show()


# import pandas as pd
# import numpy as np
# import scipy.stats as stats
# import os

# # --- PARAMÈTRES ---
# HALVING_BLOCK = 840000  
# EPOCH = 2016            
# DAA_BLOCK = HALVING_BLOCK + (EPOCH - (HALVING_BLOCK % EPOCH)) # 840672
# CSV_FILENAME = "halving_840000_data.csv"

# # --- VÉRIFICATION DU FICHIER ---
# if not os.path.exists(CSV_FILENAME):
#     print(f"Erreur : Le fichier {CSV_FILENAME} est introuvable.")
#     exit()

# df = pd.read_csv(CSV_FILENAME)
# df_clean = df.dropna(subset=['delta_t']).copy()

# # --- SÉPARATION DES PHASES ---
# # Phase 1 : Époque précédente complète (2016 blocs)
# phase1 = df_clean[(df_clean['height'] >= HALVING_BLOCK - EPOCH) & (df_clean['height'] < HALVING_BLOCK)]['delta_t']

# # Phase 2 : La Trempe (Halving jusqu'au DAA)
# phase2 = df_clean[(df_clean['height'] >= HALVING_BLOCK) & (df_clean['height'] < DAA_BLOCK)]['delta_t']

# # --- CALCULS STATISTIQUES ---
# var1 = phase1.var(ddof=1)
# var2 = phase2.var(ddof=1)
# n1 = len(phase1)
# n2 = len(phase2)

# variation_pct = ((var2 - var1) / var1) * 100

# # 1. Test F de Fisher (Ratio des variances)
# # Hypothèse Nulle (H0) : var1 == var2
# # Hypothèse Alternative (H1) : var2 > var1 (Test unilatéral)
# F_statistic = var2 / var1
# df1 = n2 - 1
# df2 = n1 - 1
# p_value_F = stats.f.sf(F_statistic, df1, df2) # sf = Survival Function (1 - CDF)

# # 2. Test de Levene (Plus robuste pour les lois exponentielles/Poisson)
# # Centré sur la médiane pour une robustesse maximale
# stat_levene, p_value_levene_bilateral = stats.levene(phase1, phase2, center='median')
# p_value_levene = p_value_levene_bilateral / 2 # Conversion en unilatéral (car on teste var2 > var1)

# # --- AFFICHAGE DES RÉSULTATS ---
# print("\n" + "="*70)
# print(" RÉSULTATS DU TEST DE SIGNIFICATIVITÉ STATISTIQUE")
# print("="*70)
# print(f"Phase 1 (Équilibre) : N1 = {n1} blocs | Variance = {var1:.2f} s^2")
# print(f"Phase 2 (Trempe)    : N2 = {n2} blocs  | Variance = {var2:.2f} s^2")
# print(f"Écart observé       : +{variation_pct:.2f} %")
# print("-" * 70)

# print("1. TEST F DE FISHER :")
# print(f"   -> Statistique F : {F_statistic:.4f}")
# print(f"   -> Valeur-p      : {p_value_F:.5f}")
# if p_value_F < 0.05:
#     print("   [CONCLUSION] : Rejet de H0. L'augmentation de la variance est STATISTIQUEMENT SIGNIFICATIVE (p < 0.05).")
# else:
#     print("   [CONCLUSION] : Échec du rejet de H0. L'augmentation n'est pas statistiquement significative (p > 0.05).")

# print("\n2. TEST DE LEVENE (Recommandé pour processus de Poisson) :")
# print(f"   -> Statistique W : {stat_levene:.4f}")
# print(f"   -> Valeur-p      : {p_value_levene:.5f}")
# if p_value_levene < 0.05:
#     print("   [CONCLUSION] : Rejet de H0. L'augmentation du bruit actif est STATISTIQUEMENT SIGNIFICATIVE (p < 0.05).")
# else:
#     print("   [CONCLUSION] : Échec du rejet de H0. Tendance observable mais non significative au seuil de 5%.")
# print("="*70 + "\n")

# import requests
# import pandas as pd
# import numpy as np
# import scipy.stats as stats
# import os
# import time
# from tqdm import tqdm

# # --- PARAMÈTRES ---
# EPOCH = 2016
# HALVINGS = [
#     {"year": 2012, "block": 210000},
#     {"year": 2016, "block": 420000},
#     {"year": 2020, "block": 630000},
#     {"year": 2024, "block": 840000}
# ]
# API_URL = "https://mempool.space/api/v1/blocks/"

# def fetch_blocks(start_height, end_height, desc):
#     """Extrait les blocs via l'API mempool.space avec une barre de progression"""
#     blocks_data = []
#     current_height = end_height
#     pbar = tqdm(total=(end_height - start_height), desc=desc)
    
#     while current_height >= start_height:
#         try:
#             response = requests.get(f"{API_URL}{current_height}")
#             response.raise_for_status()
#             batch = response.json()
            
#             for block in batch:
#                 if start_height <= block['height'] <= end_height:
#                     blocks_data.append({
#                         'height': block['height'],
#                         'timestamp': block['timestamp'],
#                         'difficulty': block['difficulty']
#                     })
            
#             current_height = batch[-1]['height'] - 1
#             pbar.update(len(batch))
#             time.sleep(0.5) # Respect du rate limit
#         except Exception as e:
#             time.sleep(2) # Backoff
            
#     pbar.close()
#     return blocks_data

# # --- STRUCTURE POUR STOCKER LES RÉSULTATS ---
# results = []

# print("=== LANCEMENT DE L'ANALYSE THERMODYNAMIQUE MULTI-HALVINGS ===\n")

# for h in HALVINGS:
#     h_block = h["block"]
#     year = h["year"]
    
#     # Calcul des bornes de l'époque
#     start_block = h_block - EPOCH
#     daa_block = h_block + (EPOCH - (h_block % EPOCH))
    
#     csv_filename = f"halving_{year}_{h_block}_data.csv"
    
#     # --- EXTRACTION OU CHARGEMENT ---
#     if os.path.exists(csv_filename):
#         print(f"[{year}] Chargement des données locales ({csv_filename})...")
#         df = pd.read_csv(csv_filename)
#     else:
#         data = fetch_blocks(start_block, daa_block, f"Extraction {year}")
#         df = pd.DataFrame(data)
#         df = df.sort_values('height').reset_index(drop=True)
#         df['delta_t'] = df['timestamp'].diff().clip(lower=0)
#         df.to_csv(csv_filename, index=False)
    
#     # --- NETTOYAGE ET SÉPARATION DES PHASES ---
#     df_clean = df.dropna(subset=['delta_t']).copy()
    
#     phase1 = df_clean[(df_clean['height'] >= start_block) & (df_clean['height'] < h_block)]['delta_t']
#     phase2 = df_clean[(df_clean['height'] >= h_block) & (df_clean['height'] < daa_block)]['delta_t']
    
#     # --- CALCULS STATISTIQUES ---
#     var1 = phase1.var(ddof=1)
#     var2 = phase2.var(ddof=1)
#     n1 = len(phase1)
#     n2 = len(phase2)
#     var_change_pct = ((var2 - var1) / var1) * 100
    
#     # Tests
#     F_stat = var2 / var1
#     p_val_F = stats.f.sf(F_stat, n2 - 1, n1 - 1)
    
#     stat_levene, p_val_levene_bilateral = stats.levene(phase1, phase2, center='median')
#     p_val_levene = p_val_levene_bilateral / 2 # Unilatéral
    
#     results.append({
#         "Année": year,
#         "Bloc": h_block,
#         "N_Equilibre": n1,
#         "N_Trempe": n2,
#         "Var_Eq": var1,
#         "Var_Trempe": var2,
#         "Delta_Var_%": var_change_pct,
#         "P_Fisher": p_val_F,
#         "P_Levene": p_val_levene
#     })

# # --- AFFICHAGE DU RAPPORT FINAL ---
# print("\n" + "="*80)
# print(" RÉSULTATS MÉTROLOGIQUES DES 4 TREMPES THERMODYNAMIQUES (HALVINGS)")
# print("="*80)
# for r in results:
#     print(f"--- HALVING {r['Année']} (Bloc {r['Bloc']}) ---")
#     print(f"Durée Phase Trempe (avant DAA) : {r['N_Trempe']} blocs")
#     print(f"Variance Eq -> Trempe          : {r['Var_Eq']:.0f} s^2 -> {r['Var_Trempe']:.0f} s^2")
#     print(f"Variation du Bruit Actif       : {r['Delta_Var_%']:+.2f} %")
    
#     sig_f = "OUI" if r['P_Fisher'] < 0.05 else "NON"
#     sig_l = "OUI" if r['P_Levene'] < 0.05 else "NON"
#     print(f"Test de Fisher (p-value)       : {r['P_Fisher']:.4f} (Significatif : {sig_f})")
#     print(f"Test de Levene (p-value)       : {r['P_Levene']:.4f} (Significatif : {sig_l})\n")
# print("="*80)

import requests
import pandas as pd
import numpy as np
import scipy.stats as stats
import os
import time
from tqdm import tqdm
import matplotlib.pyplot as plt

# --- GRAPHIC CONFIGURATION FOR PUBLICATION (RevTeX / APS) ---
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "axes.labelsize": 12,
    "font.size": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 300
})

# --- PARAMETERS ---
EPOCH = 2016
HALVINGS = [
    {"year": 2012, "block": 210000},
    {"year": 2016, "block": 420000},
    {"year": 2020, "block": 630000},
    {"year": 2024, "block": 840000}
]
API_URL = "https://mempool.space/api/v1/blocks/"

def fetch_blocks(start_height, end_height, desc):
    """Fetches blocks via mempool.space API with a progress bar"""
    blocks_data = []
    current_height = end_height
    pbar = tqdm(total=(end_height - start_height), desc=desc)
    
    while current_height >= start_height:
        try:
            response = requests.get(f"{API_URL}{current_height}")
            response.raise_for_status()
            batch = response.json()
            
            for block in batch:
                if start_height <= block['height'] <= end_height:
                    blocks_data.append({
                        'height': block['height'],
                        'timestamp': block['timestamp'],
                        'difficulty': block['difficulty']
                    })
            
            current_height = batch[-1]['height'] - 1
            pbar.update(len(batch))
            time.sleep(0.5) # Rate limit respect
        except Exception as e:
            time.sleep(2) # Backoff
            
    pbar.close()
    return blocks_data

# --- DATA STRUCTURE ---
results = []

# Prepare the 2x2 figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

print("=== STARTING MULTI-HALVING THERMODYNAMIC ANALYSIS ===\n")

for i, h in enumerate(HALVINGS):
    h_block = h["block"]
    year = h["year"]
    
    # Calculate epoch boundaries (with some padding for the plot)
    start_block = h_block - EPOCH
    daa_block = h_block + (EPOCH - (h_block % EPOCH))
    
    csv_filename = f"halving_{year}_{h_block}_data.csv"
    
    # --- FETCH OR LOAD ---
    if os.path.exists(csv_filename):
        print(f"[{year}] Loading local data ({csv_filename})...")
        df = pd.read_csv(csv_filename)
    else:
        data = fetch_blocks(start_block, daa_block, f"Fetching {year}")
        df = pd.DataFrame(data)
        df = df.sort_values('height').reset_index(drop=True)
        df['delta_t'] = df['timestamp'].diff().clip(lower=0)
        df.to_csv(csv_filename, index=False)
    
    # --- CLEANING AND PHASE SEPARATION ---
    df_clean = df.dropna(subset=['delta_t']).copy()
    
    phase1 = df_clean[(df_clean['height'] >= start_block) & (df_clean['height'] < h_block)]['delta_t']
    phase2 = df_clean[(df_clean['height'] >= h_block) & (df_clean['height'] < daa_block)]['delta_t']
    
    # --- STATISTICAL CALCULATIONS ---
    var1 = phase1.var(ddof=1)
    var2 = phase2.var(ddof=1)
    n1 = len(phase1)
    n2 = len(phase2)
    var_change_pct = ((var2 - var1) / var1) * 100
    
    F_stat = var2 / var1
    p_val_F = stats.f.sf(F_stat, n2 - 1, n1 - 1)
    stat_levene, p_val_levene_bilateral = stats.levene(phase1, phase2, center='median')
    p_val_levene = p_val_levene_bilateral / 2 # One-tailed
    
    results.append({
        "Year": year,
        "Block": h_block,
        "N_Eq": n1,
        "N_Quench": n2,
        "Var_Eq": var1,
        "Var_Quench": var2,
        "Delta_Var_%": var_change_pct,
        "P_Fisher": p_val_F,
        "P_Levene": p_val_levene
    })

    # --- PLOTTING FOR CURRENT HALVING ---
    ax = axes[i]
    
    # Center X axis on Halving block
    df_clean['relative_height'] = df_clean['height'] - h_block
    
    # Rolling mean and std dev (144 blocks = ~1 day)
    window = 144
    df_clean['rolling_mean_min'] = df_clean['delta_t'].rolling(window=window, center=True).mean() / 60
    df_clean['rolling_std_min'] = df_clean['delta_t'].rolling(window=window, center=True).std() / 60
    
    # Plot rolling mean
    ax.plot(df_clean['relative_height'], df_clean['rolling_mean_min'], 
            color='#1f77b4', linewidth=2, label=r'$\langle \Delta t \rangle$ (144-block moving avg)')
    
    # Plot variance (shaded area +/- 1 sigma)
    ax.fill_between(df_clean['relative_height'], 
                    df_clean['rolling_mean_min'] - df_clean['rolling_std_min'],
                    df_clean['rolling_mean_min'] + df_clean['rolling_std_min'], 
                    color='#1f77b4', alpha=0.2, label=r'$\pm 1 \sigma$ (Thermal noise $\zeta$)')
    
    # Strategic vertical lines
    ax.axvline(0, color='#d62728', linestyle='--', linewidth=2, label='Thermodynamic Quench (Halving)')
    daa_relative = daa_block - h_block
    ax.axvline(daa_relative, color='#2ca02c', linestyle=':', linewidth=2, label='DAA Thermostat Action')
    
    # Target 10 minutes line
    ax.axhline(10, color='black', linestyle='-', linewidth=1, alpha=0.5, label='Equilibrium Target (10 min)')
    
    # Aesthetics
    ax.set_title(f'Halving {year} (Block {h_block})', fontweight='bold')
    ax.set_xlabel('Blocks relative to Halving ($z$)')
    ax.set_ylabel('Inter-block time (minutes)')
    ax.set_ylim(0, 35) # Fixed Y-scale for visual variance comparison
    ax.set_xlim(-EPOCH/2, EPOCH) # Zoom on the event
    
    if i == 0:
        ax.legend(loc='upper left')

plt.tight_layout()
plt.savefig('fig_halvings_dynamics_revtex.pdf', format='pdf', bbox_inches='tight')
print("\n[INFO] Chart saved as 'fig_halvings_dynamics_revtex.pdf'")