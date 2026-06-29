"use client";
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  status: number | null; // HTTP status khi lỗi (0 = mất kết nối)
  reload: () => void;
}

/** Gọi một hàm API và quản lý loading/error. `deps` đổi -> tự fetch lại. */
export function useApi<T>(fn: () => Promise<T>, deps: unknown[]): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [tick, setTick] = useState(0);

  // fn được tạo mới mỗi render; ta cố tình chỉ phụ thuộc vào deps + tick.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    setStatus(null);
    run()
      .then((d) => alive && setData(d))
      .catch((e: unknown) => {
        if (!alive) return;
        setData(null);
        setError(e instanceof Error ? e.message : String(e));
        setStatus(e instanceof ApiError ? e.status : null);
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [run, tick]);

  return { data, loading, error, status, reload: () => setTick((t) => t + 1) };
}
