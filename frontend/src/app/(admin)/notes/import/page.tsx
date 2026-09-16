"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp } from "lucide-react";

import { ApiError, apiFetch, type Paginated } from "@/lib/api";

interface Subject {
  id: string;
  name: string;
  code: string;
}
interface Topic {
  id: string;
  name: string;
}
interface Subtopic {
  id: string;
  name: string;
}

function extractErrorMessage(err: unknown): string {
  if (!(err instanceof ApiError)) return "Import failed. Please try again.";
  const body = err.body as { error?: { message?: string } } | Record<string, unknown> | null;
  const nested = (body as { error?: { message?: string } } | null)?.error?.message;
  if (nested) return nested;
  if (body && typeof body === "object") {
    const parts = Object.values(body).flat().map(String);
    if (parts.length > 0) return parts.join(" ");
  }
  return "Import failed. Please try again.";
}

export default function ImportNotePage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [subtopics, setSubtopics] = useState<Subtopic[]>([]);

  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [subtopic, setSubtopic] = useState("");
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<"url" | "file">("url");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceFile, setSourceFile] = useState<File | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOptions() {
      const [subjectsRes, topicsRes, subtopicsRes] = await Promise.all([
        apiFetch<Paginated<Subject>>("/api/v1/subjects/?page_size=200"),
        apiFetch<Paginated<Topic>>("/api/v1/topics/?page_size=200"),
        apiFetch<Paginated<Subtopic>>("/api/v1/subtopics/?page_size=200"),
      ]);
      setSubjects(subjectsRes.results);
      setTopics(topicsRes.results);
      setSubtopics(subtopicsRes.results);
    }
    loadOptions();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data = new FormData();
      data.append("subject", subject);
      if (topic) data.append("topic", topic);
      if (subtopic) data.append("subtopic", subtopic);
      data.append("title", title);
      if (sourceType === "url") {
        data.append("source_url", sourceUrl);
      } else if (sourceFile) {
        data.append("source_file", sourceFile);
      }

      await apiFetch("/api/v1/notes/import/", { method: "POST", body: data });
      router.push("/notes");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <FileUp size={19} />
        </span>
        <h1 className="text-xl font-semibold">Import Note from PDF/URL</h1>
      </div>

      <p className="text-sm text-gray-500">
        Extract text from a PDF or a web page into a new draft note. It won&apos;t be shown to
        students or added to the AI Tutor&apos;s knowledge base until you review it on the Notes
        page and change its status to Published.
      </p>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
      >
        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Subject</label>
          <select
            required
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          >
            <option value="">Select a subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.code})
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Topic (optional)</label>
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            >
              <option value="">—</option>
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Subtopic (optional)</label>
            <select
              value={subtopic}
              onChange={(e) => setSubtopic(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            >
              <option value="">—</option>
              {subtopics.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Title</label>
          <input
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
        </div>

        <div className="space-y-2 border-t border-gray-100 pt-4">
          <div className="flex gap-4 text-sm text-gray-700">
            <label className="flex items-center gap-1.5">
              <input
                type="radio"
                checked={sourceType === "url"}
                onChange={() => setSourceType("url")}
              />
              Web page URL
            </label>
            <label className="flex items-center gap-1.5">
              <input
                type="radio"
                checked={sourceType === "file"}
                onChange={() => setSourceType("file")}
              />
              PDF file
            </label>
          </div>

          {sourceType === "url" ? (
            <input
              type="url"
              required
              placeholder="https://..."
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
          ) : (
            <input
              type="file"
              accept="application/pdf"
              required
              onChange={(e) => setSourceFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm"
            />
          )}
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {submitting ? "Importing..." : "Import"}
        </button>
      </form>
    </div>
  );
}
