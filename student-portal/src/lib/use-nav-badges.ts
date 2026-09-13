"use client";

import { useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
import type { StudentAnalytics, StudentSubject } from "@/lib/types";

/** Lightweight live counters shown as nav badges (subject count, streak). Fetched once per mount. */
export function useNavBadges() {
  const [subjectCount, setSubjectCount] = useState<number | null>(null);
  const [streak, setStreak] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [subjectsRes, analyticsRes] = await Promise.all([
          apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
          apiFetch<StudentAnalytics>("/api/v1/analytics/me/"),
        ]);
        if (cancelled) return;
        setSubjectCount(subjectsRes.results.length);
        setStreak(analyticsRes.streak?.current_streak ?? 0);
      } catch {
        // Badges are decorative; silently skip on failure rather than breaking nav.
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { subjectCount, streak };
}
