# Cthulhu News

Cthulhu-flavored news based on real news articles

## Embeddings

Scene embeddings use a local [fastembed](https://github.com/qdrant/fastembed)
(ONNX) model — `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions — so the
container needs no `torch`. Configure via env:

- `EMBEDDING_BACKEND` — embedding backend; default `local` (the only backend
  implemented today). A cloud backend can be added behind the same seam in
  `web/embeddings.py`.
- `EMBEDDING_CACHE_DIR` — directory where the ONNX model is cached. In Docker it
  is set to `/app/.fastembed_cache` and bind-mounted to `./web/.fastembed_cache`
  so the ~90 MB model downloads once and survives restarts. Leave it unset for
  local runs to use fastembed's default cache.