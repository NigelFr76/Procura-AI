"""Unit tests for hybrid search and Reciprocal Rank Fusion (RRF)."""

import uuid
from app.schemas.document import DocumentChunk
from app.services.retrieval.hybrid import HybridRetriever


def test_reciprocal_rank_fusion():
    """Verify RRF rank calculation and list interleaving."""
    # List 1: ["doc1", "doc2", "doc3"]
    # List 2: ["doc2", "doc1", "doc4"]
    list1 = ["doc1", "doc2", "doc3"]
    list2 = ["doc2", "doc1", "doc4"]

    merged = HybridRetriever.reciprocal_rank_fusion(
        vector_ranked_items=list1,
        keyword_ranked_items=list2,
        id_fn=lambda x: x,
        top_k=4,
        k=60,
    )

    # doc1 and doc2 appear in both lists (ranks 1 and 2)
    # doc1 score: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.01639 + 0.01613 = 0.03252
    # doc2 score: 1/(60+2) + 1/(60+1) = 0.03252
    assert len(merged) == 4
    top_two_ids = {merged[0][0], merged[1][0]}
    assert top_two_ids == {"doc1", "doc2"}
    assert merged[0][1] > merged[2][1] # Dual appearances beat single appearance


def test_simple_keyword_search():
    """Verify term frequency in-memory search."""
    doc_id = uuid.uuid4()
    c1 = DocumentChunk(
        chunk_id="c1", document_id=doc_id, page_number=1, bbox=[0, 0, 1, 1],
        text="The titanium turbine casing requires ISO 9001 certification."
    )
    c2 = DocumentChunk(
        chunk_id="c2", document_id=doc_id, page_number=1, bbox=[0, 0, 1, 1],
        text="Payment terms are Net 30 with standard delivery packaging."
    )

    results = HybridRetriever.simple_keyword_search("ISO 9001 turbine", [c1, c2])
    assert len(results) == 1
    assert results[0].chunk_id == "c1"
