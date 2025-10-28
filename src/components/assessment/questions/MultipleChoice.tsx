import { Card } from "@/components/ui/card";
import { Question } from "@/data/assessmentData";
import { Check } from "lucide-react";

interface MultipleChoiceProps {
  question: Question;
  answer: any;
  onAnswer: (answer: any) => void;
  language: "en" | "ar";
}

const MultipleChoice = ({ question, answer, onAnswer, language }: MultipleChoiceProps) => {
  const options = language === "en" ? question.options : (question.optionsAr || question.options);

  return (
    <div className="space-y-3">
      {options?.map((option, index) => {
        const isSelected = answer === option;
        return (
          <Card
            key={index}
            className={`p-4 cursor-pointer transition-all hover:shadow-md ${
              isSelected
                ? "border-primary bg-primary/5 shadow-md"
                : "hover:border-primary/50"
            }`}
            onClick={() => onAnswer(option)}
          >
            <div className="flex items-center justify-between">
              <span className="text-base">{option}</span>
              {isSelected && (
                <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                  <Check size={16} className="text-primary-foreground" />
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
};

export default MultipleChoice;
