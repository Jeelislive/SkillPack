"use client";

import { useState, useEffect, useCallback } from "react";
import type { Session } from "next-auth";
import { api } from "@/lib/api";

export function useSaves(session: Session | null) {
  const [savedSkillIds, setSavedSkillIds]   = useState<Set<number>>(new Set());
  const [savedBundleIds, setSavedBundleIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!session?.user) return;
    setLoading(true);
    api.user.saves.list(session)
      .then((data) => {
        setSavedSkillIds(new Set(data.saved_skill_ids));
        setSavedBundleIds(new Set(data.saved_bundle_ids));
      })
      .catch(() => { /* ignore */ })
      .finally(() => setLoading(false));
  }, [session]);

  const toggleSkill = useCallback(async (id: number) => {
    if (!session?.user) return;
    const isSaved = savedSkillIds.has(id);
    // Optimistic update
    setSavedSkillIds((prev) => {
      const next = new Set(prev);
      isSaved ? next.delete(id) : next.add(id);
      return next;
    });
    try {
      if (isSaved) {
        await api.user.saves.unsaveSkill(id, session);
      } else {
        await api.user.saves.saveSkill(id, session);
      }
    } catch {
      // Revert on failure
      setSavedSkillIds((prev) => {
        const next = new Set(prev);
        isSaved ? next.add(id) : next.delete(id);
        return next;
      });
    }
  }, [session, savedSkillIds]);

  const toggleBundle = useCallback(async (id: number) => {
    if (!session?.user) return;
    const isSaved = savedBundleIds.has(id);
    setSavedBundleIds((prev) => {
      const next = new Set(prev);
      isSaved ? next.delete(id) : next.add(id);
      return next;
    });
    try {
      if (isSaved) {
        await api.user.saves.unsaveBundle(id, session);
      } else {
        await api.user.saves.saveBundle(id, session);
      }
    } catch {
      setSavedBundleIds((prev) => {
        const next = new Set(prev);
        isSaved ? next.add(id) : next.delete(id);
        return next;
      });
    }
  }, [session, savedBundleIds]);

  return { savedSkillIds, savedBundleIds, toggleSkill, toggleBundle, loading };
}
