"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
import type { StudentSubject, Subject } from "@/lib/types";

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mySubjects, setMySubjects] = useState<StudentSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    const [subjectsRes, mineRes] = await Promise.all([
      apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true"),
      apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
    ]);
    setSubjects(subjectsRes.results);
    setMySubjects(mineRes.results);
    setLoading(false);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadData();
  }, [loadData]);

  const mySubjectIds = new Set(mySubjects.map((s) => s.subject.id));

  async function addSubject(subjectId: string) {
    setBusyId(subjectId);
    try {
      await apiFetch("/api/v1/profile/me/subjects/", {
        method: "POST",
        body: JSON.stringify({ subject_id: subjectId }),
      });
      await loadData();
    } finally {
      setBusyId(null);
    }
  }

  async function removeSubject(subjectId: string) {
    setBusyId(subjectId);
    try {
      await apiFetch(`/api/v1/profile/me/subjects/${subjectId}/`, { method: "DELETE" });
      await loadData();
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Subjects</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {subjects.map((subject) => {
          const selected = mySubjectIds.has(subject.id);
          return (
            <div
              key={subject.id}
              className="flex flex-col justify-between gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div>
                <p className="font-medium">{subject.name}</p>
                <p className="text-sm text-gray-500">
                  {subject.code} · {subject.level} · {subject.tier}
                </p>
              </div>
              <button
                onClick={() =>
                  selected ? removeSubject(subject.id) : addSubject(subject.id)
                }
                disabled={busyId === subject.id}
                className={
                  selected
                    ? "rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60"
                    : "rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                }
              >
                {selected ? "Remove" : "Add to my subjects"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
