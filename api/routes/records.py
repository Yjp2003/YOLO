"""
Detection records routes: CRUD for detection history.
All operations scoped to the authenticated user via RLS.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from middleware import get_current_user
from supabase_client import db_select, db_insert, db_delete

router = APIRouter()


class DetectionItem(BaseModel):
    classId: int
    className: str
    score: float
    box: List[float]  # [x1, y1, x2, y2]


class RecordCreate(BaseModel):
    time: str
    image: Optional[str] = None  # base64 snapshot
    total_detections: int = 0
    fps: float = 0
    avg_confidence: float = 0
    detections: List[DetectionItem] = []
    video_clips: Optional[list] = None  # list of {index, start_sec, end_sec, data}


class RecordResponse(BaseModel):
    id: str
    user_id: str
    time: str
    image: Optional[str] = None
    total_detections: int
    fps: float
    avg_confidence: float
    detections: list
    video_clips: Optional[list] = None
    created_at: str


@router.get("")
async def list_records(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get detection records for the current user, newest first. Supports pagination."""
    try:
        records = db_select(
            table="detection_records",
            filters={"user_id": user["id"]},
            order="created_at",
            desc=True,
            limit=limit,
            offset=offset,
            token=user["token"],
        )
        return {
            "success": True,
            "records": records,
            "total": len(records),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")


@router.post("")
async def create_record(record: RecordCreate, user: dict = Depends(get_current_user)):
    """Save a new detection record."""
    try:
        data = {
            "user_id": user["id"],
            "time": record.time,
            "image": record.image,
            "total_detections": record.total_detections,
            "fps": record.fps,
            "avg_confidence": record.avg_confidence,
            "detections": [d.model_dump() for d in record.detections],
            "video_clips": record.video_clips,
        }

        result = db_insert(
            table="detection_records",
            data=data,
            token=user["token"],
        )

        if result:
            return {"success": True, "record": result[0]}
        raise HTTPException(status_code=500, detail="保存记录失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存记录失败: {str(e)}")


@router.delete("/{record_id}")
async def delete_record(record_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific detection record."""
    try:
        db_delete(
            table="detection_records",
            filters={"id": record_id, "user_id": user["id"]},
            token=user["token"],
        )
        return {"success": True, "message": "记录已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除记录失败: {str(e)}")
