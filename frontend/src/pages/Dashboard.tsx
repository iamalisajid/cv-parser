import { useQuery } from "@tanstack/react-query";
import { Users, TrendingUp, Award, Clock } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { fetchStats } from "../api/client";
import StatCard from "../components/StatCard";

const COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#6366f1"];

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
    refetchInterval: 60_000,
  });

  if (isLoading || !stats) {
    return <div className="flex items-center justify-center h-64 text-slate-400">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Workers"
          value={stats.total_workers}
          subtitle={`${stats.completed_workers} completed`}
          icon={<Users size={22} />}
        />
        <StatCard
          title="Avg Score"
          value={stats.avg_overall_score?.toFixed(1) ?? "—"}
          subtitle="Overall score"
          icon={<TrendingUp size={22} />}
        />
        <StatCard
          title="Avg Domain Expertise"
          value={stats.avg_domain_expertise?.toFixed(1) ?? "—"}
          subtitle="Out of 10"
          icon={<Award size={22} />}
        />
        <StatCard
          title="Pending"
          value={stats.pending_workers}
          subtitle="Awaiting processing"
          icon={<Clock size={22} />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Distribution */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.score_distribution}>
              <XAxis dataKey="range" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Experience Brackets */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Experience Brackets</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.experience_brackets} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="bracket" type="category" tick={{ fontSize: 12 }} width={80} />
              <Tooltip />
              <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Education Breakdown */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Education Breakdown</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={stats.education_breakdown}
                dataKey="count"
                nameKey="level"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={({ name, value }) => `${name}: ${value}`}
              >
                {stats.education_breakdown.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Skills */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Top 20 Skills</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.top_skills.slice(0, 10)} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="skill" type="category" tick={{ fontSize: 11 }} width={120} />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Coverage */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Category Coverage</h3>
        <div className="flex flex-wrap gap-2">
          {stats.category_coverage.map((c) => (
            <span
              key={c.category}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700"
            >
              {c.category}
              <span className="bg-slate-300 text-slate-800 px-1.5 py-0.5 rounded-full text-[10px]">
                {c.workers}
              </span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
