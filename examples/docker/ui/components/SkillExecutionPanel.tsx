'use client';

import { useState } from 'react';
import { Sparkles, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { SkillEvent } from '../lib/types';

interface SkillEventCardProps {
  event: SkillEvent;
  defaultExpanded?: boolean;
}

function SkillEventCard({ event, defaultExpanded = false }: SkillEventCardProps) {
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

  const getConfidenceColor = () => {
    switch (event.confidence) {
      case 'high':
        return 'border-green-500 bg-green-500/10 text-green-300';
      case 'medium':
        return 'border-yellow-500 bg-yellow-500/10 text-yellow-300';
      case 'low':
        return 'border-gray-500 bg-gray-500/10 text-gray-300';
      default:
        return 'border-gray-500 bg-gray-500/10 text-gray-300';
    }
  };

  return (
    <div className="bg-gray-900/50 border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Zap className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-medium text-gray-200 truncate">
            {event.skill_name}
          </span>
          <span className={`text-xs px-2 py-0.5 rounded border ${getConfidenceColor()}`}>
            {event.confidence}
          </span>
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
        <div className="px-3 pb-3 border-t border-gray-700/50 space-y-2">
          {event.context_snippet && (
            <div className="mt-2">
              <div className="text-xs text-gray-500 mb-1">Context</div>
              <p className="text-xs text-gray-300 bg-gray-800/50 rounded p-2">
                {event.context_snippet}
              </p>
            </div>
          )}

          {event.matched_pattern && (
            <div>
              <div className="text-xs text-gray-500 mb-1">Matched Pattern</div>
              <code className="text-xs text-amber-300 bg-gray-800/50 rounded p-2 block">
                {event.matched_pattern}
              </code>
            </div>
          )}

          <div className="text-xs text-gray-500">
            Skill ID: {event.skill_id}
          </div>
        </div>
      )}
    </div>
  );
}

interface SkillExecutionPanelProps {
  events: SkillEvent[];
}

export function SkillExecutionPanel({ events }: SkillExecutionPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Group skills by name for summary
  const skillSummary = events.reduce((acc, event) => {
    const key = event.skill_name;
    if (!acc[key]) {
      acc[key] = { count: 0, confidence: event.confidence };
    }
    acc[key].count++;
    return acc;
  }, {} as Record<string, { count: number; confidence: string }>);

  if (events.length === 0) return null;

  return (
    <div className="bg-gray-900/30 border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-medium text-gray-300">
            Skills Used ({events.length})
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isCollapsed ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </button>

      {!isCollapsed && (
        <div className="p-3 pt-0 space-y-3">
          {/* Summary Badges */}
          <div className="flex flex-wrap gap-2">
            {Object.entries(skillSummary).map(([name, { count, confidence }]) => (
              <span
                key={name}
                className={`text-xs px-2 py-1 rounded-full border ${
                  confidence === 'high' ? 'border-green-500 bg-green-500/10 text-green-300' :
                  confidence === 'medium' ? 'border-yellow-500 bg-yellow-500/10 text-yellow-300' :
                  'border-gray-500 bg-gray-500/10 text-gray-300'
                }`}
              >
                {name} {count > 1 && `(${count})`}
              </span>
            ))}
          </div>

          {/* Event List */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {events.map((event, index) => (
              <SkillEventCard key={index} event={event} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
