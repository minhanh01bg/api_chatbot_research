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

    PROMPT_CONFIG_IMAGE_TEXT_2IMAGE = "Provide a detailed objects,colors,style,patterns of this image."
    # 'What color is in the background of the photo above? and what its content is? Please describe in detail the content of the photo, What is the main character in the photo?'

    # aws
    S3_BUCKET_NAME = toml_settings['s3']['S3_BUCKET_NAME']
    AWS_ACCESS_KEY = toml_settings['s3']['AWS_ACCESS_KEY']
    AWS_SECRET_KEY = toml_settings['s3']['AWS_SECRET_KEY']
    REGION_NAME = toml_settings['s3']['REGION_NAME']
    DISTRIBUTION_DOMAIN_NAME = toml_settings['s3']['DISTRIBUTION_DOMAIN_NAME']

    # runpod
    # eduprompt
    API_KEY_EDUPROMPT = toml_settings['runpod']['API_KEY_EDUPROMPT']
    API_URL_TEXT2IMAGE_DYNA = toml_settings['runpod']['API_URL_TEXT2IMAGE_DYNA']
    API_URL_IMAGETEXT2CAPTION_LLAMA_VISION = toml_settings[
        'runpod']['API_URL_IMAGETEXT2CAPTION_LLAMA_VISION']

    API_URL_TEXT2IMAGE_REALISTIC_VISION = toml_settings[
        'runpod']['API_URL_TEXT2IMAGE_REALISTIC_VISION']
    API_URL_TEXT2IMAGE_PONY = toml_settings['runpod']['API_URL_TEXT2IMAGE_PONY']

    # models
    API_URL_DYNA_PONY = toml_settings['runpod']['API_URL_DYNA_PONY']

    # runpod
    # account VMH
    API_KEY_VMH = toml_settings['runpod']['API_KEY_VMH']
    API_URL_ITT = toml_settings['runpod']['API_URL_ITT']

    # accounts hieuvm
    API_KEY_HIEUVM = toml_settings['runpod']['API_KEY_HIEUVM']
    # app
    DOMAIN = toml_settings['app']['DOMAIN']

    OPENAI_API_KEY = toml_settings['openai']['OPENAI_API_KEY']

    MONGO_URL = toml_settings['mongo']['MONGO_URL']

    GOOGLE_API_KEY = toml_settings['google']['GOOGLE_API_KEY']
    GENMINI_MODEL =toml_settings['google']['GENMINI_MODEL']

configs = Config()
