import { useState, useCallback } from 'react';

export const useDocumentIngest = (apiBase: string = '') => {
  const [isIngesting, setIsIngesting] = useState(false);

  // Trigger manual document re-indexing
  const handleIngest = useCallback(async (onSuccess?: () => Promise<void> | void) => {
    setIsIngesting(true);
    try {
      const res = await fetch(`${apiBase}/api/documents/ingest`, { method: 'POST' });
      if (res.ok && onSuccess) {
        await onSuccess();
      }
    } catch (err) {
      console.error('Ingest error:', err);
    } finally {
      setIsIngesting(false);
    }
  }, [apiBase]);

  // Clear database and reset index
  const handleClearDb = useCallback(async (onSuccess?: () => Promise<void> | void) => {
    if (!window.confirm('Tüm indekslenmiş veritabanı silinecek. Emin misiniz?')) {
      return;
    }
    try {
      const res = await fetch(`${apiBase}/api/database`, { method: 'DELETE' });
      if (res.ok && onSuccess) {
        await onSuccess();
      }
    } catch (err) {
      console.error('Clear DB error:', err);
    }
  }, [apiBase]);

  // Upload files securely
  const handleUploadFiles = useCallback(async (fileList: FileList, onSuccess?: () => Promise<void> | void) => {
    if (!fileList || fileList.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }

    setIsIngesting(true);
    try {
      const res = await fetch(`${apiBase}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok && onSuccess) {
        await onSuccess();
      }
    } catch (err) {
      console.error('Upload error:', err);
    } finally {
      setIsIngesting(false);
    }
  }, [apiBase]);

  return {
    isIngesting,
    handleIngest,
    handleClearDb,
    handleUploadFiles,
  };
};
