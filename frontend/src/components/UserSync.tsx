"use client";

import { useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { api } from "@/lib/api";

/**
 * Silently upserts the authenticated user into the backend on every login.
 * Renders nothing - drop into layout once inside SessionProvider.
 */
export default function UserSync() {
  const { data: session, status } = useSession();
  const synced = useRef(false);

  useEffect(() => {
    if (status === "authenticated" && session && !synced.current) {
      synced.current = true;
      api.user.sync(session).catch(() => {
        // Retry next render if it fails
        synced.current = false;
      });
    }
    if (status !== "authenticated") {
      synced.current = false;
    }
  }, [status, session]);

  return null;
}
