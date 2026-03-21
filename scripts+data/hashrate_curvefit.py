import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.ticker import FuncFormatter, NullFormatter
from datetime import timedelta

# --- GRAPHIC CONFIGURATION (APS/RevTeX style) ---
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

print("=== FETCHING HASHRATE DATA ===")
URL = "https://api.blockchain.info/charts/hash-rate?timespan=all&format=json"
response = requests.get(URL)
data = response.json()

df = pd.DataFrame(data['values'])
df.columns = ['timestamp', 'hashrate_THs']
df['date'] = pd.to_datetime(df['timestamp'], unit='s')

df = df[df['hashrate_THs'] > 0].copy()
start_date = df['date'].min()
df['days_since_start'] = (df['date'] - start_date).dt.total_seconds() / (24 * 3600)
df = df[df['days_since_start'] > 0].copy()

# --- HALVING DATES ---
halving_dates = pd.to_datetime(['2012-11-28', '2016-07-09', '2020-05-11', '2024-04-19'])
halving_days = (halving_dates - start_date).total_seconds() / (24 * 3600)

# --- FIT CALCULATION (Starting Jan 2010) ---
fit_start_date = pd.to_datetime('2010-01-01')
print(f"=== CALCULATING POWER-LAW FIT (Starting {fit_start_date.strftime('%Y-%m')}) ===")

# Filter data starting from Jan 1st, 2010
df_fit = df[df['date'] >= fit_start_date].copy()

t_fit = df_fit['days_since_start'].values
H_fit_data = df_fit['hashrate_THs'].values

log_t_fit = np.log10(t_fit)
log_H_fit = np.log10(H_fit_data)

def power_law_log(log_t, alpha, log_C):
    return alpha * log_t + log_C

# Perform the linear regression in log-log space
popt, pcov = curve_fit(power_law_log, log_t_fit, log_H_fit)
alpha, log_C = popt
C = 10**log_C

# Calculate R-squared
log_H_pred = power_law_log(log_t_fit, alpha, log_C)
r_squared = 1 - (np.sum((log_H_fit - log_H_pred)**2) / np.sum((log_H_fit - np.mean(log_H_fit))**2))

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(10, 6))

t_all = df['days_since_start'].values
H_trend = C * (t_all**alpha)

# 1. Raw Data
ax.plot(t_all, df['hashrate_THs'], color='#1f77b4', alpha=0.6, linewidth=1.5, label='Raw Hashrate')

# 2. Power-Law Fit Line
fit_label = f'Power-Law Fit ($t >$ Jan 2010): $H(t) = {C:.1e} \\cdot t^{{{alpha:.2f}}}$ ($R^2={r_squared:.3f}$)'
ax.plot(t_all, H_trend, color='#d62728', linestyle='--', linewidth=2.5, label=fit_label)

# 3. Halvings
for i, h_day in enumerate(halving_days):
    if h_day <= t_all[-1]:
        label = 'Halving' if i == 0 else ""
        ax.axvline(x=h_day, color='#2ca02c', linestyle=':', linewidth=1.5, alpha=0.8, label=label)

# --- CUSTOM LOG DATE AXIS ---
ax.set_xscale('log')
ax.set_yscale('log')

def format_date(x, pos):
    if x <= 0: return ""
    d = start_date + timedelta(days=float(x))
    return d.strftime('%Y-%m')

ax.xaxis.set_major_formatter(FuncFormatter(format_date))

# Define specific year ticks
tick_dates = pd.to_datetime(['2010-01-01', '2012-01-01', '2015-01-01', '2018-01-01', '2021-01-01', '2024-01-01', '2026-01-01'])
tick_days = (tick_dates - start_date).total_seconds() / (24 * 3600)
ax.set_xticks(tick_days)
ax.xaxis.set_minor_formatter(NullFormatter())

# -------------------------------------------------------------------
# FIX POUR LE CHEVAUCHEMENT (OVERLAP) DES DATES
# Option 1 (Activée) : Rotation à 45 degrés (Standard académique propre)
plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

# Option 2 (Désactivée) : Décalage en Y en quinconce (Ce que vous avez suggéré)
# Décommentez les 3 lignes suivantes et commentez l'Option 1 si vous préférez cette approche
# for i, tick in enumerate(ax.xaxis.get_major_ticks()):
#     tick.set_pad(15 if i % 2 != 0 else 4) # Baisse une date sur deux
# -------------------------------------------------------------------

ax.set_title('Secular Exergetic Expansion (Log-Log Scale)', fontweight='bold')
ax.set_xlabel('Time (YYYY-MM)')
ax.set_ylabel('Network Hashrate $H(t)$ [TH/s]')

ax.grid(True, which="major", ls="-", alpha=0.3)
ax.grid(True, which="minor", ls=":", alpha=0.2)
ax.legend(loc='lower right')

plt.tight_layout() # Empêche les dates tournées d'être coupées en bas
plt.savefig('fig_hashrate_powerlaw_revtex.pdf', format='pdf')
print(f"=== COMPLETED! Alpha: {alpha:.4f}, R2: {r_squared:.4f} ===")