"""
API routes for DocumentStore functionality.
Provides endpoints for consuming NVD data and retrieving stored information.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from database.document_store import DocumentStore
from database.mongodb import MongoDBConnection

router = APIRouter(prefix="/document-store", tags=["Document Store"])

async def get_document_store() -> DocumentStore:
    """Dependency to get DocumentStore instance."""
    return DocumentStore()

@router.post("/consume-nvd")
async def consume_nvd_data(
    document_store: DocumentStore = Depends(get_document_store)
) -> Dict[str, Any]:
    """
    Consume data from NVD service and store in MongoDB.
    
    Returns:
        Success message and operation details
    """
    try:
        success = await document_store.consume_and_store()
        
        if success:
            return {
                "status": "success",
                "message": "NVD data successfully consumed and stored",
                "timestamp": "2025-07-13T10:00:00Z"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to consume and store NVD data"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error consuming NVD data: {str(e)}"
        )

@router.get("/search-sessions")
async def get_search_sessions(
    limit: int = 50,
    document_store: DocumentStore = Depends(get_document_store)
) -> List[Dict[str, Any]]:
    """
    Get recent search sessions for report generation.
    
    Args:
        limit: Maximum number of sessions to return
        
    Returns:
        List of search sessions
    """
    try:
        sessions = await document_store.get_search_sessions(limit)
        return sessions
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching search sessions: {str(e)}"
        )

@router.get("/vulnerabilities/{session_id}")
async def get_vulnerabilities_by_session(
    session_id: str,
    document_store: DocumentStore = Depends(get_document_store)
) -> List[Dict[str, Any]]:
    """
    Get vulnerabilities for a specific search session.
    
    Args:
        session_id: ID of the search session
        
    Returns:
        List of vulnerabilities for the session
    """
    try:
        vulnerabilities = await document_store.get_vulnerabilities_by_session(session_id)
        return vulnerabilities
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching vulnerabilities for session {session_id}: {str(e)}"
        )

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for DocumentStore service."""
    try:
        # Test MongoDB connection
        db = MongoDBConnection.get_database()
        await db.list_collection_names()
        
        return {
            "status": "healthy",
            "service": "document-store",
            "mongodb": "connected"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
