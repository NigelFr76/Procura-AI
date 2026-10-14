"""Document chunking service that preserves visual bounding box provenance."""

import uuid
from typing import List
from app.schemas.document import ParsedDocumentResult, DocumentChunk


class DocumentChunker:
    """Partitions parsed document content into search chunks while preserving coordinates."""

    @classmethod
    def chunk(
        cls,
        parsed_doc: ParsedDocumentResult,
        target_chunk_chars: int = 500,
        min_chunk_chars: int = 80,
    ) -> List[DocumentChunk]:
        """Convert page text blocks into chunks with aggregated bounding box coordinates."""
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        # Group by page number first to maintain strict page provenance
        blocks_by_page = {}
        for block in parsed_doc.text_blocks:
            blocks_by_page.setdefault(block.page_number, []).append(block)

        for page_num, blocks in sorted(blocks_by_page.items()):
            current_texts: List[str] = []
            current_bboxes: List[List[float]] = []
            current_len = 0

            for b in blocks:
                current_texts.append(b.text)
                current_bboxes.append(b.bbox)
                current_len += len(b.text)

                if current_len >= target_chunk_chars:
                    # Merge bounding boxes: [min_x1, min_y1, max_x2, max_y2]
                    union_bbox = [
                        min(bb[0] for bb in current_bboxes),
                        min(bb[1] for bb in current_bboxes),
                        max(bb[2] for bb in current_bboxes),
                        max(bb[3] for bb in current_bboxes),
                    ]

                    chunk_id = f"{parsed_doc.document_id}:{page_num}:{chunk_idx}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            document_id=parsed_doc.document_id,
                            page_number=page_num,
                            bbox=union_bbox,
                            text="\n".join(current_texts),
                            metadata={
                                "file_name": parsed_doc.file_name,
                                "block_count": len(current_texts),
                            },
                        )
                    )
                    chunk_idx += 1
                    current_texts = []
                    current_bboxes = []
                    current_len = 0

            # Flush any remaining text on the page
            if current_texts:
                union_bbox = [
                    min(bb[0] for bb in current_bboxes),
                    min(bb[1] for bb in current_bboxes),
                    max(bb[2] for bb in current_bboxes),
                    max(bb[3] for bb in current_bboxes),
                ]
                chunk_id = f"{parsed_doc.document_id}:{page_num}:{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=parsed_doc.document_id,
                        page_number=page_num,
                        bbox=union_bbox,
                        text="\n".join(current_texts),
                        metadata={
                            "file_name": parsed_doc.file_name,
                            "block_count": len(current_texts),
                        },
                    )
                )
                chunk_idx += 1

        return chunks
