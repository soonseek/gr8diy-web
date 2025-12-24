"use client";

import { useState } from "react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, TrendingUp, TrendingDown, User } from "lucide-react";

type Category = "all" | "momentum" | "mean-reversion" | "arbitrage" | "ai-based";

const categories: { id: Category; name: string }[] = [
  { id: "all", name: "전체" },
  { id: "momentum", name: "모멘텀" },
  { id: "mean-reversion", name: "평균 회귀" },
  { id: "arbitrage", name: "차익 거래" },
  { id: "ai-based", name: "AI 기반" },
];

const mockAlgorithms = [
  {
    id: 1,
    name: "RSI 듀얼 모멘텀",
    description: "RSI 과매수/과매도 구간에서의 듀얼 모멘텀 전략",
    category: "momentum" as Category,
    author: "trader_master",
    return: 24.5,
    chartData: [0, 10, 15, 12, 20, 25, 22, 30],
  },
  {
    id: 2,
    name: "볼린저 밴드 리버설",
    description: "볼린저 밴드 이탈 시 평균 회귀 전략",
    category: "mean-reversion" as Category,
    author: "quant_dev",
    return: 18.2,
    chartData: [0, 5, 12, 10, 15, 12, 18, 20],
  },
  {
    id: 3,
    name: "삼각 차익 거래",
    description: "BTC/ETH/USDT 간 삼각 차익 기회 포착",
    category: "arbitrage" as Category,
    author: "arb_bot",
    return: 8.5,
    chartData: [0, 3, 5, 4, 7, 6, 8, 9],
  },
  {
    id: 4,
    name: "LSTM 예측 모델",
    description: "딥러닝 기반 가격 방향성 예측 및 매매",
    category: "ai-based" as Category,
    author: "ai_researcher",
    return: 32.1,
    chartData: [0, 8, 20, 18, 28, 25, 30, 35],
  },
  {
    id: 5,
    name: "MACD 골든크로스",
    description: "MACD 골든크로스/데드크로스 기반 추종 매매",
    category: "momentum" as Category,
    author: "swing_trader",
    return: 15.8,
    chartData: [0, 6, 10, 8, 14, 12, 16, 18],
  },
  {
    id: 6,
    name: "페어 트레이딩",
    description: "두 자산 간 스프레드 통계적 차익 거래",
    category: "arbitrage" as Category,
    author: "stats_arb",
    return: 12.3,
    chartData: [0, 4, 8, 7, 11, 10, 13, 14],
  },
];

function AlgorithmCard({ algorithm }: { algorithm: typeof mockAlgorithms[0] }) {
  return (
    <Card className="bg-gradient-card border-border/50 hover:border-primary/50 transition-all hover:scale-[1.02]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1">{algorithm.name}</h3>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {algorithm.description}
            </p>
          </div>
          <div
            className={`flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded ${
              algorithm.return >= 0
                ? "text-green-500 bg-green-500/10"
                : "text-red-500 bg-red-500/10"
            }`}
          >
            {algorithm.return >= 0 ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {algorithm.return > 0 ? "+" : ""}
            {algorithm.return}%
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        {/* Chart Preview */}
        <div className="h-20 flex items-end gap-1 mb-3">
          {algorithm.chartData.map((value, i) => (
            <div
              key={i}
              className="flex-1 bg-gradient-to-t from-primary/50 to-primary/20 rounded-sm transition-all hover:from-primary hover:to-primary/40"
              style={{ height: `${(value / Math.max(...algorithm.chartData)) * 100}%` }}
            />
          ))}
        </div>

        {/* Author */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <User className="w-4 h-4" />
          <span>@{algorithm.author}</span>
        </div>
      </CardContent>

      <CardFooter className="pt-3">
        <Button className="w-full gap-2" size="sm">
          <Play className="w-4 h-4" />
          바로 실행
        </Button>
      </CardFooter>
    </Card>
  );
}

export function Gallery() {
  const [activeCategory, setActiveCategory] = useState<Category>("all");

  const filteredAlgorithms =
    activeCategory === "all"
      ? mockAlgorithms
      : mockAlgorithms.filter((algo) => algo.category === activeCategory);

  return (
    <section id="gallery" className="py-24 relative">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-5xl font-bold mb-4">
            예제 알고리즘 갤러리
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            다른 사용자들이 만든 자동매매 알고리즘을 둘러보고
            <br className="hidden md:block" />
            바로 실행해보세요.
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap justify-center gap-2 mb-12">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                activeCategory === category.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              {category.name}
            </button>
          ))}
        </div>

        {/* Algorithms Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAlgorithms.map((algorithm) => (
            <AlgorithmCard key={algorithm.id} algorithm={algorithm} />
          ))}
        </div>

        {/* View More */}
        <div className="mt-12 text-center">
          <Button variant="outline" size="lg" className="rounded-full">
            더 많은 알고리즘 보기
          </Button>
        </div>
      </div>
    </section>
  );
}
