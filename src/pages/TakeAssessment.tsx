import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AssessmentHeader from "@/components/assessment/AssessmentHeader";
import AssessmentSidebar from "@/components/assessment/AssessmentSidebar";
import QuestionContainer from "@/components/assessment/QuestionContainer";
import InsightsPanel from "@/components/assessment/InsightsPanel";
import QuestionNavigation from "@/components/assessment/QuestionNavigation";
import CompletionScreen from "@/components/assessment/CompletionScreen";
import { assessmentData, Question } from "@/data/assessmentData";

const TakeAssessment = () => {
  const navigate = useNavigate();
  const [currentCategoryIndex, setCurrentCategoryIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [startTime] = useState(Date.now());
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [language, setLanguage] = useState<"en" | "ar">("en");
  const [xp, setXp] = useState(0);
  const [streak, setStreak] = useState(0);
  const [showAchievement, setShowAchievement] = useState(false);
  const [achievementText, setAchievementText] = useState("");

  const currentCategory = assessmentData.categories[currentCategoryIndex];
  const currentQuestion = currentCategory.questions[currentQuestionIndex];
  const totalQuestions = assessmentData.categories.reduce(
    (sum, cat) => sum + cat.questions.length,
    0
  );
  const answeredCount = Object.keys(answers).length;
  const overallProgress = (answeredCount / totalQuestions) * 100;

  // Timer effect
  useEffect(() => {
    if (isPaused || isCompleted) return;
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [isPaused, isCompleted, startTime]);

  // Auto-save effect
  useEffect(() => {
    if (Object.keys(answers).length === 0) return;
    const autoSave = setInterval(() => {
      // Simulate auto-save
      console.log("Auto-saved answers:", answers);
    }, 30000);
    return () => clearInterval(autoSave);
  }, [answers]);

  const handleAnswer = (questionId: string, answer: any, confidence?: string) => {
    const wasCorrect = currentQuestion.correctAnswer === answer;
    
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { answer, confidence, timestamp: Date.now() },
    }));

    // Update XP and streak
    if (wasCorrect) {
      const points = 10 + (streak * 2);
      setXp((prev) => prev + points);
      setStreak((prev) => prev + 1);

      // Check for achievements
      if (streak + 1 === 5) {
        showAchievementNotification("🔥 Hot Streak! 5 correct answers in a row!");
      } else if (streak + 1 === 10) {
        showAchievementNotification("🌟 Perfect 10! You're on fire!");
      }
    } else {
      setStreak(0);
    }
  };

  const showAchievementNotification = (text: string) => {
    setAchievementText(text);
    setShowAchievement(true);
    setTimeout(() => setShowAchievement(false), 3000);
  };

  const handleNext = () => {
    if (currentQuestionIndex < currentCategory.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else if (currentCategoryIndex < assessmentData.categories.length - 1) {
      // Show mini celebration for completing category
      showAchievementNotification(`✅ ${currentCategory.name} Complete! Moving to next section...`);
      setTimeout(() => {
        setCurrentCategoryIndex((prev) => prev + 1);
        setCurrentQuestionIndex(0);
      }, 1500);
    } else {
      // All questions completed
      setIsCompleted(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    } else if (currentCategoryIndex > 0) {
      setCurrentCategoryIndex((prev) => prev - 1);
      setCurrentQuestionIndex(
        assessmentData.categories[currentCategoryIndex - 1].questions.length - 1
      );
    }
  };

  const handleJumpToQuestion = (categoryIndex: number, questionIndex: number) => {
    setCurrentCategoryIndex(categoryIndex);
    setCurrentQuestionIndex(questionIndex);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (isCompleted) {
    return (
      <CompletionScreen
        xp={xp}
        answers={answers}
        totalQuestions={totalQuestions}
        elapsedTime={elapsedTime}
        onRestart={() => navigate("/assessments")}
      />
    );
  }

  return (
    <div className={`min-h-screen bg-background ${language === "ar" ? "rtl" : "ltr"}`}>
      <AssessmentHeader
        progress={overallProgress}
        elapsedTime={formatTime(elapsedTime)}
        language={language}
        onLanguageToggle={() => setLanguage(language === "en" ? "ar" : "en")}
        onSaveExit={() => navigate("/assessments")}
        isPaused={isPaused}
        onPauseToggle={() => setIsPaused(!isPaused)}
      />

      {/* Achievement Notification */}
      {showAchievement && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 animate-slide-in-top">
          <div className="bg-gradient-primary text-primary-foreground px-6 py-3 rounded-lg shadow-lg">
            <p className="font-semibold text-center">{achievementText}</p>
          </div>
        </div>
      )}

      <div className="flex h-[calc(100vh-64px)]">
        <AssessmentSidebar
          categories={assessmentData.categories}
          currentCategoryIndex={currentCategoryIndex}
          answers={answers}
          onCategorySelect={(index) => {
            setCurrentCategoryIndex(index);
            setCurrentQuestionIndex(0);
          }}
          language={language}
        />

        <div className="flex-1 flex flex-col overflow-hidden">
          {isPaused ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4 p-8">
                <div className="text-6xl mb-4">⏸️</div>
                <h2 className="text-2xl font-bold">Assessment Paused</h2>
                <p className="text-muted-foreground">Take a moment to breathe and relax</p>
                <button
                  onClick={() => setIsPaused(false)}
                  className="mt-4 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  Resume Assessment
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-6xl mx-auto flex gap-6">
                  <div className="flex-1">
                    <QuestionContainer
                      question={currentQuestion}
                      answer={answers[currentQuestion.id]?.answer}
                      onAnswer={(answer, confidence) =>
                        handleAnswer(currentQuestion.id, answer, confidence)
                      }
                      questionNumber={
                        assessmentData.categories
                          .slice(0, currentCategoryIndex)
                          .reduce((sum, cat) => sum + cat.questions.length, 0) +
                        currentQuestionIndex +
                        1
                      }
                      totalQuestions={totalQuestions}
                      language={language}
                    />
                  </div>

                  <InsightsPanel
                    xp={xp}
                    streak={streak}
                    answeredCount={answeredCount}
                    totalQuestions={totalQuestions}
                    currentCategory={currentCategory.name}
                    language={language}
                  />
                </div>
              </div>

              <QuestionNavigation
                currentQuestionIndex={currentQuestionIndex}
                totalQuestionsInCategory={currentCategory.questions.length}
                isFirstQuestion={currentCategoryIndex === 0 && currentQuestionIndex === 0}
                isLastQuestion={
                  currentCategoryIndex === assessmentData.categories.length - 1 &&
                  currentQuestionIndex === currentCategory.questions.length - 1
                }
                hasAnswer={!!answers[currentQuestion.id]}
                onPrevious={handlePrevious}
                onNext={handleNext}
                onSkip={() => {
                  handleAnswer(currentQuestion.id, null, "skipped");
                  handleNext();
                }}
                language={language}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TakeAssessment;
