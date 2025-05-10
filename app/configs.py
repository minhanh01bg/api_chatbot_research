import toml

import logging


class Config:
    toml_settings = toml.load("../settings.toml")
    # print(config)

    check = True
    ROUTER = '/api/v1' if check == True else ''
    #  DB
    SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite3"
    # SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/fancy"
    #
    MEDIA_URL = "alembic"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log"),  # Ghi log vào file
            logging.StreamHandler()  # Hiển thị log trong console
        ]
    )

    logger = logging.getLogger(__name__)

    # app
    DOMAIN = toml_settings['app']['DOMAIN']

    OPENAI_API_KEY = toml_settings['openai']['OPENAI_API_KEY']

    MONGO_URL = toml_settings['mongo']['MONGO_URL']

    GOOGLE_API_KEY = toml_settings['google']['GOOGLE_API_KEY']

    TAVILY_KEY = toml_settings['tavily']['TAVILY_KEY']
    
    GENMINI_MODEL =toml_settings['google']['GENMINI_MODEL']

configs = Config()
