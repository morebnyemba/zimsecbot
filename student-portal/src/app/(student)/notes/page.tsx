"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
import type { Note, Subject } from "@/lib/types";

export default function NotesPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [subjectFilter, setSubjectFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeNote, setActiveNote] = useState<Note | null>(null);

  const loadNotes = useCallback(async (subjectId: string, query: string) => {
    setLoading(true);
    const params = new URLSearchParams();
    if (subjectId) params.set("subject", subjectId);
    if (query) params.set("search", query);
    const qs = params.toString();
    const res = await apiFetch<Paginated<Note>>(`/api/v1/notes/${qs ? `?${qs}` : ""}`);
    setNotes(res.results);
    setLoading(false);
  }, []);

  useEffect(() => {
    async function loadSubjects() {
      const res = await apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true");
      setSubjects(res.results);
    }

    loadSubjects();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadNotes("", "");
  }, [loadNotes]);

  function handleFilterChange(subjectId: string) {
    setSubjectFilter(subjectId);
    loadNotes(subjectId, search);
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadNotes(subjectFilter, search);
  }

  if (activeNote) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => setActiveNote(null)}
          className="text-sm font-medium text-blue-600 hover:underline"
        >
          ← Back to notes
        </button>
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-semibold">{activeNote.title}</h1>
          <p className="mt-4 whitespace-pre-wrap text-sm text-gray-700">{activeNote.content}</p>
          {activeNote.media && (
            <a
              href={activeNote.media}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-block text-sm font-medium text-blue-600 hover:underline"
            >
              View attached media
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">Notes</h1>
        <div className="flex gap-3">
          <select
            value={subjectFilter}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">All subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search notes..."
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : notes.length === 0 ? (
        <p className="text-gray-400">No notes found.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => (
            <button
              key={note.id}
              onClick={() => setActiveNote(note)}
              className="rounded-lg border border-gray-200 bg-white p-4 text-left shadow-sm hover:border-blue-300"
            >
              <p className="font-medium">{note.title}</p>
              <p className="mt-1 line-clamp-3 text-sm text-gray-500">{note.content}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
