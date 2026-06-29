import json
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.interfaces.llm_interface import LLMInterface
from src.modules.documents.models import Document, DocumentChunk


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


class DocumentService:
    def __init__(self, db: AsyncSession, llm_client: LLMInterface):
        self.db = db
        self.llm_client = llm_client

    async def create_document(
        self,
        user_id: int,
        filename: str,
        content_type: Optional[str],
        content: Optional[bytes],
        content_text: Optional[str],
        file_size: Optional[int],
    ) -> Document:
        doc = Document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            content=content,
            content_text=content_text,
            file_size=file_size,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        if content_text:
            chunks = chunk_text(content_text)
            for i, chunk in enumerate(chunks):
                dc = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk,
                )
                self.db.add(dc)
            await self.db.commit()

        return doc

    async def list_documents(self, user_id: int) -> List[Document]:
        query = select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_document(self, document_id: int, user_id: int) -> Optional[Document]:
        query = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def delete_document(self, document_id: int, user_id: int) -> bool:
        query = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await self.db.execute(query)
        doc = result.scalars().first()
        if not doc:
            return False
        await self.db.delete(doc)
        await self.db.commit()
        return True

    async def generate_embeddings(self, document_id: int, user_id: int) -> bool:
        doc = await self.get_document(document_id, user_id)
        if not doc:
            return False

        from sqlalchemy import select as sel

        chunks_query = sel(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)
        result = await self.db.execute(chunks_query)
        chunks = result.scalars().all()

        for chunk in chunks:
            try:
                embedding = await self.llm_client.generate(
                    prompt=f"Generate an embedding for this text: {chunk.content[:100]}",
                    model=settings.OLLAMA_MODEL,
                )
                chunk.embedding = json.dumps(embedding.get("response_text", ""))
            except Exception:
                chunk.embedding = "[]"

        await self.db.commit()
        return True

    async def search_documents(self, user_id: int, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query = select(DocumentChunk).join(Document).where(Document.user_id == user_id)
        result = await self.db.execute(query)
        chunks = result.scalars().all()

        doc_map: Dict[int, Document] = {}
        doc_query = select(Document).where(Document.user_id == user_id)
        docs_result = await self.db.execute(doc_query)
        for d in docs_result.scalars().all():
            doc_map[d.id] = d

        scored = []
        for chunk in chunks:
            score = self._simple_score(query_text, chunk.content)
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        seen_docs = set()
        for score, chunk in scored[:top_k]:
            doc = doc_map.get(chunk.document_id)
            if doc and doc.id not in seen_docs:
                seen_docs.add(doc.id)
            results.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": doc.filename if doc else "unknown",
                    "content": chunk.content[:500],
                    "score": round(score, 4),
                }
            )

        return results

    @staticmethod
    def _simple_score(query: str, text: str) -> float:
        query_words = set(query.lower().split())
        text_lower = text.lower()
        if not query_words:
            return 0.0
        matches = sum(1 for w in query_words if w in text_lower)
        return matches / len(query_words)
