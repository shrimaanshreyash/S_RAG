from __future__ import annotations

from ollama import Client
from tenacity import retry, stop_after_attempt, wait_exponential


class EmbeddingCallMetrics:
    def __init__(self) -> None:
        self.total_seconds = 0.0
        self.load_seconds = 0.0
        self.eval_seconds = 0.0
        self.input_tokens = 0
        self.dimensions = 0


class OllamaEmbedder:
    def __init__(
        self,
        model: str,
        host: str = "http://127.0.0.1:11434",
        batch_size: int = 16,
    ) -> None:
        self.model = model
        self.client = Client(host=host)
        self.batch_size = batch_size
        self.last_metrics = EmbeddingCallMetrics()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            vectors.extend(self._embed(texts[start : start + self.batch_size], keep_alive="10m"))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], keep_alive="10m")[0]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4), reraise=True)
    def _embed(self, texts: list[str], keep_alive: float | str | None) -> list[list[float]]:
        response = self.client.embed(
            model=self.model,
            input=texts,
            truncate=True,
            keep_alive=keep_alive,
            options={"num_gpu": 0},
        )
        self.last_metrics.total_seconds = (response.total_duration or 0) / 1_000_000_000
        self.last_metrics.load_seconds = (response.load_duration or 0) / 1_000_000_000
        self.last_metrics.eval_seconds = (response.prompt_eval_duration or 0) / 1_000_000_000
        self.last_metrics.input_tokens = response.prompt_eval_count or 0
        self.last_metrics.dimensions = len(response.embeddings[0]) if response.embeddings else 0
        return [list(vector) for vector in response.embeddings]
