import { Slider } from "@/components/ui/slider";
import { Question } from "@/data/assessmentData";
import { useState, useEffect } from "react";

interface SliderQuestionProps {
  question: Question;
  answer: any;
  onAnswer: (answer: any) => void;
  language: "en" | "ar";
}

const SliderQuestion = ({ question, answer, onAnswer, language }: SliderQuestionProps) => {
  const [value, setValue] = useState<number[]>([answer || question.min || 1]);
  const labels = language === "en" ? question.labels : (question.labelsAr || question.labels);

  useEffect(() => {
    if (answer) {
      setValue([answer]);
    }
  }, [answer]);

  const handleChange = (newValue: number[]) => {
    setValue(newValue);
    onAnswer(newValue[0]);
  };

  return (
    <div className="space-y-6 py-6">
      <div className="px-4">
        <Slider
          value={value}
          onValueChange={handleChange}
          min={question.min || 1}
          max={question.max || 10}
          step={1}
          className="w-full"
        />
      </div>

      <div className="flex justify-between items-center px-2">
        {labels && Object.entries(labels).map(([key, label]) => (
          <div key={key} className="text-center">
            <div className="text-2xl font-bold text-primary mb-1">{key}</div>
            <div className="text-xs text-muted-foreground">{label}</div>
          </div>
        ))}
      </div>

      <div className="text-center p-4 bg-primary/5 rounded-lg">
        <p className="text-sm text-muted-foreground mb-1">
          {language === "en" ? "Your Selection" : "اختيارك"}
        </p>
        <p className="text-4xl font-bold text-primary">{value[0]}</p>
      </div>
    </div>
  );
};

export default SliderQuestion;
