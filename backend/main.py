import os
import json
import uuid
import shutil
import pytz
import httpx
import google.generativeai as genai
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# SETUP & CONFIGURATION
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['coral_ai_project']
raw_collection = db['raw_data']
response_collection = db['response_data']

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# FASTAPI APP INITIALIZATION
app = FastAPI(title="Coral AI Book Scanner API")
# Allow Next.js (usually localhost:3000) to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_DIR = "received_images" # Chage this to to folder where you want to save images
CORAL_URL = os.getenv("CORAL_URL", "http://192.168.137.77:5000")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Host the image folder so Next.js can display the pictures via URL
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# books = [
#     {
#         "id": 1,
#         "title": "เสน่หามายาจอมนาง",
#         "author": "xxx",
#         "image": "/images/book1.jpg",
#         "content": "ข้อความจาก OCR...",
#         "summary": "สรุปโดย AI...",
#         "timestamp": "2026-04-01"
#     },
#     {
#         "id": 2,
#         "title": "Lord of the Rings",
#         "author": "Tolkien",
#         "image": "/images/book1.jpg",
#         "content": "ข้อความจาก OCR...",
#         "summary": "สรุปโดย AI...",
#         "timestamp": "2026-04-15"
#     }
# ]

# POST ROUTE (For the Coral Board to trigger)
@app.post("/api/trigger")
async def handle_trigger(image: UploadFile = File(...), confidence_level: float = Form(...)):
    """Receives image from Coral Board, saves to DB, and gets LLM analysis."""
    
    # A. Generate UUID & Timestamp
    trigger_id = f"uuid-{uuid.uuid4().hex[:8]}"
    bkk_tz = pytz.timezone('Asia/Bangkok')
    current_time = datetime.now(bkk_tz).isoformat()
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    # B. Save Image Locally
    file_name = f"book_{trigger_id}.jpg"
    file_path = os.path.join(IMAGE_DIR, file_name)

    content = await image.read()
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # C. Save Raw Data to DB
    # Notice the image_path is now a URL path the frontend can use   
    raw_doc = {
        "_id": trigger_id,
        "timestamp": current_time,
        "confidence_level": confidence_level,
        "class_detected": "book",
        "image_path": f"/images/{file_name}",
        "size_kb": round(len(content) / 1024, 1)
    }

    raw_collection.insert_one(raw_doc)
    return {"status": "received", "filename": file_name}

    # D. Prepare Image for Gemini
    image_data = {
        "mime_type": "image/jpeg",
        "data": open(file_path, "rb").read()
    }

    prompt = """
    Please analyze the provided image of a book. You must extract the information and return only a valid JSON object. Do not include markdown formatting or any other text. Use this exact schema: 
    {"title": "string", "author": "string", "genre": "string", "keywords": ["array", "of", "strings"], "language": "string", "target_audience": "string", "summary": "string"}
    """
    generation_config = {
        "temperature": 0.0,
        "top_p": 0.95,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # E. Call Gemini
    response = model.generate_content(
        [prompt, image_data],
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    # F. Parse JSON and Save Response
    try:
        llm_dict = json.loads(response.text) 
    except json.JSONDecodeError:
        llm_dict = {"error": "Failed to parse JSON", "raw_text": response.text}
        
    response_doc = {
        "_id": trigger_id,
        "timestamp_received": datetime.now(bkk_tz).isoformat(),
        "llm_analysis": llm_dict
    }
    response_collection.insert_one(response_doc)
    
    return {"status": "success", "trigger_id": trigger_id, "data": llm_dict}

@app.post("/resume")
async def resume():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{CORAL_URL}/resume", timeout=5)
        return {"status": "ok", "message": "Resume signal sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

# GET ROUTE (For Next.js to fetch data)
@app.get("/api/books")
async def get_latest_books():
    """Fetches the latest analyzed books from MongoDB for the UI Dashboard."""
    # We join raw_data and response_data using an aggregation pipeline
    # This gives Next.js the image URL AND the LLM data in one easy request!
    pipeline = [
        {
            "$lookup": {
                "from": "response_data",
                "localField": "_id",
                "foreignField": "_id",
                "as": "analysis_data"
            }
        },
        {"$unwind": "$analysis_data"},
        {"$sort": {"timestamp": -1}}, # Newest first
        {"$limit": 10} # Only send the last 10 books so it loads fast
    ]
    results = list(raw_collection.aggregate(pipeline))
    
    books = []
    for item in results:
        llm = item["analysis_data"]["llm_analysis"]

        books.append({
            "id": item["_id"],
            "title": llm.get("title", "Unknown"),
            "author": llm.get("author", "Unknown"),
            "summary": llm.get("summary", ""),
            "image": item.get("image_path", ""),
            "timestamp": item.get("timestamp", "")
        })

    return books

@app.get("/api/books/{id}")
async def get_book(id: str):
    raw = raw_collection.find_one({"_id": id})
    res = response_collection.find_one({"_id": id})

    if not raw or not res:
        return {"error": "Not found"}

    llm = res["llm_analysis"]

    return {
        "id": id,
        "title": llm.get("title", ""),
        "author": llm.get("author", ""),
        "summary": llm.get("summary", ""),
        "image": raw.get("image_path", "")
    }

@app.get("/image/{filename}")
async def serve_image(filename: str):
    return FileResponse(os.path.join(IMAGE_DIR, filename))

# @app.get("/books")
# def get_books():
#     return books
    
# @app.get("/books/{id}")
# def get_book(id: int):
#     for book in books:
#         if int(book["id"]) == int(id):
#             return book
#     print("NOT FOUND ❌")
#     return {"error": "Not found"}