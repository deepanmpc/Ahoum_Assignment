from typing import Protocol, List
import numpy as np


class Embedder(Protocol):
    @property
    def model_id(self) -> str:
        """Return the unique identifier for the embedding model."""
        ...
        
    @property
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        ...
        
    def embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of strings into a NumPy array of shape (len(texts), dimension)."""
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        
    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError("Please install sentence-transformers to use this embedder.")
            self._model = SentenceTransformer(self.model_name)
        return self._model
        
    @property
    def model_id(self) -> str:
        return self.model_name
        
    @property
    def dimension(self) -> int:
        return self._get_model().get_sentence_embedding_dimension()
        
    def embed(self, texts: List[str]) -> np.ndarray:
        # returns np.ndarray implicitly if return_tensors is not specified in older versions,
        # but let's be explicit and convert to numpy.
        emb = self._get_model().encode(texts, convert_to_numpy=True)
        return np.array(emb, dtype=np.float32)


class FakeDeterministicEmbedder:
    """Mock embedder for unit tests that generates stable pseudo-embeddings."""
    def __init__(self, dim: int = 4):
        self.dim = dim
        
    @property
    def model_id(self) -> str:
        return f"fake-deterministic-{self.dim}"
        
    @property
    def dimension(self) -> int:
        return self.dim
        
    def embed(self, texts: List[str]) -> np.ndarray:
        import hashlib
        res = []
        for t in texts:
            # Deterministic hash array
            h = hashlib.md5(t.encode('utf-8')).digest()
            # Wrap around if dim > length of digest (16)
            vec = []
            for i in range(self.dim):
                vec.append(float(h[i % len(h)]) / 255.0)
            res.append(vec)
        return np.array(res, dtype=np.float32)
