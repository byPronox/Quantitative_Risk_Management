import bz2
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import IsolationForest
import joblib
import os

def train_and_save_model(bz2_path: str, output_path: str):
    print("Leyendo archivo BZ2...")
    with bz2.open(bz2_path, 'rt') as f:
        df = pd.read_csv(f, header=None, names=["timestamp", "user", "computer"])

    print("Codificando usuarios y computadores...")
    user_encoder = LabelEncoder()
    computer_encoder = LabelEncoder()
    df['user_encoded'] = user_encoder.fit_transform(df['user'])
    df['computer_encoded'] = computer_encoder.fit_transform(df['computer'])

    X = df[['timestamp', 'user_encoded', 'computer_encoded']]

    print("Entrenando modelo...")
    model = IsolationForest(contamination=0.01, random_state=42)    
    df['anomaly'] = model.fit_predict(X)

    print("Guardando modelo en:", output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump({
        "model": model,
        "user_encoder": user_encoder,
        "computer_encoder": computer_encoder
    }, output_path)

    print(f"Modelo guardado. Anomalías detectadas: {(df['anomaly'] == -1).sum()}")
    print(df[df['anomaly'] == -1].head())

if __name__ == "__main__":
    train_and_save_model(
        bz2_path=r"C:\Users\USER-PC\Downloads\lanl-auth-dataset-1-00.bz2",
        output_path="backend/app/ml/isolation_forest_model.pkl"
    )