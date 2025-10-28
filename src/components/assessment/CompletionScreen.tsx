import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Trophy, Clock, CheckCircle, Download, Share2 } from "lucide-react";
import { useEffect, useState } from "react";

interface CompletionScreenProps {
  xp: number;
  answers: Record<string, any>;
  totalQuestions: number;
  elapsedTime: number;
  onRestart: () => void;
}

const CompletionScreen = ({
  xp,
  answers,
  totalQuestions,
  elapsedTime,
  onRestart,
}: CompletionScreenProps) => {
  const [showCelebration, setShowCelebration] = useState(true);
  const answeredCount = Object.keys(answers).length;
  const score = Math.round((answeredCount / totalQuestions) * 100);

  useEffect(() => {
    const timer = setTimeout(() => setShowCelebration(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4">
      {showCelebration && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
          <div className="text-9xl animate-scale-in">🎉</div>
        </div>
      )}

      <Card className="max-w-2xl w-full p-8 shadow-lg">
        <div className="text-center space-y-6">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-primary rounded-full mb-4">
            <Trophy size={40} className="text-primary-foreground" />
          </div>

          <div>
            <h1 className="text-4xl font-bold mb-2">Assessment Complete!</h1>
            <p className="text-muted-foreground">
              Congratulations on completing the SkillPath AI assessment
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4 py-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary mb-1">{xp}</div>
              <p className="text-sm text-muted-foreground">Total XP</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-secondary mb-1">{score}%</div>
              <p className="text-sm text-muted-foreground">Score</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-accent mb-1">
                {formatTime(elapsedTime)}
              </div>
              <p className="text-sm text-muted-foreground">Time</p>
            </div>
          </div>

          <Card className="p-6 bg-gradient-primary text-primary-foreground">
            <h3 className="font-semibold mb-3">Your Results</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span>Questions Answered</span>
                <span className="font-bold">{answeredCount}/{totalQuestions}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Completion Rate</span>
                <span className="font-bold">{Math.round((answeredCount/totalQuestions)*100)}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Performance Level</span>
                <span className="font-bold">
                  {score >= 90 ? "Outstanding" : score >= 75 ? "Excellent" : score >= 60 ? "Good" : "Needs Improvement"}
                </span>
              </div>
            </div>
          </Card>

          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 bg-secondary/10 rounded-lg text-left">
              <CheckCircle className="text-secondary flex-shrink-0 mt-1" size={20} />
              <div>
                <h4 className="font-semibold mb-1">Next Steps</h4>
                <p className="text-sm text-muted-foreground">
                  Your personalized learning path is being generated based on your assessment results. 
                  Check your dashboard to see recommended courses and job matches.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Button variant="outline" className="gap-2">
                <Download size={16} />
                Download Certificate
              </Button>
              <Button variant="outline" className="gap-2">
                <Share2 size={16} />
                Share Results
              </Button>
            </div>

            <Button onClick={onRestart} className="w-full" size="lg">
              Go to Dashboard
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CompletionScreen;
