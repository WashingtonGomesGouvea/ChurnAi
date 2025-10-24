#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integração VIP com Dados de Laboratórios
========================================

Este módulo fornece funcionalidades para integrar dados VIP com os dados
de laboratórios processados pelo sistema de análise de churn, permitindo
validação, auto-completar e sugestões de laboratórios.
"""

import os
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re

# Configurações de log
logger = logging.getLogger(__name__)

class VIPIntegration:
    """Integração entre dados VIP e dados de laboratórios."""
    
    def __init__(self, diretorio_dados: str):
        """
        Inicializa a integração.
        
        Args:
            diretorio_dados: Diretório onde estão os dados
        """
        self.diretorio_dados = diretorio_dados
        self.df_laboratorios = None
        self.df_vip = None
        self._carregar_dados()
    
    def _carregar_dados(self):
        """Carrega dados de laboratórios e VIP."""
        try:
            # Carregar dados de laboratórios (churn analysis)
            arquivo_churn = os.path.join(self.diretorio_dados, "churn_analysis_latest.parquet")
            if os.path.exists(arquivo_churn):
                self.df_laboratorios = pd.read_parquet(arquivo_churn, engine='pyarrow')
                logger.info(f"Dados de laboratórios carregados: {len(self.df_laboratorios)} registros")
            else:
                # Fallback para CSV
                arquivo_csv = os.path.join(self.diretorio_dados, "churn_analysis_latest.csv")
                if os.path.exists(arquivo_csv):
                    self.df_laboratorios = pd.read_csv(arquivo_csv, encoding='utf-8-sig', low_memory=False)
                    logger.info(f"Dados de laboratórios carregados (CSV): {len(self.df_laboratorios)} registros")
                else:
                    logger.warning("Arquivo de dados de laboratórios não encontrado")
            
            # Carregar dados VIP
            arquivo_vip = os.path.join(self.diretorio_dados, "matriz_cs_normalizada.csv")
            if os.path.exists(arquivo_vip):
                # Ler CNPJ como string para preservar zeros à esquerda
                self.df_vip = pd.read_csv(
                    arquivo_vip,
                    encoding='utf-8-sig',
                    dtype={'CNPJ': 'string'}
                )
                logger.info(f"Dados VIP carregados: {len(self.df_vip)} registros")
            else:
                logger.warning("Arquivo de dados VIP não encontrado")
                
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
    
    def normalizar_cnpj(self, cnpj: str) -> str:
        """
        Normaliza CNPJ removendo pontuação e garantindo 14 dígitos.
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
        # Garantir 14 dígitos
        if len(cnpj_limpo) < 14:
            cnpj_limpo = cnpj_limpo.zfill(14)
        elif len(cnpj_limpo) > 14:
            cnpj_limpo = cnpj_limpo[-14:]
        return cnpj_limpo
    
    def validar_cnpj(self, cnpj: str) -> Tuple[bool, str]:
        """
        Valida formato do CNPJ.
        
        Args:
            cnpj: CNPJ a ser validado
            
        Returns:
            Tupla (é_válido, mensagem)
        """
        if pd.isna(cnpj) or cnpj == '':
            return False, "CNPJ não pode estar vazio"
        
        cnpj_limpo = self.normalizar_cnpj(cnpj)
        
        if len(cnpj_limpo) != 14:
            return False, f"CNPJ deve ter 14 dígitos (encontrados: {len(cnpj_limpo)})"
        
        # Verificar se todos são dígitos
        if not cnpj_limpo.isdigit():
            return False, "CNPJ deve conter apenas números"
        
        return True, "CNPJ válido"
    
    def buscar_laboratorio_por_cnpj(self, cnpj: str) -> Optional[Dict]:
        """
        Busca dados de laboratório por CNPJ.
        
        Args:
            cnpj: CNPJ do laboratório
            
        Returns:
            Dados do laboratório ou None se não encontrado
        """
        if self.df_laboratorios is None or self.df_laboratorios.empty:
            return None
        
        cnpj_normalizado = self.normalizar_cnpj(cnpj)
        if not cnpj_normalizado:
            return None
        
        # Buscar no DataFrame de laboratórios
        match = self.df_laboratorios[
            self.df_laboratorios['CNPJ_PCL'].apply(self.normalizar_cnpj) == cnpj_normalizado
        ]
        
        if not match.empty:
            row = match.iloc[0]
            return {
                'cnpj': row.get('CNPJ_PCL', ''),
                'razao_social': row.get('Razao_Social_PCL', ''),
                'nome_fantasia': row.get('Nome_Fantasia_PCL', ''),
                'estado': row.get('Estado', ''),
                'cidade': row.get('Cidade', ''),
                'representante_nome': row.get('Representante_Nome', ''),
                'representante_id': row.get('Representante_ID', ''),
                'status_risco': row.get('Status_Risco', ''),
                'tendencia': row.get('Tendencia', ''),
                'volume_total_2025': row.get('Volume_Total_2025', 0)
            }
        
        return None
    
    def verificar_cnpj_existe(self, cnpj: str) -> bool:
        """
        Verifica se CNPJ existe nos dados de laboratórios.
        
        Args:
            cnpj: CNPJ a ser verificado
            
        Returns:
            True se existe, False caso contrário
        """
        return self.buscar_laboratorio_por_cnpj(cnpj) is not None
    
    def verificar_cnpj_vip_existe(self, cnpj: str) -> bool:
        """
        Verifica se CNPJ já existe nos dados VIP.
        
        Args:
            cnpj: CNPJ a ser verificado
            
        Returns:
            True se já é VIP, False caso contrário
        """
        if self.df_vip is None or self.df_vip.empty:
            return False
        
        cnpj_normalizado = self.normalizar_cnpj(cnpj)
        if not cnpj_normalizado:
            return False
        
        # Buscar no DataFrame VIP
        match = self.df_vip[
            self.df_vip['CNPJ'].apply(self.normalizar_cnpj) == cnpj_normalizado
        ]
        
        return not match.empty
    
    def obter_sugestoes_laboratorios(self, limite: int = 20) -> List[Dict]:
        """
        Obtém sugestões de laboratórios que ainda não são VIP.
        
        Args:
            limite: Número máximo de sugestões
            
        Returns:
            Lista de laboratórios sugeridos
        """
        if self.df_laboratorios is None or self.df_laboratorios.empty:
            return []
        
        # Obter CNPJs que já são VIP
        cnpjs_vip = set()
        if self.df_vip is not None and not self.df_vip.empty:
            cnpjs_vip = set(self.df_vip['CNPJ'].apply(self.normalizar_cnpj))
        
        # Filtrar laboratórios que não são VIP
        sugestoes = []
        for _, row in self.df_laboratorios.iterrows():
            cnpj_normalizado = self.normalizar_cnpj(row.get('CNPJ_PCL', ''))
            
            if cnpj_normalizado and cnpj_normalizado not in cnpjs_vip:
                sugestoes.append({
                    'cnpj': row.get('CNPJ_PCL', ''),
                    'razao_social': row.get('Razao_Social_PCL', ''),
                    'nome_fantasia': row.get('Nome_Fantasia_PCL', ''),
                    'estado': row.get('Estado', ''),
                    'cidade': row.get('Cidade', ''),
                    'representante_nome': row.get('Representante_Nome', ''),
                    'status_risco': row.get('Status_Risco', ''),
                    'volume_total_2025': row.get('Volume_Total_2025', 0)
                })
        
        # Ordenar por volume (maior primeiro) e retornar limite
        sugestoes.sort(key=lambda x: x['volume_total_2025'], reverse=True)
        return sugestoes[:limite]
    
    def obter_estatisticas_integracao(self) -> Dict[str, Any]:
        """
        Obtém estatísticas da integração.
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_laboratorios': 0,
            'total_vips': 0,
            'laboratorios_nao_vip': 0,
            'cobertura_vip': 0.0
        }
        
        if self.df_laboratorios is not None:
            stats['total_laboratorios'] = len(self.df_laboratorios)
        
        if self.df_vip is not None:
            stats['total_vips'] = len(self.df_vip)
        
        # Calcular laboratórios não VIP
        if self.df_laboratorios is not None and self.df_vip is not None:
            cnpjs_vip = set(self.df_vip['CNPJ'].apply(self.normalizar_cnpj))
            cnpjs_laboratorios = set(self.df_laboratorios['CNPJ_PCL'].apply(self.normalizar_cnpj))
            
            stats['laboratorios_nao_vip'] = len(cnpjs_laboratorios - cnpjs_vip)
            
            if len(cnpjs_laboratorios) > 0:
                stats['cobertura_vip'] = len(cnpjs_vip & cnpjs_laboratorios) / len(cnpjs_laboratorios) * 100
        
        return stats
    
    def buscar_laboratorios_por_filtros(self, estado: str = None, cidade: str = None, 
                                      representante: str = None, status_risco: str = None) -> List[Dict]:
        """
        Busca laboratórios por filtros.
        
        Args:
            estado: Estado para filtrar
            cidade: Cidade para filtrar
            representante: Nome do representante para filtrar
            status_risco: Status de risco para filtrar
            
        Returns:
            Lista de laboratórios filtrados
        """
        if self.df_laboratorios is None or self.df_laboratorios.empty:
            return []
        
        df_filtrado = self.df_laboratorios.copy()
        
        # Aplicar filtros
        if estado:
            df_filtrado = df_filtrado[df_filtrado['Estado'] == estado]
        
        if cidade:
            df_filtrado = df_filtrado[df_filtrado['Cidade'].str.contains(cidade, case=False, na=False)]
        
        if representante:
            df_filtrado = df_filtrado[df_filtrado['Representante_Nome'].str.contains(representante, case=False, na=False)]
        
        if status_risco:
            df_filtrado = df_filtrado[df_filtrado['Status_Risco'] == status_risco]
        
        # Converter para lista de dicionários
        laboratorios = []
        for _, row in df_filtrado.iterrows():
            laboratorios.append({
                'cnpj': row.get('CNPJ_PCL', ''),
                'razao_social': row.get('Razao_Social_PCL', ''),
                'nome_fantasia': row.get('Nome_Fantasia_PCL', ''),
                'estado': row.get('Estado', ''),
                'cidade': row.get('Cidade', ''),
                'representante_nome': row.get('Representante_Nome', ''),
                'status_risco': row.get('Status_Risco', ''),
                'volume_total_2025': row.get('Volume_Total_2025', 0)
            })
        
        return laboratorios
    
    def auto_completar_dados_vip(self, cnpj: str) -> Dict[str, Any]:
        """
        Auto-completa dados VIP baseado no CNPJ.
        
        Args:
            cnpj: CNPJ do laboratório
            
        Returns:
            Dicionário com dados auto-completados
        """
        dados_lab = self.buscar_laboratorio_por_cnpj(cnpj)
        
        if dados_lab:
            return {
                'cnpj': cnpj,
                'razao_social': dados_lab.get('razao_social', ''),
                'nome_fantasia': dados_lab.get('nome_fantasia', ''),
                'estado': dados_lab.get('estado', ''),
                'cidade': dados_lab.get('cidade', ''),
                'representante_nome': dados_lab.get('representante_nome', ''),
                'status_risco': dados_lab.get('status_risco', ''),
                'volume_total_2025': dados_lab.get('volume_total_2025', 0)
            }
        
        return {
            'cnpj': cnpj,
            'razao_social': '',
            'nome_fantasia': '',
            'estado': '',
            'cidade': '',
            'representante_nome': '',
            'status_risco': '',
            'volume_total_2025': 0
        }

def main():
    """Função principal para testes."""
    # Exemplo de uso
    integration = VIPIntegration(r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs")
    
    # Testar validação de CNPJ
    cnpj_teste = "12.345.678/0001-90"
    valido, mensagem = integration.validar_cnpj(cnpj_teste)
    print(f"CNPJ {cnpj_teste}: {mensagem}")
    
    # Testar busca de laboratório
    dados_lab = integration.buscar_laboratorio_por_cnpj(cnpj_teste)
    if dados_lab:
        print(f"Laboratório encontrado: {dados_lab['nome_fantasia']}")
    else:
        print("Laboratório não encontrado")
    
    # Obter estatísticas
    stats = integration.obter_estatisticas_integracao()
    print(f"Estatísticas: {stats}")

if __name__ == "__main__":
    main()
