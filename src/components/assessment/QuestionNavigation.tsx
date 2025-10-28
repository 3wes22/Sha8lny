import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, SkipForward } from "lucide-react";

interface QuestionNavigationProps {
  currentQuestionIndex: number;
  totalQuestionsInCategory: number;
  isFirstQuestion: boolean;
  isLastQuestion: boolean;
  hasAnswer: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onSkip: () => void;
  language: "en" | "ar";
}

const QuestionNavigation = ({
  currentQuestionIndex,
  totalQuestionsInCategory,
  isFirstQuestion,
  isLastQuestion,
  hasAnswer,
  onPrevious,
  onNext,
  onSkip,
  language,
}: QuestionNavigationProps) => {
  return (
    <div className="border-t border-border bg-card p-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={onPrevious}
            disabled={isFirstQuestion}
            className="gap-2"
          >
            <ChevronLeft size={16} />
            {language === "en" ? "Previous" : "السابق"}
          </Button>

          <div className="flex items-center gap-2">
            {Array.from({ length: totalQuestionsInCategory }).map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-all ${
                  index === currentQuestionIndex
                    ? "bg-primary w-8"
                    : index < currentQuestionIndex
                    ? "bg-secondary"
                    : "bg-muted"
                }`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onSkip} className="gap-2">
              <SkipForward size={16} />
              {language === "en" ? "Skip" : "تخطي"}
            </Button>

            <Button
              onClick={onNext}
              disabled={!hasAnswer}
              className="gap-2"
            >
              {isLastQuestion
                ? language === "en"
                  ? "Finish"
                  : "إنهاء"
                : language === "en"
                ? "Next"
                : "التالي"}
              <ChevronRight size={16} />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionNavigation;
