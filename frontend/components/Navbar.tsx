"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const LINKS = [
  { href: "/upload", label: "Upload", roles: ["uploader", "reviewer", "admin"] },
  { href: "/batches", label: "Batches", roles: ["uploader", "reviewer", "admin"] },
  { href: "/jobs", label: "Jobs", roles: ["uploader", "reviewer", "admin"] },
  { href: "/review", label: "Review Queue", roles: ["reviewer", "admin"] },
  { href: "/admin/settings", label: "Admin Settings", roles: ["admin"] },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-6">
          <span className="font-semibold text-slate-900">PixelForge Studio</span>
          <nav className="flex gap-1">
            {LINKS.filter((l) => !user || l.roles.includes(user.role)).map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                  pathname?.startsWith(l.href) ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-600">
          {user && (
            <>
              <span>
                {user.email} <span className="text-slate-400">({user.role})</span>
              </span>
              <button onClick={logout} className="btn-secondary py-1">
                Sign out
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
