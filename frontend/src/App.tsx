import React, { useState, useEffect, useRef } from 'react';
import { Menu, Sparkles, Shield, Cpu } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { useDbStats } from './hooks/useDbStats';
import { useSessions } from './hooks/useSessions';
import { useDocumentIngest } from './hooks/useDocumentIngest';
import { useChatStream } from './hooks/useChatStream';
import { exportChatToMarkdown } from './utils/exportChat';

const API_BASE = '';

export const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Custom Hooks
  const { stats, fetchStats } = useDbStats(API_BASE);
  const {
    sessions,
    currentSessionId,
    messages,
    setMessages,
    fetchSessions,
    selectSession,
    createNewSession,
    deleteSession,
  } = useSessions(API_BASE);

  const { isIngesting, handleIngest, handleClearDb, handleUploadFiles } = useDocumentIngest(API_BASE);
  const { isStreaming, sendMessage } = useChatStream(API_BASE);

  // Initial Load
  useEffect(() => {
    fetchStats();
    fetchSessions();
  }, [fetchStats, fetchSessions]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSendMessage = async (text: string) => {
    await sendMessage(text, currentSessionId, setMessages);
    fetchSessions();
    fetchStats();
  };

  const handleSidebarSelectSession = (sessionId: string) => {
    selectSession(sessionId);
    setSidebarOpen(false);
  };

  const samplePrompts = [
    {
      title: 'Mali & Bütçe Analizi',
      desc: 'Projenin bütçesi ve mali tablosu nedir?',
    },
    {
      title: 'Teknik Altyapı & Mimari',
      desc: 'Teknik altyapı ve kullanılan teknolojileri özetle.',
    },
    {
      title: 'Sorun & Çözüm Matrisi',
      desc: 'En sık karşılaşılan sorunlar ve çözümleri nelerdir?',
    },
  ];

  return (
    <div className="flex h-screen w-screen ambient-canvas overflow-hidden">
      {/* Sidebar Component */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSidebarSelectSession}
        onCreateSession={createNewSession}
        onDeleteSession={deleteSession}
        stats={stats}
        onIngest={() => handleIngest(fetchStats)}
        onClearDb={() => handleClearDb(fetchStats)}
        onUploadFiles={(files) => handleUploadFiles(files, fetchStats)}
        onExportChat={() => exportChatToMarkdown(messages)}
        isIngesting={isIngesting}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Chat Workspace */}
      <main className="flex-1 flex flex-col h-full md:ml-72 relative">
        {/* Top Navbar */}
        <header className="h-14 border-b border-white/5 flex items-center justify-between px-4 bg-sidebar/50 backdrop-blur-md z-10 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden text-slate-400 hover:text-white p-1"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white">⚡ Zenith AI</span>
              <span className="text-xs text-slate-500 hidden sm:inline">•</span>
              <span className="text-xs text-slate-400 hidden sm:inline font-medium">
                Hibrit RAG Asistanı (Dense + BM25)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-medium text-slate-400 bg-white/5 px-2.5 py-1 rounded-full border border-white/5">
              <Shield className="w-3 h-3 text-emerald-400" />
              <span>%100 Yerel / Çevrimdışı</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-medium text-indigo-300 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20">
              <Cpu className="w-3 h-3 text-indigo-400" />
              <span>phi-4-mini</span>
            </div>
          </div>
        </header>

        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-2">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto text-center px-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xl shadow-xl shadow-indigo-500/20 mb-4">
                ⚡
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight mb-2">
                Zenith AI Doküman Asistanı
              </h2>
              <p className="text-xs md:text-sm text-slate-400 max-w-md mb-8 leading-relaxed">
                Kurumsal belgelerinizi tamamen çevrimdışı, sıfır bulut bağımlılığı ve Dense + BM25 FTS5 hibrit arama gücüyle analiz edin.
              </p>

              {/* Quick Prompt Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full">
                {samplePrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(p.desc)}
                    className="p-3 rounded-xl bg-card border border-white/5 hover:border-indigo-500/40 hover:bg-slate-800/60 text-left transition-all duration-200 group"
                  >
                    <div className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      {p.title}
                    </div>
                    <div className="text-xs text-slate-300 group-hover:text-white leading-relaxed">
                      {p.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.map((msg, idx) => (
                <ChatMessage key={idx} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-gradient-to-t from-background via-background to-transparent flex-shrink-0">
          <ChatInput onSendMessage={handleSendMessage} disabled={isStreaming} />
        </div>
      </main>
    </div>
  );
};

export default App;
