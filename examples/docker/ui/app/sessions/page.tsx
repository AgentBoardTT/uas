"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  Clock,
  Loader2,
  MessageSquare,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { listSessions, stopSession, SessionInfo } from "@/lib/api-client";

export default function SessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    setLoading(true);
    try {
      const sessionList = await listSessions();
      setSessions(sessionList);
    } catch (e) {
      console.error("Failed to load sessions:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(sessionId: string) {
    if (!confirm("Are you sure you want to stop this session?")) return;

    setDeleting(sessionId);
    try {
      await stopSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    } catch (e) {
      console.error("Failed to stop session:", e);
    } finally {
      setDeleting(null);
    }
  }

  function formatDate(dateStr: string) {
    const date = new Date(dateStr);
    return date.toLocaleString();
  }

  function getTimeAgo(dateStr: string) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes}m ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;

    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/")}
              className="p-2 hover:bg-gray-800 rounded-lg transition"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-bold">Active Sessions</h1>
          </div>
          <button
            onClick={loadSessions}
            disabled={loading}
            className="p-2 hover:bg-gray-800 rounded-lg transition disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-12 h-12 mx-auto mb-4 text-gray-600" />
            <p className="text-gray-400">No active sessions</p>
            <button
              onClick={() => router.push("/")}
              className="mt-4 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-500 transition"
            >
              Launch an Agent
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className="p-6 bg-gray-800/50 rounded-xl border border-gray-700 hover:border-gray-600 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                      <Bot className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{session.config_name}</h3>
                      <p className="text-sm text-gray-400">
                        {session.session_id}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        session.status === "running"
                          ? "bg-green-900/50 text-green-400"
                          : session.status === "idle"
                          ? "bg-yellow-900/50 text-yellow-400"
                          : "bg-gray-700 text-gray-400"
                      }`}
                    >
                      {session.status}
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-6 text-sm text-gray-400">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    {session.message_count} messages
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Last active: {getTimeAgo(session.last_activity)}
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-3">
                  <button
                    onClick={() => router.push(`/chat/${session.session_id}`)}
                    className="flex-1 py-2 px-4 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition"
                  >
                    Resume Chat
                  </button>
                  <button
                    onClick={() => handleDelete(session.session_id)}
                    disabled={deleting === session.session_id}
                    className="py-2 px-4 bg-red-900/30 hover:bg-red-900/50 text-red-400 rounded-lg transition flex items-center gap-2"
                  >
                    {deleting === session.session_id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                    Stop
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
