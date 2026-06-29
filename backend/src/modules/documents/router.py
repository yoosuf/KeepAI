from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.models import User
from src.modules.auth.service import get_current_user
from src.modules.documents.models import DocumentChunk
from src.modules.documents.schemas import DocumentDetail, DocumentOut

router = APIRouter()


def get_document_service(request: Request, db: AsyncSession = Depends(get_db)):
    from src.modules.documents.service import DocumentService

    return DocumentService(db, request.app.state.llm_client)


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_documents(user_id=current_user.id)


@router.post("/documents/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    content_text = content.decode("utf-8", errors="replace")
    return await service.create_document(
        user_id=current_user.id,
        filename=file.filename or "unnamed",
        content_type=file.content_type,
        content=content,
        content_text=content_text,
        file_size=len(content),
    )


@router.get("/documents/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: int,
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await service.get_document(document_id, user_id=current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunk_count_result = await db.execute(
        select(func.count()).where(DocumentChunk.document_id == document_id).select_from(DocumentChunk)
    )
    chunk_count = chunk_count_result.scalar_one()
    return DocumentDetail(
        id=doc.id,
        filename=doc.filename,
        content_type=doc.content_type,
        file_size=doc.file_size,
        content_text=doc.content_text,
        chunk_count=chunk_count,
        created_at=doc.created_at,
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    deleted = await service.delete_document(document_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/documents/search")
async def search_documents_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, le=50),
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    return await service.search_documents(user_id=current_user.id, query_text=q, top_k=top_k)


@router.post("/documents/query")
async def query_documents(
    request: Request,
    body: dict,
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    query_text = body.get("query", "")
    if not query_text:
        raise HTTPException(status_code=400, detail="Query is required")
    results = await service.search_documents(user_id=current_user.id, query_text=query_text, top_k=body.get("top_k", 5))
    return {"results": results, "response": f"Found {len(results)} relevant documents"}


@router.post("/documents/{document_id}/embed")
async def embed_document(
    document_id: int,
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    success = await service.generate_embeddings(document_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "embedded"}


@router.post("/documents/search")
async def search_documents(
    request: Request,
    body: dict,
    service=Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    query = body.get("query", "")
    top_k = body.get("top_k", 5)
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    return await service.search_documents(user_id=current_user.id, query_text=query, top_k=top_k)
