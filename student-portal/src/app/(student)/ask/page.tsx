"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send, Sparkles, User } from "lucide-react";

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
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadSubjects() {
      const res = await apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true");
      setSubjects(res.results);
    }

    loadSubjects();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

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
    <div className="flex h-[calc(100dvh-10.5rem)] max-w-2xl flex-col space-y-4 lg:h-[calc(100dvh-6.5rem)]">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
            <Sparkles size={19} />
          </span>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">AI Tutor</h1>
        </div>
        <select
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
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
        <div className="flex items-center justify-between rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
          <span>{upgradePrompt.message}</span>
          <a
            href={upgradePrompt.upgradeUrl}
            className="ml-4 shrink-0 rounded-md bg-amber-600 px-3 py-1.5 font-medium text-white hover:bg-amber-700"
          >
            Upgrade plan
          </a>
        </div>
      )}
      {error && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </p>
      )}

      <div
        ref={scrollRef}
        className="flex-1 space-y-3 overflow-y-auto rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
      >
        {messages.length === 0 ? (
          <p className="text-gray-400">Ask your AI tutor anything about your subjects.</p>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex items-end gap-2 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <span
                className={
                  m.role === "user"
                    ? "flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
                    : "flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
                }
              >
                {m.role === "user" ? <User size={14} /> : <Bot size={14} />}
              </span>
              <div
                className={
                  m.role === "user"
                    ? "max-w-[80%] rounded-lg bg-brand-600 px-3 py-2 text-sm text-white"
                    : "max-w-[80%] rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-800 dark:bg-gray-800 dark:text-gray-100"
                }
              >
                {m.content}
              </div>
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
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
        />
        <button
          type="submit"
          disabled={sending || !question.trim()}
          className="flex items-center gap-1.5 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          <Send size={15} />
          {sending ? "Asking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}
