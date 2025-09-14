"use client";
import { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";

interface Message {
  message: string;
}

export default function HomePage() {
  const [message, setMessage] = useState<string | null>(null);
  const [message2, setMessage2] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post<Message>("http://localhost:8000/", {
        text: message,
      });
      fetchMessage();
      setMessage(response.data.message);
    } catch (error: any) {
      setMessage("Error: " + error.message);
    }
  };

  const fetchMessage = async () => {
    try {
      const response = await axios.get<Message>("http://127.0.0.1:8000/");
      setMessage2(response.data.message);
    } catch (err) {
      console.error("Failed to fetch message:", err);
      setError("Failed to fetch message from the backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessage();
  }, []);

  return (
    <>
      <header>
        <Link
          className="absolute top-4 left-4 text-blue-600 hover:underline"
          href="items"
        >
          Home
        </Link>
      </header>
      <main className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Welcome to Brand2Tiktok
          </h1>
          <p className="text-gray-600 mb-6">This is the homepage.</p>
          <h2 className="text-2xl font-bold text-gray-700 mb-4">
            Message from Backend:
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-black mb-1">
                Name
              </label>
              <input
                type="text"
                value={message || ""}
                onChange={(e) => setMessage(e.target.value)}
                required
                className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Send to Backend
            </button>
          </form>

          {loading && <p className="text-gray-500">Loading...</p>}
          {error && <p className="text-red-500 font-semibold">{error}</p>}
          {message2 && (
            <p className="text-lg text-green-700 font-medium">{message2}</p>
          )}
        </div>
      </main>
    </>
  );
}
