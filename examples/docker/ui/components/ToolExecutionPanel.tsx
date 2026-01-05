'use client';

import { useState } from 'react';
import {
  Wrench,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
} from 'lucide-react';
import { ToolEvent } from '../lib/types';

interface ToolEventCardProps {
  event: ToolEvent;
  defaultExpanded?: boolean;
}

function ToolEventCard({ event, defaultExpanded = false }: ToolEventCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return '';
    }
  };

  const getStatusIcon = () => {
    switch (event.status) {
      case 'started':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'in_progress':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Wrench className="w-4 h-4 text-gray-400" />;
    }
  };

  const getBorderColor = () => {
    switch (event.status) {
      case 'started':
        return 'border-l-blue-500';
      case 'in_progress':
        return 'border-l-yellow-500';
      case 'completed':
        return 'border-l-green-500';
      case 'error':
        return 'border-l-red-500';
      default:
        return 'border-l-gray-500';
    }
  };

  const formatInput = (input: unknown): string => {
    if (!input) return '';
    if (typeof input === 'string') return input;
    try {
      return JSON.stringify(input, null, 2);
    } catch {
      return String(input);
    }
  };

  const formatOutput = (output: unknown): string => {
    if (!output) return '';
    if (typeof output === 'string') return output;
    try {
      return JSON.stringify(output, null, 2);
    } catch {
      return String(output);
    }
  };

  return (
    <div className={`bg-gray-900/50 border border-gray-700 border-l-2 ${getBorderColor()} rounded-lg overflow-hidden`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {getStatusIcon()}
          <span className="text-sm font-medium text-gray-200 truncate">
            {event.tool_name}
          </span>
          {event.duration_ms !== undefined && (
            <span className="text-xs text-gray-500">
              ({event.duration_ms}ms)
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {formatTime(event.timestamp)}
          </span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-700/50 space-y-3">
          {event.tool_input !== undefined && event.tool_input !== null && (
            <div className="mt-2">
              <div className="text-xs text-gray-500 mb-1">Input</div>
              <pre className="text-xs text-gray-300 bg-gray-800/50 rounded p-2 overflow-x-auto max-h-40 overflow-y-auto">
                {formatInput(event.tool_input)}
              </pre>
            </div>
          )}

          {event.output !== undefined && event.output !== null && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Output</div>
              <pre className="text-xs text-gray-300 bg-gray-800/50 rounded p-2 overflow-x-auto max-h-40 overflow-y-auto">
                {formatOutput(event.output)}
              </pre>
            </div>
          )}

          {/* Error */}
          {event.error && (
            <div>
              <div className="text-xs text-red-400 mb-1">Error</div>
              <pre className="text-xs text-red-300 bg-red-900/20 rounded p-2 overflow-x-auto">
                {event.error}
              </pre>
            </div>
          )}

          {/* Status Badge */}
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-0.5 rounded ${
              event.status === 'completed' ? 'bg-green-900/30 text-green-300' :
              event.status === 'error' ? 'bg-red-900/30 text-red-300' :
              event.status === 'started' ? 'bg-blue-900/30 text-blue-300' :
              'bg-yellow-900/30 text-yellow-300'
            }`}>
              {event.status}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

interface ToolExecutionPanelProps {
  events: ToolEvent[];
  isConnected?: boolean;
}

export function ToolExecutionPanel({ events, isConnected = false }: ToolExecutionPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const completedCount = events.filter(e => e.status === 'completed').length;
  const errorCount = events.filter(e => e.status === 'error').length;
  const runningCount = events.filter(e => e.status === 'started' || e.status === 'in_progress').length;

  return (
    <div className="bg-gray-900/30 border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-300">
            Tools Executed ({events.length})
          </span>
          {isConnected && (
            <span className="w-2 h-2 rounded-full bg-green-500" title="Connected" />
          )}
        </div>
        <div className="flex items-center gap-2">
          {runningCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-300">
              {runningCount} running
            </span>
          )}
          {completedCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-green-900/30 text-green-300">
              {completedCount} done
            </span>
          )}
          {errorCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded bg-red-900/30 text-red-300">
              {errorCount} failed
            </span>
          )}
          {isCollapsed ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </button>

      {!isCollapsed && (
        <div className="p-3 pt-0 space-y-2 max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">
              No tools executed yet
            </p>
          ) : (
            events.map((event, index) => (
              <ToolEventCard key={event.tool_use_id || index} event={event} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
