import { PROFICIENCY_COLORS } from "../lib/utils";

interface Props {
  name: string;
  proficiency: string;
  context?: string;
  compact?: boolean;
}

export default function SkillBadge({ name, proficiency, context, compact }: Props) {
  const colors = PROFICIENCY_COLORS[proficiency] ?? "bg-gray-100 text-gray-600";

  if (compact) {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors}`}>
        {name}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${colors}`}>
      <span>{name}</span>
      <span className="opacity-60">·</span>
      <span className="opacity-75">{proficiency}</span>
      {context && context !== "professional" && (
        <>
          <span className="opacity-60">·</span>
          <span className="opacity-50 italic">{context}</span>
        </>
      )}
    </span>
  );
}
