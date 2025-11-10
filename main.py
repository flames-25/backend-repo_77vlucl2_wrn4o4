import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Blogpost, Message

app = FastAPI(title="Fitness Influencer Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Utility ---------
class BlogPostOut(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    tags: List[str] = []
    published: bool = True
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# -------- Startup: seed sample data if empty ---------
@app.on_event("startup")
def seed_sample_blogposts():
    if db is None:
        return
    try:
        count = db["blogpost"].count_documents({})
        if count == 0:
            samples = [
                {
                    "title": "Building Strength in the City",
                    "slug": "building-strength-in-the-city",
                    "excerpt": "My go-to routine for busy Londoners who want real results.",
                    "content": (
                        "Living in London means your schedule is packed. Here's a 30-minute strength protocol "
                        "you can do in any gym: 1) Compound lifts 2) Supersets 3) Finisher sled pushes. "
                        "Track your progressive overload weekly."
                    ),
                    "cover_image": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=1600",
                    "tags": ["strength", "london", "training"],
                    "published": True,
                    "published_at": datetime.utcnow(),
                },
                {
                    "title": "Fueling for Performance: Simple Meal Guide",
                    "slug": "fueling-for-performance",
                    "excerpt": "A practical approach to macros while enjoying London food culture.",
                    "content": (
                        "Nutrition shouldn't be complicated. Focus on protein with every meal, "
                        "colourful veg, and smart carbs around training windows. Here are my staple meals..."
                    ),
                    "cover_image": "https://images.unsplash.com/photo-1505252585461-04db1eb84625?q=80&w=1600",
                    "tags": ["nutrition", "performance"],
                    "published": True,
                    "published_at": datetime.utcnow(),
                },
            ]
            for s in samples:
                create_document("blogpost", s)
    except Exception:
        # Silent fail to avoid startup crash in preview environments without DB
        pass


# -------- Basic routes ---------
@app.get("/")
def read_root():
    return {"message": "Fitness Influencer Portfolio Backend"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -------- Schema endpoint for tooling ---------
@app.get("/schema")
def get_schema():
    # Return Pydantic JSON schema for known models
    return {
        "blogpost": Blogpost.model_json_schema(),
        "message": Message.model_json_schema(),
    }


# -------- Blog endpoints ---------
@app.get("/api/blogposts", response_model=List[BlogPostOut])
def list_blogposts(tag: Optional[str] = None):
    if db is None:
        # Return sample posts when DB not available
        return [
            BlogPostOut(
                title="Building Strength in the City",
                slug="building-strength-in-the-city",
                excerpt="My go-to routine for busy Londoners who want real results.",
                content="Sample content",
                cover_image="https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=1600",
                tags=["strength", "london", "training"],
                published=True,
            ),
        ]
    q = {"published": True}
    if tag:
        q["tags"] = tag
    docs = get_documents("blogpost", q, limit=50)
    return [BlogPostOut(**{
        **{k: v for k, v in d.items() if k in BlogPostOut.model_fields},
        "created_at": d.get("created_at"),
        "updated_at": d.get("updated_at"),
    }) for d in docs]


@app.get("/api/blogposts/{slug}", response_model=BlogPostOut)
def get_blogpost(slug: str):
    if db is None:
        if slug == "building-strength-in-the-city":
            return BlogPostOut(
                title="Building Strength in the City",
                slug="building-strength-in-the-city",
                excerpt="My go-to routine for busy Londoners who want real results.",
                content="Sample content",
                cover_image="https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=1600",
                tags=["strength", "london", "training"],
                published=True,
            )
        raise HTTPException(status_code=404, detail="Post not found")

    doc = db["blogpost"].find_one({"slug": slug, "published": True})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return BlogPostOut(**{
        **{k: v for k, v in doc.items() if k in BlogPostOut.model_fields},
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    })


# -------- Contact endpoint ---------
@app.post("/api/contact")
def submit_contact(msg: Message):
    data = msg.model_dump()
    try:
        if db is not None:
            create_document("message", data)
        # Always return success to keep UX smooth in demo environments
        return {"status": "ok", "message": "Thanks for reaching out!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
