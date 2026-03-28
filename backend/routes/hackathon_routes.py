from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Hackathon
from schemas import HackathonCreate, HackathonOut

router = APIRouter()


@router.post("", response_model=HackathonOut, status_code=status.HTTP_201_CREATED)
def create_hackathon(payload: HackathonCreate, db: Session = Depends(get_db)):
    hackathon = Hackathon(**payload.model_dump())
    db.add(hackathon)
    db.commit()
    db.refresh(hackathon)
    return hackathon


@router.get("", response_model=List[HackathonOut])
def list_hackathons(active_only: bool = Query(False), db: Session = Depends(get_db)):
    query = db.query(Hackathon)
    if active_only:
        query = query.filter(Hackathon.is_active.is_(True))
    return query.order_by(Hackathon.id.asc()).all()
