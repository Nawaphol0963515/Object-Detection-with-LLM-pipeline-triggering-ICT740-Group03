"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

export default function BookDetail() {
  const { id } = useParams();
  const router = useRouter();

  const [book, setBook] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState("");

  useEffect(() => {
    if (!id) return;

    const fetchBook = async () => {
      const res = await fetch(`http://127.0.0.1:8000/api/books/${id}`);
      const data = await res.json();

      setBook(data);

      // default = รูปแรก
      if (data.images && data.images.length > 0) {
        setSelectedImage(data.images[0]);
      } else {
        setSelectedImage(data.image);
      }
    };

    fetchBook();
  }, [id]);

  if (!book) return <p className="p-6">Loading...</p>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-100 p-6">

      {/* BACK */}
      <div className="mb-6 flex items-center gap-2 text-gray-600">
        <button
          onClick={() => router.push("/")}
          className="hover:text-black"
        >
          ← Back
        </button>

        <span className="text-gray-400">•</span>

        <span className="font-medium text-gray-800">
          {book.title}
        </span>
      </div>

      {/* MAIN */}
      <div className="flex gap-10">

        {/* LEFT */}
        <div className="flex gap-4">

          {/* BIG IMAGE */}
          <img
            src={selectedImage || "https://via.placeholder.com/500"}
            className="w-[420px] h-auto rounded-xl shadow-lg"
          />

          {/* THUMBNAILS */}
          <div className="flex flex-col gap-4">
            {(book.images || [book.image]).map((img: string, index: number) => (
              <img
                key={index}
                src={img || "https://via.placeholder.com/100"}
                onClick={() => setSelectedImage(img)}
                className={`w-24 h-auto rounded-lg shadow cursor-pointer transition
                  ${selectedImage === img
                    ? "ring-4 ring-indigo-400"
                    : "opacity-70 hover:opacity-100"
                  }
                `}
              />
            ))}
          </div>

        </div>

        {/* RIGHT */}
        <div className="max-w-xl">

          <h1 className="text-4xl font-bold text-gray-900 leading-tight">
            {book.title}
          </h1>

          <p className="text-xl text-gray-600 mt-2">
            {book.author}
          </p>

          <p className="mt-6 text-gray-600 leading-relaxed text-lg">
            {book.summary || book.content || "ไม่มีคำอธิบาย"}
          </p>

        </div>
      </div>
    </div>
  );
}