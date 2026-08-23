import React, { useState } from 'react';
import { Volume2, VolumeX, ChevronDown, ChevronUp, FileText, Clock, Zap } from 'lucide-react';
import type { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [activeTooltip, setActiveTooltip] = useState<number | null>(null);

  const isAssistant = message.role === 'assistant';

  const handleSpeak = () => {
    if (!('speechSynthesis' in window)) {
      alert('Tarayıcınız ses sentezini desteklemiyor.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const clean = message.content.replace(/\[\d+\]/g, '').replace(/[*#_`~>|\-\[\]\(\)]/g, ' ');
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = 'tr-TR';
    utterance.rate = 1.0;

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  // Metin içindeki [1], [2] alıntılarını interaktif rozetlere dönüştür
  const renderFormattedContent = (content: string) => {
    const parts = content.split(/(\[\d+\])/g);

    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationNum = parseInt(match[1], 10);
        const matchedSource = message.sources?.find((s) => s.citation_index === citationNum);

        return (
          <span
            key={index}
            className="relative inline-block"
            onMouseEnter={() => setActiveTooltip(citationNum)}
            onMouseLeave={() => setActiveTooltip(null)}
          >
            <span className="inline-flex items-center justify-center bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 hover:text-white border border-indigo-500/40 rounded-md text-[11px] font-bold px-1.5 py-0.5 mx-0.5 cursor-pointer transition-colors">
              [{citationNum}]
            </span>

            {/* Hover Tooltip Card */}
            {activeTooltip === citationNum && matchedSource && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2.5 bg-slate-900/95 border border-white/10 rounded-xl shadow-2xl backdrop-blur-xl z-50 text-left pointer-events-none animate-in fade-in zoom-in-95 duration-150">
                <div className="flex items-center justify-between text-[11px] font-semibold text-white mb-1">
                  <div className="flex items-center gap-1 truncate">
                    <FileText className="w-3 h-3 text-indigo-400 flex-shrink-0" />
                    <span className="truncate">{matchedSource.source_file}</span>
                  </div>
                  <span className="text-[10px] text-indigo-400 px-1.5 py-0.5 bg-indigo-500/10 rounded border border-indigo-500/20">
                    %{matchedSource.relevance} Alaka
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 line-clamp-3 leading-relaxed bg-black/40 p-1.5 rounded border border-white/5">
                  {matchedSource.content}
                </div>
              </div>
            )}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className={`flex gap-3 py-4 ${isAssistant ? 'bg-white/[0.01]' : ''}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold shadow-md ${
          isAssistant
            ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-indigo-500/20'
            : 'bg-slate-800 border border-white/10 text-slate-200'
        }`}
      >
        {isAssistant ? '⚡' : '🧑‍💻'}
      </div>

      {/* Content Area */}
      <div className="flex-1 space-y-2 overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-200">
            {isAssistant ? 'Zenith AI' : 'Kullanıcı'}
          </span>
          {message.created_at && (
            <span className="text-[10px] text-slate-500">{message.created_at}</span>
          )}
        </div>

        {/* Message Body */}
        <div className="text-sm text-slate-200 leading-relaxed break-words whitespace-pre-wrap">
          {renderFormattedContent(message.content)}
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 ml-1 bg-indigo-400 animate-pulse align-middle" />
          )}
        </div>

        {/* Assistant Action Bar & Sources */}
        {isAssistant && !message.isStreaming && (
          <div className="pt-2 space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              {/* TTS Button */}
              {message.content && (
                <button
                  onClick={handleSpeak}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                    isSpeaking
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/30 animate-pulse'
                      : 'bg-white/5 hover:bg-white/10 text-slate-300 border-white/5'
                  }`}
                >
                  {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                  {isSpeaking ? 'Durdur' : 'Seslendir'}
                </button>
              )}

              {/* Verified Sources Toggle */}
              {message.sources && message.sources.length > 0 && (
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5 transition-colors"
                >
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  Doğrulanan Kaynaklar ({message.sources.length})
                  {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
              )}

              {/* Telemetry Pill */}
              {message.search_time !== undefined && message.gen_time !== undefined && (
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg text-[11px] text-slate-400 bg-white/[0.02] border border-white/5">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" /> Arama: <b>{message.search_time}s</b>
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Zap className="w-3 h-3 text-indigo-400" /> Çıkarım: <b>{message.gen_time}s</b>
                  </span>
                </div>
              )}
            </div>

            {/* Expanded Sources Details */}
            {showSources && message.sources && (
              <div className="mt-2 space-y-2 bg-black/30 p-3 rounded-xl border border-white/5">
                {message.sources.map((src, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-medium text-slate-200">
                        <span className="bg-indigo-500/20 text-indigo-300 text-[10px] font-bold px-1.5 py-0.5 rounded border border-indigo-500/30">
                          [{src.citation_index}]
                        </span>
                        <span>📄 {src.source_file}</span>
                        <span className="text-[10px] text-slate-500">(Bölüm {src.chunk_index + 1})</span>
                      </div>
                      <span className="text-[10px] font-semibold text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        %{src.relevance} Alaka ({src.match_type.toUpperCase()})
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 leading-relaxed bg-black/40 p-2 rounded border border-white/[0.03]">
                      {src.content}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
