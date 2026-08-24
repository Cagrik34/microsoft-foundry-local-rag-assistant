import { useState, useCallback } from 'react';
import type { DbStats } from '../types';

export const useDbStats = (apiBase: string = '') => {
  const [stats, setStats] = useState<DbStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/stats`);
      if (res.ok) {
        const data: DbStats = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Stats fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [apiBase]);

  return {
    stats,
    isLoading,
    fetchStats,
  };
};
