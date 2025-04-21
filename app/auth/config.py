import toml

class Settings:
    toml_settings = toml.load("../settings.toml")
    
    SECRET_KEY = toml_settings['auth']['SECRET_KEY']
    ALGORITHM = toml_settings['auth']['ALGORITHM']
    ACCESS_TOKEN_EXPIRE_MINUTES = toml_settings['auth']['ACCESS_TOKEN_EXPIRE_MINUTES']

settings = Settings()