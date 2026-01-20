import pandas as pd
import os

def load_data():
    file_path=os.path.join('data','final_laliga.csv')
    df=pd.read_csv(file_path)
    return df