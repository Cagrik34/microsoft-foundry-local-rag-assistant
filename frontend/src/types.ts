export interface SourceItem {
  source_file: string;
  chunk_index: number;
  similarity: number;
  relevance: number;
  citation_index: number;
  match_type: string;
  content: string;
}

export interface Message {
  id?: number;
  session_id?: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceItem[];
  search_time?: number;
  gen_time?: number;
  created_at?: string;
  isStreaming?: boolean;
}

export interface Session {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface FileStat {
  name: string;
  chunks: number;
}

export interface DbStats {
  total_chunks: number;
  total_files: number;
  files: FileStat[];
  db_size_mb: number;
}
