import os
import json
import uuid
import pytz
import httpx
import asyncio
import certifi
import traceback
import google.generativeai as genai
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ============================================================
# SETUP & CONFIGURATION
# ============================================================
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Connect to MongoDB ---
# Database: Detection-LLM-DB
# Collections: raw_data, response_data
client = MongoClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
)
db = client['Detection-LLM-DB']
raw_collection = db['raw_data']
response_collection = db['response_data']

# Quick ping at startup so we fail fast if Mongo is unreachable
try:
    client.admin.command('ping')
    print("[MONGO] Connected to Detection-LLM-DB ✓")
except Exception as e:
    print(f"[MONGO ERROR] Cannot connect: {e}")

# --- Configure Gemini ---
if not GEMINI_API_KEY:
    print("[GEMINI WARNING] GEMINI_API_KEY not set in .env")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Use a real, current model name.
# 'gemini-2.0-flash' is stable. 'gemini-2.5-flash' also works.
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
model = genai.GenerativeModel(GEMINI_MODEL_NAME)
print(f"[GEMINI] Using model: {GEMINI_MODEL_NAME}")


# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(title="Coral AI Book Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMAGE_DIR is where files actually live on disk.
# IMAGE_PATH_PREFIX is what we STORE in MongoDB (must match your schema).
IMAGE_DIR = "images"
IMAGE_PATH_PREFIX = "backend/images"   # <-- stored in DB exactly like this
CORAL_URL = os.getenv("CORAL_URL", "http://192.168.137.77:5000")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Expose images to the frontend via URL
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")


# ============================================================
# HELPER: send resume signal to Coral
# ============================================================
async def send_resume_to_coral():
    try:
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.post(f"{CORAL_URL}/resume", timeout=5)
            print(f"[RESUME] Sent resume to Coral: {resp.status_code}")
    except Exception as e:
        print(f"[RESUME ERROR] {e}")


# ============================================================
# HELPER: process image with Gemini (background task)
# ============================================================
def _extract_text_from_response(response) -> str:
    """Safely pull text out of a Gemini response.

    `response.text` raises if there are no candidates / safety block.
    Manually walking `candidates[].content.parts[].text` is more reliable.
    """
    # Try the easy path first, but catch whatever it throws
    try:
        t = response.text
        if t:
            return t
    except Exception as e:
        print(f"[GEMINI] response.text raised: {type(e).__name__}: {e}")

    # Manual walk
    try:
        out = []
        for cand in getattr(response, "candidates", []) or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                ptxt = getattr(part, "text", None)
                if ptxt:
                    out.append(ptxt)
        if out:
            return "".join(out)
    except Exception as e:
        print(f"[GEMINI] Manual walk failed: {e}")

    return ""


def _diagnose_empty_response(response) -> str:
    """Build a human-readable reason string when response is empty."""
    reasons = []
    try:
        pf = getattr(response, "prompt_feedback", None)
        if pf:
            reasons.append(f"prompt_feedback={pf}")
    except Exception:
        pass

    try:
        for i, cand in enumerate(getattr(response, "candidates", []) or []):
            fr = getattr(cand, "finish_reason", None)
            sr = getattr(cand, "safety_ratings", None)
            reasons.append(f"candidate[{i}] finish_reason={fr} safety_ratings={sr}")
    except Exception as e:
        reasons.append(f"(failed to read candidates: {e})")

    return " | ".join(reasons) if reasons else "no diagnostic info"


async def process_with_gemini(trigger_id: str, file_path: str):
    """Analyze image with Gemini -> save to response_data -> resume Coral."""
    bkk_tz = pytz.timezone('Asia/Bangkok')
    llm_dict = None

    try:
        print(f"[GEMINI] Starting analysis for {trigger_id}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image not found at {file_path}")

        file_size = os.path.getsize(file_path)
        print(f"[GEMINI] Image size: {file_size} bytes")

        if file_size == 0:
            raise ValueError("Image file is empty (0 bytes)")

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        image_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes,
        }

        prompt = (
            "Analyze the provided image of a book cover and extract information. "
            "Return ONLY a JSON object with this schema: "
            '{"title": "string", "author": "string", "genre": "string", '
            '"keywords": ["string"], "language": "string", '
            '"target_audience": "string", "summary": "string"}. '
            "If you cannot read some fields, use empty string or empty array. "
            "Do not include markdown or code fences."
        )

        # NOTE: do NOT use response_mime_type="application/json" —
        # some model versions return empty candidates when the schema
        # can't be enforced. We parse JSON manually instead.
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        }

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        print(f"[GEMINI] Calling {GEMINI_MODEL_NAME}...")
        response = await asyncio.to_thread(
            model.generate_content,
            [prompt, image_part],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        # Dump everything we can see for debugging
        print(f"[GEMINI] Response object type: {type(response).__name__}")
        try:
            print(f"[GEMINI] prompt_feedback: {response.prompt_feedback}")
        except Exception:
            pass
        try:
            print(f"[GEMINI] # candidates: {len(response.candidates)}")
            for i, c in enumerate(response.candidates):
                print(f"[GEMINI] candidate[{i}].finish_reason = {c.finish_reason}")
        except Exception:
            pass

        raw_text = _extract_text_from_response(response)
        print(f"[GEMINI] Extracted text ({len(raw_text)} chars): {raw_text[:500]}")

        if not raw_text:
            diag = _diagnose_empty_response(response)
            raise ValueError(f"Gemini returned empty response -> {diag}")

        # Clean markdown fences if the model slipped them in
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[-1]  # after opening fence
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            if "```" in cleaned:
                cleaned = cleaned.split("```")[0]
            cleaned = cleaned.strip()

        # Parse JSON
        try:
            llm_dict = json.loads(cleaned)
            print(f"[GEMINI] Parsed OK. Title: {llm_dict.get('title')}")
        except json.JSONDecodeError as je:
            print(f"[GEMINI] JSON parse failed: {je}")
            llm_dict = {"error": "Failed to parse JSON", "raw_text": raw_text}

    except Exception as e:
        print(f"[GEMINI ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        llm_dict = {"error": f"{type(e).__name__}: {str(e)}"}

    # Always write a respond_data document, even if Gemini failed
    try:
        respond_doc = {
            "_id": trigger_id,
            "timestamp_received": datetime.now(bkk_tz).isoformat(),
            "llm_analysis": llm_dict,
        }
        response_collection.insert_one(respond_doc)
        print(f"[MONGO] respond_data inserted for {trigger_id}")
    except Exception as e:
        print(f"[MONGO ERROR] Failed to insert respond_data: {e}")

    # Always tell Coral to resume
    await send_resume_to_coral()


# ============================================================
# POST /upload — Coral posts captured frame here
# ============================================================
@app.post("/upload")
async def handle_upload(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    confidence_level: float = Form(default=0.95),
):
    # A. ID + timestamp
    trigger_id = f"uuid-{uuid.uuid4().hex[:8]}"
    bkk_tz = pytz.timezone('Asia/Bangkok')
    current_time = datetime.now(bkk_tz).isoformat()

    # B. Save image to disk
    file_name = f"book_{trigger_id}.jpg"
    file_path = os.path.join(IMAGE_DIR, file_name)

    content = await image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    print(f"[UPLOAD] Saved {file_path} ({len(content)} bytes)")

    # C. Save raw_data to Mongo (matches required schema exactly)
    raw_doc = {
        "_id": trigger_id,
        "timestamp": current_time,
        "confidence_level": confidence_level,
        "class_detected": "book",
        "image_path": f"{IMAGE_PATH_PREFIX}/{file_name}",
    }

    try:
        raw_collection.insert_one(raw_doc)
        print(f"[MONGO] raw_data inserted: {trigger_id}")
    except Exception as e:
        print(f"[MONGO ERROR] Failed to insert raw_data: {e}")
        return {"status": "error", "message": f"DB insert failed: {e}"}

    # D. Run Gemini + resume in background
    background_tasks.add_task(process_with_gemini, trigger_id, file_path)

    return {
        "status": "received",
        "trigger_id": trigger_id,
        "filename": file_name,
    }


# ============================================================
# POST /resume — manual resume trigger
# ============================================================
@app.post("/resume")
async def resume():
    try:
        await send_resume_to_coral()
        return {"status": "ok", "message": "Resume signal sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================================
# GET /api/books — for Next.js dashboard
# ============================================================
@app.get("/api/books")
async def get_latest_books():
    pipeline = [
        {
            "$lookup": {
                "from": "response_data",
                "localField": "_id",
                "foreignField": "_id",
                "as": "analysis_data",
            }
        },
        {"$unwind": {"path": "$analysis_data", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"timestamp": -1}},
        {"$limit": 10},
    ]
    results = list(raw_collection.aggregate(pipeline))

    books = []
    for item in results:
        analysis = item.get("analysis_data") or {}
        llm = analysis.get("llm_analysis", {}) if analysis else {}

        # Stored path is "backend/images/xxx.jpg" -> convert to URL
        stored = item.get("image_path", "")
        filename = os.path.basename(stored) if stored else ""
        image_url = f"/images/{filename}" if filename else ""

        books.append({
            "id": item["_id"],
            "title": llm.get("title", "Processing..."),
            "author": llm.get("author", "—"),
            "summary": llm.get("summary", ""),
            "image": image_url,
            "timestamp": item.get("timestamp", ""),
        })
    return books

@app.get("/api/books/{book_id}")
async def get_book(book_id: str):
    raw = raw_collection.find_one({"_id": book_id})
    res = response_collection.find_one({"_id": book_id})

    if not raw:
        return {"error": "Not found"}

    llm = (res or {}).get("llm_analysis", {})

    stored = raw.get("image_path", "")
    filename = os.path.basename(stored) if stored else ""
    image_url = f"/images/{filename}" if filename else ""

    return {
        "id": book_id,
        "title": llm.get("title", "Processing..."),
        "author": llm.get("author", ""),
        "genre": llm.get("genre", ""),
        "keywords": llm.get("keywords", []),
        "language": llm.get("language", ""),
        "target_audience": llm.get("target_audience", ""),
        "summary": llm.get("summary", ""),
        "image": image_url,
        "timestamp": raw.get("timestamp", ""),
    }


@app.get("/image/{filename}")
async def serve_image(filename: str):
    return FileResponse(os.path.join(IMAGE_DIR, filename))

@app.get("/api/images")
async def get_images():
    results = list(raw_collection.find().sort("timestamp", -1).limit(20))

    images = []
    for item in results:
        stored = item.get("image_path", "")
        filename = os.path.basename(stored) if stored else ""

        images.append({
            "filename": filename,
            "timestamp": item.get("timestamp", ""),
            "size_kb": 0  # ยังไม่มี ก็ใส่ 0 ไปก่อน
        })

    return images

# ============================================================
# DEBUG: test Gemini without Coral
# Usage:  curl -X POST -F "image=@book.jpg" http://localhost:8000/debug/test-gemini
# ============================================================
@app.post("/debug/test-gemini")
async def debug_test_gemini(image: UploadFile = File(...)):
    trigger_id = f"debug-{uuid.uuid4().hex[:6]}"
    file_name = f"debug_{trigger_id}.jpg"
    file_path = os.path.join(IMAGE_DIR, file_name)

    content = await image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    await process_with_gemini(trigger_id, file_path)

    result = response_collection.find_one({"_id": trigger_id})
    return {"trigger_id": trigger_id, "result": result}
