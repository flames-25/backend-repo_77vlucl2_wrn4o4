"""
Database Schemas for Fitness Influencer Portfolio

Each Pydantic model represents a collection in MongoDB. Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class Blogpost(BaseModel):
    """
    Blog posts about fitness, nutrition, events, etc.
    Collection: "blogpost"
    """
    title: str = Field(..., description="Post title")
    slug: str = Field(..., description="URL-friendly slug")
    excerpt: Optional[str] = Field(None, description="Short summary")
    content: str = Field(..., description="Full markdown or HTML content")
    cover_image: Optional[str] = Field(None, description="Hero image URL")
    tags: List[str] = Field(default_factory=list, description="List of tags")
    published: bool = Field(True, description="Whether post is published")
    published_at: Optional[datetime] = Field(None, description="Publish datetime")

class Message(BaseModel):
    """
    Contact form submissions from the website.
    Collection: "message"
    """
    name: str = Field(..., description="Sender name")
    email: EmailStr = Field(..., description="Sender email")
    phone: Optional[str] = Field(None, description="Phone number")
    subject: Optional[str] = Field(None, description="Subject")
    message: str = Field(..., description="Message body")
    source: str = Field("website", description="Where the message came from")
