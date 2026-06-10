"""Text embedding generation behind a swappable provider seam."""

from __future__ import annotations

import numpy as np
from dotenv import find_dotenv, load_dotenv
from envparse import env

from shared.log_utils import logger

load_dotenv(find_dotenv())

EMBEDDING_BACKEND = env.str("EMBEDDING_BACKEND", default="local")
EMBEDDING_MODEL = env.str("EMBEDDING_MODEL", default="sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_VECTOR_SIZE = env.int("EMBEDDING_VECTOR_SIZE", default=384)
EMBEDDING_CACHE_DIR = env.str("EMBEDDING_CACHE_DIR", default=None)
EMBEDDING_MAX_INPUT_LENGTH = env.int("EMBEDDING_MAX_INPUT_LENGTH", default=10000)
EPS = 1e-4


_provider: EmbeddingProvider | None = None


class EmbeddingProvider:
    """Base class for embedding providers."""

    dimension: int

    def embed(self, text: str) -> np.ndarray:
        """Return a raw (un-normalized) embedding vector for ``text``."""
        ...


class LocalEmbeddingProvider(EmbeddingProvider):
    """fastembed / ONNX backend running all-MiniLM-L6-v2 on CPU."""

    dimension: int = EMBEDDING_VECTOR_SIZE

    def __init__(self) -> None:
        self._model = None

    def _get_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            logger.info("Loading fastembed model")
            self._model = TextEmbedding(model_name=EMBEDDING_MODEL, cache_dir=EMBEDDING_CACHE_DIR)
            logger.info("Embedding model loaded")
        return self._model

    def embed(self, text: str) -> np.ndarray:
        model = self._get_model()
        return next(iter(model.embed([text])))


class CloudEmbeddingProvider(EmbeddingProvider):
    """Placeholder for a future cloud embedding backend, e.g. OpenAI or Cohere."""

    dimension: int = EMBEDDING_VECTOR_SIZE

    def embed(self, text: str) -> np.ndarray:
        raise NotImplementedError("Cloud embedding provider not implemented yet")


def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider (cached singleton)."""
    global _provider
    if _provider is None:
        if EMBEDDING_BACKEND == "local":
            _provider = LocalEmbeddingProvider()
        elif EMBEDDING_BACKEND == "cloud":
            _provider = CloudEmbeddingProvider()
        else:
            raise ValueError(f"Unknown EMBEDDING_BACKEND={EMBEDDING_BACKEND!r}")
    return _provider


def generate_embedding_vector(text: str) -> np.ndarray:
    """Generate a normalized float32 embedding vector for ``text``.

    Provider-agnostic: handles empty/long text and L2-normalizes the result so a
    dot product equals cosine similarity for any backend.
    """
    text = text.strip()
    provider = get_embedding_provider()
    if len(text) == 0:
        logger.warning("Empty text provided for embedding generation")
        return np.zeros(provider.dimension, dtype=np.float32)
    if len(text) > EMBEDDING_MAX_INPUT_LENGTH:
        logger.warning(f"Text for embedding is long length={len(text)}")

    embedding = np.asarray(provider.embed(text), dtype=np.float32)
    norm = np.linalg.norm(embedding)
    embedding = embedding / (norm + EPS)
    return embedding.astype(np.float32)
