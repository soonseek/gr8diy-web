import { Card, CardContent } from "@/components/ui/card";
import { MessageSquare, Bot, Cpu, Zap } from "lucide-react";

const steps = [
  {
    number: "01",
    title: "프롬프트 작성",
    description: "원하는 매매 전략을 자연어로 설명하세요. 복잡한 코딩 지식이 필요 없습니다.",
    icon: MessageSquare,
  },
  {
    number: "02",
    title: "AI 대화",
    description: "AI가 질문을 통해 알고리즘의 세부 사항을 파악하고 함께 완성해 나갑니다.",
    icon: Bot,
  },
  {
    number: "03",
    title: "알고리즘 생성",
    description: "대화가 완성되면 자동으로 실행 가능한 자동매매 알고리즘으로 변환됩니다.",
    icon: Cpu,
  },
  {
    number: "04",
    title: "자동 실행",
    description: "생성된 알고리즘은 설정된 주기마다 자동으로 실행되고 결과를 보고합니다.",
    icon: Zap,
  },
];

export function HowItWorks() {
  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold mb-4">
            어떻게 작동하나요?
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            4단계만으로 나만의 자동매매 알고리즘을 완성하세요.
            <br className="hidden md:block" />
            코딩 경험이 전혀 없어도 괜찮습니다.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative">
                {/* Connection Line (Desktop) */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-16 left-full w-full h-0.5 bg-gradient-to-r from-primary/50 to-transparent" />
                )}

                <Card className="bg-gradient-card border-border/50 h-full hover:border-primary/50 transition-colors">
                  <CardContent className="p-6">
                    {/* Step Number */}
                    <div className="text-6xl font-bold text-primary/20 mb-4">
                      {step.number}
                    </div>

                    {/* Icon */}
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>

                    {/* Title */}
                    <h3 className="text-xl font-semibold mb-3">{step.title}</h3>

                    {/* Description */}
                    <p className="text-muted-foreground text-sm leading-relaxed">
                      {step.description}
                    </p>
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-muted-foreground mb-6">
            지금 바로 시작하고 나만의 알고리즘을 만들어보세요
          </p>
        </div>
      </div>
    </section>
  );
}
