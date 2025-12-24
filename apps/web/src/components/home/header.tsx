"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Github, Menu, X } from "lucide-react";
import { useState } from "react";

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { name: "홈", href: "/" },
    { name: "갤러리", href: "#gallery" },
    { name: "문서", href: "#docs" },
    { name: "GitHub", href: "https://github.com/soonseek/gr8diy-web", external: true },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2" aria-label="gr8diy 홈으로 이동">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-emerald-500 flex items-center justify-center">
            <span className="text-white font-bold text-lg">G</span>
          </div>
          <span className="font-bold text-xl">gr8diy</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6" aria-label="주요 메뉴">
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              target={item.external ? "_blank" : undefined}
              rel={item.external ? "noopener noreferrer" : undefined}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              aria-label={`${item.name}${item.external ? " (새 창)" : ""}`}
            >
              {item.name === "GitHub" ? (
                <span className="flex items-center gap-1">
                  <Github className="w-4 h-4" aria-hidden="true" />
                  {item.name}
                </span>
              ) : (
                item.name
              )}
            </Link>
          ))}
        </nav>

        {/* CTA Button */}
        <div className="hidden md:block">
          <Button size="sm" className="rounded-full" asChild>
            <Link href="/create" aria-label="알고리즘 만들기 페이지로 이동">
              알고리즘 만들기
            </Link>
          </Button>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2 text-muted-foreground"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label={mobileMenuOpen ? "메뉴 닫기" : "메뉴 열기"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Menu Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border/40 bg-background relative z-50">
          <nav className="container mx-auto px-4 py-4 flex flex-col gap-4" aria-label="모바일 메뉴">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                target={item.external ? "_blank" : undefined}
                rel={item.external ? "noopener noreferrer" : undefined}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors py-2"
                onClick={() => setMobileMenuOpen(false)}
                aria-label={`${item.name}${item.external ? " (새 창)" : ""}`}
              >
                {item.name === "GitHub" ? (
                  <span className="flex items-center gap-2">
                    <Github className="w-4 h-4" aria-hidden="true" />
                    {item.name}
                  </span>
                ) : (
                  item.name
                )}
              </Link>
            ))}
            <Button size="sm" className="rounded-full w-full" asChild>
              <Link href="/create" onClick={() => setMobileMenuOpen(false)}>
                알고리즘 만들기
              </Link>
            </Button>
          </nav>
        </div>
      )}
    </header>
  );
}
