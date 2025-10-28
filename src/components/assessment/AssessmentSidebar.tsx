import { Card } from "@/components/ui/card";
import { CheckCircle, Clock, Lock } from "lucide-react";
import { Category } from "@/data/assessmentData";

interface AssessmentSidebarProps {
  categories: Category[];
  currentCategoryIndex: number;
  answers: Record<string, any>;
  onCategorySelect: (index: number) => void;
  language: "en" | "ar";
}

const AssessmentSidebar = ({
  categories,
  currentCategoryIndex,
  answers,
  onCategorySelect,
  language,
}: AssessmentSidebarProps) => {
  const getAnsweredCount = (category: Category) => {
    return category.questions.filter((q) => answers[q.id]).length;
  };

  const getStatusIcon = (category: Category, index: number) => {
    const answered = getAnsweredCount(category);
    const total = category.questions.length;

    if (category.status === "locked") {
      return <Lock size={20} className="text-muted-foreground" />;
    }
    if (answered === total) {
      return <CheckCircle size={20} className="text-secondary" />;
    }
    if (answered > 0) {
      return <div className="w-5 h-5 rounded-full bg-accent animate-pulse" />;
    }
    return <Clock size={20} className="text-muted-foreground" />;
  };

  return (
    <div className="w-80 bg-card border-r border-border overflow-y-auto">
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-4">
          {language === "en" ? "Assessment Categories" : "فئات التقييم"}
        </h2>

        <div className="space-y-3">
          {categories.map((category, index) => {
            const answeredCount = getAnsweredCount(category);
            const totalQuestions = category.questions.length;
            const progress = (answeredCount / totalQuestions) * 100;
            const isActive = index === currentCategoryIndex;
            const isLocked = category.status === "locked";

            return (
              <Card
                key={category.id}
                className={`p-4 cursor-pointer transition-all ${
                  isActive
                    ? "border-primary bg-primary/5 shadow-md"
                    : "hover:border-primary/50 hover:shadow-sm"
                } ${isLocked ? "opacity-50 cursor-not-allowed" : ""}`}
                onClick={() => !isLocked && onCategorySelect(index)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{category.icon}</span>
                    <div>
                      <h3 className="font-semibold text-sm">
                        {language === "en" ? category.name : category.nameAr}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {category.estimatedTime} {language === "en" ? "min" : "دقيقة"}
                      </p>
                    </div>
                  </div>
                  {getStatusIcon(category, index)}
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>
                      {answeredCount}/{totalQuestions}{" "}
                      {language === "en" ? "questions" : "أسئلة"}
                    </span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AssessmentSidebar;
