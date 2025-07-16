from datetime import date, datetime
from app.schema.enums import PrivacyLevel, Gender
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class ProfileBase(BaseModel):
    name: str
    avatar: Optional[str]

class BiometricsBase(BaseModel):
    dob: Optional[date]
    gender: Optional[Gender]
    weight: Optional[float]
    height: Optional[float]

class PrivacyBase(BaseModel):
    profile: Optional[PrivacyLevel]
    messages: Optional[PrivacyLevel]
    comments: Optional[PrivacyLevel]

class AccountMeta(BaseModel):
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    email_confirmed: bool
    
class AccountBase(BaseModel):
    username: str
    email: str
    password: str
    metadata: AccountMeta
    bio: Optional[BiometricsBase]
    profile: Optional[ProfileBase]
    privacy: Optional[PrivacyBase]

class AccountInDB(AccountBase):
    id: str = Optional[Field(alias="_id")]
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = { ObjectId: str }
        from_attributes = True