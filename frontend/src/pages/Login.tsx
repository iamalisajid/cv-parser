import { GoogleLogin, type CredentialResponse } from "@react-oauth/google";
import { useAuth } from "../context/auth-context";
import { useState } from "react";

export default function Login() {
  const { login } = useAuth();
  const [error, setError] = useState("");
  const allowedDomain = import.meta.env.VITE_ALLOWED_EMAIL_DOMAIN;

  const handleSuccess = async (response: CredentialResponse) => {
    if (!response.credential) {
      setError("No credential received from Google");
      return;
    }
    try {
      await login(response.credential);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-slate-900 mb-4">
              <svg
                className="w-7 h-7 text-white"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
                />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-slate-900">CV Parser</h1>
            <p className="text-sm text-slate-500 mt-1">
              Sign in to access the Skill Analysis Platform
            </p>
          </div>

          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleSuccess}
              onError={() => setError("Google sign-in failed")}
              size="large"
              width="300"
              theme="outline"
              text="signin_with"
            />
          </div>

          {error && (
            <p className="mt-4 text-sm text-red-600 text-center bg-red-50 rounded-lg p-2">
              {error}
            </p>
          )}
        </div>

        {allowedDomain && (
          <p className="text-xs text-slate-400 text-center mt-6">
            Only @{allowedDomain} Google accounts can access this application.
          </p>
        )}
      </div>
    </div>
  );
}
