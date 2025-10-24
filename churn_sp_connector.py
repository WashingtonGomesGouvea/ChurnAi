# churn_sp_connector.py
# Versão personalizada do SP Connector para o projeto Churn PCLs
# Adaptado para leitura e armazenamento de dados de VIPs

import io
import time
import requests
import msal
import pandas as pd
import os
from urllib.parse import quote
from datetime import datetime
import streamlit as st

GRAPH = "https://graph.microsoft.com/v1.0"

class ChurnSPConnector:
    """
    Conector personalizado para SharePoint/OneDrive no projeto Churn PCLs.
    Especializado em:
      - Leitura de dados de VIPs
      - Armazenamento de novos dados de VIPs
      - Sincronização com pasta local OneDrive
      - Integração com o sistema Churn
    """

    def __init__(self, config=None):
        """
        Inicializa o conector com configurações do Streamlit secrets ou config passado.

        Args:
            config: Dicionário com configurações (opcional, usa st.secrets por padrão)
        """
        if config is None:
            try:
                config = st.secrets
            except:
                raise RuntimeError("Configurações não encontradas. Use st.secrets ou passe config manualmente.")

        # Configurações Graph API
        graph_config = config.get("graph", {})
        self.tenant_id = graph_config.get("tenant_id")
        self.client_id = graph_config.get("client_id")
        self.client_secret = graph_config.get("client_secret")
        self.hostname = graph_config.get("hostname")
        self.site_path = graph_config.get("site_path")
        self.library_name = graph_config.get("library_name")

        # Configurações OneDrive
        onedrive_config = config.get("onedrive", {})
        self.user_upn = onedrive_config.get("user_upn")

        # Configurações de arquivos
        files_config = config.get("files", {})
        self.arquivo_principal = files_config.get("arquivo")

        # Caminho local OneDrive
        self.local_path = config.get("output_dir", "D:\\OneDrive - Synvia Group\\Data Analysis\\Churn PCLs")

        # Validação das configurações
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Configurações Graph API incompletas")

        # Inicialização MSAL
        self._app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )
        self._tok = None
        self._exp = 0
        self._site_id_cache = None
        self._drive_id_cache = None

    # -------- Autenticação --------
    def _token(self):
        """Obtém token de acesso válido"""
        now = time.time()
        if self._tok and now < self._exp:
            return self._tok

        res = self._app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in res:
            raise RuntimeError(res.get("error_description") or res)

        self._tok = res["access_token"]
        self._exp = now + int(res.get("expires_in", 3600)) - 60
        return self._tok

    def _headers(self):
        """Retorna headers com token de autenticação"""
        return {"Authorization": f"Bearer {self._token()}"}

    # -------- Modo de operação --------
    @property
    def is_onedrive(self) -> bool:
        """Verifica se está operando em modo OneDrive"""
        return bool(self.user_upn)

    # -------- Descoberta de recursos --------
    def _site_id(self):
        """Obtém ID do site SharePoint"""
        if self.is_onedrive:
            return None
        if self._site_id_cache:
            return self._site_id_cache

        url = f"{GRAPH}/sites/{self.hostname}:/{self.site_path}"
        r = requests.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()
        self._site_id_cache = r.json()["id"]
        return self._site_id_cache

    def _drive_id(self):
        """Obtém ID do drive/biblioteca"""
        if self.is_onedrive:
            return None
        if self._drive_id_cache:
            return self._drive_id_cache

        url = f"{GRAPH}/sites/{self._site_id()}/drives"
        r = requests.get(url, headers=self._headers(), timeout=30)
        r.raise_for_status()

        drives = r.json().get("value", [])
        for d in drives:
            if d.get("name", "").lower() == self.library_name.lower():
                self._drive_id_cache = d["id"]
                return self._drive_id_cache

        for d in drives:
            if d.get("driveType") == "documentLibrary":
                self._drive_id_cache = d["id"]
                return self._drive_id_cache

        raise RuntimeError(f"Biblioteca '{self.library_name}' não encontrada")

    # -------- Normalização de caminhos --------
    def normalize_path(self, path: str) -> str:
        """
        Normaliza caminho para o formato correto do Graph API

        Args:
            path: Caminho do arquivo

        Returns:
            Caminho normalizado
        """
        if not path:
            raise ValueError("Caminho vazio.")

        path = path.strip()

        if self.is_onedrive:
            # OneDrive: relativo a Documents/
            if path.startswith("/"):
                marker = "/Documents/"
                idx = path.lower().find(marker.lower())
                if idx == -1:
                    raise ValueError("Para OneDrive, o caminho deve conter /Documents/.")
                return path[idx + len(marker):]
            return path
        else:
            # SharePoint
            if path.startswith("/"):
                prefix = f"/{self.site_path}/{self.library_name}/"
                if not path.startswith(prefix):
                    raise ValueError(f"Caminho deve começar com {prefix}")
                return path[len(prefix):]
            return path

    # -------- Operações básicas de arquivo --------
    def download(self, path: str) -> bytes:
        """
        Baixa arquivo do SharePoint/OneDrive

        Args:
            path: Caminho do arquivo

        Returns:
            Conteúdo do arquivo em bytes
        """
        rel = quote(self.normalize_path(path), safe="/")

        if self.is_onedrive:
            url = f"{GRAPH}/users/{self.user_upn}/drive/root:/{rel}:/content"
        else:
            url = f"{GRAPH}/drives/{self._drive_id()}/root:/{rel}:/content"

        r = requests.get(url, headers=self._headers(), timeout=180)
        if r.status_code == 404:
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        r.raise_for_status()
        return r.content

    def upload_small(self, path: str, content: bytes, overwrite: bool = True):
        """
        Faz upload de arquivo pequeno para SharePoint/OneDrive

        Args:
            path: Caminho de destino
            content: Conteúdo em bytes
            overwrite: Se deve sobrescrever arquivo existente
        """
        rel = quote(self.normalize_path(path), safe="/")
        params = {"@microsoft.graph.conflictBehavior": "replace" if overwrite else "fail"}

        if self.is_onedrive:
            url = f"{GRAPH}/users/{self.user_upn}/drive/root:/{rel}:/content"
        else:
            url = f"{GRAPH}/drives/{self._drive_id()}/root:/{rel}:/content"

        r = requests.put(url, headers=self._headers(), params=params, data=content, timeout=300)
        r.raise_for_status()
        return r.json()

    # -------- Funções específicas para dados de VIP --------
    def carregar_dados_vip(self, arquivo: str = None) -> pd.DataFrame:
        """
        Carrega dados de VIPs do SharePoint/OneDrive

        Args:
            arquivo: Caminho do arquivo (usa arquivo principal se None)

        Returns:
            DataFrame com dados dos VIPs
        """
        if arquivo is None:
            arquivo = self.arquivo_principal

        try:
            print(f"Carregando dados VIP de: {arquivo}")
            dados = self.read_csv(arquivo)
            print(f"Dados carregados com sucesso: {len(dados)} registros")
            return dados
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {arquivo}")
            return pd.DataFrame()  # Retorna DataFrame vazio
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            raise

    def salvar_dados_vip(self, df: pd.DataFrame, arquivo: str = None, backup: bool = True) -> bool:
        """
        Salva dados de VIPs no SharePoint/OneDrive e localmente

        Args:
            df: DataFrame com dados dos VIPs
            arquivo: Caminho do arquivo (usa arquivo principal se None)
            backup: Se deve fazer backup antes de salvar

        Returns:
            True se salvo com sucesso
        """
        if arquivo is None:
            arquivo = self.arquivo_principal

        try:
            # Faz backup se solicitado
            if backup:
                self._fazer_backup(arquivo)

            # Salva no SharePoint/OneDrive
            print(f"Salvando dados no SharePoint: {arquivo}")
            self.write_csv(df, arquivo, overwrite=True)

            # Salva localmente também
            caminho_local = self._caminho_local_para_arquivo(arquivo)
            print(f"Salvando dados localmente: {caminho_local}")
            df.to_csv(caminho_local, index=False)

            print("Dados salvos com sucesso!")
            return True

        except Exception as e:
            print(f"Erro ao salvar dados: {str(e)}")
            raise

    def adicionar_vip(self, dados_vip: dict, arquivo: str = None) -> bool:
        """
        Adiciona novo VIP aos dados existentes

        Args:
            dados_vip: Dicionário com dados do novo VIP
            arquivo: Arquivo onde salvar (usa principal se None)

        Returns:
            True se adicionado com sucesso
        """
        try:
            # Carrega dados existentes
            df = self.carregar_dados_vip(arquivo)

            # Converte dados do VIP para DataFrame
            novo_vip = pd.DataFrame([dados_vip])

            # Adiciona timestamp se não existir
            if 'data_adicao' not in novo_vip.columns:
                novo_vip['data_adicao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Adiciona aos dados existentes
            df_atualizado = pd.concat([df, novo_vip], ignore_index=True)

            # Remove duplicatas se houver (baseado em alguma coluna chave, ex: email)
            if 'email' in df_atualizado.columns:
                df_atualizado = df_atualizado.drop_duplicates(subset=['email'], keep='last')

            # Salva dados atualizados
            return self.salvar_dados_vip(df_atualizado, arquivo)

        except Exception as e:
            print(f"Erro ao adicionar VIP: {str(e)}")
            raise

    def atualizar_vip(self, identificador: str, dados_atualizados: dict, coluna_id: str = 'email', arquivo: str = None) -> bool:
        """
        Atualiza dados de um VIP existente

        Args:
            identificador: Valor para identificar o VIP (ex: email)
            dados_atualizados: Dicionário com dados a atualizar
            coluna_id: Coluna usada como identificador
            arquivo: Arquivo onde salvar (usa principal se None)

        Returns:
            True se atualizado com sucesso
        """
        try:
            # Carrega dados existentes
            df = self.carregar_dados_vip(arquivo)

            if df.empty:
                raise ValueError("Não há dados para atualizar")

            # Encontra o índice do VIP
            if coluna_id not in df.columns:
                raise ValueError(f"Coluna identificadora '{coluna_id}' não encontrada")

            mask = df[coluna_id] == identificador
            if not mask.any():
                raise ValueError(f"VIP não encontrado: {identificador}")

            # Atualiza os dados
            for coluna, valor in dados_atualizados.items():
                df.loc[mask, coluna] = valor

            # Adiciona timestamp de atualização
            df.loc[mask, 'data_atualizacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Salva dados atualizados
            return self.salvar_dados_vip(df, arquivo)

        except Exception as e:
            print(f"Erro ao atualizar VIP: {str(e)}")
            raise

    # -------- Funções utilitárias --------
    def _fazer_backup(self, arquivo: str):
        """Cria backup do arquivo antes de sobrescrever"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho_backup = arquivo.replace('.csv', f'_backup_{timestamp}.csv')
            print(f"Criando backup: {caminho_backup}")

            # Tenta baixar arquivo atual
            try:
                conteudo = self.download(arquivo)
                self.upload_small(caminho_backup, conteudo, overwrite=False)
                print("Backup criado com sucesso")
            except FileNotFoundError:
                print("Arquivo original não existe, pulando backup")

        except Exception as e:
            print(f"Aviso: Não foi possível criar backup: {str(e)}")

    def _caminho_local_para_arquivo(self, arquivo_sharepoint: str) -> str:
        """Converte caminho do SharePoint para caminho local OneDrive"""
        # Remove a parte do SharePoint e mantém apenas o caminho relativo
        caminho_relativo = arquivo_sharepoint.replace('/personal/washington_gouvea_synvia_com_/Documents/', '')
        return os.path.join(self.local_path, caminho_relativo)

    def sincronizar_com_local(self, arquivo: str = None):
        """
        Sincroniza arquivo do SharePoint para pasta local

        Args:
            arquivo: Arquivo a sincronizar (usa principal se None)
        """
        if arquivo is None:
            arquivo = self.arquivo_principal

        try:
            # Baixa do SharePoint
            conteudo = self.download(arquivo)

            # Salva localmente
            caminho_local = self._caminho_local_para_arquivo(arquivo)
            os.makedirs(os.path.dirname(caminho_local), exist_ok=True)

            with open(caminho_local, 'wb') as f:
                f.write(conteudo)

            print(f"Arquivo sincronizado localmente: {caminho_local}")

        except Exception as e:
            print(f"Erro ao sincronizar com local: {str(e)}")
            raise

    # -------- Conveniências DataFrame --------
    def read_excel(self, path: str, **kw) -> pd.DataFrame:
        """Lê arquivo Excel do SharePoint/OneDrive"""
        return pd.read_excel(io.BytesIO(self.download(path)), **kw)

    def read_csv(self, path: str, **kw) -> pd.DataFrame:
        """Lê arquivo CSV do SharePoint/OneDrive"""
        return pd.read_csv(io.BytesIO(self.download(path)), **kw)

    def write_excel(self, df: pd.DataFrame, path: str, overwrite: bool = True):
        """Salva DataFrame como Excel no SharePoint/OneDrive"""
        bio = io.BytesIO()
        df.to_excel(bio, index=False)
        return self.upload_small(path, bio.getvalue(), overwrite=overwrite)

    def write_csv(self, df: pd.DataFrame, path: str, overwrite: bool = True):
        """Salva DataFrame como CSV no SharePoint/OneDrive"""
        bio = io.BytesIO()
        df.to_csv(bio, index=False)
        return self.upload_small(path, bio.getvalue(), overwrite=overwrite)

    # -------- Funções de diagnóstico --------
    def testar_conexao(self) -> bool:
        """
        Testa a conexão com o SharePoint/OneDrive

        Returns:
            True se conexão OK
        """
        try:
            # Tenta obter token
            token = self._token()
            if not token:
                return False

            # Tenta acessar o drive
            if self.is_onedrive:
                url = f"{GRAPH}/users/{self.user_upn}/drive"
            else:
                url = f"{GRAPH}/drives/{self._drive_id()}"

            r = requests.get(url, headers=self._headers(), timeout=30)
            return r.status_code == 200

        except Exception as e:
            print(f"Erro na conexão: {str(e)}")
            return False

    def listar_arquivos(self, pasta: str = "") -> list:
        """
        Lista arquivos em uma pasta

        Args:
            pasta: Pasta a listar (vazia para raiz)

        Returns:
            Lista de nomes de arquivos
        """
        try:
            rel = quote(self.normalize_path(pasta), safe="/") if pasta else ""

            if self.is_onedrive:
                url = f"{GRAPH}/users/{self.user_upn}/drive/root/children"
                if rel:
                    url = f"{GRAPH}/users/{self.user_upn}/drive/root:/{rel}:/children"
            else:
                url = f"{GRAPH}/drives/{self._drive_id()}/root/children"
                if rel:
                    url = f"{GRAPH}/drives/{self._drive_id()}/root:/{rel}:/children"

            r = requests.get(url, headers=self._headers(), timeout=30)
            r.raise_for_status()

            items = r.json().get("value", [])
            return [item["name"] for item in items if "file" in item]

        except Exception as e:
            print(f"Erro ao listar arquivos: {str(e)}")
            return []
