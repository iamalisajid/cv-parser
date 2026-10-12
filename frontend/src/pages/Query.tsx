import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, Search, Download, Bookmark } from "lucide-react";
import { fetchSkillNames, queryBySkills, type SkillCondition } from "../api/client";
import ExportDialog from "../components/ExportDialog";
import SaveViewDialog from "../components/SaveViewDialog";
import ViewSelector from "../components/ViewSelector";

const PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"];

export default function Query() {
  const navigate = useNavigate();
  const [conditions, setConditions] = useState<SkillCondition[]>([
    { skill_name: "", min_proficiency: "Intermediate" },
  ]);
  const [matchAll, setMatchAll] = useState(true);
  const [page, setPage] = useState(1);
  const [triggered, setTriggered] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const pageSize = 50;

  const currentFilters = () =>
    JSON.stringify({ conditions, match_all: matchAll });

  const loadFilters = (filtersJson: string) => {
    try {
      const f = JSON.parse(filtersJson);
      if (f.conditions) setConditions(f.conditions);
      if (f.match_all !== undefined) setMatchAll(f.match_all);
      setPage(1);
      setTriggered(true);
    } catch { /* ignore */ }
  };

  const { data: skillNames } = useQuery({
    queryKey: ["skill-names"],
    queryFn: fetchSkillNames,
  });

  const validConditions = conditions.filter((c) => c.skill_name.trim() !== "");

  const { data, isLoading } = useQuery({
    queryKey: ["skill-query", validConditions, matchAll, page],
    queryFn: () =>
      queryBySkills({
        conditions: validConditions,
        match_all: matchAll,
        page,
        page_size: pageSize,
      }),
    enabled: triggered && validConditions.length > 0,
  });

  const addCondition = () => {
    setConditions([...conditions, { skill_name: "", min_proficiency: "Intermediate" }]);
  };

  const removeCondition = (i: number) => {
    setConditions(conditions.filter((_, idx) => idx !== i));
  };

  const updateCondition = (i: number, field: keyof SkillCondition, value: string) => {
    const updated = [...conditions];
    updated[i] = { ...updated[i], [field]: value };
    setConditions(updated);
  };

  const runQuery = () => {
    setPage(1);
    setTriggered(true);
  };

  const resultIds = data?.items.map((w) => w.id);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Skill Query</h1>
        <div className="flex items-center gap-2">
          <ViewSelector viewType="query" onLoad={loadFilters} />
          <button
            onClick={() => setSaveOpen(true)}
            className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 transition-colors"
          >
            <Bookmark size={16} />
            Save Query
          </button>
          {data && data.items.length > 0 && (
            <button
              onClick={() => setExportOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800 transition-colors"
            >
              <Download size={16} />
              Export Results
            </button>
          )}
        </div>
      </div>

      {/* Query Builder */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-sm font-medium text-slate-700">Match:</span>
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="radio"
              checked={matchAll}
              onChange={() => setMatchAll(true)}
              className="accent-blue-600"
            />
            ALL conditions (AND)
          </label>
          <label className="flex items-center gap-1.5 text-sm">
            <input
              type="radio"
              checked={!matchAll}
              onChange={() => setMatchAll(false)}
              className="accent-blue-600"
            />
            ANY condition (OR)
          </label>
        </div>

        {conditions.map((cond, i) => (
          <div key={i} className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Skill name (e.g. Python)"
              value={cond.skill_name}
              onChange={(e) => updateCondition(i, "skill_name", e.target.value)}
              list="skill-suggestions"
              className="flex-1 border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={cond.min_proficiency}
              onChange={(e) => updateCondition(i, "min_proficiency", e.target.value)}
              className="border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PROFICIENCY_LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}+
                </option>
              ))}
            </select>
            {conditions.length > 1 && (
              <button
                onClick={() => removeCondition(i)}
                className="text-slate-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={18} />
              </button>
            )}
          </div>
        ))}

        <datalist id="skill-suggestions">
          {(skillNames ?? []).map((n) => (
            <option key={n} value={n} />
          ))}
        </datalist>

        <div className="flex items-center gap-3">
          <button
            onClick={addCondition}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
          >
            <Plus size={16} />
            Add condition
          </button>
          <div className="flex-1" />
          <button
            onClick={runQuery}
            disabled={validConditions.length === 0}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-40"
          >
            <Search size={16} />
            Search
          </button>
        </div>
      </div>

      {/* Results */}
      {triggered && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
            <span className="text-sm font-medium text-slate-700">
              {isLoading ? "Searching..." : `${data?.total ?? 0} workers found`}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-600">
                  <th className="px-4 py-3 text-left font-medium">Name</th>
                  <th className="px-4 py-3 text-left font-medium">Email</th>
                  <th className="px-4 py-3 text-left font-medium">Score</th>
                  <th className="px-4 py-3 text-left font-medium">YOE</th>
                  <th className="px-4 py-3 text-left font-medium">Education</th>
                  <th className="px-4 py-3 text-left font-medium">Skills</th>
                </tr>
              </thead>
              <tbody>
                {(data?.items ?? []).map((w) => (
                  <tr
                    key={w.id}
                    onClick={() => navigate(`/workers/${w.id}`)}
                    className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-slate-900">{w.name}</td>
                    <td className="px-4 py-3 text-slate-600">{w.email}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                        {w.overall_score ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{w.years_of_experience ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-600">{w.education_level}</td>
                    <td className="px-4 py-3 text-slate-600">{w.skill_count}</td>
                  </tr>
                ))}
                {!isLoading && (data?.items.length ?? 0) === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-slate-400">
                      No workers match these criteria
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        workerIds={resultIds}
      />
      <SaveViewDialog
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        viewType="query"
        filters={currentFilters()}
      />
    </div>
  );
}
