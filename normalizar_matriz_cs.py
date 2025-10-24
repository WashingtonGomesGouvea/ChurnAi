#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Normalização da Matriz CS 2025
========================================

Este script normaliza os dados do arquivo Excel "Matriz CS 2025 ATUAL.xlsx",
corrigindo problemas de formatação, espaços extras, e padronizando valores
para melhor integração com o sistema de análise de churn.

Principais normalizações:
- Ranking Rede: Remove espaços, pontos, converte para maiúsculas
- CNPJ: Remove pontuação e normaliza formato
- Outros campos: Remove espaços extras, normaliza capitalização
"""

import os
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

# Configurações de log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('normalizar_matriz_cs.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MatrizCSNormalizer:
    """Normalizador da Matriz CS 2025."""
    
    # Categorias fixas para Ranking Rede
    CATEGORIAS_RANKING_REDE = {
        'BRONZE': ['bronze', 'bronze ', 'bronze.', 'BRONZE', 'Bronze'],
        'PRATA': ['prata', 'prata ', 'prata.', 'PRATA', 'Prata'],
        'OURO': ['ouro', 'ouro ', 'ouro.', 'OURO', 'Ouro'],
        'DIAMANTE': ['diamante', 'diamante ', 'diamante.', 'DIAMANTE', 'Diamante'],
        'DELETADO': ['deletado', 'deletado ', 'deletado.', 'DELETADO', 'Deletado'],
        'INATIVO': ['inativo', 'inativo ', 'inativo.', 'INATIVO', 'Inativo'],
        'IM': ['im', 'im ', 'im.', 'IM', 'Im']
    }
    
    # Categorias fixas para Ranking individual
    CATEGORIAS_RANKING = {
        'BRONZE': ['bronze', 'bronze ', 'bronze.', 'BRONZE', 'Bronze'],
        'PRATA': ['prata', 'prata ', 'prata.', 'PRATA', 'Prata'],
        'OURO': ['ouro', 'ouro ', 'ouro.', 'OURO', 'Ouro'],
        'DIAMANTE': ['diamante', 'diamante ', 'diamante.', 'DIAMANTE', 'Diamante']
    }
    
    def __init__(self, arquivo_excel: str, diretorio_saida: str):
        """
        Inicializa o normalizador.
        
        Args:
            arquivo_excel: Caminho para o arquivo Excel original
            diretorio_saida: Diretório onde salvar o CSV normalizado
        """
        self.arquivo_excel = arquivo_excel
        self.diretorio_saida = diretorio_saida
        self.normalizacoes_realizadas = []
        
    def normalizar_cnpj(self, cnpj: str) -> str:
        """
        Normaliza CNPJ removendo pontuação e garantindo 14 dígitos.
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            CNPJ apenas com números (14 dígitos, com zeros à esquerda se necessário)
        """
        if pd.isna(cnpj) or cnpj == '':
            return ''
        
        # Converter numéricos para string sem decimais (evita sufixo '.0')
        if isinstance(cnpj, (int, float)):
            try:
                cnpj = str(int(cnpj))
            except Exception:
                cnpj = str(cnpj)

        # Remove tudo exceto dígitos
        cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
        
        # Garantir que tenha exatamente 14 dígitos, preenchendo com zeros à esquerda se necessário
        if len(cnpj_limpo) < 14:
            cnpj_limpo = cnpj_limpo.zfill(14)
        elif len(cnpj_limpo) > 14:
            # Se tiver mais de 14 dígitos, pegar apenas os últimos 14
            cnpj_limpo = cnpj_limpo[-14:]
        
        return cnpj_limpo
    
    def normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto removendo espaços extras e normalizando capitalização.
        
        Args:
            texto: Texto a ser normalizado
            
        Returns:
            Texto normalizado
        """
        if pd.isna(texto) or texto == '':
            return ''
        
        # Remove espaços extras e quebras de linha
        texto_limpo = re.sub(r'\s+', ' ', str(texto).strip())
        return texto_limpo
    
    def mapear_ranking_rede(self, valor: str) -> str:
        """
        Mapeia valor de Ranking Rede para categoria fixa.
        
        Args:
            valor: Valor original do Ranking Rede
            
        Returns:
            Categoria normalizada
        """
        if pd.isna(valor) or valor == '':
            return ''
        
        valor_limpo = str(valor).strip()
        
        # Buscar em todas as categorias
        for categoria, variacoes in self.CATEGORIAS_RANKING_REDE.items():
            if valor_limpo in variacoes:
                return categoria
        
        # Se não encontrou, retornar valor limpo em maiúsculas
        return valor_limpo.upper()
    
    def mapear_ranking(self, valor: str) -> str:
        """
        Mapeia valor de Ranking para categoria fixa.
        
        Args:
            valor: Valor original do Ranking
            
        Returns:
            Categoria normalizada
        """
        if pd.isna(valor) or valor == '':
            return ''
        
        valor_limpo = str(valor).strip()
        
        # Buscar em todas as categorias
        for categoria, variacoes in self.CATEGORIAS_RANKING.items():
            if valor_limpo in variacoes:
                return categoria
        
        # Se não encontrou, retornar valor limpo em maiúsculas
        return valor_limpo.upper()
    
    def normalizar_telefone(self, telefone: str) -> str:
        """
        Normaliza número de telefone.
        
        Args:
            telefone: Número de telefone original
            
        Returns:
            Telefone normalizado
        """
        if pd.isna(telefone) or telefone == '':
            return ''
        
        # Remove tudo exceto dígitos, parênteses, hífens e espaços
        telefone_limpo = re.sub(r'[^\d\s\(\)\-]', '', str(telefone))
        return telefone_limpo.strip()
    
    def criar_backup(self) -> str:
        """
        Cria backup do arquivo Excel original.
        
        Returns:
            Caminho do arquivo de backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_backup = f"Matriz_CS_2025_BACKUP_{timestamp}.xlsx"
        caminho_backup = os.path.join(self.diretorio_saida, nome_backup)
        
        try:
            # Copiar arquivo original para backup
            import shutil
            shutil.copy2(self.arquivo_excel, caminho_backup)
            logger.info(f"Backup criado: {caminho_backup}")
            return caminho_backup
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return ""
    
    def carregar_excel(self) -> Optional[pd.DataFrame]:
        """
        Carrega dados do arquivo Excel.
        
        Returns:
            DataFrame com os dados ou None se houver erro
        """
        try:
            logger.info(f"Carregando arquivo: {self.arquivo_excel}")
            # Usar converters para CNPJ evitar leitura como float e perda de zeros à esquerda
            df = pd.read_excel(
                self.arquivo_excel,
                engine='openpyxl',
                converters={
                    'CNPJ': lambda v: (
                        '' if pd.isna(v) else (
                            str(int(v)) if isinstance(v, (int, float)) else str(v).strip()
                        )
                    )
                }
            )
            logger.info(f"Dados carregados: {len(df)} registros, {len(df.columns)} colunas")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar Excel: {e}")
            return None
    
    def normalizar_dados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica todas as normalizações nos dados.
        
        Args:
            df: DataFrame original
            
        Returns:
            DataFrame normalizado
        """
        logger.info("Iniciando normalização dos dados...")
        df_normalizado = df.copy()
        
        # Normalizar CNPJ
        if 'CNPJ' in df_normalizado.columns:
            logger.info("Normalizando CNPJs...")
            df_normalizado['CNPJ'] = df_normalizado['CNPJ'].apply(self.normalizar_cnpj)
            self.normalizacoes_realizadas.append("CNPJ: Removida pontuação")
        
        # Normalizar Ranking Rede
        if 'Ranking Rede' in df_normalizado.columns:
            logger.info("Normalizando Ranking Rede...")
            valores_originais = df_normalizado['Ranking Rede'].value_counts()
            df_normalizado['Ranking Rede'] = df_normalizado['Ranking Rede'].apply(self.mapear_ranking_rede)
            valores_normalizados = df_normalizado['Ranking Rede'].value_counts()
            
            # Log das normalizações
            for valor_orig, count in valores_originais.items():
                if pd.notna(valor_orig) and valor_orig != '':
                    valor_norm = self.mapear_ranking_rede(valor_orig)
                    if valor_orig != valor_norm:
                        self.normalizacoes_realizadas.append(f"Ranking Rede: '{valor_orig}' → '{valor_norm}' ({count} registros)")
        
        # Normalizar Ranking individual
        if 'Ranking' in df_normalizado.columns:
            logger.info("Normalizando Ranking...")
            valores_originais = df_normalizado['Ranking'].value_counts()
            df_normalizado['Ranking'] = df_normalizado['Ranking'].apply(self.mapear_ranking)
            valores_normalizados = df_normalizado['Ranking'].value_counts()
            
            # Log das normalizações
            for valor_orig, count in valores_originais.items():
                if pd.notna(valor_orig) and valor_orig != '':
                    valor_norm = self.mapear_ranking(valor_orig)
                    if valor_orig != valor_norm:
                        self.normalizacoes_realizadas.append(f"Ranking: '{valor_orig}' → '{valor_norm}' ({count} registros)")
        
        # Normalizar campos de texto
        campos_texto = ['RAZÃO SOCIAL', 'NOME FANTASIA', 'Cidade ', 'UF', 'Contato PCL', 'REP', 'CS', 'STATUS', 'Rede']
        for campo in campos_texto:
            if campo in df_normalizado.columns:
                df_normalizado[campo] = df_normalizado[campo].apply(self.normalizar_texto)
        
        # Normalizar telefone
        if 'Whatsapp/telefone' in df_normalizado.columns:
            df_normalizado['Whatsapp/telefone'] = df_normalizado['Whatsapp/telefone'].apply(self.normalizar_telefone)
        
        logger.info(f"Normalização concluída. {len(self.normalizacoes_realizadas)} tipos de normalização realizadas.")
        return df_normalizado
    
    def salvar_csv(self, df: pd.DataFrame) -> str:
        """
        Salva DataFrame normalizado como CSV.
        
        Args:
            df: DataFrame normalizado
            
        Returns:
            Caminho do arquivo CSV salvo
        """
        try:
            # Criar diretório se não existir
            os.makedirs(self.diretorio_saida, exist_ok=True)
            
            # Caminho do arquivo CSV
            caminho_csv = os.path.join(self.diretorio_saida, "matriz_cs_normalizada.csv")
            
            # Garantir que CNPJ seja salvo como string para preservar zeros à esquerda
            df_salvar = df.copy()
            if 'CNPJ' in df_salvar.columns:
                # Forçar string e preservar zeros à esquerda
                df_salvar['CNPJ'] = df_salvar['CNPJ'].astype(str)
            
            # Salvar CSV forçando CNPJ como string com aspas
            import csv
            with open(caminho_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                # Escrever cabeçalho
                writer.writerow(df_salvar.columns)
                # Escrever dados
                for _, row in df_salvar.iterrows():
                    writer.writerow(row.values)
            logger.info(f"CSV normalizado salvo: {caminho_csv}")
            
            # Salvar relatório de normalizações
            self.salvar_relatorio()
            
            return caminho_csv
        except Exception as e:
            logger.error(f"Erro ao salvar CSV: {e}")
            return ""
    
    def salvar_relatorio(self):
        """Salva relatório das normalizações realizadas."""
        try:
            relatorio_path = os.path.join(self.diretorio_saida, "relatorio_normalizacao.txt")
            
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                f.write("RELATÓRIO DE NORMALIZAÇÃO - MATRIZ CS 2025\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Arquivo original: {self.arquivo_excel}\n")
                f.write(f"Diretório de saída: {self.diretorio_saida}\n\n")
                
                f.write("NORMALIZAÇÕES REALIZADAS:\n")
                f.write("-" * 30 + "\n")
                for i, normalizacao in enumerate(self.normalizacoes_realizadas, 1):
                    f.write(f"{i}. {normalizacao}\n")
                
                f.write(f"\nTotal de normalizações: {len(self.normalizacoes_realizadas)}\n")
            
            logger.info(f"Relatório salvo: {relatorio_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")
    
    def executar_normalizacao(self) -> bool:
        """
        Executa o processo completo de normalização.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            logger.info("=== INICIANDO NORMALIZAÇÃO DA MATRIZ CS 2025 ===")
            
            # 1. Criar backup
            backup_path = self.criar_backup()
            if not backup_path:
                logger.warning("Não foi possível criar backup, continuando mesmo assim...")
            
            # 2. Carregar dados
            df = self.carregar_excel()
            if df is None:
                return False
            
            # 3. Normalizar dados
            df_normalizado = self.normalizar_dados(df)
            
            # 4. Salvar CSV
            csv_path = self.salvar_csv(df_normalizado)
            if not csv_path:
                return False
            
            logger.info("=== NORMALIZAÇÃO CONCLUÍDA COM SUCESSO ===")
            logger.info(f"Arquivo CSV: {csv_path}")
            logger.info(f"Registros processados: {len(df_normalizado)}")
            logger.info(f"Normalizações realizadas: {len(self.normalizacoes_realizadas)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante normalização: {e}")
            return False

def main():
    """Função principal."""
    # Configurações
    arquivo_excel = "Matriz CS 2025 ATUAL.xlsx"
    diretorio_saida = r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_excel):
        logger.error(f"Arquivo não encontrado: {arquivo_excel}")
        return
    
    # Criar normalizador
    normalizador = MatrizCSNormalizer(arquivo_excel, diretorio_saida)
    
    # Executar normalização
    sucesso = normalizador.executar_normalizacao()
    
    if sucesso:
        print("\n✅ Normalização concluída com sucesso!")
        print(f"📁 Arquivo CSV: {diretorio_saida}\\matriz_cs_normalizada.csv")
        print(f"📋 Relatório: {diretorio_saida}\\relatorio_normalizacao.txt")
    else:
        print("\n❌ Erro durante a normalização. Verifique o log para detalhes.")

if __name__ == "__main__":
    main()
