import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, MapPin, GraduationCap, Briefcase } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { fetchWorker, fetchWorkerSkills, fetchWorkerDomainScores, fetchWorkerSubdomainScores } from "../api/client";
import type { SubdomainScore } from "../api/client";
import SkillBadge from "../components/SkillBadge";

export default function WorkerDetail() {
  const { id } = useParams<{ id: string }>();
  const workerId = Number(id);

  const { data: worker, isLoading: wLoading } = useQuery({
    queryKey: ["worker", workerId],
    queryFn: () => fetchWorker(workerId),
    enabled: !!workerId,
  });

  const { data: skillsData, isLoading: sLoading } = useQuery({
    queryKey: ["worker-skills", workerId],
    queryFn: () => fetchWorkerSkills(workerId),
    enabled: !!workerId,
  });

  const { data: domainScores } = useQuery({
    queryKey: ["worker-domain-scores", workerId],
    queryFn: () => fetchWorkerDomainScores(workerId),
    enabled: !!workerId,
  });

  const { data: subdomainScores } = useQuery({
    queryKey: ["worker-subdomain-scores", workerId],
    queryFn: () => fetchWorkerSubdomainScores(workerId),
    enabled: !!workerId,
  });

  if (wLoading || sLoading) {
    return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  }

  if (!worker) {
    return <div className="text-center py-12 text-slate-500">Worker not found</div>;
  }

  const skills = skillsData?.skills_by_category ?? {};
  const domainChartData = (domainScores ?? [])
    .filter((d) => d.score > 0)
    .map((d) => ({ domain: d.domain, score: d.score }));

  const tierOrder = ["Core ML Process", "ML Techniques", "Specialized Domains", "MLOps"];
  const tierColors: Record<string, string> = {
    "Core ML Process": "#3b82f6",
    "ML Techniques": "#8b5cf6",
    "Specialized Domains": "#06b6d4",
    "MLOps": "#f59e0b",
  };

  const subdomainsByTier = tierOrder
    .map((tier) => {
      const items = (subdomainScores ?? [])
        .filter((s: SubdomainScore) => s.tier === tier && s.score > 0)
        .sort((a: SubdomainScore, b: SubdomainScore) => b.score - a.score);
      return { tier, items, color: tierColors[tier] ?? "#6b7280" };
    })
    .filter((g) => g.items.length > 0);

  return (
    <div className="space-y-6">
      <Link
        to="/workers"
        className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft size={16} />
        Back to workers
      </Link>

      {/* Header */}
      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{worker.name}</h1>
            <p className="text-sm text-slate-500 mt-0.5">{worker.email}</p>
            <div className="flex flex-wrap gap-4 mt-3 text-sm text-slate-600">
              {worker.location && (
                <span className="flex items-center gap-1">
                  <MapPin size={14} className="text-slate-400" />
                  {worker.location}
                </span>
              )}
              {worker.education_level && (
                <span className="flex items-center gap-1">
                  <GraduationCap size={14} className="text-slate-400" />
                  {worker.education_level}
                  {worker.education_field ? ` in ${worker.education_field}` : ""}
                </span>
              )}
              {worker.years_of_experience != null && (
                <span className="flex items-center gap-1">
                  <Briefcase size={14} className="text-slate-400" />
                  {worker.years_of_experience} years
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-3 shrink-0">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{worker.overall_score ?? "—"}</p>
              <p className="text-[10px] uppercase tracking-wider text-slate-500">Score</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-purple-600">
                {worker.domain_expertise_rating ?? "—"}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-slate-500">Domain</p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary & Reasoning */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {worker.summary && (
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Summary</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{worker.summary}</p>
          </div>
        )}
        {worker.reasoning && (
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Reasoning</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{worker.reasoning}</p>
          </div>
        )}
      </div>

      {/* Domain Scores */}
      {domainChartData.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">
            Domain Scores
          </h3>
          <ResponsiveContainer width="100%" height={Math.max(180, domainChartData.length * 32)}>
            <BarChart data={domainChartData} layout="vertical">
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
              <YAxis
                dataKey="domain"
                type="category"
                tick={{ fontSize: 12 }}
                width={140}
              />
              <Tooltip
                formatter={(value) => [`${value}/100`, "Score"]}
              />
              <Bar dataKey="score" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Subdomain Expertise */}
      {subdomainsByTier.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-6">
          <h3 className="text-sm font-semibold text-slate-700">
            Subdomain Expertise
          </h3>
          {subdomainsByTier.map(({ tier, items, color }) => (
            <div key={tier}>
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                  {tier}
                </span>
              </div>
              <ResponsiveContainer
                width="100%"
                height={Math.max(80, items.length * 32)}
              >
                <BarChart data={items} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <YAxis
                    dataKey="subdomain"
                    type="category"
                    tick={{ fontSize: 11 }}
                    width={200}
                  />
                  <Tooltip
                    formatter={(value) => [`${value}/100`, "Score"]}
                  />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {items.map((entry: SubdomainScore) => (
                      <Cell key={entry.subdomain} fill={color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ))}
        </div>
      )}

      {/* Skills by Category */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Skills</h2>
        {Object.keys(skills).length === 0 ? (
          <p className="text-sm text-slate-400">No skills extracted yet.</p>
        ) : (
          Object.entries(skills)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([category, items]) => (
              <div
                key={category}
                className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm"
              >
                <h3 className="text-sm font-semibold text-slate-700 mb-3">{category}</h3>
                <div className="flex flex-wrap gap-2">
                  {items
                    .sort((a, b) => {
                      const ord: Record<string, number> = {
                        Expert: 4,
                        Advanced: 3,
                        Intermediate: 2,
                        Beginner: 1,
                      };
                      return (ord[b.proficiency] ?? 0) - (ord[a.proficiency] ?? 0);
                    })
                    .map((s) => (
                      <SkillBadge
                        key={s.skill_name}
                        name={s.skill_name}
                        proficiency={s.proficiency}
                        context={s.context}
                      />
                    ))}
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
