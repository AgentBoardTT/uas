"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bot,
  Key,
  Loader2,
  Play,
  Settings,
  Sparkles,
  List,
} from "lucide-react";
import { ConfigInfo, healthCheck, launchAgent, listConfigs } from "@/lib/api-client";
import { useAppStore } from "@/lib/store";

export default function Dashboard() {
  const router = useRouter();
  const { apiKey, setApiKey } = useAppStore();
  const [configs, setConfigs] = useState<ConfigInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">(
    "checking"
  );

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      // Check API health
      await healthCheck();
      setApiStatus("online");

      // Load configs
      const configList = await listConfigs();
      setConfigs(configList);
    } catch (e) {
      setApiStatus("offline");
      setError("Failed to connect to API server");
    } finally {
      setLoading(false);
    }
  }

  async function handleLaunch(configId: string) {
    if (!apiKey) {
      setError("Please enter your API key first");
      return;
    }

    setLaunching(configId);
    setError(null);

    try {
      const result = await launchAgent({
        api_key: apiKey,
        config_id: configId,
      });
      router.push(`/chat/${result.session_id}`);
    } catch (e: any) {
      setError(e.message || "Failed to launch agent");
    } finally {
      setLaunching(null);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Universal Agent SDK</h1>
              <p className="text-sm text-gray-400">AI Agent Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span
              className={`px-3 py-1 rounded-full text-sm ${
                apiStatus === "online"
                  ? "bg-green-900/50 text-green-400"
                  : apiStatus === "offline"
                  ? "bg-red-900/50 text-red-400"
                  : "bg-yellow-900/50 text-yellow-400"
              }`}
            >
              {apiStatus === "online"
                ? "API Online"
                : apiStatus === "offline"
                ? "API Offline"
                : "Checking..."}
            </span>
            <a
              href="/sessions"
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
            >
              <List className="w-4 h-4" />
              Sessions
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* API Key Input */}
        <div className="mb-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700">
          <div className="flex items-center gap-3 mb-4">
            <Key className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold">API Key</h2>
          </div>
          <div className="flex gap-4">
            <input
              type="password"
              placeholder="Enter your Anthropic or OpenAI API key..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="flex-1 px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 transition"
            />
          </div>
          <p className="mt-2 text-sm text-gray-400">
            Your API key is stored locally and never sent to our servers.
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300">
            {error}
          </div>
        )}

        {/* Presets Grid */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Agent Presets</h2>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            </div>
          ) : configs.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No agent presets found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {configs.map((config) => (
                <div
                  key={config.id}
                  className="p-6 bg-gray-800/50 rounded-xl border border-gray-700 hover:border-gray-600 transition group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                      <Bot className="w-6 h-6" />
                    </div>
                    <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                      {config.provider}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold mb-2">{config.name}</h3>
                  <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                    {config.description || "No description available"}
                  </p>

                  <div className="flex flex-wrap gap-1 mb-4">
                    {config.allowed_tools.slice(0, 4).map((tool) => (
                      <span
                        key={tool}
                        className="px-2 py-0.5 bg-gray-700/50 rounded text-xs text-gray-300"
                      >
                        {tool}
                      </span>
                    ))}
                    {config.allowed_tools.length > 4 && (
                      <span className="px-2 py-0.5 bg-gray-700/50 rounded text-xs text-gray-300">
                        +{config.allowed_tools.length - 4} more
                      </span>
                    )}
                  </div>

                  <button
                    onClick={() => handleLaunch(config.id)}
                    disabled={launching !== null || !apiKey}
                    className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition flex items-center justify-center gap-2"
                  >
                    {launching === config.id ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Launching...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Launch Agent
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
