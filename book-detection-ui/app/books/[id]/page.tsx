"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

const API = "http://localhost:8000";

type Book = {
  id: string;
  title: string;
  author: string;
  genre: string;
  keywords: string[];
  language: string;
  summary: string;
  image: string;
  timestamp: string;
};

export default function BookDetail() {
  const { id } = useParams();
  const router = useRouter();

  const [book, setBook] = useState<Book | null>(null);

  useEffect(() => {
    const fetchBook = async () => {
      const res = await fetch(`${API}/api/books/${id}`);
      const data = await res.json();
      setBook(data);
    };

    fetchBook();
  }, [id]);

  if (!book) {
    return <div className="p-10 text-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-pink-50 p-6">

      {/* 🔙 BACK BUTTON (outside card) */}
      <button
        onClick={() => router.push("/")}
        className="mb-6 bg-white border border-pink-300 text-pink-600 px-5 py-2 rounded-xl shadow hover:bg-pink-100 transition"
      >
        ← Back
      </button>

      {/* 🧾 MAIN CARD */}
      <div className="max-w-6xl mx-auto bg-white rounded-3xl shadow-xl border border-pink-100 p-10 flex gap-10">

        {/* 📷 LEFT: IMAGE */}
        <div className="w-1/2 flex justify-center items-center">
          <img
            src={`${API}${book.image}`}
            className="rounded-2xl shadow-lg max-h-[600px] object-contain"
          />
        </div>

        {/* 📄 RIGHT: INFO */}
        <div className="w-1/2 flex flex-col">

          {/* TITLE */}
          <h1 className="text-4xl font-bold text-pink-600 mb-2">
            {book.title}
          </h1>

          {/* AUTHOR */}
          <p className="text-gray-600 mb-4 text-lg">
            {book.author}
          </p>

          {/* LINE */}
          <div className="h-[2px] bg-pink-200 mb-6 rounded-full" />

          {/* INFO BOX */}
          <div className="bg-pink-50 rounded-2xl p-6 shadow-sm border border-pink-100 space-y-3">

            <p>
              <span className="font-semibold text-pink-500">📅 Date:</span>{" "}
              {book.timestamp?.replace("T", " ").slice(0, 19)}
            </p>

            <p>
              <span className="font-semibold text-pink-500">📚 Genre:</span>{" "}
              {book.genre || "-"}
            </p>

            <p>
              <span className="font-semibold text-pink-500">🌐 Language:</span>{" "}
              {book.language || "-"}
            </p>

            {/* KEYWORDS */}
            <div>
              <p className="font-semibold text-pink-500 mb-2">
                🏷 Keywords
              </p>
              <div className="flex flex-wrap gap-2">
                {book.keywords?.map((k, i) => (
                  <span
                    key={i}
                    className="bg-white border border-pink-300 text-pink-600 px-3 py-1 rounded-full text-sm"
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* SUMMARY */}
          <div className="mt-6">
            <p className="font-semibold text-pink-500 mb-2 text-lg">
              📖 Summary
            </p>
            <p className="text-gray-600 leading-relaxed">
              {book.summary}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}