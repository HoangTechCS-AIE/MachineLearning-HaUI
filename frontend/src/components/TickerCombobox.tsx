"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { MagnifyingGlass } from "@phosphor-icons/react/dist/ssr";
import { api } from "@/lib/api";

export function TickerCombobox({
  tickers: provided,
  autoFocus,
  placeholder = "Tìm mã cổ phiếu (vd FPT, HPG)…",
}: {
  tickers?: string[];
  autoFocus?: boolean;
  placeholder?: string;
}) {
  const router = useRouter();
  const [tickers, setTickers] = useState<string[]>(provided ?? []);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (provided) return;
    let alive = true;
    api.tickers().then((d) => alive && setTickers(d.tickers)).catch(() => {});
    return () => {
      alive = false;
    };
  }, [provided]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const query = q.trim().toUpperCase();
  const matches = (query ? tickers.filter((t) => t.includes(query)) : tickers).slice(0, 8);

  const go = (t: string) => {
    if (!t) return;
    setOpen(false);
    router.push(`/stock/${t}`);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      go(matches[active] ?? query);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={boxRef} className="relative w-full">
      <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 focus-within:border-accent transition-colors">
        <MagnifyingGlass size={18} className="text-muted shrink-0" />
        <input
          // eslint-disable-next-line jsx-a11y/no-autofocus
          autoFocus={autoFocus}
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
            setActive(0);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKey}
          placeholder={placeholder}
          className="w-full bg-transparent py-2.5 text-sm outline-none placeholder:text-muted uppercase"
          aria-label="Tìm mã cổ phiếu"
        />
      </div>
      {open && matches.length > 0 && (
        <ul className="absolute z-30 mt-1.5 w-full overflow-hidden rounded-lg border border-border bg-surface-2 shadow-xl shadow-black/40">
          {matches.map((t, i) => (
            <li key={t}>
              <button
                onMouseEnter={() => setActive(i)}
                onClick={() => go(t)}
                className={`flex w-full items-center justify-between px-3 py-2 text-sm transition-colors ${
                  i === active ? "bg-accent/10 text-text" : "text-muted hover:bg-surface"
                }`}
              >
                <span className="font-semibold tracking-tight tabular">{t}</span>
                <span className="text-xs text-muted">Xem dự báo →</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
