"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API = "http://localhost:8000";

type ImageInfo = {
  filename: string;
  timestamp: string;
  size_kb: number;
};

export default function Home() {
  const [images, setImages] = useState<ImageInfo[]>([]);
  const router = useRouter();

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
    <div className="min-h-screen bg-pink-50 p-6">
      <div className="mb-4">
        <button
          onClick={() => router.push("/")}
          className="bg-white border border-pink-300 text-pink-600 px-4 py-2 rounded-xl shadow hover:bg-pink-50 transition"
        >
          ← Back
        </button>
      </div>

      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-pink-600">
            📷 Detection Log
          </h1>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleResume}
            className="bg-pink-500 hover:bg-pink-600 text-white px-5 py-2 rounded-xl shadow"
          >
            ▶ Resume Detection
          </button>

          <button
            onClick={fetchImages}
            className="bg-white border border-pink-300 text-pink-600 px-5 py-2 rounded-xl shadow hover:bg-pink-50"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* COUNT */}
      <div className="bg-white p-4 rounded-xl shadow border border-pink-100 mb-6">
        <p className="text-sm text-gray-500">Total Images</p>
        <h2 className="text-2xl font-bold text-pink-600">
          {images.length}
        </h2>
      </div>

      {/* GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">

        {[...images].reverse().map((img) => (
          <div
            key={img.filename}
            className="bg-white rounded-2xl shadow-md hover:shadow-xl transition overflow-hidden border border-pink-100"
          >
            {/* IMAGE */}
            <img
              src={`${API}/image/${img.filename}`}
              className="w-full h-48 object-cover"
            />

            {/* INFO */}
            <div className="p-3 text-sm text-gray-500">
              <p className="truncate">{img.filename}</p>
              <p className="text-xs mt-1">
                📅 {img.timestamp}
              </p>
              <p className="text-xs text-gray-400">
                {img.size_kb} KB
              </p>
            </div>
          </div>
        ))}

      </div>
    </div>

    // <main style={{ background: "#0f0f23", color: "#eee", minHeight: "100vh", padding: 20 }}>
    //   <h1 style={{ textAlign: "center", color: "#00d4ff" }}>Book Detection Server</h1>
    //   <div style={{ textAlign: "center", margin: 20 }}>
    //     <button onClick={handleResume}>Resume Detection</button>
    //     <button onClick={fetchImages}>Refresh</button>
    //   </div>
    //   <p style={{ textAlign: "center" }}>Total images: {images.length}</p>
    //   <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 15 }}>
    //     {[...images].reverse().map((img) => (
    //       <div key={img.filename} style={{ background: "#1a1a3e", borderRadius: 8, overflow: "hidden" }}>
    //         <img src={`${API}/image/${img.filename}`} style={{ width: "100%" }} />
    //         <div style={{ padding: 10, fontSize: 13, color: "#aaa" }}>
    //           {img.timestamp} — {img.size_kb} KB
    //         </div>
    //       </div>
    //     ))}
    //   </div>
    // </main>
  );
}