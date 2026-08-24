import React, { useState, useRef } from 'react';
import { ArrowUp, Mic, MicOff, Loader2 } from 'lucide-react';
import { AudioWaveform } from './AudioWaveform';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [speechNotice, setSpeechNotice] = useState<string | null>(null);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const hasRecognizedTextRef = useRef<boolean>(false);

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        160
      )}px`;
    }
  };

  const startListening = async () => {
    setSpeechNotice(null);
    hasRecognizedTextRef.current = false;
    audioChunksRef.current = [];

    try {
      // 1. Mikrofon akışını al
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      // 2. Canlı ses dalgaları için Web Audio API AnalyserNode başlat
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      setAnalyserNode(analyser);

      // 3. Yerel Whisper için MediaRecorder başlat (%100 Çevrimdışı ve Güvenilir)
      try {
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/mp4';

        const recorder = new MediaRecorder(stream, { mimeType });
        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        recorder.onstop = async () => {
          if (audioChunksRef.current.length > 0) {
            const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
            // Eğer Web Speech API metin üretemediyse (ör. Brave kalkanları aktifse), yerel Whisper'a gönder
            if (!hasRecognizedTextRef.current && audioBlob.size > 1000) {
              await sendAudioToLocalWhisper(audioBlob);
            }
          }
        };

        mediaRecorderRef.current = recorder;
        recorder.start(250); // 250ms dilimlerle veri topla
      } catch (recErr) {
        console.warn('MediaRecorder başlatılamadı:', recErr);
      }

      // 4. Paralel olarak Web Speech API varsa başlat (Edge/Chrome için anlık harf harf akış)
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.lang = 'tr-TR';
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.maxAlternatives = 1;

          const baseText = input ? input.trim() + ' ' : '';

          recognition.onresult = (event: any) => {
            let interim = '';
            let final = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
              const t = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                final += t;
              } else {
                interim += t;
              }
            }

            const current = (baseText + final + interim).trimStart();
            if (current.trim()) {
              hasRecognizedTextRef.current = true;
              setInput(current);
              if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
                textareaRef.current.style.height = `${Math.min(
                  textareaRef.current.scrollHeight,
                  160
                )}px`;
              }
            }
          };

          recognition.onerror = (e: any) => {
            console.warn('SpeechRecognition warning:', e.error);
          };

          recognition.onend = () => {
            // Whisper devrede olduğu için hata basmaya gerek yok
          };

          recognitionRef.current = recognition;
          recognition.start();
        } catch (speechErr) {
          console.warn('SpeechRecognition başlatılamadı:', speechErr);
        }
      }

      setIsListening(true);
    } catch (err: any) {
      console.error('Mikrofon erişim hatası:', err);
      setSpeechNotice('Mikrofon erişimine izin verilmedi veya mikrofon bulunamadı.');
      setIsListening(false);
    }
  };

  const sendAudioToLocalWhisper = async (blob: Blob) => {
    setIsTranscribing(true);
    try {
      const formData = new FormData();
      formData.append('audio_file', blob, 'recording.webm');

      const res = await fetch('/api/speech/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        if (data.text && data.text.trim()) {
          const baseText = input ? input.trim() + ' ' : '';
          const fullText = (baseText + data.text.trim()).trimStart();
          setInput(fullText);
          if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(
              textareaRef.current.scrollHeight,
              160
            )}px`;
          }
        }
      }
    } catch (whisperErr) {
      console.error('Yerel Whisper transkripsiyon hatası:', whisperErr);
    } finally {
      setIsTranscribing(false);
    }
  };

  const stopListening = () => {
    setIsListening(false);

    // 1. MediaRecorder'ı durdur (kaydı finalize edip Whisper'a aktarır)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }

    // 2. Web Speech API'yi durdur
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }

    // 3. Web Audio API ve mikrofonu serbest bırak
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }
    setAnalyserNode(null);
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
    if (isListening) {
      stopListening();
    }
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div className="relative max-w-4xl mx-auto w-full px-4">
      {/* Header Visualizer & Notice */}
      <div className="flex items-center justify-between gap-2 mb-2 min-h-[32px]">
        {isListening ? (
          <AudioWaveform analyserNode={analyserNode} isActive={isListening} />
        ) : isTranscribing ? (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Yerel Whisper sesi metne dönüştürüyor...</span>
          </div>
        ) : (
          <div />
        )}

        {speechNotice && (
          <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center justify-between gap-2 shadow-lg backdrop-blur-md animate-in fade-in">
            <span>⚠️ {speechNotice}</span>
            <button
              onClick={() => setSpeechNotice(null)}
              className="text-amber-400 hover:text-white text-[11px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20"
            >
              Tamam
            </button>
          </div>
        )}
      </div>

      <div
        className={`relative flex items-end bg-slate-900/90 border rounded-2xl p-2 shadow-2xl backdrop-blur-xl transition-all duration-300 ${
          isListening
            ? 'border-indigo-500/80 shadow-[0_0_25px_rgba(99,102,241,0.25)] ring-1 ring-indigo-500/40'
            : 'border-white/10 focus-within:border-indigo-500/50'
        }`}
      >
        {/* Microphone Button */}
        <button
          type="button"
          onClick={toggleListening}
          disabled={isTranscribing}
          className={`p-2.5 rounded-xl transition-all duration-300 flex-shrink-0 relative ${
            isListening
              ? 'bg-gradient-to-r from-rose-500 to-indigo-600 text-white shadow-[0_0_15px_rgba(244,63,94,0.6)] animate-pulse'
              : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
          }`}
          title={isListening ? 'Konuşmayı Tamamla (Tıklayın)' : 'Sesli Soru Sor (%100 Yerel Whisper & Waveform)'}
        >
          {isListening ? (
            <MicOff className="w-4 h-4" />
          ) : isTranscribing ? (
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening
              ? 'Konuşun, ses dalgaları canlı algılanıyor (Durdurmak için butona tıklayın)...'
              : isTranscribing
              ? 'Yapay zeka sesinizi metne döküyor...'
              : 'Dokümanlarınız hakkında bir soru yazın (Enter ile gönder)...'
          }
          rows={1}
          disabled={disabled || isTranscribing}
          className="flex-1 bg-transparent border-0 focus:ring-0 text-sm text-slate-100 placeholder-slate-500 resize-none max-h-40 py-2.5 px-3 focus:outline-none"
        />

        {/* Submit Button */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!input.trim() || disabled || isTranscribing}
          className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 disabled:hover:bg-indigo-600 text-white flex-shrink-0 transition-all duration-200 shadow-md shadow-indigo-600/20"
        >
          <ArrowUp className="w-4 h-4" />
        </button>
      </div>

      <div className="text-center text-[11px] text-slate-500 mt-2">
        Zenith AI • Microsoft Foundry Local SDK & Yerel Whisper ile %100 çevrimdışı ve güvenli.
      </div>
    </div>
  );
};
