import pandas as pd
import numpy as np
import scipy.stats as stats
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
MAX_ANTICIPATION_EPOCHS = 14 # Test up to ~6.5 months back
BASELINE_DURATION = 6 * EPOCH # Set a 3-month baseline before anticipation for comparison

HALVINGS = [
    {"year": 2012, "block": 210000},
    {"year": 2016, "block": 420000},
    {"year": 2020, "block": 630000},
    {"year": 2024, "block": 840000}
]

MASTER_CSV_FILE = "bitcoindata.csv"

print("=== LOADING LOCAL DATASET ===")
try:
    df = pd.read_csv(MASTER_CSV_FILE)
    if 'number' in df.columns:
        df.rename(columns={'number': 'height'}, inplace=True)
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('height').reset_index(drop=True)
    df['delta_t'] = df['timestamp'].diff().dt.total_seconds().clip(lower=0) / 60.0
    
    print(f"[{len(df)} blocks loaded and processed successfully.]\n")
except FileNotFoundError:
    print(f"ERROR: File {MASTER_CSV_FILE} not found.")
    exit()

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

print("=== ANTICIPATION HORIZON SENSITIVITY ANALYSIS ===")

for i, h in enumerate(HALVINGS):
    h_block = h["block"]
    year = h["year"]
    daa_block = h_block + (EPOCH - (h_block % EPOCH))
    
    print(f"\n{'-'*50}\nHALVING {year} (Block {h_block})\n{'-'*50}")
    print(f"{'Epochs':<8} | {'Var Anticip':<12} | {'Var Quench':<12} | {'Delta Var %':<12} | {'P-Fisher':<12} | {'P-Levene'}")
    
    best_p_fisher = 1.0
    optimal_epochs = 1
    sweep_results = []
    
    # 1. SWEEP OF ANTICIPATION EPOCHS
    for k in range(1, MAX_ANTICIPATION_EPOCHS + 1):
        anticipation_start = h_block - (k * EPOCH)
        
        # Phase extraction
        mask_anticip = (df['height'] >= anticipation_start) & (df['height'] < h_block)
        mask_quench = (df['height'] >= h_block) & (df['height'] < daa_block)
        
        phase_anticip = df[mask_anticip]['delta_t'].dropna()
        phase_quench = df[mask_quench]['delta_t'].dropna()
        
        if len(phase_anticip) < 100 or len(phase_quench) < 100:
            continue
            
        var_ant = phase_anticip.var(ddof=1)
        var_q = phase_quench.var(ddof=1)
        
        # Delta Variance calculation
        delta_var_pct = ((var_q - var_ant) / var_ant) * 100
        
        # Statistical Tests (Anticipation vs Quench)
        F_stat = var_q / var_ant if var_q > var_ant else var_ant / var_q
        n_ant, n_q = len(phase_anticip), len(phase_quench)
        p_fisher = stats.f.sf(F_stat, n_q - 1, n_ant - 1) * 2 # Two-tailed
        
        stat_levene, p_levene = stats.levene(phase_anticip, phase_quench, center='median')
        
        print(f"{k:<8} | {var_ant:<12.2f} | {var_q:<12.2f} | {delta_var_pct:>8.2f} %  | {p_fisher:<12.4e} | {p_levene:.4e}")
        
        # Save if it's the strongest Quench signal (minimum p_fisher)
        if p_fisher < best_p_fisher and delta_var_pct > 0: # Looking for a variance explosion
            best_p_fisher = p_fisher
            optimal_epochs = k
            
    print(f"--> Optimal Horizon Selected for plot: {optimal_epochs} Epochs (~{optimal_epochs * 2} weeks)")

    # 2. PLOT GENERATION WITH OPTIMAL HORIZON
    opt_anticipation_start = h_block - (optimal_epochs * EPOCH)
    opt_baseline_start = opt_anticipation_start - BASELINE_DURATION
    
    mask_plot = (df['height'] >= opt_baseline_start) & (df['height'] <= daa_block + EPOCH)
    df_plot = df[mask_plot].dropna(subset=['delta_t']).copy()
    
    ax = axes[i]
    df_plot['relative_height'] = df_plot['height'] - h_block
    window = 144
    
    df_plot['rolling_mean'] = df_plot['delta_t'].rolling(window=window, center=True).mean()
    df_plot['rolling_std'] = df_plot['delta_t'].rolling(window=window, center=True).std()
    
    ax.plot(df_plot['relative_height'], df_plot['rolling_mean'], color='#1f77b4', linewidth=2, label=r'$\langle \Delta t \rangle$ (Avg 144)')
    ax.fill_between(df_plot['relative_height'], 
                    df_plot['rolling_mean'] - df_plot['rolling_std'], 
                    df_plot['rolling_mean'] + df_plot['rolling_std'], 
                    color='#1f77b4', alpha=0.2)
                    
    # Lines
    ax.axvline(-optimal_epochs * EPOCH, color='#ff7f0e', linestyle='-.', linewidth=2, label=f'Anticipation (-{optimal_epochs} ep)')
    ax.axvline(0, color='#d62728', linestyle='--', linewidth=2, label='Quench (Halving)')
    ax.axvline(daa_block - h_block, color='#2ca02c', linestyle=':', linewidth=2, label='DAA')
    ax.axhline(10, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    ax.set_title(f'Halving {year} (Optimal Horizon: {optimal_epochs} ep)', fontweight='bold')
    ax.set_xlabel('Blocks relative to Halving ($z$)')
    ax.set_ylabel('Inter-block time (min)')
    ax.set_ylim(0, 35) 
    ax.set_xlim(-optimal_epochs * EPOCH * 1.5, EPOCH * 1.5)
    if i == 0:
        ax.legend(loc='upper left')

plt.tight_layout()
plt.savefig('fig_halvings_sensitivity_revtex.pdf', format='pdf', bbox_inches='tight')
print("\n[INFO] Plot saved as 'fig_halvings_sensitivity_revtex.pdf'")