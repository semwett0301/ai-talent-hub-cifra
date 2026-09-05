import { useEffect, useState } from "react";

/** Keep prototype actions through navigation/reload without a backend. */
export function useSessionState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const saved = sessionStorage.getItem(`gs-monitoring-v1:${key}`);
      return saved === null ? initial : (JSON.parse(saved) as T);
    } catch {
      return initial;
    }
  });
  useEffect(() => {
    try {
      sessionStorage.setItem(`gs-monitoring-v1:${key}`, JSON.stringify(value));
    } catch {
      /* Private mode/storage limits: keep in-memory state. */
    }
  }, [key, value]);
  return [value, setValue] as const;
}
