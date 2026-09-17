from __future__ import annotations

from srag.config import Settings
from srag.embedding import OllamaEmbedder
from srag.handoffproof.agent import OllamaSuccessorAgent
from srag.handoffproof.execution import AgentExperimentRunner
from srag.handoffproof.retrieval import HandoffEvidenceRetriever
from srag.handoffproof.service import HandoffProofService


def create_handoff_service(settings: Settings) -> HandoffProofService:
    service = HandoffProofService(
        settings.handoff_dir,
        reference_corpora_root=settings.data_dir / "reference-corpora",
    )
    agent = OllamaSuccessorAgent(
        model=settings.generation_model,
        host=settings.ollama_host,
        context_window=settings.generation_context_tokens,
        max_output_tokens=max(settings.max_output_tokens, 768),
    )
    retriever = HandoffEvidenceRetriever(
        root=settings.handoff_dir / "indexes",
        embedder=OllamaEmbedder(
            model=settings.embedding_model,
            host=settings.ollama_host,
        ),
        top_k=settings.default_top_k,
    )
    service.runner = AgentExperimentRunner(
        agent=agent,
        retriever=retriever,
        store=service.store,
    )
    return service
