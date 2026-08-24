import { useState, useCallback } from 'react';
import type { Session, Message } from '../types';

export const useSessions = (apiBase: string = '') => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Load message history for a specific session
  const selectSession = useCallback(async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    try {
      const res = await fetch(`${apiBase}/api/sessions/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (err) {
      console.error('Messages fetch error:', err);
    }
  }, [apiBase]);

  // Fetch all chat sessions
  const fetchSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const res = await fetch(`${apiBase}/api/sessions`);
      if (res.ok) {
        const data: Session[] = await res.json();
        setSessions(data);
        if (data.length > 0 && !currentSessionId) {
          await selectSession(data[0].session_id);
        } else if (data.length === 0 && !currentSessionId) {
          // Auto create initial session
          const initRes = await fetch(`${apiBase}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'Analiz #1' }),
          });
          if (initRes.ok) {
            const initData = await initRes.json();
            setCurrentSessionId(initData.session_id);
            setMessages([]);
            setSessions([{
              session_id: initData.session_id,
              title: 'Analiz #1',
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            }]);
          }
        }
      }
    } catch (err) {
      console.error('Sessions fetch error:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  }, [apiBase, currentSessionId, selectSession]);

  // Create a new session
  const createNewSession = useCallback(async () => {
    try {
      const title = `Analiz #${sessions.length + 1}`;
      const res = await fetch(`${apiBase}/api/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentSessionId(data.session_id);
        setMessages([]);
        await fetchSessions();
      }
    } catch (err) {
      console.error('Create session error:', err);
    }
  }, [apiBase, sessions.length, fetchSessions]);

  // Delete a session
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await fetch(`${apiBase}/api/sessions/${sessionId}`, { method: 'DELETE' });
      const updated = sessions.filter((s) => s.session_id !== sessionId);
      setSessions(updated);
      if (currentSessionId === sessionId) {
        if (updated.length > 0) {
          await selectSession(updated[0].session_id);
        } else {
          await createNewSession();
        }
      }
    } catch (err) {
      console.error('Delete session error:', err);
    }
  }, [apiBase, sessions, currentSessionId, selectSession, createNewSession]);

  return {
    sessions,
    currentSessionId,
    messages,
    setMessages,
    setCurrentSessionId,
    isLoadingSessions,
    fetchSessions,
    selectSession,
    createNewSession,
    deleteSession,
  };
};
