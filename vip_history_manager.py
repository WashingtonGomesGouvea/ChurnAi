#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Histórico de Alterações VIP
==========================================

Este módulo gerencia o histórico de todas as alterações realizadas nos dados VIP,
incluindo inserções, edições e exclusões. Mantém um registro detalhado para auditoria
e possibilidade de reversão de alterações.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pandas as pd

# Configurações de log
logger = logging.getLogger(__name__)

@dataclass
class AlteracaoVIP:
    """Representa uma alteração nos dados VIP."""
    timestamp: str
    tipo: str  # 'insercao', 'edicao', 'exclusao'
    cnpj: str
    campo_alterado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    usuario: str = "sistema"
    dados_completos_antes: Optional[Dict] = None
    dados_completos_depois: Optional[Dict] = None
    observacoes: Optional[str] = None

class VIPHistoryManager:
    """Gerenciador do histórico de alterações VIP."""
    
    def __init__(self, diretorio_dados: str):
        """
        Inicializa o gerenciador de histórico.
        
        Args:
            diretorio_dados: Diretório onde estão os dados VIP
        """
        self.diretorio_dados = diretorio_dados
        self.arquivo_historico = os.path.join(diretorio_dados, "vip_alteracoes_history.json")
        self.historico = self._carregar_historico()
    
    def _carregar_historico(self) -> List[Dict]:
        """
        Carrega histórico existente do arquivo JSON.
        
        Returns:
            Lista de alterações
        """
        try:
            if os.path.exists(self.arquivo_historico):
                with open(self.arquivo_historico, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('alteracoes', [])
            return []
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            return []
    
    def _salvar_historico(self):
        """Salva histórico no arquivo JSON."""
        try:
            os.makedirs(self.diretorio_dados, exist_ok=True)
            
            data = {
                'metadata': {
                    'ultima_atualizacao': datetime.now().isoformat(),
                    'total_alteracoes': len(self.historico)
                },
                'alteracoes': self.historico
            }
            
            with open(self.arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Histórico salvo: {self.arquivo_historico}")
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
    
    def registrar_insercao(self, cnpj: str, dados_novos: Dict, usuario: str = "sistema", observacoes: str = None):
        """
        Registra uma inserção de novo VIP.
        
        Args:
            cnpj: CNPJ do laboratório
            dados_novos: Dados completos do novo VIP
            usuario: Usuário que fez a alteração
            observacoes: Observações adicionais
        """
        alteracao = AlteracaoVIP(
            timestamp=datetime.now().isoformat(),
            tipo='insercao',
            cnpj=cnpj,
            dados_completos_depois=dados_novos,
            usuario=usuario,
            observacoes=observacoes
        )
        
        self.historico.append(asdict(alteracao))
        self._salvar_historico()
        logger.info(f"Inserção registrada: CNPJ {cnpj}")
    
    def registrar_edicao(self, cnpj: str, campo_alterado: str, valor_anterior: str, 
                        valor_novo: str, dados_antes: Dict, dados_depois: Dict, 
                        usuario: str = "sistema", observacoes: str = None):
        """
        Registra uma edição de VIP existente.
        
        Args:
            cnpj: CNPJ do laboratório
            campo_alterado: Nome do campo alterado
            valor_anterior: Valor anterior do campo
            valor_novo: Novo valor do campo
            dados_antes: Dados completos antes da alteração
            dados_depois: Dados completos depois da alteração
            usuario: Usuário que fez a alteração
            observacoes: Observações adicionais
        """
        alteracao = AlteracaoVIP(
            timestamp=datetime.now().isoformat(),
            tipo='edicao',
            cnpj=cnpj,
            campo_alterado=campo_alterado,
            valor_anterior=valor_anterior,
            valor_novo=valor_novo,
            dados_completos_antes=dados_antes,
            dados_completos_depois=dados_depois,
            usuario=usuario,
            observacoes=observacoes
        )
        
        self.historico.append(asdict(alteracao))
        self._salvar_historico()
        logger.info(f"Edição registrada: CNPJ {cnpj}, campo '{campo_alterado}'")
    
    def registrar_exclusao(self, cnpj: str, dados_removidos: Dict, usuario: str = "sistema", observacoes: str = None):
        """
        Registra uma exclusão de VIP.
        
        Args:
            cnpj: CNPJ do laboratório
            dados_removidos: Dados completos do VIP removido
            usuario: Usuário que fez a alteração
            observacoes: Observações adicionais
        """
        alteracao = AlteracaoVIP(
            timestamp=datetime.now().isoformat(),
            tipo='exclusao',
            cnpj=cnpj,
            dados_completos_antes=dados_removidos,
            usuario=usuario,
            observacoes=observacoes
        )
        
        self.historico.append(asdict(alteracao))
        self._salvar_historico()
        logger.info(f"Exclusão registrada: CNPJ {cnpj}")
    
    def buscar_historico_cnpj(self, cnpj: str) -> List[Dict]:
        """
        Busca histórico de alterações para um CNPJ específico.
        
        Args:
            cnpj: CNPJ a ser pesquisado
            
        Returns:
            Lista de alterações para o CNPJ
        """
        return [alt for alt in self.historico if alt['cnpj'] == cnpj]
    
    def buscar_historico_periodo(self, data_inicio: datetime, data_fim: datetime) -> List[Dict]:
        """
        Busca histórico de alterações em um período.
        
        Args:
            data_inicio: Data de início
            data_fim: Data de fim
            
        Returns:
            Lista de alterações no período
        """
        alteracoes_periodo = []
        
        for alt in self.historico:
            try:
                timestamp = datetime.fromisoformat(alt['timestamp'])
                if data_inicio <= timestamp <= data_fim:
                    alteracoes_periodo.append(alt)
            except Exception as e:
                logger.warning(f"Erro ao processar timestamp: {alt['timestamp']} - {e}")
        
        return alteracoes_periodo
    
    def buscar_historico_tipo(self, tipo: str) -> List[Dict]:
        """
        Busca histórico por tipo de alteração.
        
        Args:
            tipo: Tipo de alteração ('insercao', 'edicao', 'exclusao')
            
        Returns:
            Lista de alterações do tipo especificado
        """
        return [alt for alt in self.historico if alt['tipo'] == tipo]
    
    def obter_ultimas_alteracoes(self, limite: int = 10) -> List[Dict]:
        """
        Obtém as últimas alterações realizadas.
        
        Args:
            limite: Número máximo de alterações a retornar
            
        Returns:
            Lista das últimas alterações
        """
        return sorted(self.historico, key=lambda x: x['timestamp'], reverse=True)[:limite]
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do histórico.
        
        Returns:
            Dicionário com estatísticas
        """
        total = len(self.historico)
        
        if total == 0:
            return {
                'total_alteracoes': 0,
                'por_tipo': {},
                'por_usuario': {},
                'ultima_alteracao': None
            }
        
        # Contar por tipo
        por_tipo = {}
        for alt in self.historico:
            tipo = alt['tipo']
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        
        # Contar por usuário
        por_usuario = {}
        for alt in self.historico:
            usuario = alt['usuario']
            por_usuario[usuario] = por_usuario.get(usuario, 0) + 1
        
        # Última alteração
        ultima = max(self.historico, key=lambda x: x['timestamp'])
        
        return {
            'total_alteracoes': total,
            'por_tipo': por_tipo,
            'por_usuario': por_usuario,
            'ultima_alteracao': ultima['timestamp']
        }
    
    def exportar_historico_csv(self, caminho_saida: str = None) -> str:
        """
        Exporta histórico para CSV.
        
        Args:
            caminho_saida: Caminho para salvar o CSV (opcional)
            
        Returns:
            Caminho do arquivo CSV gerado
        """
        try:
            if caminho_saida is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                caminho_saida = os.path.join(self.diretorio_dados, f"historico_vip_{timestamp}.csv")
            
            # Converter para DataFrame
            df = pd.DataFrame(self.historico)
            
            # Reordenar colunas
            colunas_principais = ['timestamp', 'tipo', 'cnpj', 'campo_alterado', 
                                'valor_anterior', 'valor_novo', 'usuario']
            colunas_existentes = [col for col in colunas_principais if col in df.columns]
            colunas_restantes = [col for col in df.columns if col not in colunas_principais]
            df = df[colunas_existentes + colunas_restantes]
            
            # Salvar CSV
            df.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
            logger.info(f"Histórico exportado: {caminho_saida}")
            
            return caminho_saida
        except Exception as e:
            logger.error(f"Erro ao exportar histórico: {e}")
            return ""
    
    def limpar_historico_antigo(self, dias_manter: int = 365):
        """
        Remove alterações antigas do histórico.
        
        Args:
            dias_manter: Número de dias para manter no histórico
        """
        try:
            data_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            data_limite = data_limite.replace(day=data_limite.day - dias_manter)
            
            historico_filtrado = []
            removidas = 0
            
            for alt in self.historico:
                try:
                    timestamp = datetime.fromisoformat(alt['timestamp'])
                    if timestamp >= data_limite:
                        historico_filtrado.append(alt)
                    else:
                        removidas += 1
                except Exception as e:
                    logger.warning(f"Erro ao processar timestamp: {alt['timestamp']} - {e}")
                    # Manter registros com timestamp inválido
                    historico_filtrado.append(alt)
            
            self.historico = historico_filtrado
            self._salvar_historico()
            
            logger.info(f"Histórico limpo: {removidas} registros removidos")
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")

def main():
    """Função principal para testes."""
    # Exemplo de uso
    manager = VIPHistoryManager(r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs")
    
    # Exemplo de registro de alteração
    manager.registrar_insercao(
        cnpj="12.345.678/0001-90",
        dados_novos={
            "CNPJ": "12.345.678/0001-90",
            "Razao_Social": "Laboratório Teste",
            "Ranking": "BRONZE",
            "Ranking Rede": "OURO"
        },
        usuario="admin",
        observacoes="Laboratório adicionado via script de migração"
    )
    
    # Obter estatísticas
    stats = manager.obter_estatisticas()
    print(f"Estatísticas: {stats}")

if __name__ == "__main__":
    main()
