from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from dataclasses import dataclass
import httpx
import os
from urllib.parse import urljoin

# Base URL for the avatar images
BASE_AVATAR_URL = "http://www.tam-files.toko-aplikasi.my.id/images/avatars/"

@dataclass
class Avatar:
    name: str
    imageurl: str
    
    @classmethod
    def from_filename(cls, filename: str):
        """Create Avatar instance from filename"""
        name = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
        imageurl = urljoin(BASE_AVATAR_URL, filename)
        return cls(name=name, imageurl=imageurl)

# Initialize FastAPI app
app = FastAPI(
    title="Avatar API",
    description="API for serving avatar images",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for avatar list
avatar_cache = []
avatar_dict = {}

@app.on_event("startup")
async def load_avatars():
    """Load avatar list on startup"""
    global avatar_cache, avatar_dict
    try:
        # In production, you'd want to fetch this list dynamically
        # For now, I've extracted the filenames from your directory listing
        filenames = [
            "Abraham Baker.png", "Adem Lane.png", "Adil Floyd.png", 
            "Adriana O'Sullivan.png", "Alec Whitten.png", "Alesha Barry.png",
            "Ali Mahdi.png", "Aliah Lane.png", "Alisa Hester.png",
            "Amanda Lowery.png", "Amelie Bennett.png", "Amelie Laurent.png",
            "Ammar Foley.png", "Anaiah Whitten.png", "Andi Lane.png",
            "Angelica Wallace.png", "Anita Cruz.png", "Ashton Blackwell.png",
            "Ashwin Santiago.png", "Aston Hood.png", "Ava Bentley.png",
            "Ava Wright.png", "Ayah Wilkinson.png", "Aysha Becker.png",
            "Bailey Richards.png", "Bec Ferguson.png", "Belle Woods.png",
            "Benedict Doherty.png", "Billie Wright.png", "Blake Riley.png",
            "Brianna Ware.png", "Byron Robertson.png", "Caitlyn King.png",
            "Cameron Yang.png", "Candice Wu.png", "Clifford Jennings.png",
            "Cohen Lozano.png", "Courtney Turner.png", "Danyal Lester.png",
            "Demi Wilkinson.png", "Dillan Nguyen.png", "Drew Cano.png",
            "Eduard Franz.png", "Elena Owens.png", "Elisa Nishikawa.png",
            "Elsie Roy.png", "Erica Wyatt.png", "Ethan Campbell.png",
            "Ethan Valdez.png", "Eva Bond.png", "Eve Leroy.png",
            "Fergus Gray.png", "Fleur Cook.png", "Florence Shaw.png",
            "Frank Whitaker.png", "Franklin Mays.png", "Freya Browning.png",
            "Genevieve Mclean.png", "Harriet Rojas.png", "Harry Bender.png",
            "Hasan Johns.png", "Herbert Fowler.png", "Isla Allison.png",
            "Isobel Carroll.png", "Isobel Fuller.png", "Jackson Reed.png",
            "Jay Shepard.png", "Jaya Willis.png", "Jayden Moss.png",
            "Jessie Meyton.png", "Jonathan Kelly.png", "Jordan Burgess.png",
            "Joshua Wilson.png", "Julius Vaughan.png", "Kaden Scott.png",
            "Kaitlin Hale.png", "Kari Rasmussen.png", "Kate Morrison.png",
            "Katherine Moss.png", "Katy Fuller.png", "Kelly Williams.png",
            "Kelsey Lowe.png", "Koray Okumus.png", "Kyla Clay.png",
            "Lana Steiner.png", "Levi Rocha.png", "Leyton Fields.png",
            "Liam Hood.png", "Lily-Rose Chedjou.png", "Loki Bright.png",
            "Lola Sanders.png", "Lori Bryson.png", "Lucy Bond.png",
            "Lulu Meyers.png", "Luqman Anthony.png", "Lyle Kauffman.png",
            "Maddison Gillespie.png", "Madeleine Pitts.png", "Marco Gross.png",
            "Marco Kelly.png", "Marvin Robbins.png", "Mathilde Lewis.png",
            "Maxwell Tan.png", "Mikey Lawrence.png", "Mollie Hall.png",
            "Molly Vaughan.png", "Nala Goins.png", "Natali Craig.png",
            "Nic Fassbender.png", "Nicola Harris.png", "Nicolas Trevino.png",
            "Nicolas Wang.png", "Nikolas Gibbons.png", "Noah Pierre.png",
            "Noel Baldwin.png", "Olivia Rhye.png", "Olly Schroeder.png",
            "Orlando Diggs.png", "Owen Garcia.png", "Owen Harding.png",
            "Phoenix Baker.png", "Pippa Wilkinson.png", "Priya Shepard.png",
            "Rachael Strong.png", "Rayhan Zua.png", "Rene Wells.png",
            "Rhea Levine.png", "Rhianna Shepard.png", "Riley O'Moore.png",
            "Rory Huff.png", "Rosalee Melvin.png", "Sally Mason.png",
            "Sarah Page.png", "Scott Clayton.png", "Sienna Hewitt.png",
            "Sophia Perez.png", "Stefan Sears.png", "Youssef Roberson.png",
            "Zahir Mays.png", "Zahra Christensen.png", "Zaid Schwartz.png",
            "Zara Bush.png", "Zaynab Donnelly.png", "Zuzanna Burke.png"
        ]
        
        avatar_cache = [Avatar.from_filename(f) for f in filenames]
        avatar_dict = {avatar.name.lower(): avatar for avatar in avatar_cache}
        
        print(f"Loaded {len(avatar_cache)} avatars")
    except Exception as e:
        print(f"Error loading avatars: {e}")

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/api/avatars", response_model=List[dict])
async def get_all_avatars(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None
):
    """
    Get all avatars with pagination and search
    
    - **skip**: Number of avatars to skip (default: 0)
    - **limit**: Maximum number of avatars to return (default: 100, max: 200)
    - **search**: Optional search term to filter by name
    """
    avatars = avatar_cache
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        avatars = [a for a in avatars if search_lower in a.name.lower()]
    
    # Apply pagination
    paginated = avatars[skip:skip + limit]
    
    return [
        {
            "name": avatar.name,
            "imageurl": avatar.imageurl,
            "filename": avatar.imageurl.split('/')[-1]
        }
        for avatar in paginated
    ]

@app.get("/api/avatars/{avatar_name}")
async def get_avatar_by_name(avatar_name: str):
    """
    Get a specific avatar by name
    
    - **avatar_name**: The name of the avatar (case-insensitive)
    """
    # Try exact match first
    avatar = avatar_dict.get(avatar_name.lower())
    
    # If not found, try partial match
    if not avatar:
        matches = [a for a in avatar_cache if avatar_name.lower() in a.name.lower()]
        if matches:
            avatar = matches[0]
    
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar '{avatar_name}' not found")
    
    return {
        "name": avatar.name,
        "imageurl": avatar.imageurl,
        "filename": avatar.imageurl.split('/')[-1]
    }

@app.get("/api/avatars/random/{count}")
async def get_random_avatars(count: int = 1):
    """
    Get random avatars
    
    - **count**: Number of random avatars to return (default: 1, max: 50)
    """
    import random
    
    if count < 1:
        raise HTTPException(status_code=400, detail="Count must be at least 1")
    
    if count > 50:
        count = 50
    
    selected = random.sample(avatar_cache, min(count, len(avatar_cache)))
    
    return [
        {
            "name": avatar.name,
            "imageurl": avatar.imageurl,
            "filename": avatar.imageurl.split('/')[-1]
        }
        for avatar in selected
    ]

@app.get("/api/avatars/stats/info")
async def get_avatar_stats():
    """Get statistics about the avatar collection"""
    return {
        "total_avatars": len(avatar_cache),
        "base_url": BASE_AVATAR_URL,
        "file_types": set([url.split('.')[-1] for url in [a.imageurl for a in avatar_cache]]),
        "sample_avatars": [
            {"name": a.name, "url": a.imageurl} 
            for a in avatar_cache[:5]
        ]
    }

@app.get("/api/avatars/{avatar_name}/image")
async def get_avatar_image(avatar_name: str):
    """Fetch and serve the actual image"""
    avatar = avatar_dict.get(avatar_name.lower())
    if not avatar:
        raise HTTPException(status_code=404)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(avatar.imageurl)
        return Response(
            content=response.content,
            media_type="image/png"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "avatars_loaded": len(avatar_cache)
    }

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import httpx
from dataclasses import dataclass
from urllib.parse import urljoin

# Base URL for your static avatar server
BASE_AVATAR_URL = "http://www.tam-files.toko-aplikasi.my.id/images/avatars/"

@dataclass
class Avatar:
    name: str
    imageurl: str
    
    @classmethod
    def from_filename(cls, filename: str):
        name = filename.replace('.png', '')
        imageurl = urljoin(BASE_AVATAR_URL, filename.replace(' ', '%20'))
        return cls(name=name, imageurl=imageurl)

# Initialize FastAPI
app = FastAPI(
    title="Avatar API",
    description="Serving avatar images from toko-aplikasi.my.id",
    version="1.0.0"
)

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your avatar list (shortened for testing - add all later)
FILENAMES = [
    "Abraham Baker.png",
    "Adem Lane.png",
    "Adil Floyd.png",
    "Adriana O'Sullivan.png",
    "Alec Whitten.png",
    # ... add the rest of your 150+ filenames here
]

avatar_cache = []
avatar_dict = {}

@app.on_event("startup")
async def load_avatars():
    global avatar_cache, avatar_dict
    avatar_cache = [Avatar.from_filename(f) for f in FILENAMES]
    avatar_dict = {a.name.lower(): a for a in avatar_cache}
    print(f"✅ Loaded {len(avatar_cache)} avatars")
    print(f"📊 Sample: {avatar_cache[0].name if avatar_cache else 'None'}")

# ============= CRITICAL: HEALTH CHECK ENDPOINT =============
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "avatars_loaded": len(avatar_cache),
        "service": "avatar-api"
    }
# ============================================================

@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return RedirectResponse(url="/docs")

@app.get("/api/avatars")
async def get_avatars(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    """Get all avatars with pagination and search"""
    avatars = avatar_cache
    
    if search:
        search_lower = search.lower()
        avatars = [a for a in avatars if search_lower in a.name.lower()]
    
    paginated = avatars[skip:skip + limit]
    
    return [
        {
            "name": a.name,
            "imageurl": a.imageurl,
            "filename": a.imageurl.split('/')[-1]
        }
        for a in paginated
    ]

@app.get("/api/avatars/{avatar_name}")
async def get_avatar(avatar_name: str):
    """Get specific avatar by name"""
    avatar = avatar_dict.get(avatar_name.lower())
    
    if not avatar:
        # Try partial match
        matches = [a for a in avatar_cache if avatar_name.lower() in a.name.lower()]
        if matches:
            avatar = matches[0]
    
    if not avatar:
        raise HTTPException(status_code=404, detail=f"Avatar '{avatar_name}' not found")
    
    return {
        "name": avatar.name,
        "imageurl": avatar.imageurl,
        "filename": avatar.imageurl.split('/')[-1]
    }

if __name__ == "__main__":
    import uvicorn
    # CRITICAL: Use Railway's PORT env var or default to 8000
    port = int(os.environ.get("PORT", 8000))
    # CRITICAL: Bind to 0.0.0.0
    uvicorn.run(app, host="0.0.0.0", port=port)