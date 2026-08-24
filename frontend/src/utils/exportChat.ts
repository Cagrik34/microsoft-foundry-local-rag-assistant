import type { Message } from '../types';

export const exportChatToMarkdown = (messages: Message[]): void => {
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
    if (m.search_time !== undefined && m.gen_time !== undefined) {
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
