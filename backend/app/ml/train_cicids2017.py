import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

def train_and_save_model(csv_path: str, output_path: str):
    print("Leyendo archivo CSV CIC-IDS2017...")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    

    features = [
        'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
        'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
        'Fwd Packet Length Mean', 'Bwd Packet Length Mean',
        'Flow Bytes/s', 'Flow Packets/s', 'Packet Length Mean',
        'Packet Length Std', 'Average Packet Size', 'Avg Fwd Segment Size',
        'Avg Bwd Segment Size', 'Init_Win_bytes_forward', 'Init_Win_bytes_backward'
    ]

    # Limpia datos faltantes o infinitos
    df = df.replace([np.inf, -np.inf], 0).dropna(subset=features + ['Label'])

    # Convierte la etiqueta a binaria
    df['Label'] = (df['Label'] != 'BENIGN').astype(int)

    X = df[features]
    y = df['Label']

    print("Entrenando modelo RandomForest...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("Guardando modelo en:", output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)

    print("Modelo entrenado y guardado.")

if __name__ == "__main__":
    train_and_save_model(
        csv_path=r"C:\Users\USER-PC\Downloads\MachineLearningCSV\MachineLearningCVE\Wednesday-workingHours.pcap_ISCX.csv",
        output_path="backend/app/ml/rf_cicids2017_model.pkl"
    )