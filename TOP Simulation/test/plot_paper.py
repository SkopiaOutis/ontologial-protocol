import pandas as pd
import matplotlib.pyplot as plt

# Style-Setup
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({'font.family': 'serif', 'font.size': 12})

def plot_simulation_results(csv_file="simulation_data.csv"):
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Fehler: {csv_file} nicht gefunden.")
        return

    # PLOT 1: Thermodynamics (Supply vs Burn)
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(df['Epoch'], df['Total_Burn'], label='Accumulated Burn', color='#d62728', linestyle='--')
    ax1.plot(df['Epoch'], df['Liquid_Supply'], label='Liquid Supply ($M_{liq}$)', color='#1f77b4')
    ax1.set_title('Figure 1: Thermodynamic Bounding')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Volume')
    ax1.legend()
    plt.savefig('fig1_thermo.png', dpi=300)
    print("Generated fig1_thermo.png")

    # PLOT 2: Sybil Resistance (ROI)
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    # ROI = (Income - Burn) / Burn. 
    # Achtung: Wenn Burn=0 (unwahrscheinlich im Test), Division abfangen.
    # Wir nutzen hier die rohen Income Werte zur Visualisierung der Schere.
    ax2.plot(df['Epoch'], df['Income_Hans'], label='Honest Node Income', color='green')
    ax2.plot(df['Epoch'], df['Income_Sybil'], label='Sybil Attack Income', color='red')
    ax2.set_title('Figure 2: Income Gap (Honest vs Sybil)')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Income per Epoch')
    ax2.legend()
    plt.savefig('fig2_sybil.png', dpi=300)
    print("Generated fig2_sybil.png")

    # PLOT 3: Price Homeostasis
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    ax3.plot(df['Epoch'], df['Price_Food'], label='Price (Food)', color='orange')
    ax3.plot(df['Epoch'], df['Backlog_Food'], label='Backlog (Demand Shock)', color='gray', alpha=0.5, linestyle=':')
    ax3.set_title('Figure 3: Price Response to Demand')
    ax3.set_xlabel('Epoch')
    ax3.legend()
    plt.savefig('fig3_price.png', dpi=300)
    print("Generated fig3_price.png")

if __name__ == "__main__":
    plot_simulation_results()