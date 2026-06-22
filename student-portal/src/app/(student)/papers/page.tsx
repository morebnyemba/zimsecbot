"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
import type { PastPaper, Subject } from "@/lib/types";

export default function PapersPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [papers, setPapers] = useState<PastPaper[]>([]);
  const [subjectFilter, setSubjectFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const loadPapers = useCallback(async (subjectId: string) => {
    setLoading(true);
    const query = subjectId ? `?subject=${subjectId}` : "";
    const res = await apiFetch<Paginated<PastPaper>>(`/api/v1/papers/${query}`);
    setPapers(res.results);
    setLoading(false);
  }, []);

  useEffect(() => {
    async function loadSubjects() {
      const res = await apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true");
      setSubjects(res.results);
    }

    loadSubjects();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadPapers("");
  }, [loadPapers]);

  async function handleDownload(paper: PastPaper) {
    const data = await apiFetch<{ file_url: string }>(`/api/v1/papers/${paper.id}/download/`);
    window.open(data.file_url, "_blank");
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Past Papers</h1>
        <select
          value={subjectFilter}
          onChange={(e) => {
            setSubjectFilter(e.target.value);
            loadPapers(e.target.value);
          }}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">All subjects</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="text-gray-400">Loading…</p>
      ) : papers.length === 0 ? (
        <p className="text-gray-400">No past papers found.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500">
              <tr>
                <th className="px-4 py-2">Subject</th>
                <th className="px-4 py-2">Year</th>
                <th className="px-4 py-2">Session</th>
                <th className="px-4 py-2">Paper</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {papers.map((paper) => (
                <tr key={paper.id} className="border-t border-gray-100">
                  <td className="px-4 py-2">{paper.subject_name}</td>
                  <td className="px-4 py-2">{paper.year}</td>
                  <td className="px-4 py-2">{paper.session}</td>
                  <td className="px-4 py-2">{paper.paper_number}</td>
                  <td className="px-4 py-2">{paper.paper_type}</td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleDownload(paper)}
                      className="rounded-md border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
