from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class SkillTeach(BaseModel):
    skill: str
    level: str = "Intermediate"

    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        allowed = {"Beginner","Intermediate","Advanced","Expert"}
        if v not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v


class UserCreate(BaseModel):
    display_name: str
    college: str = ""
    bio: str = ""


class UserUpdate(BaseModel):
    display_name:  Optional[str]             = None
    college:       Optional[str]             = None
    bio:           Optional[str]             = None
    skills_teach:  Optional[list[SkillTeach]]= None
    skills_learn:  Optional[list[str]]       = None


class UserProfile(BaseModel):
    uid:            str
    display_name:   str
    email:          str
    college:        str
    bio:            str
    photo_url:      Optional[str]
    skills_teach:   list[SkillTeach]
    skills_learn:   list[str]
    rating:         float
    rating_count:   int
    sessions_count: int
    badges:         list[str]


class MatchCreate(BaseModel):
    target_uid: str


class MatchOut(BaseModel):
    match_id:             str
    partner_uid:          str
    partner_name:         str
    partner_college:      str
    partner_rating:       float
    partner_sessions:     int
    partner_skills_teach: list[SkillTeach]
    partner_skills_learn: list[str]
    match_pct:            int
    status:               str
    sender_uid:           str = ""   # ADD THIS LINE


class SuggestedMatch(BaseModel):
    uid:            str
    display_name:   str
    college:        str
    rating:         float
    rating_count:   int
    sessions_count: int
    skills_teach:   list[SkillTeach]
    skills_learn:   list[str]
    match_pct:      int


class SessionCreate(BaseModel):
    partner_uid: str
    topic:       str
    date_time:   datetime
    duration:    str = "60 minutes"
    meet_link:   Optional[str] = None


class SessionUpdate(BaseModel):
    meet_link: Optional[str] = None
    status:    Optional[str] = None


class SessionOut(BaseModel):
    session_id:   str
    partner_uid:  str
    partner_name: str
    topic:        str
    date_time:    str
    duration:     str
    meet_link:    Optional[str]
    status:       str


class ReviewCreate(BaseModel):
    to_uid:     str
    session_id: str
    rating:     int = Field(..., ge=1, le=5)
    text:       str = Field(..., min_length=5, max_length=1000)


class ReviewOut(BaseModel):
    review_id:  str
    from_uid:   str
    from_name:  str
    to_uid:     str
    session_id: str
    rating:     int
    text:       str
    created_at: str


class ChatMessage(BaseModel):
    chat_id: str
    text:    str = Field(..., min_length=1, max_length=2000)


class MessageOut(BaseModel):
    msg_id:     str
    sender_uid: str
    text:       str
    timestamp:  int


class LeaderboardEntry(BaseModel):
    uid:            str
    display_name:   str
    college:        str
    sessions_count: int
    rating:         float
    badges:         list[str]


class StatusMsg(BaseModel):
    message: str
    data:    Optional[dict] = None
