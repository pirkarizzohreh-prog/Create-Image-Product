import base64
import io

import requests
from django.conf import settings
from PIL import Image

from .base import AIRecreateError, AIRecreateProvider

OPENAI_IMAGES_EDIT_URL = "https://api.openai.com/v1/images/edits"


class OpenAIRecreateProvider(AIRecreateProvider):
    """Uses OpenAI's image-edit endpoint to regenerate the product as a
    front-facing studio photo while preserving identity, guided by the
    admin-configured prompt template. Requires OPENAI_API_KEY."""

    def __init__(self, api_key: str = None, model: str = None, timeout: int = 90):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_IMAGE_MODEL
        self.timeout = timeout

    def recreate(self, image: Image.Image, prompt: str) -> Image.Image:
        if not self.api_key:
            raise AIRecreateError("OPENAI_API_KEY is not configured.")

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)

        try:
            response = requests.post(
                OPENAI_IMAGES_EDIT_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={
                    "model": self.model,
                    "prompt": prompt,
                    "size": "1024x1024",
                    "n": 1,
                },
                files={"image": ("source.png", buf, "image/png")},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise AIRecreateError(f"OpenAI request failed: {exc}") from exc

        if response.status_code != 200:
            raise AIRecreateError(f"OpenAI image edit failed ({response.status_code}): {response.text[:500]}")

        payload = response.json()
        try:
            item = payload["data"][0]
        except (KeyError, IndexError) as exc:
            raise AIRecreateError(f"Unexpected OpenAI response shape: {payload}") from exc

        if "b64_json" in item:
            image_bytes = base64.b64decode(item["b64_json"])
        elif "url" in item:
            img_resp = requests.get(item["url"], timeout=self.timeout)
            img_resp.raise_for_status()
            image_bytes = img_resp.content
        else:
            raise AIRecreateError(f"OpenAI response had neither b64_json nor url: {item}")

        try:
            result = Image.open(io.BytesIO(image_bytes))
            result.load()
        except Exception as exc:
            raise AIRecreateError(f"Could not decode OpenAI image response: {exc}") from exc

        return result.convert("RGB")
