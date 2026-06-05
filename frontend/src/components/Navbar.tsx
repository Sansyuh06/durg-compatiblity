"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";

const NAV_LINKS = [
  { href: "/analyze", label: "Analyze" },
  { href: "/compare", label: "Compare" },
  { href: "/trials", label: "Trials" },
  { href: "/agent", label: "Agent" },
  { href: "/pk", label: "PK" },
  { href: "/ddi", label: "DDI" },
  { href: "/protein", label: "Protein" },
  { href: "/admet", label: "ADMET" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-6 py-3",
        scrolled && "backdrop-blur-xl border-b border-white/[0.07] bg-[#080A0F]/80"
      )}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/" className="font-mono text-sm tracking-[0.2em] text-white/80 hover:text-white transition-colors">
          FOLDABLES
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "text-xs font-mono tracking-wider transition-colors",
                pathname === l.href ? "text-[#4AFA9A]" : "text-white/50 hover:text-white/80"
              )}
            >
              {l.label}
            </Link>
          ))}
          <Link
            href="/analyze"
            className="ml-4 px-4 py-1.5 text-xs font-mono tracking-wider bg-[#4AFA9A] text-[#080A0F] rounded hover:bg-[#3de88a] transition-colors"
          >
            Analyze →
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button className="md:hidden text-white/60" onClick={() => setOpen(!open)}>
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden mt-3 pb-4 border-t border-white/[0.07] pt-3 flex flex-col gap-3">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className={cn(
                "text-sm font-mono px-2",
                pathname === l.href ? "text-[#4AFA9A]" : "text-white/60"
              )}
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
