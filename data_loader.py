import pandas as pd
def load_data(file_path='final_laliga.csv'):
    df=pd.read_csv(file_path)
    return df