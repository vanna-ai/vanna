import { TecknoworksChat } from "@/app/components/chat/TecknoworksChat";
import { AnimatedChartBackground } from "@/app/components/AnimatedChartBackground";
import { BarChart3, TrendingUp, Zap, Database } from "lucide-react";
import { Badge } from "@/app/components/ui/badge";

export default function App() {
  return (
    <div className="dark min-h-screen bg-background text-foreground relative overflow-hidden">
      {/* Animated Background Chart */}
      <AnimatedChartBackground />
      
      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-border/50 bg-background/80 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 md:px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="size-10 rounded-xl bg-chart-1 flex items-center justify-center">
                <BarChart3 className="size-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg">Urban Eats AI</h1>
                <p className="text-xs text-muted-foreground">Restaurant Analytics Platform</p>
              </div>
            </div>
            <Badge variant="outline" className="border-chart-1/50 text-chart-1">
              <div className="size-2 rounded-full bg-chart-1 animate-pulse mr-2" />
              Live Demo
            </Badge>
          </div>
        </header>

        {/* Main Section */}
        <main className="flex-1 flex items-center justify-center p-4 md:p-6 lg:p-8">
          <div className="max-w-7xl w-full grid lg:grid-cols-[1fr,650px] gap-8 lg:gap-12 items-start lg:items-center">
            {/* Left Side - Info */}
            <div className="space-y-6 animate-in fade-in slide-in-from-left duration-700 order-2 lg:order-1">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-chart-1/10 border border-chart-1/20">
                  <Zap className="size-4 text-chart-1" />
                  <span className="text-sm text-chart-1">Powered by Tecknoworks AI</span>
                </div>
                <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
                  Ask. Analyze.
                  <br />
                  <span className="text-chart-1">Act.</span>
                </h2>
                <p className="text-lg text-muted-foreground max-w-xl">
                  Transform your restaurant data into actionable insights through natural conversation. No SQL required.
                </p>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 pt-6">
                <div className="p-4 rounded-xl bg-card/30 border border-border/50 backdrop-blur-sm">
                  <div className="text-3xl font-bold text-chart-1">25</div>
                  <div className="text-sm text-muted-foreground mt-1">Locations</div>
                </div>
                <div className="p-4 rounded-xl bg-card/30 border border-border/50 backdrop-blur-sm">
                  <div className="text-3xl font-bold text-chart-1">293K+</div>
                  <div className="text-sm text-muted-foreground mt-1">Orders</div>
                </div>
                <div className="p-4 rounded-xl bg-card/30 border border-border/50 backdrop-blur-sm">
                  <div className="text-3xl font-bold text-chart-1">$16.4M</div>
                  <div className="text-sm text-muted-foreground mt-1">Revenue</div>
                </div>
                <div className="p-4 rounded-xl bg-card/30 border border-border/50 backdrop-blur-sm">
                  <div className="text-3xl font-bold text-chart-1">2,000</div>
                  <div className="text-sm text-muted-foreground mt-1">Customers</div>
                </div>
              </div>

              {/* Data Presentation Tips - Removed as per request */}
            </div>

            {/* Right Side - Chat (The Star) */}
            <div className="animate-in fade-in slide-in-from-right duration-700 delay-150 order-1 lg:order-2">
              <div className="relative">
                {/* Glow effect */}
                <div className="absolute -inset-2 bg-gradient-to-r from-chart-1/20 via-chart-2/20 to-chart-3/20 rounded-3xl blur-2xl opacity-75 animate-pulse" style={{ animationDuration: '3s' }} />
                {/* Spotlight effect */}
                <div className="absolute -inset-4 bg-gradient-to-br from-chart-1/5 to-transparent rounded-3xl blur-3xl" />
                <div className="relative">
                  <TecknoworksChat isEmbedded={true} />
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-border/50 bg-background/80 backdrop-blur-sm py-4">
          <div className="max-w-7xl mx-auto px-4 md:px-6 text-center text-sm text-muted-foreground">
            <p>Demo for Urban Eats Restaurant Chain • Powered by Tecknoworks AI • January 2026</p>
          </div>
        </footer>
      </div>
    </div>
  );
}