"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Book = {
  id: number;
  title: string;
  author: string;
  timestamp: string;
};

export default function Home() {
  const [books, setBooks] = useState<Book[]>([]);
  const [search, setSearch] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      const res = await fetch("http://127.0.0.1:8000/api/books");
      const data = await res.json();

      if (Array.isArray(data)) {
        setBooks(data);
      } else {
        setBooks([]);
      }
    };

    fetchData();
  }, []);

  const filteredBooks = books.filter((book) => {
    const matchTitle = book.title
      .toLowerCase()
      .includes(search.toLowerCase());

    const matchDate = selectedDate
      ? book.timestamp?.startsWith(selectedDate)
      : true;

    return matchTitle && matchDate;
  });

  return (
    <div className="min-h-screen bg-pink-50 p-6">

      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-pink-600">
            📚 Book History
          </h1>
        </div>

        <button
          onClick={() => router.push("/detect")}
          className="bg-pink-500 hover:bg-pink-600 text-white px-5 py-2 rounded-xl shadow-lg transition"
        >
          📷 Image Log
        </button>
      </div>

      {/* 📊 DASHBOARD (Count Respond) */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">

        <div className="bg-white p-4 rounded-xl shadow border border-pink-100">
          <p className="text-sm text-gray-500">Total Books</p>
          <h2 className="text-2xl font-bold text-pink-600">
            {books.length}
          </h2>
        </div>

        <div className="bg-white p-4 rounded-xl shadow border border-pink-100">
          <p className="text-sm text-gray-500">Filtered</p>
          <h2 className="text-2xl font-bold text-purple-500">
            {filteredBooks.length}
          </h2>
        </div>

        <div className="bg-white p-4 rounded-xl shadow border border-pink-100">
          <p className="text-sm text-gray-500">Today</p>
          <h2 className="text-2xl font-bold text-blue-500">
            {
              books.filter((b) =>
                b.timestamp?.startsWith(
                  new Date().toISOString().slice(0, 10)
                )
              ).length
            }
          </h2>
        </div>

      </div>

      {/* FILTER */}
      <div className="flex gap-3 mb-6">

        {/* SEARCH */}
        <input
          type="text"
          placeholder="🔍 Search book..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-4 py-3 rounded-xl border border-pink-200 
          shadow-md bg-white focus:outline-none focus:ring-2 focus:ring-pink-400"
        />

        {/* DATE */}
        <div className="bg-white px-4 py-2 rounded-xl shadow-md border border-pink-200 flex items-center gap-2">
          📅
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-transparent outline-none text-gray-700"
          />
        </div>
      </div>

      {/* LIST */}
      <div className="space-y-4">
        {filteredBooks.length === 0 && (
          <p className="text-center text-gray-400">No data...</p>
        )}

        {filteredBooks.map((book, index) => (
          <div
            key={book.id}
            className="flex items-center bg-white p-4 rounded-2xl shadow-md hover:shadow-xl transition border border-pink-100"
          >
            {/* NUMBER */}
            <div className="w-14 h-14 bg-pink-400 text-white flex items-center justify-center rounded-xl text-lg font-bold mr-4 shadow">
              #{index + 1}
            </div>

            {/* INFO */}
            <div className="flex-1">
              <p className="text-lg font-bold text-gray-800">
                {book.title}
              </p>
              <p className="text-gray-500 text-sm mt-1">
                Author: {book.author}
              </p>

              {book.timestamp && (
                <p className="text-xs text-gray-400 mt-1">
                  📅 {book.timestamp}
                </p>
              )}
            </div>

            {/* BUTTON */}
            <button
              onClick={() => router.push(`/books/${book.id}`)}
              className="bg-pink-500 hover:bg-pink-600 text-white px-5 py-2 rounded-lg shadow transition"
            >
              Detail →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}