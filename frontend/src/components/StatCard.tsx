import { type ReactNode } from "react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
}

export default function StatCard({ title, value, subtitle, icon }: Props) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
    </div>
  );
}
