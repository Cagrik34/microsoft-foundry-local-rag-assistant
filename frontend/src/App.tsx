import React, { useState, useEffect, useRef } from 'react';
import { Menu, Sparkles, Shield, Cpu } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import type { Message, Session, DbStats, SourceItem } from './types';

const API_BASE = ''; // Same origin when served via FastAPI, or proxy in dev

export const App: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState<DbStats | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initial Data Fetch
  useEffect(() => {
    fetchStats();
    fetchSessions();
  }, []);

  // Fetch stats from backend
  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Stats fetch error:', err);
    }
  };

  // Fetch chat sessions
  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`);
      if (res.ok) {
        const data: Session[] = await res.json();
        setSessions(data);
        if (data.length > 0 && !currentSessionId) {
          selectSession(data[0].session_id);
        } else if (data.length === 0 && !currentSessionId) {
          createNewSession();
        }
      }
    } catch (err) {
      console.error('Sessions fetch error:', err);
    }
  };

  // Select active session and load messages
  const selectSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (err) {
      console.error('Messages fetch error:', err);
    }
    setSidebarOpen(false);
  };

  // Create new session
  const createNewSession = async () => {
    try {
      const title = `Analiz #${sessions.length + 1}`;
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentSessionId(data.session_id);
        setMessages([]);
        fetchSessions();
      }
    } catch (err) {
      console.error('Create session error:', err);
    }
  };

  // Delete session
  const deleteSession = async (sessionId: string) => {
    try {
      await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' });
      const updated = sessions.filter((s) => s.session_id !== sessionId);
      setSessions(updated);
      if (currentSessionId === sessionId) {
        if (updated.length > 0) {
          selectSession(updated[0].session_id);
        } else {
          createNewSession();
        }
      }
    } catch (err) {
      console.error('Delete session error:', err);
    }
  };

  // Trigger document re-indexing
  const handleIngest = async () => {
    setIsIngesting(true);
    try {
      await fetch(`${API_BASE}/api/documents/ingest`, { method: 'POST' });
      await fetchStats();
    } catch (err) {
      console.error('Ingest error:', err);
    } finally {
      setIsIngesting(false);
    }
  };

  // Clear database
  const handleClearDb = async () => {
    if (window.confirm('Tüm indekslenmiş veritabanı silinecek. Emin misiniz?')) {
      try {
        await fetch(`${API_BASE}/api/database`, { method: 'DELETE' });
        await fetchStats();
      } catch (err) {
        console.error('Clear DB error:', err);
      }
    }
  };

  // Upload files
  const handleUploadFiles = async (fileList: FileList) => {
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }
    setIsIngesting(true);
    try {
      await fetch(`${API_BASE}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      await fetchStats();
    } catch (err) {
      console.error('Upload error:', err);
    } finally {
      setIsIngesting(false);
    }
  };

  // Send message and stream response via Server-Sent Events (SSE)
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    const userMessage: Message = {
      role: 'user',
      content: text,
      created_at: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    };

    const initialAssistantMessage: Message = {
      role: 'assistant',
      content: '',
      isStreaming: true,
      created_at: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: text,
          session_id: currentSessionId,
        }),
      });

      if (!response.body) throw new Error('ReadableStream not supported.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let assistantContent = '';
      let sources: SourceItem[] = [];
      let searchTime = 0;
      let genTime = 0;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        const lines = chunkText.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'meta') {
                sources = data.sources || [];
                searchTime = data.search_time || 0;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      sources,
                      search_time: searchTime,
                    };
                  }
                  return updated;
                });
              } else if (data.type === 'chunk') {
                assistantContent += data.text;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      content: assistantContent,
                    };
                  }
                  return updated;
                });
              } else if (data.type === 'done') {
                genTime = data.gen_time || 0;
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      content: data.full_text,
                      gen_time: genTime,
                      isStreaming: false,
                    };
                  }
                  return updated;
                });
              }
            } catch (jsonErr) {
              console.error('SSE parse error:', jsonErr);
            }
          }
        }
      }

      fetchSessions();
      fetchStats();
    } catch (err) {
      console.error('Stream error:', err);
      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
          updated[lastIdx] = {
            ...updated[lastIdx],
            content: 'Yanıt üretilirken bir bağlantı hatası oluştu.',
            isStreaming: false,
          };
        }
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  // Export current chat as Markdown
  const handleExportChat = () => {
    if (messages.length === 0) return;
    let md = '# ⚡ Zenith AI — Doküman Analiz Raporu\n\n';
    messages.forEach((m) => {
      const role = m.role === 'user' ? '🧑‍💻 Kullanıcı' : '⚡ Zenith AI';
      md += `### ${role}\n${m.content}\n\n`;
      if (m.sources && m.sources.length > 0) {
        md += '#### Doğrulanan Kaynaklar:\n';
        m.sources.forEach((s) => {
          md += `- **[${s.citation_index}] ${s.source_file}** (Bölüm ${s.chunk_index + 1}) — %${s.relevance} Alaka (${s.match_type.toUpperCase()})\n`;
        });
        md += '\n';
      }
      if (m.search_time && m.gen_time) {
        md += `*⏱️ Arama: ${m.search_time}s | ⚡ Çıkarım: ${m.gen_time}s*\n\n`;
      }
      md += '---\n\n';
    });

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `zenith_ai_analiz_${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // Sample quick questions
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
        onSelectSession={selectSession}
        onCreateSession={createNewSession}
        onDeleteSession={deleteSession}
        stats={stats}
        onIngest={handleIngest}
        onClearDb={handleClearDb}
        onUploadFiles={handleUploadFiles}
        onExportChat={handleExportChat}
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
                SOTA Hibrit RAG Asistanı
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-medium text-slate-400 bg-white/5 px-2.5 py-1 rounded-full border border-white/5">
              <Shield className="w-3 h-3 text-emerald-400" />
              <span>%100 Yerel Bellek</span>
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
                Zenith AI Kurumsal Doküman Asistanı
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
