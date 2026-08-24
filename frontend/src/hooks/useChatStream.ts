import { useState, useCallback } from 'react';
import type { Message, SourceItem } from '../types';

export const useChatStream = (apiBase: string = '') => {
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (
      text: string,
      currentSessionId: string | null,
      setMessages: React.Dispatch<React.SetStateAction<Message[]>>
    ) => {
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
        const response = await fetch(`${apiBase}/api/chat/stream`, {
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
                } else if (data.type === 'error') {
                  setMessages((prev) => {
                    const updated = [...prev];
                    const lastIdx = updated.length - 1;
                    if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
                      updated[lastIdx] = {
                        ...updated[lastIdx],
                        content: data.content || 'Bir hata oluştu.',
                        isStreaming: false,
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
                        content: data.full_text || assistantContent,
                        gen_time: genTime,
                        isStreaming: false,
                      };
                    }
                    return updated;
                  });
                }
              } catch (parseErr) {
                console.error('SSE JSON parse error:', parseErr, line);
              }
            }
          }
        }
      } catch (err: any) {
        console.error('Stream request error:', err);
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: `Bağlantı hatası: ${err.message || 'Sunucuya ulaşılamadı.'}`,
              isStreaming: false,
            };
          }
          return updated;
        });
      } finally {
        setIsStreaming(false);
      }
    },
    [apiBase, isStreaming]
  );

  return {
    isStreaming,
    sendMessage,
  };
};
