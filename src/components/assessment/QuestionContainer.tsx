import { Card } from "@/components/ui/card";
import { Question } from "@/data/assessmentData";
import MultipleChoice from "./questions/MultipleChoice";
import SliderQuestion from "./questions/SliderQuestion";
import CodeEditor from "./questions/CodeEditor";
import DragDropRanking from "./questions/DragDropRanking";
import TextQuestion from "./questions/TextQuestion";
import { Lightbulb } from "lucide-react";

interface QuestionContainerProps {
  question: Question;
  answer: any;
  onAnswer: (answer: any, confidence?: string) => void;
  questionNumber: number;
  totalQuestions: number;
  language: "en" | "ar";
}

const QuestionContainer = ({
  question,
  answer,
  onAnswer,
  questionNumber,
  totalQuestions,
  language,
}: QuestionContainerProps) => {
  const renderQuestion = () => {
    switch (question.type) {
      case "multiple-choice":
        return (
          <MultipleChoice
            question={question}
            answer={answer}
            onAnswer={onAnswer}
            language={language}
          />
        );
      case "slider":
        return (
          <SliderQuestion
            question={question}
            answer={answer}
            onAnswer={onAnswer}
            language={language}
          />
        );
      case "code":
        return (
          <CodeEditor
            question={question}
            answer={answer}
            onAnswer={onAnswer}
            language={language}
          />
        );
      case "drag-drop":
        return (
          <DragDropRanking
            question={question}
            answer={answer}
            onAnswer={onAnswer}
            language={language}
          />
        );
      case "text":
        return (
          <TextQuestion
            question={question}
            answer={answer}
            onAnswer={onAnswer}
            language={language}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Card className="p-8 shadow-card">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-primary">
            {language === "en" ? "Question" : "سؤال"} {questionNumber} {language === "en" ? "of" : "من"}{" "}
            {totalQuestions}
          </span>
          <span className="text-xs text-muted-foreground uppercase tracking-wide">
            {question.type.replace("-", " ")}
          </span>
        </div>

        <h2 className="text-xl font-semibold mb-4">
          {language === "en" ? question.question : (question.questionAr || question.question)}
        </h2>

        {question.hint && (
          <div className="flex gap-2 p-3 bg-accent/10 rounded-lg mb-4">
            <Lightbulb size={18} className="text-accent flex-shrink-0 mt-0.5" />
            <p className="text-sm text-muted-foreground">
              {language === "en" ? question.hint : (question.hintAr || question.hint)}
            </p>
          </div>
        )}
      </div>

      {renderQuestion()}
    </Card>
  );
};

export default QuestionContainer;
