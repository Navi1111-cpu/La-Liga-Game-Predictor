import pandas as pd
import numpy as np
from trueskill import Rating , rate_1vs1 , TrueSkill
from glicko2 import Player

def calculate_elo(df):
    rating={}
    k_factor=[]
    home_elo_before=[]
    away_elo_before=[]
    home_elo_after=[]
    away_elo_after=[]
    Home_advantage=50

    def get_k(games_played):
        """
        Dynamic K-Factor Based on number of games played
        - New teams (<10 games): k=40 (rating adjusted quickly)
        - Developing teams (10-30 games): k=30
        - Estalished teams (>30 games): k=20
        """
        if games_played<10:
            return 40
        elif games_played <30:
            return 30
        else:
            return 20

    def convert_result_to_proper_elo(encoded_result):
        """
        Convert encoded result to elo score from home teams perceptive
        assuming A=0,D=1,H=2
        return:0(loss),0.5(draw),1(win)
        """
        if encoded_result == 0:
            return 0
        elif encoded_result==1:
            return 0.5
        elif encoded_result==2:
            return 1
        else:
            raise ValueError(f'Unexpected result value:{encoded_result}')

    games_played={}
    for index , row in df.iterrows():
        home=row['HomeTeam']
        away=row['AwayTeam']
        encoded_result=row['FTR_Encoded']
        result=convert_result_to_proper_elo(encoded_result)
        
        rh=rating.setdefault(home,1500)
        ra=rating.setdefault(away,1500)
        
        games_played.setdefault(home,0)
        games_played.setdefault(away,0)
        
        rh_adjusted=rh+Home_advantage
        home_elo_before.append(rh)
        away_elo_before.append(ra)
        eh=1/(1+10**((ra-rh_adjusted)/400))
        ea=1-eh
        k_home=get_k(games_played[home])
        k_away=get_k(games_played[away])
        k=(k_home+k_away)/2
        k_factor.append(k)
        

        
        rh_new=rh+k*(result-eh)
        ra_new=ra+k*((1-result)-(1-eh))
        
        rating[home]=rh_new
        rating[away]=ra_new
        games_played[home]+=1
        games_played[away]+=1
        home_elo_after.append(rh_new)
        away_elo_after.append(ra_new)

    df['home_elo_before']=home_elo_before
    df['away_elo_before']=away_elo_before
    df['home_elo_after']=home_elo_after
    df['away_elo_after']=away_elo_after
    df['k_factor']=k_factor

    for team, elo in sorted(rating.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{team}: {elo:.0f} (played {games_played[team]} games)")

    df['elo_diff']=df['home_elo_before']-df['away_elo_before']
    print(df['elo_diff'])
    return df

##true skill 

def calculate_trueskill(df):
    env=TrueSkill(draw_probability=0.25)
    ts_rating={}
    home_mu=[]
    away_mu=[]
    home_sigma=[]
    away_sigma=[]
    for index , row in df.iterrows():
        home=row['HomeTeam']
        away=row['AwayTeam']
        result=row['FTR_Encoded']
        ts_rating.setdefault(home,Rating())
        ts_rating.setdefault(away,Rating())
        r_home=ts_rating[home]
        r_away=ts_rating[away]
        home_mu.append(r_home.mu)
        away_mu.append(r_away.mu)
        home_sigma.append(r_home.sigma)
        away_sigma.append(r_away.sigma)

        if result==2:
            ts_rating[home],ts_rating[away]=rate_1vs1(r_home,r_away)
        elif result==0:
            ts_rating[away],ts_rating[home]=rate_1vs1(r_away,r_home)
        else:
            ts_rating[home],ts_rating[away]=rate_1vs1(r_home,r_away,drawn=True)

    df['ts_home_mu']=home_mu
    df['ts_away_mu']=away_mu
    df['ts_home_sigma']=home_sigma
    df['ts_away_sigma']=away_sigma
    df['ts_mu_diff']=df['ts_home_mu']-df['ts_away_mu']
    df['ts_sigma_diff']=df['ts_home_sigma']-df['ts_away_sigma']
    df['ts_conservative_diff']=(
        (df['ts_home_mu']-3*df['ts_home_sigma'])-
        (df['ts_away_mu']-3*df['ts_away_sigma'])
    )
    return df
def calculate_glicko(df):
    glicko={}
    g_home_rating=[]
    g_away_rating=[]
    g_home_rd=[]
    g_away_rd=[]
    def glicko_result(encode):
        if encode==2:
            return 1
        elif encode==1:
            return 0.5
        else:
            return 0

    for index , row in df.iterrows():
        home=row['HomeTeam']
        away=row['AwayTeam']
        result=glicko_result(row['FTR_Encoded'])
        glicko.setdefault(home,Player())
        glicko.setdefault(away,Player())
        h=glicko[home]
        a=glicko[away]
        g_home_rating.append(h.rating)
        g_away_rating.append(a.rating)
        g_home_rd.append(h.rd)
        g_away_rd.append(a.rd)
        h.update_player([a.rating],[a.rd],[result])
        a.update_player([h.rating],[h.rd],[1-result])

    df["glicko_home_rating"] = g_home_rating
    df["glicko_away_rating"] = g_away_rating
    df["glicko_home_rd"] = g_home_rd
    df["glicko_away_rd"] = g_away_rd

    df["glicko_diff"] = df["glicko_home_rating"] - df["glicko_away_rating"]
    return df

def compute_all_rating(df):
    df=calculate_elo(df)
    df=calculate_trueskill(df)
    df=calculate_glicko(df)
    return df
