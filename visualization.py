import matplotlib.pyplot as plt
import pandas as pd

def plot_elo_evolution(df, teams):
    plt.figure(figsize=(10, 6))

    for team in teams:
        # Home matches
        home = df[df['HomeTeam'] == team][
            ['Date', 'home_elo_after']
        ].rename(columns={'home_elo_after': 'elo'})

        # Away matches
        away = df[df['AwayTeam'] == team][
            ['Date', 'away_elo_after']
        ].rename(columns={'away_elo_after': 'elo'})

        # Combine and sort chronologically
        team_data = pd.concat([home, away]).sort_values('Date')

        # Plot Elo
        plt.plot(team_data['elo'].values, label=team)

    plt.xlabel('Match Number')
    plt.ylabel('Elo Rating')
    plt.title('Elo Rating Evolution')
    plt.legend()

    return plt
