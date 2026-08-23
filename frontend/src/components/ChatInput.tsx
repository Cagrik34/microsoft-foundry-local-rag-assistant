import React, { useState, useRef } from 'react';
import { ArrowUp, Mic, MicOff } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [speechNotice, setSpeechNotice] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionInstanceRef = useRef<any>(null);

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechNotice(
        'Tarayıcınız Web Speech API ses tanıma özelliğini desteklemiyor. Lütfen Google Chrome veya Microsoft Edge kullanın.'
      );
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'tr-TR';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      let previousText = input ? input + ' ' : '';

      recognition.onstart = () => {
        setIsListening(true);
        setSpeechNotice(null);
      };

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const currentText = previousText + finalTranscript + interimTranscript;
        setInput(currentText);

        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.style.height = `${Math.min(
            textareaRef.current.scrollHeight,
            160
          )}px`;
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition event error:', event.error);
        setIsListening(false);

        if (event.error === 'not-allowed') {
          setSpeechNotice(
            'Mikrofon izni verilmedi. Lütfen adres çubuğundaki kilit simgesine tıklayıp mikrofon iznini verin.'
          );
        } else if (
          event.error === 'service-not-allowed' ||
          event.error === 'network'
        ) {
          setSpeechNotice(
            'Brave tarayıcısı kullanıyorsanız: brave://settings/privacy sayfasına gidip "Ses tanıma için Google servislerini kullan" seçeneğini aktif edin veya Microsoft Edge / Chrome kullanın.'
          );
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionInstanceRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.error('Speech recognition start error:', err);
      setIsListening(false);
    }
  };

  const stopListening = () => {
    if (recognitionInstanceRef.current) {
      try {
        recognitionInstanceRef.current.stop();
      } catch (e) {}
    }
    setIsListening(false);
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  return (
    <div className="relative max-w-4xl mx-auto w-full px-4">
      {speechNotice && (
        <div className="mb-2 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center justify-between gap-2 shadow-lg backdrop-blur-md animate-in fade-in slide-in-from-bottom-2">
          <span>⚠️ {speechNotice}</span>
          <button
            onClick={() => setSpeechNotice(null)}
            className="text-amber-400 hover:text-white text-[11px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20"
          >
            Tamam
          </button>
        </div>
      )}

      <div className="relative flex items-end bg-slate-900/90 border border-white/10 focus-within:border-indigo-500/50 rounded-2xl p-2 shadow-2xl backdrop-blur-xl transition-all duration-200">
        {/* Microphone Button */}
        <button
          type="button"
          onClick={toggleListening}
          className={`p-2.5 rounded-xl transition-all duration-200 flex-shrink-0 ${
            isListening
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
              : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
          }`}
          title={isListening ? 'Dinleniyor... (Durdurmak için tıklayın)' : 'Sesli Soru Sor (Mikrofon)'}
        >
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening
              ? 'Konuşun, dinleniyor...'
              : 'Dokümanlarınız hakkında bir soru yazın (Enter ile gönder)...'
          }
          rows={1}
          disabled={disabled}
          className="flex-1 bg-transparent border-0 focus:ring-0 text-sm text-slate-100 placeholder-slate-500 resize-none max-h-40 py-2.5 px-3 focus:outline-none"
        />

        {/* Submit Button */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:hover:bg-indigo-600 text-white flex-shrink-0 transition-all duration-200 shadow-md shadow-indigo-600/20"
        >
          <ArrowUp className="w-4 h-4" />
        </button>
      </div>

      <div className="text-center text-[11px] text-slate-500 mt-2">
        Zenith AI • Microsoft Foundry Local SDK ile %100 yerel ve güvenli çıkarım.
      </div>
    </div>
  );
};
