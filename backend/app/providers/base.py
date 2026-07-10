from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AudioResult:
    audio_bytes: bytes
    duration_seconds: float
    format: str = "mp3"


@dataclass
class ImageResult:
    image_bytes: bytes
    format: str = "png"


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str) -> AudioResult: ...

    @abstractmethod
    async def list_voices(self) -> list[dict]: ...


class ImageProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        reference_image_url: str | None = None,
    ) -> ImageResult: ...


class VideoProvider(ABC):
    """Mode B（AI短片拼接）预留扩展点，本次 MVP 不实现。"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        reference_image_url: str | None = None,
    ) -> bytes: ...
