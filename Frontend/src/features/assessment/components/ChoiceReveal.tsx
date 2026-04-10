interface ChoiceRevealProps {
  value?: string | number;
}

export function ChoiceReveal({ value }: ChoiceRevealProps) {
  if (value === undefined || value === "") {
    return null;
  }

  return (
    <div className="rounded-[1.25rem] border border-primary/20 bg-primary/5 p-4">
      <p className="type-kicker">Selected signal</p>
      <p className="mt-2 text-lg font-semibold">{String(value)}</p>
    </div>
  );
}
