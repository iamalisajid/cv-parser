import { useState } from "react";
import { Download, FileJson, Sheet, X } from "lucide-react";
import { getExportCsvUrl, getExportJsonUrl, exportToSheets } from "../api/client";

interface Props {
  open: boolean;
  onClose: () => void;
  workerIds?: number[];
}

export default function ExportDialog({ open, onClose, workerIds }: Props) {
  const [sheetsMsg, setSheetsMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [sheetUrl, setSheetUrl] = useState("");
  const [showUrlInput, setShowUrlInput] = useState(false);

  if (!open) return null;

  const handleSheets = async () => {
    setLoading(true);
    setSheetsMsg("");
    try {
      const res = await exportToSheets(
        sheetUrl.trim() || undefined,
        workerIds,
      );
      setSheetsMsg(res.message);
    } catch {
      setSheetsMsg("Export failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Export Results</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>
        <div className="space-y-3">
          <a
            href={getExportCsvUrl(workerIds)}
            download
            className="flex items-center gap-3 w-full px-4 py-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <Download size={20} className="text-green-600" />
            <div>
              <p className="text-sm font-medium">Download CSV</p>
              <p className="text-xs text-slate-500">Wide-format skill matrix</p>
            </div>
          </a>
          <a
            href={getExportJsonUrl(workerIds)}
            download
            className="flex items-center gap-3 w-full px-4 py-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <FileJson size={20} className="text-blue-600" />
            <div>
              <p className="text-sm font-medium">Download JSON</p>
              <p className="text-xs text-slate-500">Structured with grouped skills</p>
            </div>
          </a>
          <div className="rounded-lg border border-slate-200 overflow-hidden">
            <button
              onClick={() => {
                if (!showUrlInput) {
                  setShowUrlInput(true);
                } else {
                  handleSheets();
                }
              }}
              disabled={loading}
              className="flex items-center gap-3 w-full px-4 py-3 hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              <Sheet size={20} className="text-emerald-600" />
              <div className="text-left">
                <p className="text-sm font-medium">Export to Google Sheets</p>
                <p className="text-xs text-slate-500">
                  {sheetsMsg || (showUrlInput ? "Click to export" : "Push to a Google Sheet")}
                </p>
              </div>
            </button>
            {showUrlInput && (
              <div className="px-4 pb-3 space-y-2">
                <input
                  type="url"
                  value={sheetUrl}
                  onChange={(e) => setSheetUrl(e.target.value)}
                  placeholder="Paste target Sheet URL (leave empty for default)"
                  className="w-full border border-slate-200 rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSheets}
                  disabled={loading}
                  className="w-full px-3 py-1.5 bg-emerald-600 text-white rounded-md text-xs font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
                >
                  {loading ? "Exporting..." : "Export"}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
