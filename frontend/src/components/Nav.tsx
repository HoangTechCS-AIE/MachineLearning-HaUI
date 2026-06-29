"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChartLineUp } from "@phosphor-icons/react/dist/ssr";

const LINKS = [
  { href: "/", label: "Tổng quan" },
  { href: "/stock", label: "Cổ phiếu" },
  { href: "/top", label: "Top-N" },
  { href: "/model", label: "Mô hình" },
];

export function Nav() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/85 backdrop-blur">
      <nav className="mx-auto flex h-16 w-full max-w-[1280px] items-center gap-6 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <ChartLineUp size={22} weight="bold" className="text-accent" />
          <span className="font-semibold tracking-tight hidden sm:inline">VN Stock Forecast</span>
        </Link>
        <div className="flex items-center gap-1 text-sm">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-md px-3 py-1.5 transition-colors ${
                isActive(l.href)
                  ? "bg-surface-2 text-text"
                  : "text-muted hover:text-text hover:bg-surface"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
