import logging
import structlog
from pydantic_settings import BaseSettings
import platform

class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO" 
    
    # LLM
    OPENAI_API_KEY: str = "your_openai_key_here"
    GROQ_API_KEY: str = "your_groq_key_here"

    # PostgreSQL
    PG_DB_HOST: str = "mysqlawxdb-ch2-a3p.dbaas.comcast.net"
    PG_DB_PORT: int = 5432
    PG_DB_NAME: str = "chatops_db"
    PG_DB_USER: str = "chatops"
    PG_DB_PASSWORD: str
    
    # Azure
    AZURE_TENANT_ID: str
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    
    # Placeholder for redirect (dynamically set later)
    REDIRECT_URI: str = ""

    # Cloud Foundry
    CF_USERNAME: str = "cdvprov"
    CF_PASSWORD: str
    
    # OAuth2
    TOKEN_URL: str = "https://sat-prod.codebig2.net/v2/ws/token.oauth2"

    # ChatOps Service
    SCOPE_CHATOPS_SERVICE: str = "sfa:tars-chatops"
    CLIENT_ID_CHATOPS: str = "sfa-tars-ira-prod"
    CLIENT_SECRET_CHATOPS_SERVICE: str
    
    BASE_URL_CHATOPS_SERVICE: str = "https://chatops-service.xsp.comcast.net/api/v1"
    # BASE_URL_CHATOPS_SERVICE: str = "http://127.0.0.1:8000/api/v1"
    API_URL_CHATOPS_CF_RESTART: str = ""
    # API_URL_IS_APP_AVAIL_TO_USER: str = ""
    API_URL_CHATOPS_CF_START: str = ""
    API_URL_CHATOPS_CF_STOP: str = ""
    API_URL_CHATOPS_CF_CHECK_HEALTH: str = ""

    def model_post_init(self, __context):
        # Set Azure REDIRECT_URI based on OS
        if not self.REDIRECT_URI:
            system = platform.system()
            if system in ("Windows", "Darwin"):
                uri = "http://localhost:8501"
            else:
                uri = "https://chatops-ui.wc-g2.cf.comcast.net/"
            object.__setattr__(self, "REDIRECT_URI", uri)

        # Set dependent API endpoint
        object.__setattr__(
            self,
            "API_URL_CHATOPS_CF_RESTART",
            # self.BASE_URL_CHATOPS_SERVICE + "/cloudfoundry/restart-application-simulated"
            self.BASE_URL_CHATOPS_SERVICE + "/cloudfoundry/restart-application"
        )
        
        object.__setattr__(
            self,
            "API_URL_CHATOPS_CF_START",
            self.BASE_URL_CHATOPS_SERVICE + "/cloudfoundry/start-application"
        )

        object.__setattr__(
            self,
            "API_URL_CHATOPS_CF_STOP",
            self.BASE_URL_CHATOPS_SERVICE + "/cloudfoundry/stop-application"
        )

        object.__setattr__(
            self,
            "API_URL_CHATOPS_CF_CHECK_HEALTH",
            self.BASE_URL_CHATOPS_SERVICE + "/cloudfoundry/check-application-health"
        )        
        
        # Not part of tools but used in the app
        object.__setattr__(
            self,
            "API_URL_IS_APP_AVAIL_TO_USER",
            self.BASE_URL_CHATOPS_SERVICE + "/cloudfoundry/is-application-available-to-user"
        )        

    class Config:
        env_file = ".env"

# Load settings
settings = Settings()

# Logging Configuration
def setup_logging():
    logging.basicConfig(
        format="%(message)s",
        level=settings.LOG_LEVEL,
        handlers=[logging.StreamHandler()],
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

setup_logging()