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
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const router = useRouter();

  const fetchImages = async () => {
    const res = await fetch(`${API}/api/images`);
    const data = await res.json();

    if (Array.isArray(data)) {
      setImages(data);
    } else {
      setImages([]);
    }

    setLastUpdate(new Date());
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);

    const pad = (n: number) => n.toString().padStart(2, "0");

    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} 
  ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  };

  useEffect(() => {
    fetchImages();

    const interval = setInterval(fetchImages, 5000); // ✅ ทุก 5 วิ

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-pink-50 p-6">

      {/* 🔙 BACK */}
      <div className="mb-4">
        <button
          onClick={() => router.push("/")}
          className="bg-white border border-pink-300 text-pink-600 px-4 py-2 rounded-xl shadow hover:bg-pink-50 transition"
        >
          ← Back
        </button>
      </div>

      {/* 🧾 HEADER */}
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold text-pink-600">
          📷 Detection Log
        </h1>
      </div>

      {/* 🔄 STATUS */}
      <div className="text-sm text-gray-400 mb-4 flex justify-between">
        <span>🔄 Auto updating every 5 seconds</span>
        <span>
          {lastUpdate && `Last updated: ${lastUpdate.toLocaleTimeString()}`}
        </span>
      </div>

      {/* 📊 COUNT */}
      <div className="bg-white p-4 rounded-xl shadow border border-pink-100 mb-6">
        <p className="text-sm text-gray-500">Total Images</p>
        <h2 className="text-2xl font-bold text-pink-600">
          {images.length}
        </h2>
      </div>

      {/* 🖼️ GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">

        {images.length === 0 && (
          <p className="col-span-full text-center text-gray-400">
            No images...
          </p>
        )}

        {[...images].map((img, index) => (
          <div
            key={img.filename}
            className="bg-white rounded-2xl shadow-md hover:shadow-2xl transition duration-300 overflow-hidden border border-pink-100 hover:scale-[1.02]"
          >
            <div className="relative">
              <img
                src={`${API}/image/${img.filename}`}
                className="w-full h-48 object-cover"
              />
            </div>

            <div className="p-3 text-sm">
              <p className="font-semibold text-gray-700 truncate">
                {img.filename}
              </p>

              <p className="text-xs text-gray-400 mt-1">
                📅 {formatDate(img.timestamp)}
              </p>
            </div>
          </div>
        ))}

      </div>
    </div>
  );
}