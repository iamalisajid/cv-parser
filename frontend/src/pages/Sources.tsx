import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Trash2,
  RefreshCw,
  ExternalLink,
  Clock,
  Users,
  X,
  Loader2,
} from "lucide-react";
import {
  fetchSources,
  createSource,
  deleteSource,
  fetchTabsFromUrl,
  ingestFromSource,
  fetchJob,
  type DataSource,
  type SheetTab,
  type IngestResponse,
} from "../api/client";

export default function Sources() {
  const [showAdd, setShowAdd] = useState(false);

  const { data: sources, isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: fetchSources,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
          <p className="text-sm text-slate-500 mt-1">
            Connect Google Sheets to ingest worker data
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800 transition-colors"
        >
          <Plus size={16} />
          Add Source
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-40 text-slate-400">
          Loading...
        </div>
      ) : !sources?.length ? (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center shadow-sm">
          <div className="mx-auto w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-4">
            <Plus size={24} className="text-slate-400" />
          </div>
          <h3 className="text-sm font-semibold text-slate-700 mb-1">
            No data sources configured
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            Add a Google Sheet to start ingesting worker data
          </p>
          <button
            onClick={() => setShowAdd(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
          >
            Add your first source
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sources.map((s) => (
            <SourceCard key={s.id} source={s} />
          ))}
        </div>
      )}

      {showAdd && <AddSourceDialog onClose={() => setShowAdd(false)} />}
    </div>
  );
}

function SourceCard({ source }: { source: DataSource }) {
  const qc = useQueryClient();
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  const deleteMut = useMutation({
    mutationFn: () => deleteSource(source.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg("");
    try {
      const res: IngestResponse = await ingestFromSource(source.id);
      setSyncMsg(res.message);
      if (res.job_id) {
        pollJob(res.job_id);
      }
    } catch {
      setSyncMsg("Sync failed");
      setSyncing(false);
    }
  };

  const pollJob = async (jobId: string) => {
    try {
      const job = await fetchJob(jobId);
      if (job.status === "running") {
        setSyncMsg(`Processing ${job.completed}/${job.total}...`);
        setTimeout(() => pollJob(jobId), 3000);
      } else {
        setSyncMsg(job.message);
        setSyncing(false);
        qc.invalidateQueries({ queryKey: ["sources"] });
      }
    } catch {
      setSyncing(false);
    }
  };

  const lastSync = source.last_synced_at
    ? new Date(source.last_synced_at).toLocaleString()
    : "Never";

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 truncate">
            {source.name}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5 truncate">
            {source.tab_name || `Tab GID: ${source.gid}`}
          </p>
        </div>
        <a
          href={source.sheet_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-400 hover:text-slate-600 shrink-0 ml-2"
        >
          <ExternalLink size={16} />
        </a>
      </div>

      <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
        <span className="flex items-center gap-1">
          <Clock size={12} />
          {lastSync}
        </span>
        <span className="flex items-center gap-1">
          <Users size={12} />
          {source.worker_count} workers
        </span>
      </div>

      {syncMsg && (
        <p className="text-xs text-slate-600 bg-slate-50 rounded px-2 py-1 mb-3">
          {syncMsg}
        </p>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={12} className={syncing ? "animate-spin" : ""} />
          {syncing ? "Syncing..." : "Sync"}
        </button>
        <button
          onClick={() => {
            if (confirm("Delete this data source?")) deleteMut.mutate();
          }}
          disabled={deleteMut.isPending}
          className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-md text-xs text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <Trash2 size={12} />
          Delete
        </button>
      </div>
    </div>
  );
}

function AddSourceDialog({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [step, setStep] = useState<"url" | "tabs">("url");
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [tabs, setTabs] = useState<SheetTab[]>([]);
  const [selectedTab, setSelectedTab] = useState<SheetTab | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFetchTabs = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await fetchTabsFromUrl(url);
      setTabs(result);
      if (result.length > 0) setSelectedTab(result[0]);
      setStep("tabs");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch tabs");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!name.trim() || !selectedTab) return;
    setLoading(true);
    setError("");
    try {
      await createSource({
        name,
        sheet_url: url,
        gid: selectedTab.gid,
        tab_name: selectedTab.title,
      });
      qc.invalidateQueries({ queryKey: ["sources"] });
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create source");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">Add Data Source</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">
            {error}
          </div>
        )}

        {step === "url" ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Google Sheets URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://docs.google.com/spreadsheets/d/..."
                className="w-full border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleFetchTabs}
              disabled={loading || !url.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-40"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              Fetch Worksheets
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Source Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Candidate spreadsheet"
                className="w-full border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Select Worksheet
              </label>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {tabs.map((tab) => (
                  <label
                    key={tab.gid}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md border cursor-pointer transition-colors ${
                      selectedTab?.gid === tab.gid
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="tab"
                      checked={selectedTab?.gid === tab.gid}
                      onChange={() => setSelectedTab(tab)}
                      className="accent-blue-600"
                    />
                    <div>
                      <span className="text-sm font-medium">{tab.title}</span>
                      <span className="text-xs text-slate-500 ml-2">
                        ~{tab.row_count} rows
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setStep("url")}
                className="px-4 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleCreate}
                disabled={loading || !name.trim() || !selectedTab}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-40"
              >
                {loading && <Loader2 size={16} className="animate-spin" />}
                Add Source
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
