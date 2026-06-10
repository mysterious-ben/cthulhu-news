import numpy as np
import pytest

from shared.embed_utils import EMBEDDING_VECTOR_SIZE, generate_embedding_vector
from web.mapping import EMBEDDING_VECTOR_SIZE as MAPPING_EMBEDDING_VECTOR_SIZE


def test_embedding_equal_dims():
    assert EMBEDDING_VECTOR_SIZE == MAPPING_EMBEDDING_VECTOR_SIZE, (
        "Embedding vector size mismatch between web.embeddings and web.mapping"
    )


@pytest.mark.integration
def test_embedding_shape_dtype_normalized():
    v = generate_embedding_vector("The ancient one stirs beneath the waves.")
    assert v.shape == (EMBEDDING_VECTOR_SIZE,)
    assert v.dtype == np.float32
    assert np.isclose(np.linalg.norm(v), 1.0, atol=1e-4)


def test_empty_text_returns_zero_vector():
    v = generate_embedding_vector("   ")
    assert v.shape == (EMBEDDING_VECTOR_SIZE,)
    assert v.dtype == np.float32
    assert np.allclose(v, 0.0)


@pytest.mark.integration
def test_semantic_similarity_ordering():
    a = generate_embedding_vector("The cat sat on the warm windowsill.")
    b = generate_embedding_vector("A kitten rested by the sunny window.")
    c = generate_embedding_vector("Quarterly bond yields rose across markets.")
    assert float(np.dot(a, b)) > float(np.dot(a, c))
