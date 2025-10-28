import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Save, Clock, Pause, Play, Globe } from "lucide-react";

interface AssessmentHeaderProps {
  progress: number;
  elapsedTime: string;
  language: "en" | "ar";
  onLanguageToggle: () => void;
  onSaveExit: () => void;
  isPaused: boolean;
  onPauseToggle: () => void;
}

const AssessmentHeader = ({
  progress,
  elapsedTime,
  language,
  onLanguageToggle,
  onSaveExit,
  isPaused,
  onPauseToggle,
}: AssessmentHeaderProps) => {
  return (
    <div className="bg-card border-b border-border shadow-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-primary">
              {language === "en" ? "SkillPath AI" : "SkillPath AI"}
            </h1>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock size={16} />
              <span>{elapsedTime}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={onPauseToggle}
              className="gap-2"
            >
              {isPaused ? <Play size={16} /> : <Pause size={16} />}
              {language === "en" ? (isPaused ? "Resume" : "Pause") : (isPaused ? "استئناف" : "إيقاف مؤقت")}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={onLanguageToggle}
              className="gap-2"
            >
              <Globe size={16} />
              {language === "en" ? "العربية" : "English"}
            </Button>

            <Button variant="outline" size="sm" onClick={onSaveExit} className="gap-2">
              <Save size={16} />
              {language === "en" ? "Save & Exit" : "حفظ وخروج"}
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {language === "en" ? "Overall Progress" : "التقدم الإجمالي"}
            </span>
            <span className="font-semibold">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      </div>
    </div>
  );
};

export default AssessmentHeader;
