"""Hybrid retrieval combining semantic vector search and keyword full-text search via RRF."""

import math
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from app.schemas.document import DocumentChunk


class HybridRetriever:
    """Combines dense semantic vector search and sparse keyword search via Reciprocal Rank Fusion (RRF)."""

    RRF_K = 60 # Standard smoothing constant

    @classmethod
    def reciprocal_rank_fusion(
        cls,
        vector_ranked_items: List[Any],
        keyword_ranked_items: List[Any],
        id_fn: Callable[[Any], str],
        top_k: int = 5,
        k: int = RRF_K,
    ) -> List[Tuple[Any, float]]:
        """Merge two ranked lists using Reciprocal Rank Fusion.
        
        Formula:
        RRF_Score(d) = (1 / (k + rank_vector(d))) + (1 / (k + rank_keyword(d)))
        """
        rrf_scores: Dict[str, float] = {}
        item_map: Dict[str, Any] = {}

        # Process vector ranks (1-indexed)
        for rank, item in enumerate(vector_ranked_items, start=1):
            item_id = id_fn(item)
            item_map[item_id] = item
            rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + (1.0 / (k + rank))

        # Process keyword ranks (1-indexed)
        for rank, item in enumerate(keyword_ranked_items, start=1):
            item_id = id_fn(item)
            item_map[item_id] = item
            rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + (1.0 / (k + rank))

        # Sort by composite RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        return [(item_map[item_id], rrf_scores[item_id]) for item_id in sorted_ids[:top_k]]

    @classmethod
    def simple_keyword_search(
        cls,
        query: str,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """In-memory keyword search scoring chunks based on term frequency."""
        query_terms = [re.escape(t.lower()) for t in re.split(r"\W+", query) if len(t) > 2]
        if not query_terms:
            return chunks

        scored_chunks: List[Tuple[DocumentChunk, int]] = []
        for chunk in chunks:
            chunk_lower = chunk.text.lower()
            score = 0
            for term in query_terms:
                matches = re.findall(rf"\b{term}", chunk_lower)
                score += len(matches)
            if score > 0:
                scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored_chunks]

    @classmethod
    def simple_vector_search(
        cls,
        query_vector: List[float],
        indexed_vectors: List[Tuple[DocumentChunk, List[float]]],
    ) -> List[DocumentChunk]:
        """In-memory cosine similarity search."""
        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.sqrt(sum(a * a for a in v1)) or 1e-9
            norm2 = math.sqrt(sum(b * b for b in v2)) or 1e-9
            return dot / (norm1 * norm2)

        scored = [
            (chunk, cosine_similarity(query_vector, vec))
            for chunk, vec in indexed_vectors
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in scored]
