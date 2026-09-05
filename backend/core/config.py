from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Fenix Messenger"
    database_url: str = "sqlite:///./fenix.db"
    jwt_secret: str = "CHANGE_THIS_IN_PRODUCTION_USE_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 24 * 365
    upload_dir: str = "./uploads"
    cors_origins: str = "*"
    otp_pepper: str = "CHANGE_ME_OTP_PEPPER"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_verify_service_sid: str = ""
    brevo_api_key: str = ""
    mail_from: str = ""
    mail_from_name: str = "Fenix Messenger"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_dev_mode: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
