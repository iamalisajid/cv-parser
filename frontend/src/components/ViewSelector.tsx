import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, Trash2 } from "lucide-react";
import { fetchViews, deleteView } from "../api/client";

interface Props {
  viewType: "workers" | "query";
  onLoad: (filters: string) => void;
}

export default function ViewSelector({ viewType, onLoad }: Props) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: views } = useQuery({
    queryKey: ["views", viewType],
    queryFn: () => fetchViews(viewType),
  });

  const deleteMut = useMutation({
    mutationFn: deleteView,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["views"] }),
  });

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (!views?.length) return null;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50 transition-colors"
      >
        Saved Views
        <ChevronDown size={14} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-white rounded-lg border border-slate-200 shadow-lg z-40 py-1 max-h-64 overflow-y-auto">
          {views.map((v) => (
            <div
              key={v.id}
              className="flex items-center justify-between px-3 py-2 hover:bg-slate-50 group"
            >
              <button
                onClick={() => {
                  onLoad(v.filters);
                  setOpen(false);
                }}
                className="flex-1 text-left min-w-0"
              >
                <p className="text-sm font-medium text-slate-800 truncate">
                  {v.name}
                </p>
                {v.description && (
                  <p className="text-xs text-slate-500 truncate">
                    {v.description}
                  </p>
                )}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteMut.mutate(v.id);
                }}
                className="ml-2 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
