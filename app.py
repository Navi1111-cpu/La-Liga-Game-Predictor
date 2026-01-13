import streamlit as st
from data_loader import load_data
from ratings import compute_all_rating
from visualization import plot_elo_evolution

st.title("La Liga Team Rating Analyzer")
st.subheader("From 2012 to 2025 August")

# Load data
df = load_data()

if 'FTR' in df.columns:
    # If you have FTR column (H/D/A format)
    df['FTR_Encoded'] = df['FTR'].map({
        'H': 2,  # Home win
        'D': 1,  # Draw
        'A': 0   # Away win
    })
else:
    # If you need to create it from goals
    df['FTR_Encoded'] = 1  # Default draw
    df.loc[df['FTHG'] > df['FTAG'], 'FTR_Encoded'] = 2  # Home win
    df.loc[df['FTHG'] < df['FTAG'], 'FTR_Encoded'] = 0  # Away win

# Compute ratings
df = compute_all_rating(df)

# Sidebar for user input
teams = st.multiselect("Select teams to plot", df['HomeTeam'].unique(), default=['Real Madrid', 'Barcelona', 'Ath Madrid'])

# Display DataFrame
st.dataframe(df.head())

# Plot
if teams:
    fig = plot_elo_evolution(df, teams)
    st.pyplot(fig)

# Additional features: e.g., top teams table
top_teams = df.groupby('HomeTeam')['home_elo_after'].mean().sort_values(ascending=False).head(10)
st.table(top_teams)