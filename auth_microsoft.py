"""
Sistema de Autenticação Microsoft para Streamlit
Implementa login via Azure AD com MSAL
"""

import streamlit as st
import msal
import requests
import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MicrosoftAuth:
    """Classe para gerenciar autenticação Microsoft via Azure AD"""

    def __init__(self):
        """Inicializar com configurações do Streamlit secrets"""
        try:
            auth_config = st.secrets.get("auth", {})

            self.client_id = auth_config.get("client_id", os.getenv("AZURE_CLIENT_ID"))
            self.client_secret = auth_config.get("client_secret", os.getenv("AZURE_CLIENT_SECRET"))
            self.tenant_id = auth_config.get("tenant_id", os.getenv("AZURE_TENANT_ID"))
            self.redirect_uri_local = auth_config.get("redirect_uri_local", "http://localhost:8501")
            self.redirect_uri_prod = auth_config.get("redirect_uri_prod", "https://syntoxchurn.streamlit.app")
            self.authority = auth_config.get("authority", f"https://login.microsoftonline.com/{self.tenant_id}")
            self.scope = auth_config.get("scope", ["https://graph.microsoft.com/User.Read"])

            # Determinar redirect URI baseado no ambiente
            self.redirect_uri = self._get_redirect_uri()

            # Validar configurações
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                raise ValueError("Configurações de autenticação Microsoft incompletas")

        except Exception as e:
            logger.error(f"Erro ao inicializar MicrosoftAuth: {e}")
            raise

    def _get_redirect_uri(self) -> str:
        """Determinar URI de redirecionamento baseado no ambiente"""
        try:
            # Estratégia simplificada: detectar se estamos no Streamlit Cloud
            # No Streamlit Cloud, várias variáveis específicas estão presentes
            streamlit_env_vars = [
                "STREAMLIT_RUNTIME_VERSION",
                "IS_STREAMLIT_CLOUD",
                "STREAMLIT_SERVER_BASE_URL_PATH"
            ]

            # Verificar se pelo menos uma variável específica do Streamlit Cloud existe
            is_streamlit_cloud = any(os.getenv(var) for var in streamlit_env_vars)

            # Verificar se o hostname sugere produção
            hostname = os.getenv("HOSTNAME", "")
            is_production_hostname = "streamlit" in hostname.lower() or hostname.startswith("pod-")

            # Verificar se estamos rodando em um path que sugere produção
            base_url_path = os.getenv("STREAMLIT_SERVER_BASE_URL_PATH", "")
            is_production_url = "streamlit.app" in base_url_path

            # Combinação final: se qualquer indicador de produção for verdadeiro
            is_production = is_streamlit_cloud or is_production_hostname or is_production_url

            # Log detalhado
            logger.info(f"Detecção produção - Cloud: {is_streamlit_cloud}, Hostname: {hostname}, URL: {base_url_path}")
            logger.info(f"IS_PRODUCTION: {is_production}")

            if is_production:
                # Em produção (Streamlit Cloud), usar URI de produção
                logger.info("Ambiente de PRODUÇÃO detectado - usando redirect_uri_prod")
                return self.redirect_uri_prod
            else:
                # Em desenvolvimento local, usar URI local se disponível
                logger.warning("Ambiente de DESENVOLVIMENTO detectado")
                logger.warning("IMPORTANTE: Adicione 'http://localhost:8501' como Redirect URI no Azure AD")

                # Usar URI local para desenvolvimento
                if hasattr(self, 'redirect_uri_local') and self.redirect_uri_local:
                    logger.info(f"Usando URI local: {self.redirect_uri_local}")
                    return self.redirect_uri_local

                # Fallback para produção (não funcionará completamente, mas pelo menos tentará)
                logger.warning("FALLBACK: usando redirect_uri_prod (adicione localhost no Azure AD)")
                return self.redirect_uri_prod

        except Exception as e:
            logger.error(f"Erro ao determinar redirect URI: {e}")
            return self.redirect_uri_prod

    def get_login_url(self) -> str:
        """Gera URL de autenticação Microsoft"""
        try:
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )

            # MSAL automaticamente solicita offline_access quando usado dessa forma
            auth_url = app.get_authorization_request_url(
                self.scope,
                redirect_uri=self.redirect_uri,
                prompt="select_account"  # Permite seleção de conta
            )
            return auth_url
        except Exception as e:
            logger.error(f"Erro ao gerar URL de login: {e}")
            raise

    def get_token_from_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Troca código de autorização por token de acesso e refresh token"""
        try:
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )

            # MSAL automaticamente retorna refresh_token quando disponível
            result = app.acquire_token_by_authorization_code(
                code,
                scopes=self.scope,
                redirect_uri=self.redirect_uri
            )

            if "access_token" in result:
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token"),
                    "expires_in": result.get("expires_in", 3600)
                }

            if "error" in result:
                logger.error(f"Erro na autenticação: {result['error_description']}")
                return None

            return None

        except Exception as e:
            logger.error(f"Erro ao obter token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Renova o access token usando refresh token"""
        try:
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )

            # MSAL automaticamente retorna novo refresh_token
            result = app.acquire_token_by_refresh_token(
                refresh_token,
                scopes=self.scope
            )

            if "access_token" in result:
                logger.info("Token renovado com sucesso")
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", refresh_token),
                    "expires_in": result.get("expires_in", 3600)
                }

            if "error" in result:
                logger.error(f"Erro ao renovar token: {result.get('error_description')}")
                return None

            return None

        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return None

    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Obtém informações do usuário autenticado via Microsoft Graph"""
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                # Adicionar campos calculados
                user_data['domain'] = user_data.get('userPrincipalName', '').split('@')[-1] if user_data.get('userPrincipalName') else ''
                return user_data
            else:
                logger.error(f"Erro ao obter informações do usuário: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao obter informações do usuário: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao obter informações do usuário: {e}")
            return None

    def validate_token(self, token: str) -> bool:
        """Valida se o token ainda é válido"""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


class AuthManager:
    """Gerenciador de estado de autenticação para Streamlit"""

    @staticmethod
    def init_session_state():
        """Inicializar estado da sessão para autenticação"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user_info" not in st.session_state:
            st.session_state.user_info = None
        if "token" not in st.session_state:
            st.session_state.token = None
        if "refresh_token" not in st.session_state:
            st.session_state.refresh_token = None
        if "token_expiry" not in st.session_state:
            st.session_state.token_expiry = None
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0

    @staticmethod
    def login(user_info: Dict[str, Any], token: str, refresh_token: str = None, expires_in: int = 3600):
        """Realizar login do usuário"""
        import datetime
        st.session_state.authenticated = True
        st.session_state.user_info = user_info
        st.session_state.token = token
        st.session_state.refresh_token = refresh_token
        st.session_state.token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        st.session_state.login_attempts = 0
        logger.info(f"Usuário {user_info.get('displayName')} fez login com sucesso")

    @staticmethod
    def logout():
        """Realizar logout do usuário"""
        user_name = st.session_state.user_info.get('displayName') if st.session_state.user_info else 'Unknown'
        logger.info(f"Usuário {user_name} fez logout")

        # Limpar estado da sessão
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.token = None
        st.session_state.login_attempts = 0

    @staticmethod
    def is_authenticated() -> bool:
        """Verificar se usuário está autenticado"""
        return st.session_state.get("authenticated", False)

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Obter informações do usuário atual"""
        return st.session_state.get("user_info")

    @staticmethod
    def require_auth():
        """Exigir autenticação - redirecionar para login se não autenticado"""
        if not AuthManager.is_authenticated():
            st.error("🔐 Acesso negado. Faça login para continuar.")
            st.stop()

    @staticmethod
    def get_token() -> Optional[str]:
        """Obter token atual"""
        return st.session_state.get("token")

    @staticmethod
    def increment_login_attempts():
        """Incrementar contador de tentativas de login"""
        st.session_state.login_attempts = st.session_state.get("login_attempts", 0) + 1

    @staticmethod
    def get_login_attempts() -> int:
        """Obter número de tentativas de login"""
        return st.session_state.get("login_attempts", 0)
    
    @staticmethod
    def check_and_refresh_token(auth: 'MicrosoftAuth') -> bool:
        """
        Verifica se o token está próximo de expirar e renova automaticamente.
        Retorna True se o token está válido (renovado ou ainda válido).
        """
        import datetime
        
        if not AuthManager.is_authenticated():
            return False
        
        # Verificar se temos refresh_token
        refresh_token = st.session_state.get("refresh_token")
        if not refresh_token:
            logger.warning("Sem refresh_token disponível. Usuário precisará fazer login novamente.")
            return True  # Token atual ainda pode estar válido
        
        # Verificar expiração do token
        token_expiry = st.session_state.get("token_expiry")
        if not token_expiry:
            return True  # Sem informação de expiração, assumir válido
        
        # Renovar token se faltar menos de 5 minutos para expirar
        time_until_expiry = token_expiry - datetime.datetime.now()
        if time_until_expiry.total_seconds() < 300:  # 5 minutos
            logger.info(f"Token expira em {time_until_expiry.total_seconds():.0f}s. Renovando...")
            
            # Tentar renovar token
            new_token_data = auth.refresh_access_token(refresh_token)
            if new_token_data:
                # Atualizar session_state com novo token
                st.session_state.token = new_token_data["access_token"]
                st.session_state.refresh_token = new_token_data.get("refresh_token", refresh_token)
                st.session_state.token_expiry = datetime.datetime.now() + datetime.timedelta(
                    seconds=new_token_data.get("expires_in", 3600)
                )
                logger.info("Token renovado com sucesso!")
                return True
            else:
                logger.error("Falha ao renovar token. Usuário precisará fazer login novamente.")
                # Limpar autenticação se não conseguir renovar
                AuthManager.logout()
                return False
        
        return True


def create_login_page(auth: MicrosoftAuth) -> bool:
    """
    Criar página de login Microsoft
    Retorna True se login foi bem-sucedido
    """
    AuthManager.init_session_state()

    # Se já autenticado, não mostrar página de login
    if AuthManager.is_authenticated():
        return True

    st.title("🔐 Login Microsoft")
    st.markdown("---")

    # Layout centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### Acesso Seguro ao Dashboard Churn

        Faça login com sua conta Microsoft para acessar o sistema de análise de retenção de laboratórios.
        """)

        # Verificar se há código de autorização na URL
        query_params = st.query_params

        if "code" in query_params:
            # Processar código de autorização
            with st.spinner("🔄 Autenticando..."):
                code = query_params["code"]
                token_data = auth.get_token_from_code(code)

                if token_data and token_data.get("access_token"):
                    access_token = token_data["access_token"]
                    refresh_token = token_data.get("refresh_token")
                    expires_in = token_data.get("expires_in", 3600)
                    
                    user_info = auth.get_user_info(access_token)
                    if user_info:
                        AuthManager.login(user_info, access_token, refresh_token, expires_in)
                        st.success("✅ Login realizado com sucesso!")
                        st.balloons()
                        # Limpar parâmetros da URL
                        st.query_params.clear()
                        return True
                    else:
                        AuthManager.increment_login_attempts()
                        st.error("❌ Erro ao obter informações do usuário")
                        if AuthManager.get_login_attempts() >= 3:
                            st.warning("⚠️ Muitas tentativas falharam. Recarregue a página e tente novamente.")
                        return False
                else:
                    AuthManager.increment_login_attempts()
                    st.error("❌ Falha na autenticação. Verifique suas credenciais.")
                    if AuthManager.get_login_attempts() >= 3:
                        st.warning("⚠️ Muitas tentativas falharam. Recarregue a página e tente novamente.")
                    return False

        elif "error" in query_params:
            # Tratar erros de autenticação
            error = query_params.get("error", [""])[0]
            error_description = query_params.get("error_description", ["Erro desconhecido"])[0]
            st.error(f"❌ Erro de autenticação: {error}")
            st.warning(f"Detalhes: {error_description}")
            return False

        else:
            # Mostrar botão de login
            st.markdown("### 🔑 Entrar com Microsoft")

            # Informações sobre o domínio
            st.info("ℹ️ Use sua conta Microsoft corporativa (@synvia.com) para fazer login.")

            # Botão de login estilizado
            login_url = auth.get_login_url()

            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <a href="{login_url}" style="
                    display: inline-block;
                    padding: 15px 30px;
                    background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.3)'"
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)'">
                    🚀 Entrar com Microsoft
                </a>
            </div>
            """, unsafe_allow_html=True)

            # Informações adicionais
            with st.expander("ℹ️ Sobre a Autenticação"):
                st.markdown("""
                **Por que preciso fazer login?**
                - Acesso seguro aos dados de análise de churn
                - Controle de permissões por usuário
                - Auditoria de atividades no sistema

                **Problemas comuns:**
                - Certifique-se de usar uma conta Microsoft válida
                - Verifique se o navegador permite pop-ups
                - Se o login falhar, tente limpar o cache do navegador
                """)

    return False


def create_user_header():
    """Mostrar informações do usuário e botão de logout na sidebar (discreto)."""
    if not AuthManager.is_authenticated():
        return

    user = AuthManager.get_current_user()
    if not user:
        return

    with st.sidebar:
        display_name = user.get('displayName', 'Usuário')
        email = user.get('mail') or user.get('userPrincipalName', '')

        # Bloco discreto de conta na sidebar
        st.caption("Conta")
        st.markdown(f"👤 {display_name}")
        if email:
            st.caption(f"📧 {email}")

        if st.button("🚪 Logout", key="logout_sidebar", type="secondary", help="Sair da conta"):
            AuthManager.logout()
            st.rerun()


# Função de compatibilidade para código existente
def check_authentication():
    """Função de compatibilidade - verificar se usuário está autenticado"""
    return AuthManager.is_authenticated()


def get_current_user_info():
    """Função de compatibilidade - obter informações do usuário atual"""
    return AuthManager.get_current_user()
