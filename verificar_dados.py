#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar se os dados de churn estão disponíveis
"""

import os
import pandas as pd
from config_churn import OUTPUT_DIR, CHURN_ANALYSIS_FILE, ENCODING

def verificar_dados():
    """Verifica se os dados de churn estão disponíveis."""
    print("Verificando dados de churn...")
    
    # Verificar diretório
    if not os.path.exists(OUTPUT_DIR):
        print(f"ERRO: Diretorio nao encontrado: {OUTPUT_DIR}")
        return False
    
    print(f"OK: Diretorio encontrado: {OUTPUT_DIR}")
    
    # Verificar arquivo parquet
    arquivo_parquet = os.path.join(OUTPUT_DIR, CHURN_ANALYSIS_FILE)
    if os.path.exists(arquivo_parquet):
        print(f"OK: Arquivo parquet encontrado: {arquivo_parquet}")
        try:
            df = pd.read_parquet(arquivo_parquet, engine='pyarrow')
            print(f"OK: Dados carregados: {len(df)} laboratorios")
            return True
        except Exception as e:
            print(f"ERRO ao carregar parquet: {e}")
    
    # Verificar arquivo CSV
    arquivo_csv = os.path.join(OUTPUT_DIR, "churn_analysis_latest.csv")
    if os.path.exists(arquivo_csv):
        print(f"OK: Arquivo CSV encontrado: {arquivo_csv}")
        try:
            df = pd.read_csv(arquivo_csv, encoding=ENCODING, low_memory=False)
            print(f"OK: Dados carregados (CSV): {len(df)} laboratorios")
            return True
        except Exception as e:
            print(f"ERRO ao carregar CSV: {e}")
    
    print("ERRO: Nenhum arquivo de analise encontrado")
    return False

if __name__ == "__main__":
    if verificar_dados():
        print("\nDados disponiveis! Voce pode executar o Streamlit.")
    else:
        print("\nDados nao encontrados! Execute o gerador de dados primeiro.")
        print("Execute: python gerador_dados_churn.py")
