import os
import httpx
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ให้ Next.js เรียก API ข้าม port ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "received_images"
CORAL_URL = os.getenv("CORAL_URL", "http://192.168.137.77:5000")
os.makedirs(UPLOAD_DIR, exist_ok=True)

received_images = []

@app.post("/upload")
async def upload(image: UploadFile = File(...)):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"book_{timestamp}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)

    info = {
        "filename": filename,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "size_kb": round(len(content) / 1024, 1),
    }
    received_images.append(info)
    return {"status": "received", "filename": filename}

@app.get("/images")
async def list_images():
    return received_images

@app.get("/image/{filename}")
async def serve_image(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename))

@app.post("/resume")
async def resume():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{CORAL_URL}/resume", timeout=5)
        return {"status": "ok", "message": "Resume signal sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}