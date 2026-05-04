import type { AssessmentQuestion } from "@/lib/api";

interface ChoiceRevealProps {
  question?: AssessmentQuestion;
  value?: string | number | string[];
}

export function ChoiceReveal({ question, value }: ChoiceRevealProps) {
  if (
    value === undefined ||
    value === "" ||
    (Array.isArray(value) && value.length === 0)
  ) {
    return null;
  }

  let displayValue = Array.isArray(value) ? value.join(", ") : String(value);
  if (question?.type === "multiple_choice" && question.options) {
    if (Array.isArray(value)) {
      const selectedLabels = question.options
        .filter((option) => value.includes(option.value))
        .map((option) => option.label);
      if (selectedLabels.length > 0) {
        displayValue = selectedLabels.join(", ");
      }
    } else if (typeof value === "string") {
      const selectedOption = question.options.find((option) => option.value === value);
      if (selectedOption?.label) {
        displayValue = selectedOption.label;
      }
    }
  }

  return (
    <div className="rounded-[1.25rem] border border-primary/20 bg-primary/5 p-4">
      <p className="type-kicker">{Array.isArray(value) ? "Selected signals" : "Selected signal"}</p>
      <p className="mt-2 text-lg font-semibold">{displayValue}</p>
    </div>
  );
}
