import { Textarea } from "@/components/ui/textarea";
import { Question } from "@/data/assessmentData";
import { useState, useEffect } from "react";

interface TextQuestionProps {
  question: Question;
  answer: any;
  onAnswer: (answer: any) => void;
  language: "en" | "ar";
}

const TextQuestion = ({ question, answer, onAnswer, language }: TextQuestionProps) => {
  const [text, setText] = useState(answer || "");
  const minLength = 50;
  const maxLength = 500;

  useEffect(() => {
    if (answer) {
      setText(answer);
    }
  }, [answer]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setText(newText);
    if (newText.length >= minLength) {
      onAnswer(newText);
    }
  };

  return (
    <div className="space-y-4">
      <Textarea
        value={text}
        onChange={handleChange}
        placeholder={
          language === "en"
            ? "Type your answer here..."
            : "اكتب إجابتك هنا..."
        }
        className="min-h-[200px] text-base"
        maxLength={maxLength}
      />

      <div className="flex justify-between text-sm text-muted-foreground">
        <span>
          {language === "en"
            ? `Minimum ${minLength} characters`
            : `الحد الأدنى ${minLength} حرفًا`}
        </span>
        <span
          className={text.length >= minLength ? "text-secondary" : "text-muted-foreground"}
        >
          {text.length}/{maxLength}
        </span>
      </div>

      {text.length > 0 && text.length < minLength && (
        <p className="text-sm text-amber-600">
          {language === "en"
            ? `Please write at least ${minLength - text.length} more characters`
            : `يرجى كتابة ${minLength - text.length} حرفًا على الأقل`}
        </p>
      )}
    </div>
  );
};

export default TextQuestion;
