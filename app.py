import streamlit as st
import matplotlib.pyplot as plt
from data_loader import load_data
from ratings import compute_all_rating
from visualization import plot_elo_evolution
import joblib
import pandas as pd
@st.cache_resource
def load_model():
    model=joblib.load('la_liga_model.joblib')
    return model

model=load_model()


st.title("La Liga Team Rating Analyzer")
st.subheader("From 2012 to 2025 August")

# Load data
df = load_data()

if 'FTR' in df.columns:
  
    df['FTR_Encoded'] = df['FTR'].map({
        'H': 2, 
        'D': 1,  
        'A': 0   
    })
else:
    
    df['FTR_Encoded'] = 1  
    df.loc[df['FTHG'] > df['FTAG'], 'FTR_Encoded'] = 2  # Home win
    df.loc[df['FTHG'] < df['FTAG'], 'FTR_Encoded'] = 0  # Away win

# Compute ratings
df = compute_all_rating(df)

def get_latest_rating(df,team_name):
    home_matches=df[df['HomeTeam']==team_name]
    away_matches=df[df['AwayTeam']==team_name]

    if len(home_matches)>0:
        latest_home=home_matches.iloc[-1]
        return {
            'elo':latest_home['home_elo_before'],
            'ts_mu':latest_home['ts_home_mu'],
            'ts_sigma':latest_home['ts_home_sigma'],
            'glicko_rating':latest_home['glicko_home_rating'],
            'glicko_rd':latest_home['glicko_home_rd']

        }
    elif len(away_matches)>0:
        latest_away=away_matches.iloc[-1]
        return {
            'elo':latest_away['away_elo_before'],
            'ts_mu':latest_away['ts_away_mu'],
            'ts_sigma':latest_away['ts_away_sigma'],
            'glicko_rating':latest_away['glicko_away_rating'],
            'glicko_rd':latest_away['glicko_away_rd']

        }
    else:
        return None
    
def get_recent_form(df,team_name,is_home=True):
    '''CALCULATE AVEARGE POINTS FROM LAST 5 MATCHES'''
    if is_home:
        matches=df[df['HomeTeam']==team_name].tail(5)
        points=[]

        for _,row in matches.iterrows():
            if row['FTR']=="H":
                points.append(3)
            elif row['FTR']=="D":
                points.append(1)
            else:
                points.append(0)
    else:
        matches=df[df['AwayTeam']==team_name].tail(5)
        points=[]
        for _,row in matches.iterrows():
            if row['FTR']=='A':
                points.append(3)
            elif row['FTR']=='D':
                points.append(1)
            else:
                points.append(0)
    return sum(points)/len(points) if points else 0

def create_features(home_team,away_team,b365h,b365d,b365a,df):

    home_rating=get_latest_rating(df,home_team)
    away_rating=get_latest_rating(df,away_team)

    if home_rating is None:
        st.error(f"Team {home_team} not found in data!")
        return None
    if away_rating is None:
        st.error(f"Team {away_team} not found in data!")
        return None
    home_form=get_recent_form(df,home_team,is_home=True)
    away_form=get_recent_form(df,away_team,is_home=False)

    elo_diff=home_rating['elo']-away_rating['elo']
    ts_mu_diff=home_rating['ts_mu']-away_rating['ts_mu']
    ts_sigma_diff=home_rating['ts_sigma']-away_rating['ts_sigma']
    glicko_diff=home_rating['glicko_rating']-away_rating['glicko_rating']

    ts_conservative_diff=(
        (home_rating['ts_mu']-3*home_rating['ts_sigma'])-
        (away_rating['ts_mu']-3*away_rating['ts_sigma'])
    )
    form_diff=home_form-away_form

    features = {
    'B365H': b365h,
    'B365A': b365a,
    'B365D': b365d,

    'home_elo_before': home_rating['elo'],
    'away_elo_before': away_rating['elo'],
    'elo_diff': elo_diff,

    'ts_home_mu': home_rating['ts_mu'],
    'ts_away_mu': away_rating['ts_mu'],
    'ts_home_sigma': home_rating['ts_sigma'],
    'ts_away_sigma': away_rating['ts_sigma'],
    'ts_mu_diff': ts_mu_diff,
    'ts_sigma_diff': ts_sigma_diff,
    'ts_conservative_diff': ts_conservative_diff,

    'glicko_home_rating': home_rating['glicko_rating'],
    'glicko_away_rating': away_rating['glicko_rating'],
    'glicko_home_rd': home_rating['glicko_rd'],
    'glicko_away_rd': away_rating['glicko_rd'],
    'glicko_diff': glicko_diff,

    'home_point_last5': home_form,
    'away_point_last5': away_form,
    'form': form_diff
}
    return features
# CREATE TAB
tab1,tab2,tab3=st.tabs(["OVERVIEW","EL CLASSICO","Prediction"])
#tab1 overview
with tab1:
    st.header('Team Rating Evolution')

    teams=st.multiselect(
        "Select teams to plot",
        df['HomeTeam'].unique(),
        default=['Barcelona','Real Madrid']
    )
    if teams:
        fig=plot_elo_evolution(df,teams)
        st.pyplot(fig)
    st.subheader('Top 10 ratings of team by elo score')
    top_teams=df.groupby('HomeTeam')['home_elo_after'].mean().sort_values(ascending=False).head(10)
    st.table(top_teams)
with tab2:
    
    st.header('EL CLASSICO: Barcelona vs Real Madrid')
    real="Real Madrid"
    barca="Barcelona"
    matches = df[
        ((df['HomeTeam']==real) & (df['AwayTeam']==barca)) |
        ((df['HomeTeam']==barca) & (df['AwayTeam']==real))
    ]
    barca_won=0
    real_won=0
    draw=0
    for _ , row in matches.iterrows():
        home=row['HomeTeam']
        away=row['AwayTeam']
        result=row['FTR']
        if result=='H' and home=='Barcelona':
            barca_won += 1
        elif result=='A' and away=='Barcelona':
            barca_won +=1
        elif result=='D':
            draw += 1
        else:
            real_won+=1
    col1 , col2 , col3 , col4   = st.columns(4)
    with col1:
         st.metric('Barcelona Wins',barca_won)
    with col2:
        st.metric('Draws',draw)
    with col3:
        st.metric('Real Madrid Wins',real_won)
    with col4:
        st.metric("TOTAL CLASHES",barca_won+real_won+draw)
    fig,ax=plt.subplots(figsize=(7,4))
    ax.set_facecolor("#0b1c2d")
    plt.gcf().patch.set_facecolor("#0b1c2d")
    teams_list=['Barcelona','Real Madrid','Draws']
    colors=['#A50044', '#808080','#FEBE10']
    result=[barca_won,real_won,draw]
    ax.bar(teams_list,result,color=colors) 
    for i , value in enumerate(result):
            ax.text(i,value+0.3,str(value),ha='center',fontsize=12,fontweight='bold')
    ax.set_title('EL CLASSICO RESULTS (2021-2025)',fontsize=16)
    ax.set_ylabel('Number of Matches',fontsize=12)
    ax.spines[['top','right']].set_visible(False)

    st.pyplot(fig)
with tab3:
    st.header("🔮 Predict Match Outcome")

    #get all teams
    all_teams=sorted(df['HomeTeam'].unique())

    #team selection
    col1,col2=st.columns(2)
    with col1:
        home_team=st.selectbox('Home Team',all_teams,index=all_teams.index('Barcelona') if 'Barcelona' in all_teams else 0)
    with col2:
        away_team=[t for t in all_teams if t != home_team]
        away_team=st.selectbox('Away Team',away_team,index=away_team.index('Real Madrid') if 'Real Madrid' in away_team else 0)

    st.subheader("Betting Odds")
    st.caption('Provide the betting odds from ANY RELIABLE PLATFORM')
    col1,col2,col3=st.columns(3)
    with col1:
        b365h=st.number_input("Home Win Odds",min_value=1.00,max_value=50.00,value=2.5,step=0.1)
    with col2:
        b365d=st.number_input("Draw Odds",min_value=1.0,max_value=50.00,value=3.0,step=0.1)
    with col3:
        b365a=st.number_input("Away Win Odds",min_value=1.0,max_value=50.00,value=2.8,step=0.1) 
    if st.button("Predict Outcome",type="primary"):
        with st.spinner('Calculating features and making prediction'):
            features=create_features(home_team,away_team,b365h,b365d,b365a,df)
            if features is not None:
                X_predict=pd.DataFrame([features])

                prediction=model.predict(X_predict)[0]
                probabilities=model.predict_proba(X_predict)[0]

                prob_not_home_win=probabilities[0]
                prob_home_win=probabilities[1]
                confidence=max(prob_home_win,prob_not_home_win)
                st.success(f"Prediction Complete !!!!")

                col1,col2,col3=st.columns(3)
                with col1:
                    st.metric('Home Win Probablities',f"{prob_home_win:.2%}")
                with col2:
                    st.metric('Not Home Win Probabilities',f"{prob_not_home_win:.2%}")
                with col3:
                    st.metric('Model Confidence',f"{confidence:.2%}")
                if prediction==1:
                    st.balloons()
                    st.success(f"### Prediction **{home_team}** will win at home!")
                else:
                    st.info(f"### Prediction **{home_team}** will NOT win at home!")

                st.subheader('Teams Comparison')

                col1,col2=st.columns(2)

                home_ratings=get_latest_rating(df,home_team)
                away_ratings=get_latest_rating(df,away_team)

                with col1:
                    st.write(f"**{home_team}**(Home)")
                    st.write(f"ELO SCORE: {home_ratings['elo']:.2f}")
                    st.write(f"TrueSkill : {home_ratings['ts_mu']:.1f}")
                    st.write(f"Glicko Rating: {home_ratings['glicko_rating']:.1f}")
                    st.write(f"Form (last 5): {features['home_point_last5']:.2f} points per game")

                with col2:
                    st.write(f"**{away_team}**(Away)")
                    st.write(f"ELO SCORE: {away_ratings['elo']:.2f}")
                    st.write(f"TrueSkill : {away_ratings['ts_mu']:.1f}")
                    st.write(f"Glicko Rating: {away_ratings['glicko_rating']:.1f}")
                    st.write(f"Form (last 5): {features['away_point_last5']:.2f} points per game")

