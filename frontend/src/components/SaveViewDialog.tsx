import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { createView } from "../api/client";

interface Props {
  open: boolean;
  onClose: () => void;
  viewType: "workers" | "query";
  filters: string;
}

export default function SaveViewDialog({
  open,
  onClose,
  viewType,
  filters,
}: Props) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      createView({ name, description, view_type: viewType, filters }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["views"] });
      setName("");
      setDescription("");
      onClose();
    },
    onError: (e: Error) => setError(e.message),
  });

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Save View</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2 mb-3">
            {error}
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Senior ML Engineers"
              className="w-full border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Description (optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Workers with Advanced+ ML skills and 5+ YOE"
              className="w-full border border-slate-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={() => mutation.mutate()}
            disabled={!name.trim() || mutation.isPending}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-40"
          >
            {mutation.isPending ? "Saving..." : "Save View"}
          </button>
        </div>
      </div>
    </div>
  );
}
