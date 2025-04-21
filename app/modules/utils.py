from urllib.parse import urlparse
import aiohttp
from configs import configs
from fastapi import UploadFile
from PIL import Image
import base64
import io
import uuid
import random
import numpy as np
from datetime import datetime
import re

session = None


async def init_session():
    global session
    if session is None:
        session = aiohttp.ClientSession()


async def close_session():
    global session
    if session:
        await session.close()
        session = None


async def call_api(api_key, url, payload):
    global session
    if session is None:
        print("Init session")
        await init_session()

    headers = {"Authorization": f"Bearer {api_key}",
               "Content-Type": "application/json"}

    async with session.post(url, json={"input": payload}, headers=headers) as response:
        api_response = await response.json()

    return api_response


def random_filename(user_id: str, extension='png'):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return f"{user_id}_{timestamp}_{uuid.uuid4().hex}.{extension}"


def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)


def save_base64_image(base64_image: str, image_url: str):
    Image.open(io.BytesIO(base64.b64decode(base64_image))).save(image_url)


async def convert_to_base64(file: UploadFile):
    # Read the uploaded file as bytes
    image_bytes = await file.read()
    # Convert bytes to base64 string
    base64_str = base64.b64encode(image_bytes).decode("utf-8")

    return base64_str


def pil_to_base64(pil_img, format='PNG'):
    buffered = io.BytesIO()
    pil_img.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str


def get_url_image(image_url: str):
    """
    :param image_url:
    http://localhost:7000/app/alembic/example.png
    return: app/alembic/example.png
    """
    image_ = urlparse(image_url)
    image = image_.path
    image = image[1:]
    return image


def extract_assistant_response(text):
    match = re.search(
        r"<\|start_header_id\|>assistant<\|end_header_id\|>\n\n(.*?)(?:<\|eot_id\|>|$)", text, re.DOTALL
    )
    if match:
        return match.group(1).strip()  # get content of assistant
    return None


async def image_text_2text(base64_image: str):
    configs.logger.info('Create text from image and text')
    payload_imgtext2img = {"prompt": configs.PROMPT_CONFIG_IMAGE_TEXT_2IMAGE,
                           "source": base64_image}
    imgtxt2image_response = await call_api(configs.API_KEY_EDUPROMPT, configs.API_URL_IMAGETEXT2CAPTION_LLAMA_VISION, payload=payload_imgtext2img)
    output_it2txt = imgtxt2image_response.get('output')
    it2text = output_it2txt.get('text')
    # print(f"Log image to caption: {it2text}")
    it2text = extract_assistant_response(it2text)
    return it2text


def generate_seed():
    return random.randint(0, 10**18 - 1)

