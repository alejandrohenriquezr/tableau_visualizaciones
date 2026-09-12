import pandas as pd

class BaseExtractor:  # <-- Asegúrate de que esté escrito exactamente así
    def __init__(self, name: str):
        self.name = name

    def fetch_raw_data(self) -> dict:
        raise NotImplementedError("Cada extractor debe implementar fetch_raw_data")

    def transform(self, raw_data: dict) -> pd.DataFrame:
        raise NotImplementedError("Cada extractor debe implementar transform")

    def run(self) -> pd.DataFrame:
        print(f" Iniciando extracción para: {self.name}")
        raw = self.fetch_raw_data()
        df = self.transform(raw)
        print(f" Transformación exitosa. Filas obtenidas: {len(df)}")
        return df
