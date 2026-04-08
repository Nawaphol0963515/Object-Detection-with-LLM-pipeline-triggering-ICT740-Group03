"use client";
import { useState, useEffect } from "react";

const API = "http://localhost:8000";

type ImageInfo = {
  filename: string;
  timestamp: string;
  size_kb: number;
};

export default function Home() {
  const [images, setImages] = useState<ImageInfo[]>([]);

  const fetchImages = async () => {
    const res = await fetch(`${API}/images`);
    const data = await res.json();
    setImages(data);
  };

  useEffect(() => {
    fetchImages();
    const interval = setInterval(fetchImages, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleResume = async () => {
    const res = await fetch(`${API}/resume`, { method: "POST" });
    const data = await res.json();
    alert(data.message);
  };

  return (
    <main style={{ background: "#0f0f23", color: "#eee", minHeight: "100vh", padding: 20 }}>
      <h1 style={{ textAlign: "center", color: "#00d4ff" }}>Book Detection Server</h1>
      <div style={{ textAlign: "center", margin: 20 }}>
        <button onClick={handleResume}>Resume Detection</button>
        <button onClick={fetchImages}>Refresh</button>
      </div>
      <p style={{ textAlign: "center" }}>Total images: {images.length}</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 15 }}>
        {[...images].reverse().map((img) => (
          <div key={img.filename} style={{ background: "#1a1a3e", borderRadius: 8, overflow: "hidden" }}>
            <img src={`${API}/image/${img.filename}`} style={{ width: "100%" }} />
            <div style={{ padding: 10, fontSize: 13, color: "#aaa" }}>
              {img.timestamp} — {img.size_kb} KB
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}