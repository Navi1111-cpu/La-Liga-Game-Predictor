import streamlit as st
import matplotlib.pyplot as plt
from data_loader import load_data
from ratings import compute_all_rating
from visualization import plot_elo_evolution

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

# CREATE TAB
tab1,tab2,tab3=st.tabs(["OVERVIEW","EL CLASSICO","MORE TO FOLLOW"])
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
    
