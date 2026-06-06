from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.session import Session as DbSession
from app.schemas.auth import SessionResponse
from app.core.security import get_refresh_token_hash

router = APIRouter()

@router.get("/", response_model=List[SessionResponse])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(DbSession).filter(
        DbSession.user_id == current_user.id,
        DbSession.is_revoked == False
    ).all()
    return sessions

@router.delete("/{session_id}")
def revoke_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(DbSession).filter(
        DbSession.id == session_id,
        DbSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_revoked = True
    db.commit()
    return {"message": "Session revoked successfully"}

@router.post("/revoke-all")
def revoke_all_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_refresh_token = request.cookies.get("refresh_token")
    
    query = db.query(DbSession).filter(
        DbSession.user_id == current_user.id,
        DbSession.is_revoked == False
    )
    
    if current_refresh_token:
        token_hash = get_refresh_token_hash(current_refresh_token)
        query = query.filter(DbSession.refresh_token_hash != token_hash)
        
    sessions_to_revoke = query.all()
    
    for session in sessions_to_revoke:
        session.is_revoked = True
        
    db.commit()
    return {"message": f"Revoked {len(sessions_to_revoke)} other sessions"}
