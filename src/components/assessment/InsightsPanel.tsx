import { Card } from "@/components/ui/card";
import { Trophy, Zap, Target, TrendingUp } from "lucide-react";

interface InsightsPanelProps {
  xp: number;
  streak: number;
  answeredCount: number;
  totalQuestions: number;
  currentCategory: string;
  language: "en" | "ar";
}

const InsightsPanel = ({
  xp,
  streak,
  answeredCount,
  totalQuestions,
  currentCategory,
  language,
}: InsightsPanelProps) => {
  const accuracy = answeredCount > 0 ? Math.round((answeredCount / totalQuestions) * 85) : 0;

  return (
    <div className="w-80 space-y-4">
      <Card className="p-6 bg-gradient-primary text-primary-foreground">
        <div className="text-center">
          <Trophy size={48} className="mx-auto mb-3 opacity-90" />
          <div className="text-4xl font-bold mb-2">{xp}</div>
          <p className="text-sm opacity-90">
            {language === "en" ? "Total XP" : "إجمالي النقاط"}
          </p>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
            <Zap className="text-accent" size={20} />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">
              {language === "en" ? "Current Streak" : "السلسلة الحالية"}
            </p>
            <p className="text-2xl font-bold">{streak}</p>
          </div>
        </div>

        {streak >= 3 && (
          <div className="p-3 bg-accent/10 rounded-lg">
            <p className="text-sm text-accent font-medium">
              🔥 {language === "en" ? "You're on fire!" : "أنت مشتعل!"}
            </p>
          </div>
        )}
      </Card>

      <Card className="p-6 space-y-4">
        <h3 className="font-semibold">
          {language === "en" ? "Quick Stats" : "إحصائيات سريعة"}
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target size={16} className="text-primary" />
              <span className="text-sm">
                {language === "en" ? "Progress" : "التقدم"}
              </span>
            </div>
            <span className="font-semibold">
              {answeredCount}/{totalQuestions}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-secondary" />
              <span className="text-sm">
                {language === "en" ? "Accuracy" : "الدقة"}
              </span>
            </div>
            <span className="font-semibold">{accuracy}%</span>
          </div>
        </div>
      </Card>

      <Card className="p-6 bg-secondary/5">
        <h3 className="font-semibold mb-3">
          {language === "en" ? "AI Insight" : "رؤية الذكاء الاصطناعي"}
        </h3>
        <p className="text-sm text-muted-foreground">
          {language === "en"
            ? `You're showing strong skills in ${currentCategory}. Keep up the great work!`
            : `تُظهر مهارات قوية في ${currentCategory}. استمر في العمل الرائع!`}
        </p>
      </Card>

      <Card className="p-6 bg-accent/5">
        <h3 className="font-semibold mb-2">
          💡 {language === "en" ? "Tip" : "نصيحة"}
        </h3>
        <p className="text-sm text-muted-foreground">
          {language === "en"
            ? "Take your time with each question. Quality over speed!"
            : "خذ وقتك مع كل سؤال. الجودة أهم من السرعة!"}
        </p>
      </Card>
    </div>
  );
};

export default InsightsPanel;
