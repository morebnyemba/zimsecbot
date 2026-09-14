"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Paperclip, Search, StickyNote as StickyNoteIcon } from "lucide-react";

import { apiFetch, type Paginated } from "@/lib/api";
import { subjectColor } from "@/lib/subject-colors";
import type { Note, StudentSubject, Subject } from "@/lib/types";

export default function NotesPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mySubjects, setMySubjects] = useState<StudentSubject[]>([]);
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
    async function loadFilters() {
      const [subjectsRes, mineRes] = await Promise.all([
        apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true"),
        apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
      ]);
      setSubjects(subjectsRes.results);
      setMySubjects(mineRes.results);
    }

    loadFilters();
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
    const color = subjectColor(activeNote.subject_code || activeNote.subject);
    return (
      <div className="space-y-4">
        <button
          onClick={() => setActiveNote(null)}
          className="flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline"
        >
          <ArrowLeft size={15} />
          Back to notes
        </button>
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${color.bg} ${color.text}`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${color.dot}`} />
              {activeNote.subject_name}
            </span>
            {activeNote.topic_name && (
              <span className="text-xs text-gray-400">{activeNote.topic_name}</span>
            )}
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">{activeNote.title}</h1>
          <p className="mt-4 whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
            {activeNote.content}
          </p>
          {activeNote.media.length > 0 && (
            <div className="mt-4 flex flex-col gap-1.5">
              {activeNote.media.map((url, i) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline"
                >
                  <Paperclip size={14} />
                  {activeNote.media.length > 1 ? `Attached media ${i + 1}` : "View attached media"}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Notes</h1>
        <div className="flex flex-wrap gap-3">
          <select
            value={subjectFilter}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
            <option value="">All subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative">
              <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search notes..."
                className="rounded-md border border-gray-300 py-1.5 pl-8 pr-3 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              />
            </div>
            <button
              type="submit"
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {mySubjects.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleFilterChange("")}
            className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
              subjectFilter === ""
                ? "bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
            }`}
          >
            All
          </button>
          {mySubjects.map((s) => {
            const color = subjectColor(s.subject.code || s.subject.id);
            const active = subjectFilter === s.subject.id;
            return (
              <button
                key={s.id}
                onClick={() => handleFilterChange(s.subject.id)}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                  active
                    ? `${color.bg} ${color.text} ring-1 ${color.ring}`
                    : "bg-gray-50 text-gray-500 hover:bg-gray-100 dark:bg-gray-800/60 dark:text-gray-400 dark:hover:bg-gray-800"
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${color.dot}`} />
                {s.subject.name}
              </button>
            );
          })}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
            />
          ))}
        </div>
      ) : notes.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-gray-200 bg-white p-10 text-center dark:border-gray-800 dark:bg-gray-900">
          <StickyNoteIcon size={26} className="text-gray-300 dark:text-gray-600" />
          <p className="text-sm text-gray-400">No notes found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => {
            const color = subjectColor(note.subject_code || note.subject);
            return (
              <button
                key={note.id}
                onClick={() => setActiveNote(note)}
                className="flex flex-col items-start rounded-lg border border-gray-200 bg-white p-4 text-left shadow-sm transition-shadow hover:border-brand-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-brand-700"
              >
                <span
                  className={`mb-2 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${color.bg} ${color.text}`}
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${color.dot}`} />
                  {note.subject_name}
                </span>
                <p className="font-medium text-gray-900 dark:text-gray-50">{note.title}</p>
                <p className="mt-1 line-clamp-3 text-sm text-gray-500 dark:text-gray-400">{note.content}</p>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
