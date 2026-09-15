from abc import ABC, abstractmethod

from PIL import Image


class AIRecreateError(Exception):
    pass


class AIRecreateProvider(ABC):
    """Pluggable interface for Recreate Studio Mode. Implementations take an
    enhanced source photo + a rendered prompt and return a regenerated
    front-facing studio product photo. Must raise AIRecreateError (never a
    provider-specific exception) on failure so the pipeline can route
    predictably to the review queue."""

    @abstractmethod
    def recreate(self, image: Image.Image, prompt: str) -> Image.Image:
        raise NotImplementedError
