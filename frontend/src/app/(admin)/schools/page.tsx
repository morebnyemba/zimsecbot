"use client";

import { useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";

interface School {
  id: string;
  name: string;
  admin_user: string;
  seat_count: number;
}

interface SchoolSeat {
  id: string;
  school: string;
  user: string;
  is_active: boolean;
}

interface SchoolAnalytics {
  student_count: number;
  average_accuracy: number | null;
  weak_topic_count: number;
}

export default function SchoolsPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [seats, setSeats] = useState<SchoolSeat[]>([]);
  const [analytics, setAnalytics] = useState<SchoolAnalytics | null>(null);
  const [newSeatUserId, setNewSeatUserId] = useState("");

  async function loadSchools() {
    const res = await apiFetch<Paginated<School>>("/api/v1/schools/");
    setSchools(res.results);
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadSchools();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setError(null);
    setCreating(true);
    try {
      await apiFetch<School>("/api/v1/schools/", {
        method: "POST",
        body: JSON.stringify({ name: newName }),
      });
      setNewName("");
      await loadSchools();
    } catch {
      setError("Could not create school.");
    } finally {
      setCreating(false);
    }
  }

  async function toggleExpand(school: School) {
    if (expandedId === school.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(school.id);
    const [seatsRes, analyticsRes] = await Promise.all([
      apiFetch<SchoolSeat[]>(`/api/v1/schools/${school.id}/seats/`),
      apiFetch<SchoolAnalytics>(`/api/v1/schools/${school.id}/analytics/`),
    ]);
    setSeats(seatsRes);
    setAnalytics(analyticsRes);
  }

  async function handleAddSeat(schoolId: string, e: React.FormEvent) {
    e.preventDefault();
    if (!newSeatUserId.trim()) return;
    const seat = await apiFetch<SchoolSeat>(`/api/v1/schools/${schoolId}/seats/`, {
      method: "POST",
      body: JSON.stringify({ user_id: newSeatUserId }),
    });
    setSeats((prev) => [...prev, seat]);
    setNewSeatUserId("");
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Schools</h1>

      <form
        onSubmit={handleCreate}
        className="flex max-w-md items-end gap-2 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      >
        <div className="flex-1 space-y-1">
          <label className="text-sm font-medium text-gray-700">New school name</label>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          Create
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {schools.length === 0 ? (
        <p className="text-gray-400">No schools yet.</p>
      ) : (
        <div className="space-y-3">
          {schools.map((school) => (
            <div key={school.id} className="rounded-lg border border-gray-200 bg-white shadow-sm">
              <button
                onClick={() => toggleExpand(school)}
                className="flex w-full items-center justify-between px-4 py-3 text-left"
              >
                <span className="font-medium">{school.name}</span>
                <span className="text-sm text-gray-500">{school.seat_count} seats</span>
              </button>

              {expandedId === school.id && (
                <div className="space-y-4 border-t border-gray-100 p-4">
                  {analytics && (
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div>
                        <p className="text-gray-500">Students</p>
                        <p className="font-semibold">{analytics.student_count}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Avg accuracy</p>
                        <p className="font-semibold">
                          {analytics.average_accuracy !== null
                            ? `${analytics.average_accuracy.toFixed(0)}%`
                            : "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Weak topics</p>
                        <p className="font-semibold">{analytics.weak_topic_count}</p>
                      </div>
                    </div>
                  )}

                  <div>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                      Seats
                    </h3>
                    <ul className="space-y-1 text-sm">
                      {seats.map((seat) => (
                        <li key={seat.id} className="flex justify-between">
                          <span>{seat.user}</span>
                          <span className="text-gray-500">
                            {seat.is_active ? "Active" : "Inactive"}
                          </span>
                        </li>
                      ))}
                      {seats.length === 0 && <li className="text-gray-400">No seats yet.</li>}
                    </ul>
                    <form
                      onSubmit={(e) => handleAddSeat(school.id, e)}
                      className="mt-2 flex gap-2"
                    >
                      <input
                        type="text"
                        placeholder="User ID"
                        value={newSeatUserId}
                        onChange={(e) => setNewSeatUserId(e.target.value)}
                        className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                      />
                      <button
                        type="submit"
                        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        Add seat
                      </button>
                    </form>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
