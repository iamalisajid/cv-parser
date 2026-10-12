import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PROFICIENCY_ORDER: Record<string, number> = {
  Beginner: 1,
  Intermediate: 2,
  Advanced: 3,
  Expert: 4,
};

export const PROFICIENCY_COLORS: Record<string, string> = {
  Expert: "bg-purple-100 text-purple-800 border-purple-300",
  Advanced: "bg-blue-100 text-blue-800 border-blue-300",
  Intermediate: "bg-green-100 text-green-800 border-green-300",
  Beginner: "bg-gray-100 text-gray-700 border-gray-300",
};
