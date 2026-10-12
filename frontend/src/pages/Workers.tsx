import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Download, Search, ChevronLeft, ChevronRight, Bookmark } from "lucide-react";
import { fetchWorkers, fetchDomains, fetchSubdomains } from "../api/client";
import ExportDialog from "../components/ExportDialog";
import SaveViewDialog from "../components/SaveViewDialog";
import ViewSelector from "../components/ViewSelector";

export default function Workers() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [minScore, setMinScore] = useState(searchParams.get("min_score") || "");
  const [maxScore] = useState("");
  const [minYoe, setMinYoe] = useState(searchParams.get("min_yoe") || "");
  const [education] = useState("");
  const [skillName, setSkillName] = useState(searchParams.get("skill_name") || "");
  const [minProf, setMinProf] = useState(searchParams.get("min_proficiency") || "");
  const [domain, setDomain] = useState(searchParams.get("domain") || "");
  const [subdomain, setSubdomain] = useState(searchParams.get("subdomain") || "");
  const [sortBy, setSortBy] = useState(searchParams.get("sort_by") || "overall_score");
  const [sortDir, setSortDir] = useState(searchParams.get("sort_dir") || "desc");
  const [exportOpen, setExportOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const pageSize = 25;

  const { data: domains } = useQuery({
    queryKey: ["domains"],
    queryFn: fetchDomains,
  });

  const { data: subdomainList } = useQuery({
    queryKey: ["subdomains"],
    queryFn: fetchSubdomains,
  });

  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
    search,
    sort_by: sortBy,
    sort_dir: sortDir,
  };
  if (minScore) params.min_score = minScore;
  if (maxScore) params.max_score = maxScore;
  if (minYoe) params.min_yoe = minYoe;
  if (education) params.education_level = education;
  if (skillName) params.skill_name = skillName;
  if (minProf) params.min_proficiency = minProf;
  if (domain) params.domain = domain;
  if (subdomain) params.subdomain = subdomain;

  const { data, isLoading } = useQuery({
    queryKey: ["workers", params],
    queryFn: () => fetchWorkers(params),
    refetchInterval: 60_000,
  });

  const currentFilters = () =>
    JSON.stringify({
      search, min_score: minScore, min_yoe: minYoe, skill_name: skillName,
      min_proficiency: minProf, domain, subdomain, sort_by: sortBy, sort_dir: sortDir,
    });

  const loadFilters = (filtersJson: string) => {
    try {
      const f = JSON.parse(filtersJson);
      setSearch(f.search || "");
      setMinScore(f.min_score || "");
      setMinYoe(f.min_yoe || "");
      setSkillName(f.skill_name || "");
      setMinProf(f.min_proficiency || "");
      setDomain(f.domain || "");
      setSubdomain(f.subdomain || "");
      setSortBy(f.sort_by || "overall_score");
      setSortDir(f.sort_dir || "desc");
      setPage(1);
    } catch { /* ignore bad json */ }
  };

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortDir("desc");
    }
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortBy !== col) return null;
    return <span className="ml-1 text-[10px]">{sortDir === "asc" ? "▲" : "▼"}</span>;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Workers</h1>
        <div className="flex items-center gap-2">
          <ViewSelector viewType="workers" onLoad={loadFilters} />
          <button
            onClick={() => setSaveOpen(true)}
            className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 transition-colors"
          >
            <Bookmark size={16} />
            Save View
          </button>
          <button
            onClick={() => setExportOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800 transition-colors"
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <div className="col-span-2 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search name or email..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <input
            type="number"
            placeholder="Min Score"
            value={minScore}
            onChange={(e) => { setMinScore(e.target.value); setPage(1); }}
            className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="number"
            placeholder="Min YOE"
            value={minYoe}
            onChange={(e) => { setMinYoe(e.target.value); setPage(1); }}
            className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            placeholder="Skill name"
            value={skillName}
            onChange={(e) => { setSkillName(e.target.value); setPage(1); }}
            className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={minProf}
            onChange={(e) => { setMinProf(e.target.value); setPage(1); }}
            className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Min Proficiency</option>
            <option value="Beginner">Beginner+</option>
            <option value="Intermediate">Intermediate+</option>
            <option value="Advanced">Advanced+</option>
            <option value="Expert">Expert</option>
          </select>
          <select
            value={domain}
            onChange={(e) => { setDomain(e.target.value); setPage(1); }}
            className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Domain Score</option>
            {(domains ?? []).map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <select
            value={subdomain}
            onChange={(e) => { setSubdomain(e.target.value); setPage(1); }}
            className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Subdomain</option>
            {(subdomainList ?? []).map((s) => (
              <option key={s.subdomain} value={s.subdomain}>{s.subdomain}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                {[
                  { key: "name", label: "Name" },
                  { key: "email", label: "Email" },
                  { key: "location", label: "Location" },
                  { key: "education_level", label: "Education" },
                  { key: "years_of_experience", label: "YOE" },
                  { key: "overall_score", label: "Score" },
                  { key: "domain_expertise_rating", label: "Domain" },
                  ...(domain ? [{ key: "domain_score", label: `${domain} Score` }] : []),
                  ...(subdomain ? [{ key: "subdomain_score", label: `${subdomain}` }] : []),
                  { key: "skill_count", label: "Skills" },
                ].map(({ key, label }) => (
                  <th
                    key={key}
                    onClick={() => handleSort(key)}
                    className="px-4 py-3 text-left font-medium cursor-pointer hover:text-slate-900 select-none"
                  >
                    {label}
                    <SortIcon col={key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={8 + (domain ? 1 : 0) + (subdomain ? 1 : 0)} className="text-center py-8 text-slate-400">
                    Loading...
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={8 + (domain ? 1 : 0) + (subdomain ? 1 : 0)} className="text-center py-8 text-slate-400">
                    No workers found
                  </td>
                </tr>
              ) : (
                data?.items.map((w) => (
                  <tr
                    key={w.id}
                    onClick={() => navigate(`/workers/${w.id}`)}
                    className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-slate-900">{w.name}</td>
                    <td className="px-4 py-3 text-slate-600">{w.email}</td>
                    <td className="px-4 py-3 text-slate-600">{w.location}</td>
                    <td className="px-4 py-3 text-slate-600">{w.education_level}</td>
                    <td className="px-4 py-3 text-slate-600">{w.years_of_experience ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                        {w.overall_score ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{w.domain_expertise_rating ?? "—"}</td>
                    {domain && (
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800">
                          {w.domain_score ?? "—"}
                        </span>
                      </td>
                    )}
                    {subdomain && (
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-cyan-100 text-cyan-800">
                          {w.subdomain_score ?? "—"}
                        </span>
                      </td>
                    )}
                    <td className="px-4 py-3 text-slate-600">{w.skill_count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50">
            <span className="text-xs text-slate-500">
              Showing {((page - 1) * pageSize) + 1}–{Math.min(page * pageSize, data?.total ?? 0)} of {data?.total}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1 rounded hover:bg-slate-200 disabled:opacity-30"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-xs text-slate-600 px-2">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1 rounded hover:bg-slate-200 disabled:opacity-30"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} />
      <SaveViewDialog
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        viewType="workers"
        filters={currentFilters()}
      />
    </div>
  );
}
