"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, Send } from "lucide-react";

const examplePrompts = [
  "RSI 과매수/과매도 구간에서 매수/매도",
  "볼린저 밴드 돌파 시 추종 매매",
  "MACD 골든크로스 때 매수",
] as const;

export function Hero() {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      // TODO: 알고리즘 생성 페이지로 이동
      window.location.href = `/create?prompt=${encodeURIComponent(prompt)}`;
    }
  };

  const handleExampleClick = (example: string) => {
    setPrompt(example);
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-hero" />

      {/* Animated gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl animate-pulse delay-1000" />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 py-32 text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm text-primary">오픈소스 자동매매 혁명</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          혁명적인
          <br />
          <span className="text-gradient-primary">DIY 자동매매</span>
        </h1>

        {/* Description */}
        <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed">
          누구나 프롬프트로 자동매매 알고리즘을 만들고 배포할 수 있습니다.
          <br className="hidden md:block" />
          AI와 대화하며 완성도 있는 알고리즘을 정의해보세요.
        </p>

        {/* Prompt Input Section */}
        <div className="max-w-3xl mx-auto mb-8">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex flex-col gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="원하는 매매 전략을 설명하세요..."
                  rows={4}
                  aria-label="매매 전략 프롬프트 입력"
                  className="w-full px-6 py-4 pr-12 rounded-2xl bg-background/50 border border-border/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none"
                />
                {prompt && (
                  <button
                    type="button"
                    onClick={() => setPrompt("")}
                    aria-label="입력 내용 삭제"
                    className="absolute right-4 top-4 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    ×
                  </button>
                )}
              </div>
              <div className="flex items-center justify-between gap-3">
                <Button
                  type="submit"
                  size="lg"
                  className="flex-1 rounded-full px-8 py-4 text-lg group"
                  disabled={!prompt.trim()}
                  aria-label="알고리즘 만들기"
                >
                  <Send className="w-5 h-5 mr-2 group-hover:translate-x-1 transition-transform" />
                  만들기
                </Button>
              </div>
            </div>
          </form>

          {/* Example Prompts */}
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <span className="text-sm text-muted-foreground">예시:</span>
            {examplePrompts.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => handleExampleClick(example)}
                className={`text-sm px-3 py-1 rounded-full transition-all ${
                  prompt === example
                    ? "bg-primary/20 text-primary border border-primary/30"
                    : "bg-secondary/50 text-muted-foreground hover:bg-secondary hover:text-foreground border border-transparent"
                }`}
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        {/* Secondary CTA */}
        <Link href="#gallery">
          <Button size="lg" variant="ghost" className="rounded-full text-lg px-8 py-6">
            갤러리 둘러보기
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </Link>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">100%</div>
            <div className="text-sm text-muted-foreground">오픈소스</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">AI</div>
            <div className="text-sm text-muted-foreground">프롬프트 기반</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">DIY</div>
            <div className="text-sm text-muted-foreground">누구나 가능</div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 rounded-full border-2 border-muted-foreground/30 flex items-start justify-center p-2">
          <div className="w-1 h-2 bg-muted-foreground/50 rounded-full" />
        </div>
      </div>
    </section>
  );
}
