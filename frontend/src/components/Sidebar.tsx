import React, { useState, useRef } from 'react';
import {
  Plus,
  MessageSquare,
  Trash2,
  FileText,
  UploadCloud,
  RefreshCw,
  Download,
  X
} from 'lucide-react';
import type { Session, DbStats } from '../types';

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  stats: DbStats | null;
  onIngest: () => void;
  onClearDb: () => void;
  onUploadFiles: (files: FileList) => void;
  onExportChat: () => void;
  isIngesting: boolean;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  stats,
  onIngest,
  onClearDb,
  onUploadFiles,
  onExportChat,
  isIngesting,
  isOpen,
  onClose,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUploadFiles(e.dataTransfer.files);
    }
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-72 bg-sidebar border-r border-white/5 flex flex-col transition-transform duration-300 ease-in-out md:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Brand Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              ⚡ Zenith AI
            </span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Hibrit SOTA
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Microsoft Foundry Local SDK • %100 Çevrimdışı
          </p>
        </div>
        <button
          onClick={onClose}
          className="md:hidden text-slate-400 hover:text-white p-1"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3 border-b border-white/5">
        <button
          onClick={onCreateSession}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/20 transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          Yeni Doküman Analizi
        </button>
      </div>

      {/* Scrollable Center Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Past Sessions */}
        {sessions.length > 0 && (
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2">
              Geçmiş Analizler
            </span>
            <div className="mt-1 space-y-1">
              {sessions.map((sess) => {
                const isActive = sess.session_id === currentSessionId;
                return (
                  <div
                    key={sess.session_id}
                    className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
                      isActive
                        ? 'bg-white/10 text-white font-medium border border-indigo-500/30'
                        : 'text-slate-300 hover:bg-white/5 hover:text-white'
                    }`}
                    onClick={() => onSelectSession(sess.session_id)}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <MessageSquare className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                      <span className="truncate">{sess.title}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(sess.session_id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-400 p-0.5 rounded transition-opacity"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Database Telemetry Metrics */}
        {stats && (
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2">
              Veritabanı Metrikleri
            </span>
            <div className="grid grid-cols-2 gap-2 mt-1.5">
              <div className="bg-card p-2.5 rounded-xl border border-white/5 text-center">
                <div className="text-lg font-bold text-white leading-none">
                  {stats.total_chunks}
                </div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-1">
                  Hibrit Öbek
                </div>
              </div>
              <div className="bg-card p-2.5 rounded-xl border border-white/5 text-center">
                <div className="text-lg font-bold text-white leading-none">
                  {stats.total_files}
                </div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-1">
                  Doküman
                </div>
              </div>
            </div>
            <div className="flex justify-between text-[11px] text-slate-400 px-2 mt-1.5">
              <span>DB Boyutu: <b className="text-slate-300">{stats.db_size_mb} MB</b></span>
              <span>Boyut: <b className="text-slate-300">1024d</b></span>
            </div>
          </div>
        )}

        {/* Ingestion & DB Actions */}
        <div>
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2">
            Doküman İşlemleri
          </span>
          <div className="grid grid-cols-2 gap-2 mt-1.5">
            <button
              onClick={onIngest}
              disabled={isIngesting}
              className="flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-200 text-xs border border-white/5 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isIngesting ? 'animate-spin' : ''}`} />
              {isIngesting ? 'İşleniyor...' : 'İndeksle'}
            </button>
            <button
              onClick={onClearDb}
              className="flex items-center justify-center gap-1.5 py-1.5 px-2.5 rounded-lg bg-white/5 hover:bg-rose-500/10 text-slate-200 hover:text-rose-300 text-xs border border-white/5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Sıfırla
            </button>
          </div>

          {/* File Upload Dropzone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`mt-2 border border-dashed rounded-xl p-3 text-center cursor-pointer transition-colors ${
              dragActive
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-white/10 hover:border-white/20 bg-white/[0.02]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".md,.txt,.pdf,.docx,.xlsx,.pptx"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  onUploadFiles(e.target.files);
                }
              }}
            />
            <UploadCloud className="w-5 h-5 mx-auto text-slate-400" />
            <div className="text-[11px] font-medium text-slate-300 mt-1">
              Dokümanları buraya bırakın
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              PDF, DOCX, XLSX, PPTX, MD, TXT
            </div>
          </div>
        </div>

        {/* Active Indexed Documents */}
        {stats && stats.files.length > 0 && (
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2">
              Aktif Dokümanlar ({stats.files.length})
            </span>
            <div className="mt-1 space-y-1">
              {stats.files.map((file, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between px-2 py-1 rounded bg-white/[0.02] text-[11px] text-slate-300"
                >
                  <div className="flex items-center gap-1.5 truncate">
                    <FileText className="w-3 h-3 text-slate-400 flex-shrink-0" />
                    <span className="truncate">{file.name}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 ml-2 flex-shrink-0">
                    {file.chunks} öbek
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer System Info & Export */}
      <div className="p-3 border-t border-white/5 space-y-2 bg-sidebar">
        <button
          onClick={onExportChat}
          className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs border border-white/5 transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Raporu İndir (.md)
        </button>

        <div className="text-[10px] text-slate-500 space-y-0.5 px-1">
          <div className="flex items-center justify-between">
            <span>🧠 Model:</span>
            <b className="text-slate-400">phi-4-mini</b>
          </div>
          <div className="flex items-center justify-between">
            <span>📐 Vektör:</span>
            <b className="text-slate-400">qwen3-embedding</b>
          </div>
          <div className="flex items-center justify-between">
            <span>🔒 Arama:</span>
            <b className="text-slate-400">Dense + FTS5 BM25</b>
          </div>
        </div>
      </div>
    </aside>
  );
};
