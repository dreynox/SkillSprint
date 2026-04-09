import os
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from auth import get_current_user
from database import SessionLocal
from models import Message, User
from schemas import MessageCreate, MessageOut

router = APIRouter(prefix="/messages", tags=["messages"])

UPLOAD_DIR = "backend/uploads/messages"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/conversations", response_model=List[dict])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of all conversations for the current user"""
    conversations = (
        db.query(Message)
        .filter(
            or_(
                Message.sender_id == current_user.id,
                Message.recipient_id == current_user.id,
            )
        )
        .order_by(Message.created_at.desc())
        .all()
    )

    # Build unique conversations
    conv_map = {}
    for msg in conversations:
        other_user_id = (
            msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        )
        if other_user_id not in conv_map:
            other_user = db.query(User).filter(User.id == other_user_id).first()
            conv_map[other_user_id] = {
                "user_id": other_user.id,
                "name": other_user.name,
                "email": other_user.email,
                "avatar_url": other_user.avatar_url,
                "last_message": msg.content or f"[{msg.media_type}]",
                "last_message_time": msg.created_at.isoformat(),
                "unread_count": 0,
            }

        # Count unread messages
        if msg.recipient_id == current_user.id and not msg.is_read:
            conv_map[other_user_id]["unread_count"] += 1

    return list(conv_map.values())


@router.get("/with/{user_id}", response_model=List[MessageOut])
def get_messages_with_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all messages between current user and another user"""
    messages = (
        db.query(Message)
        .filter(
            or_(
                and_(
                    Message.sender_id == current_user.id,
                    Message.recipient_id == user_id,
                ),
                and_(
                    Message.sender_id == user_id,
                    Message.recipient_id == current_user.id,
                ),
            )
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    # Mark received messages as read
    for msg in messages:
        if msg.recipient_id == current_user.id and not msg.is_read:
            msg.is_read = True
    db.commit()

    # Debug logging: print full thread in server terminal for easier verification.
    print(
        f"[messages] thread current_user={current_user.id} peer_user={user_id} total={len(messages)}"
    )
    for msg in messages:
        print(
            "[messages]",
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "recipient_id": msg.recipient_id,
                "media_type": msg.media_type,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            },
        )

    return messages


@router.post("/send", response_model=MessageOut)
def send_message(
    msg_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a text message"""
    if not msg_data.content and msg_data.media_type == "text":
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    db_message = Message(
        sender_id=current_user.id,
        recipient_id=msg_data.recipient_id,
        content=msg_data.content,
        media_type=msg_data.media_type or "text",
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    print(
        "[messages] sent",
        {
            "id": db_message.id,
            "sender_id": db_message.sender_id,
            "recipient_id": db_message.recipient_id,
            "media_type": db_message.media_type,
            "content": db_message.content,
            "created_at": db_message.created_at.isoformat() if db_message.created_at else None,
        },
    )

    return db_message


@router.post("/upload/{user_id}", response_model=MessageOut)
async def upload_and_send_media(
    user_id: int,
    file: UploadFile = File(...),
    media_type: str = "file",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a file/image/video and send as message"""
    if media_type not in ["image", "video", "file", "voice"]:
        raise HTTPException(status_code=400, detail="Invalid media type")

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Create message record
        db_message = Message(
            sender_id=current_user.id,
            recipient_id=user_id,
            content=file.filename,
            media_type=media_type,
            file_path=f"/messages/file/{filename}",
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/file/{filename}")
async def get_file(filename: str):
    """Serve uploaded file"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    from fastapi.responses import FileResponse

    return FileResponse(file_path)


@router.get("/{message_id}/read")
def mark_as_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark message as read"""
    message = (
        db.query(Message)
        .filter(
            and_(Message.id == message_id, Message.recipient_id == current_user.id)
        )
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.is_read = True
    db.commit()
    return {"status": "ok"}
