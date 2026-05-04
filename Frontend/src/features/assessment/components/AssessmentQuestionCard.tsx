import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ChoiceCard } from "@/shared/components/ChoiceCard";
import type { AssessmentQuestion } from "@/lib/api";

interface AssessmentQuestionCardProps {
  question: AssessmentQuestion;
  value?: string | number | string[];
  onChange: (value: string | number | string[]) => void;
}

export function AssessmentQuestionCard({
  question,
  value,
  onChange,
}: AssessmentQuestionCardProps) {
  const selectedValues = Array.isArray(value) ? value.map(String) : [];

  const toggleMultiSelectValue = (optionValue: string) => {
    const nextValues = new Set(selectedValues);
    if (nextValues.has(optionValue)) {
      nextValues.delete(optionValue);
    } else {
      nextValues.add(optionValue);
    }
    onChange(Array.from(nextValues));
  };

  return (
    <div className="atlas-panel p-6">
      <p className="type-kicker">{question.category}</p>
      <h2 className="mt-3 text-3xl font-bold">{question.question}</h2>
      {question.helper ? (
        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{question.helper}</p>
      ) : null}

      <div className="mt-6 space-y-4">
        {question.type === "multiple_choice" && question.options ? (
          <div className="grid gap-3 md:grid-cols-2">
            {question.options.map((option) => (
              <ChoiceCard
                key={option.id ?? option.value}
                onClick={() =>
                  question.interaction_mode === "multi_select"
                    ? toggleMultiSelectValue(option.value)
                    : onChange(option.value)
                }
                selected={
                  question.interaction_mode === "multi_select"
                    ? selectedValues.includes(option.value)
                    : value === option.value
                }
                title={option.label}
              />
            ))}
          </div>
        ) : null}

        {question.type === "scale" ? (
          <div className="grid gap-3 sm:grid-cols-5">
            {Array.from(
              { length: (question.max_value ?? 5) - (question.min_value ?? 1) + 1 },
              (_, index) => (question.min_value ?? 1) + index,
            ).map((scaleValue) => (
              <Button
                key={scaleValue}
                onClick={() => onChange(scaleValue)}
                type="button"
                variant={Number(value) === scaleValue ? "default" : "outline"}
              >
                {scaleValue}
              </Button>
            ))}
          </div>
        ) : null}

        {question.type === "text" ? (
          <Textarea
            className="min-h-[140px]"
            onChange={(event) => onChange(event.target.value)}
            placeholder="Write your answer here..."
            value={String(value ?? "")}
          />
        ) : null}
      </div>
    </div>
  );
}
