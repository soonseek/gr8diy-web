import { Header } from "@/components/home/header";
import { Hero } from "@/components/home/hero";
import { HowItWorks } from "@/components/home/how-it-works";
import { Gallery } from "@/components/home/gallery";
import { Github } from "lucide-react";

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <Header />
      <Hero />
      <HowItWorks />
      <Gallery />

      {/* Footer */}
      <footer className="border-t border-border/40 bg-secondary/20">
        <div className="container mx-auto px-4 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-emerald-500 flex items-center justify-center">
                  <span className="text-white font-bold text-lg">G</span>
                </div>
                <span className="font-bold text-xl">gr8diy</span>
              </div>
              <p className="text-muted-foreground max-w-md">
                누구나 프롬프트로 자동매매 알고리즘을 만들고 배포할 수 있는
                오픈소스 플랫폼
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-semibold mb-4">링크</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    홈
                  </a>
                </li>
                <li>
                  <a href="#gallery" className="hover:text-foreground transition-colors">
                    갤러리
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    문서
                  </a>
                </li>
              </ul>
            </div>

            {/* Community */}
            <div>
              <h4 className="font-semibold mb-4">커뮤니티</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <a
                    href="https://github.com/soonseek/gr8diy-web"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground transition-colors flex items-center gap-1"
                  >
                    <Github className="w-4 h-4" />
                    GitHub
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-foreground transition-colors">
                    Discord
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Copyright */}
          <div className="pt-8 border-t border-border/40 text-center text-sm text-muted-foreground">
            <p>&copy; {new Date().getFullYear()} gr8diy. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </main>
  );
}
