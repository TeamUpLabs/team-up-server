import logging
import json
from sqlalchemy.orm import Session
from models.member import Member as MemberModel
from schemas.member import MemberCreate
from auth import get_password_hash

def create_member(db: Session, member: MemberCreate):
    try:
        logging.info("Creating new member")
        member_data = member.dict()
        member_data["password"] = get_password_hash(member.password)
        
        # Ensure JSON fields are properly handled
        json_fields = ['skills', 'projects', 'workingHours', 'languages', 'socialLinks']
        for field in json_fields:
            if field in member_data and member_data[field] is not None:
                if isinstance(member_data[field], str):
                    member_data[field] = json.loads(member_data[field])
        
        db_member = MemberModel(**member_data)
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return db_member
    except Exception as e:
        logging.error(f"Error in create_member: {str(e)}")
        db.rollback()
        raise

def get_member(db: Session, member_id: int):
    return db.query(MemberModel).filter(MemberModel.id == member_id).first()

def get_member_by_email(db: Session, email: str):
    return db.query(MemberModel).filter(MemberModel.email == email).first()

def get_members(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MemberModel).offset(skip).limit(limit).all()