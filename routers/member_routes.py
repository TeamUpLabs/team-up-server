from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from database import SessionLocal
from typing import List, Optional
import logging
from schemas.member import MemberCreate, Member, MemberCheck, MemberUpdate
from schemas.project import Project
from crud.member import create_member, get_member_by_email, get_members, get_member, get_member_projects, update_member_by_id, update_member_profile_image_by_id
from crud.project import get_project
import os
from supabase_client import supabase
import random
from utils.sse_manager import project_sse_manager
import json

router = APIRouter(
    prefix="/member",
    tags=["member"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=Member)
async def handle_create_member(
    profileImage: Optional[UploadFile] = File(None),
    payload: Optional[str] = Form(None),
    db: SessionLocal = Depends(get_db)  # type: ignore
):
  try:
    if payload:
      import json
      member_data = MemberCreate(**json.loads(payload))
      
    if not member_data:
      raise HTTPException(status_code=400, detail="Missing required member data")
      
    logging.info(f"Creating new member with email: {member_data.email}")
    existing_member = get_member_by_email(db, member_data.email)
    if existing_member:
        logging.warning(f"Email already exists: {member_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
      
      
    if profileImage:
      profile_image_path = f"{random.randint(1000000000000, 9999999999999)}"
      contents = await profileImage.read()
      try:
        res = supabase.storage.from_("profile-images").upload(file=contents, path=profile_image_path, file_options={"content-type": profileImage.content_type})
        if hasattr(res, 'error') and res.error:
            logging.error(f"Supabase storage error: {res.error}")
            raise HTTPException(status_code=400, detail=f"Failed to upload profile image: {res.error}")
          
        # Create public URL
        public_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/profile-images/{profile_image_path}"
        member_data.profileImage = public_url
      except Exception as e:
        logging.error(f"Supabase storage upload error: {str(e)}")
        # Continue without profile image if upload fails
        member_data.profileImage = None
        
    db_member = create_member(db, member_data)
    logging.info(f"Successfully created member with id: {db_member.id}")
    return db_member
      
  except HTTPException as he:
    logging.error(f"HTTP Exception during member creation: {str(he)}")
    raise
  except Exception as e:
      logging.error(f"Unexpected error during member creation: {str(e)}")
      db.rollback()
      raise HTTPException(
          status_code=500,
          detail="Internal server error occurred while creating member"
      )

@router.post("/check")
def check_member(member_check: MemberCheck, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        member = get_member_by_email(db, member_check.email)
        if member:
            return {"status": "exists", "message": "Member already exists"}
        else:
            return {"status": "not_exists", "message": "Member does not exist"}
    except Exception as e:
        logging.error(f"Unexpected error during member check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[Member])
def read_members(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        members = get_members(db, skip=skip, limit=limit)
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{member_id}", response_model=Member)
def read_member(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        member = get_member(db, member_id)
        if member is None:
            raise HTTPException(status_code=404, detail=f"Member {member_id} not found")
        return member
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.get("/{member_id}/project", response_model=List[Project])
def read_member_projects(member_id: int, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        return get_member_projects(db, member_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.put("/{member_id}")
async def update_member(member_id: int, member_update: MemberUpdate, db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
        updated_member = update_member_by_id(db, member_id, member_update)
        if not updated_member:
            raise HTTPException(status_code=404, detail="Member not found")
            
        if updated_member.projects:
            logging.info(f"Updated member projects: {updated_member.projects}")
            for project_id in updated_member.projects:
                project_data = get_project(db, project_id)
                logging.info(f"Project data: {project_data}")
                await project_sse_manager.send_event(
                    project_id,
                    json.dumps(project_sse_manager.convert_to_dict(project_data))
                )
                logging.info(f"[SSE] Project {project_id} updated from Member {member_id} update.")
        
        logging.info(f"[SSE] Member {member_id} updated from Member update.")
        return updated_member
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@router.put("/{member_id}/profile-image")
async def update_member_profile_image(member_id: int, profileImage: UploadFile = File(None), db: SessionLocal = Depends(get_db)):  # type: ignore
    try:
      public_url = None
      if profileImage:
        profile_image_path = f"{random.randint(1000000000000, 9999999999999)}"
        contents = await profileImage.read()
        try:
          res = supabase.storage.from_("profile-images").upload(file=contents, path=profile_image_path, file_options={"content-type": profileImage.content_type})
          if hasattr(res, 'error') and res.error:
              logging.error(f"Supabase storage error: {res.error}")
              raise HTTPException(status_code=400, detail=f"Failed to upload profile image: {res.error}")
            
          # Create public URL
          public_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/profile-images/{profile_image_path}"
        except Exception as e:
          logging.error(f"Supabase storage upload error: {str(e)}")
          
      updated_member = update_member_profile_image_by_id(db, member_id, public_url)
      if updated_member:
        project_datas = get_project(db, updated_member.projects)
        for project_data in project_datas:
          await project_sse_manager.send_event(
              project_data.id,
              json.dumps(project_sse_manager.convert_to_dict(project_data))
        )
        logging.info(f"[SSE] Member {member_id} updated from Member profile image update.")
      else:
        raise HTTPException(status_code=404, detail="Member not found")
      return updated_member
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))