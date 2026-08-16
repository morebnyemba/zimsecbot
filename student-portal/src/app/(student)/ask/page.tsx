"use client";

import { useEffect, useState } from "react";

import { apiFetch, isFeatureLockedError, type Paginated } from "@/lib/api";
import type { AskResponse, Subject } from "@/lib/types";

type ChatMessage = { role: "user" | "assistant"; content: string };

export default function AskPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [upgradePrompt, setUpgradePrompt] = useState<{ message: string; upgradeUrl: string } | null>(
    null,
  );

  useEffect(() => {
    async function loadSubjects() {
      const res = await apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true");
      setSubjects(res.results);
    }

    loadSubjects();
  }, []);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setError(null);
    setUpgradePrompt(null);
    setSending(true);
    const asked = question;
    setMessages((prev) => [...prev, { role: "user", content: asked }]);
    setQuestion("");

    try {
      const res = await apiFetch<AskResponse>("/api/v1/ai-tutor/ask/", {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId ?? undefined,
          question: asked,
          subject_id: subjectId || undefined,
        }),
      });
      setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
    } catch (err) {
      if (isFeatureLockedError(err)) {
        setUpgradePrompt({
          message: err.body.error.message,
          upgradeUrl: err.body.error.upgrade_url,
        });
      } else {
        setError("Could not reach the AI tutor. Please try again.");
      }
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] max-w-2xl flex-col space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">AI Tutor</h1>
        <select
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">Any subject</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {upgradePrompt && (
        <div className="flex items-center justify-between rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <span>{upgradePrompt.message}</span>
          <a
            href={upgradePrompt.upgradeUrl}
            className="ml-4 shrink-0 rounded-md bg-amber-600 px-3 py-1.5 font-medium text-white hover:bg-amber-700"
          >
            Upgrade plan
          </a>
        </div>
      )}
      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <div className="flex-1 space-y-3 overflow-y-auto rounded-lg border border-gray-200 bg-white p-4">
        {messages.length === 0 ? (
          <p className="text-gray-400">Ask your AI tutor anything about your subjects.</p>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "ml-auto max-w-[80%] rounded-lg bg-blue-600 px-3 py-2 text-sm text-white"
                  : "max-w-[80%] rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-800"
              }
            >
              {m.content}
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={sending || !question.trim()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {sending ? "Asking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}
