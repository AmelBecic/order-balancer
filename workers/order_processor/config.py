from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # These variables are loaded automatically from the environment
    MONGODB_URL: str
    DATABASE_NAME: str
    RABBITMQ_URL: str

    # --- Add these new settings for blockchain interaction ---
    SETTLEMENT_CONTRACT_ADDRESS: str
    SEPOLIA_RPC_URL: str
    BACKEND_WALLET_PRIVATE_KEY: str

    class Config:
        # Pydantic will look for a .env file if this is set,
        # but Docker Compose already places them in the environment.
        case_sensitive = True

settings = Settings()
