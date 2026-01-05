'use client';

import { useState } from 'react';
import { Brain, ChevronDown, ChevronUp } from 'lucide-react';
import { ThinkingEvent } from '../lib/types';

interface ThinkingCardProps {
  event: ThinkingEvent;
  defaultExpanded?: boolean;
}

export function ThinkingCard({ event, defaultExpanded = false }: ThinkingCardProps) {
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

  const truncatedContent = event.content.length > 100
    ? event.content.substring(0, 100) + '...'
    : event.content;

  return (
    <div className="bg-gradient-to-r from-gray-900/40 to-gray-800/40 border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">Thinking</span>
          {event.timestamp && (
            <span className="text-xs text-gray-500">
              {formatTime(event.timestamp)}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {!isExpanded && (
        <div className="px-3 pb-3">
          <p className="text-xs text-gray-400 line-clamp-2">{truncatedContent}</p>
        </div>
      )}

      {isExpanded && (
        <div className="px-3 pb-3 border-t border-gray-700/50">
          <pre className="text-xs text-gray-300 whitespace-pre-wrap mt-2 max-h-64 overflow-y-auto">
            {event.content}
          </pre>
        </div>
      )}
    </div>
  );
}

interface ThinkingListProps {
  events: ThinkingEvent[];
}

export function ThinkingList({ events }: ThinkingListProps) {
  if (events.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-400 mb-2">
        <Brain className="w-4 h-4" />
        <span>Agent Thinking ({events.length})</span>
      </div>
      {events.map((event, index) => (
        <ThinkingCard key={index} event={event} />
      ))}
    </div>
  );
}
