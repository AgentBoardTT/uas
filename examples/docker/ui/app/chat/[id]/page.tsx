"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  Loader2,
  Send,
  User,
  StopCircle,
  Upload,
  PanelRightOpen,
  PanelRightClose,
  ChevronDown,
  ChevronRight,
  Brain,
  Wrench,
  CheckCircle,
  XCircle,
  Clock,
  MessageSquare,
} from "lucide-react";
import { getSession, sendMessage, SessionInfo } from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import { ToolEvent, SkillEvent } from "@/lib/types";
import { ToolExecutionPanel } from "@/components/ToolExecutionPanel";
import { SkillExecutionPanel } from "@/components/SkillExecutionPanel";
import { FileUploadModal } from "@/components/FileUploadModal";

interface AgentStep {
  type: "thinking" | "tool_start" | "tool_complete" | "tool_error" | "text";
  content?: string;
  tool_name?: string;
  tool_use_id?: string;
  tool_input?: any;
  output?: string;
  error?: string;
  status?: string;
  duration_ms?: number;
  timestamp: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  steps?: AgentStep[];
  timestamp?: string;
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;
  const { apiKey } = useAppStore();

  const [session, setSession] = useState<SessionInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Panel states
  const [showSidebar, setShowSidebar] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Event states
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [skillEvents, setSkillEvents] = useState<SkillEvent[]>([]);

  // Track expanded thinking sections per message
  const [expandedThinking, setExpandedThinking] = useState<Set<number>>(new Set());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const thinkingBufferRef = useRef<string>("");
  const stepsRef = useRef<AgentStep[]>([]);
  const textBufferRef = useRef<string>("");
  const hasMoreToolsRef = useRef<boolean>(false);

  useEffect(() => {
    loadSession();
    return () => {
      abortControllerRef.current?.abort();
    };
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function loadSession() {
    try {
      const sessionInfo = await getSession(sessionId);
      setSession(sessionInfo);
    } catch (e) {
      setError("Session not found or expired");
    } finally {
      setIsLoading(false);
    }
  }

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  const handleStreamEvent = useCallback((data: any, updateMessage: (thinking: string, steps: AgentStep[]) => void) => {
    const timestamp = data.timestamp || new Date().toISOString();

    switch (data.type) {
      case "thinking":
        // Accumulate thinking content into buffer
        thinkingBufferRef.current += data.content || "";
        // Update the current assistant message with accumulated thinking
        updateMessage(thinkingBufferRef.current, stepsRef.current);
        break;

      case "tool_start":
        // If there's accumulated text before this tool call, save it as an intermediate step
        if (textBufferRef.current.trim()) {
          const textStep: AgentStep = {
            type: "text",
            content: textBufferRef.current.trim(),
            timestamp,
          };
          stepsRef.current = [...stepsRef.current, textStep];
          textBufferRef.current = ""; // Clear the buffer
        }

        // Mark that we have more tools coming (text after this will be intermediate)
        hasMoreToolsRef.current = true;

        // Add tool start step
        const toolStartStep: AgentStep = {
          type: "tool_start",
          tool_name: data.tool_name || "unknown",
          tool_use_id: data.tool_use_id,
          tool_input: data.tool_input,
          status: "started",
          timestamp,
        };
        stepsRef.current = [...stepsRef.current, toolStartStep];
        updateMessage(thinkingBufferRef.current, stepsRef.current);

        // Also update sidebar events
        setToolEvents((prev) => [
          ...prev,
          {
            type: "tool_start",
            tool_name: data.tool_name || "unknown",
            tool_use_id: data.tool_use_id,
            status: "started",
            timestamp,
          },
        ]);
        break;

      case "tool_complete":
        // Update the tool step to completed
        stepsRef.current = stepsRef.current.map((step) => {
          if (step.tool_use_id === data.tool_use_id ||
              (step.tool_name === data.tool_name && step.status === "started")) {
            return {
              ...step,
              type: "tool_complete" as const,
              output: data.output,
              status: "completed",
              duration_ms: data.duration_ms,
              timestamp,
            };
          }
          return step;
        });
        updateMessage(thinkingBufferRef.current, stepsRef.current);

        // Also update sidebar events
        setToolEvents((prev) => {
          const existingIndex = prev.findIndex(
            (t) =>
              t.tool_use_id === data.tool_use_id ||
              (t.tool_name === data.tool_name && t.status === "started")
          );
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = {
              type: "tool_complete",
              tool_name: data.tool_name,
              tool_use_id: data.tool_use_id,
              tool_input: data.tool_input,
              output: data.output,
              status: "completed",
              duration_ms: data.duration_ms,
              timestamp,
            };
            return updated;
          }
          return [
            ...prev,
            {
              type: "tool_complete",
              tool_name: data.tool_name,
              tool_use_id: data.tool_use_id,
              tool_input: data.tool_input,
              output: data.output,
              status: "completed",
              duration_ms: data.duration_ms,
              timestamp,
            },
          ];
        });
        break;

      case "tool_error":
        // Update the tool step to error
        stepsRef.current = stepsRef.current.map((step) => {
          if (step.tool_use_id === data.tool_use_id ||
              (step.tool_name === data.tool_name && step.status === "started")) {
            return {
              ...step,
              type: "tool_error" as const,
              error: data.error,
              status: "error",
              timestamp,
            };
          }
          return step;
        });
        updateMessage(thinkingBufferRef.current, stepsRef.current);

        // Also update sidebar events
        setToolEvents((prev) => {
          const existingIndex = prev.findIndex(
            (t) =>
              t.tool_use_id === data.tool_use_id ||
              (t.tool_name === data.tool_name && t.status === "started")
          );
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = {
              type: "tool_error",
              tool_name: data.tool_name,
              tool_use_id: data.tool_use_id,
              error: data.error,
              status: "error",
              timestamp,
            };
            return updated;
          }
          return prev;
        });
        break;

      case "skill_detection":
        setSkillEvents((prev) => [
          ...prev,
          {
            type: "skill_detection",
            skill_id: data.skill_id || "",
            skill_name: data.skill_name || "",
            confidence: data.confidence || "medium",
            matched_pattern: data.matched_pattern,
            context_snippet: data.context_snippet,
            timestamp,
          },
        ]);
        break;
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsStreaming(true);
    setError(null);

    // Clear events for new message
    setToolEvents([]);
    setSkillEvents([]);
    thinkingBufferRef.current = "";
    stepsRef.current = [];
    textBufferRef.current = "";
    hasMoreToolsRef.current = false;

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await sendMessage(sessionId, userMessage);

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let assistantContent = "";

      // Add placeholder for assistant message
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              // Handle tool/thinking/skill events with thinking and steps accumulation
              const updateMessageState = (thinking: string, steps: AgentStep[]) => {
                setMessages((prev) => {
                  const updated = [...prev];
                  if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      thinking,
                      steps: [...steps],
                    };
                  }
                  return updated;
                });
              };
              handleStreamEvent(data, updateMessageState);

              if (
                data.type === "stream" &&
                (data.delta?.type === "text_delta" || data.delta?.type === "text") &&
                data.delta?.text
              ) {
                // Accumulate text into buffer (this segment might become intermediate)
                textBufferRef.current += data.delta.text;
                // Also track total for backwards compatibility
                assistantContent += data.delta.text;

                // Show current text segment as content (will be updated if more tools come)
                setMessages((prev) => {
                  const updated = [...prev];
                  const currentMsg = updated[updated.length - 1];
                  updated[updated.length - 1] = {
                    role: "assistant",
                    content: textBufferRef.current, // Only show current segment
                    thinking: currentMsg?.thinking,
                    steps: currentMsg?.steps,
                  };
                  return updated;
                });
              } else if (data.type === "message" && data.content) {
                // Final message - content is the last text segment
                setMessages((prev) => {
                  const updated = [...prev];
                  const currentMsg = updated[updated.length - 1];
                  updated[updated.length - 1] = {
                    role: "assistant",
                    content: textBufferRef.current || data.content,
                    thinking: currentMsg?.thinking,
                    steps: currentMsg?.steps,
                  };
                  return updated;
                });
              } else if (data.type === "error") {
                throw new Error(data.error);
              }
            } catch (parseError) {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") {
        setError(e.message || "Failed to get response");
        // Remove empty assistant message on error
        setMessages((prev) => {
          if (prev[prev.length - 1]?.content === "") {
            return prev.slice(0, -1);
          }
          return prev;
        });
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }

  function handleStop() {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
      </div>
    );
  }

  if (error && !session) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-500 transition"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-900/80 backdrop-blur sticky top-0 z-10">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/")}
              className="p-2 hover:bg-gray-800 rounded-lg transition"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="font-semibold">{session?.config_name || "Agent"}</h1>
              <p className="text-xs text-gray-400">
                Session: {sessionId.slice(0, 12)}...
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowUploadModal(true)}
              className="p-2 hover:bg-gray-800 rounded-lg transition"
              title="Upload files"
            >
              <Upload className="w-5 h-5 text-gray-400" />
            </button>
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 hover:bg-gray-800 rounded-lg transition"
              title={showSidebar ? "Hide sidebar" : "Show sidebar"}
            >
              {showSidebar ? (
                <PanelRightClose className="w-5 h-5 text-gray-400" />
              ) : (
                <PanelRightOpen className="w-5 h-5 text-gray-400" />
              )}
            </button>
            <span
              className={`px-2 py-1 rounded text-xs ${
                session?.status === "running"
                  ? "bg-green-900/50 text-green-400"
                  : "bg-gray-700 text-gray-400"
              }`}
            >
              {session?.status || "unknown"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <Bot className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                  <p className="text-gray-400">
                    Start a conversation with the agent
                  </p>
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex gap-4 ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-blue-600"
                        : "bg-gray-800 border border-gray-700"
                    }`}
                  >
                    {/* Collapsible Agent Steps Section for Assistant Messages */}
                    {message.role === "assistant" && (message.thinking || (message.steps && message.steps.length > 0)) && (
                      <div className="mb-3">
                        <button
                          onClick={() => {
                            setExpandedThinking((prev) => {
                              const next = new Set(prev);
                              if (next.has(index)) {
                                next.delete(index);
                              } else {
                                next.add(index);
                              }
                              return next;
                            });
                          }}
                          className="flex items-center gap-2 text-xs text-purple-400 hover:text-purple-300 transition-colors w-full"
                        >
                          {expandedThinking.has(index) ? (
                            <ChevronDown className="w-3 h-3" />
                          ) : (
                            <ChevronRight className="w-3 h-3" />
                          )}
                          <Brain className="w-3 h-3" />
                          <span>Agent Steps</span>
                          <span className="text-gray-500 ml-auto">
                            {message.thinking ? "Thinking" : ""}
                            {message.thinking && message.steps && message.steps.length > 0 ? " + " : ""}
                            {message.steps && message.steps.length > 0
                              ? `${message.steps.length} step(s)`
                              : ""}
                          </span>
                        </button>
                        {expandedThinking.has(index) && (
                          <div className="mt-2 space-y-2 max-h-80 overflow-y-auto">
                            {/* Thinking Section */}
                            {message.thinking && (
                              <div className="p-3 bg-purple-900/20 border border-purple-800/30 rounded-lg">
                                <div className="flex items-center gap-2 text-xs text-purple-400 mb-2">
                                  <Brain className="w-3 h-3" />
                                  <span className="font-medium">Thinking</span>
                                </div>
                                <div className="text-xs text-gray-300 whitespace-pre-wrap max-h-40 overflow-y-auto">
                                  {message.thinking}
                                </div>
                              </div>
                            )}

                            {/* All Steps (Text + Tools) */}
                            {message.steps && message.steps.map((step, stepIndex) => (
                              <div key={stepIndex}>
                                {/* Text Step (Intermediate Response) */}
                                {step.type === "text" && step.content && (
                                  <div className="p-3 bg-gray-700/30 border border-gray-600/30 rounded-lg">
                                    <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                                      <MessageSquare className="w-3 h-3" />
                                      <span className="font-medium">Intermediate Response</span>
                                    </div>
                                    <div className="text-xs text-gray-300 whitespace-pre-wrap">
                                      {step.content}
                                    </div>
                                  </div>
                                )}

                                {/* Tool Step */}
                                {(step.type === "tool_start" || step.type === "tool_complete" || step.type === "tool_error") && (
                                  <div
                                    className={`p-3 rounded-lg border ${
                                      step.status === "completed"
                                        ? "bg-green-900/20 border-green-800/30"
                                        : step.status === "error"
                                        ? "bg-red-900/20 border-red-800/30"
                                        : "bg-blue-900/20 border-blue-800/30"
                                    }`}
                                  >
                                    <div className="flex items-center gap-2 text-xs mb-2">
                                      {step.status === "completed" ? (
                                        <CheckCircle className="w-3 h-3 text-green-400" />
                                      ) : step.status === "error" ? (
                                        <XCircle className="w-3 h-3 text-red-400" />
                                      ) : (
                                        <Clock className="w-3 h-3 text-blue-400 animate-pulse" />
                                      )}
                                      <Wrench className="w-3 h-3 text-gray-400" />
                                      <span className={`font-medium ${
                                        step.status === "completed"
                                          ? "text-green-400"
                                          : step.status === "error"
                                          ? "text-red-400"
                                          : "text-blue-400"
                                      }`}>
                                        {step.tool_name}
                                      </span>
                                      {step.duration_ms && (
                                        <span className="text-gray-500 ml-auto">
                                          {step.duration_ms}ms
                                        </span>
                                      )}
                                    </div>

                                    {/* Tool Input */}
                                    {step.tool_input && (
                                      <div className="mb-2">
                                        <div className="text-xs text-gray-500 mb-1">Input:</div>
                                        <div className="text-xs text-gray-300 bg-black/20 rounded p-2 max-h-20 overflow-y-auto font-mono">
                                          {typeof step.tool_input === "string"
                                            ? step.tool_input
                                            : JSON.stringify(step.tool_input, null, 2)}
                                        </div>
                                      </div>
                                    )}

                                    {/* Tool Output or Error */}
                                    {step.output && (
                                      <div>
                                        <div className="text-xs text-gray-500 mb-1">Output:</div>
                                        <div className="text-xs text-gray-300 bg-black/20 rounded p-2 max-h-32 overflow-y-auto font-mono whitespace-pre-wrap">
                                          {typeof step.output === "string"
                                            ? step.output.slice(0, 500) + (step.output.length > 500 ? "..." : "")
                                            : JSON.stringify(step.output, null, 2).slice(0, 500)}
                                        </div>
                                      </div>
                                    )}
                                    {step.error && (
                                      <div>
                                        <div className="text-xs text-red-400 mb-1">Error:</div>
                                        <div className="text-xs text-red-300 bg-black/20 rounded p-2 max-h-20 overflow-y-auto">
                                          {step.error}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    <div className="prose prose-invert max-w-none whitespace-pre-wrap">
                      {message.content || (
                        <span className="text-gray-500 animate-pulse">
                          {message.steps && message.steps.some(s => s.status === "started")
                            ? "Running tool..."
                            : message.thinking
                            ? "Generating response..."
                            : "Thinking..."}
                        </span>
                      )}
                    </div>
                  </div>

                  {message.role === "user" && (
                    <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {error && (
                <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-center">
                  {error}
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input */}
          <div className="border-t border-gray-700 bg-gray-900/80 backdrop-blur">
            <form
              onSubmit={handleSubmit}
              className="max-w-4xl mx-auto px-4 py-4 flex gap-4"
            >
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message... (Shift+Enter for new line)"
                rows={1}
                disabled={isStreaming}
                className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:outline-none focus:border-blue-500 resize-none transition disabled:opacity-50"
                style={{
                  minHeight: "48px",
                  maxHeight: "200px",
                }}
              />

              {isStreaming ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="px-4 py-3 bg-red-600 hover:bg-red-500 rounded-xl transition flex items-center gap-2"
                >
                  <StopCircle className="w-5 h-5" />
                  Stop
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-xl transition flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                  Send
                </button>
              )}
            </form>
          </div>
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <div className="w-80 border-l border-gray-700 bg-gray-900/50 overflow-y-auto p-4 space-y-4">
            {/* Tool Events */}
            <ToolExecutionPanel
              events={toolEvents}
              isConnected={isStreaming}
            />

            {/* Skill Events */}
            {skillEvents.length > 0 && (
              <SkillExecutionPanel events={skillEvents} />
            )}
          </div>
        )}
      </div>

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        sessionId={sessionId}
        apiKey={apiKey}
        onUploadComplete={(files) => {
          console.log("Uploaded files:", files);
        }}
      />
    </div>
  );
}
