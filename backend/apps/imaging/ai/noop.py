from PIL import Image

from .base import AIRecreateProvider


class NoopRecreateProvider(AIRecreateProvider):
    """Passthrough provider used when no AI_RECREATE_PROVIDER/API key is
    configured, so the rest of the pipeline (background removal, white
    composite, squaring, QC) remains fully testable offline. Returns the
    input image unchanged."""

    def recreate(self, image: Image.Image, prompt: str) -> Image.Image:
        return image.copy()
