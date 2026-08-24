import React, { useEffect, useRef, useState } from 'react';

interface AudioWaveformProps {
  analyserNode: AnalyserNode | null;
  isActive: boolean;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ analyserNode, isActive }) => {
  const [frequencies, setFrequencies] = useState<number[]>([4, 6, 8, 6, 4]);
  const animationFrameRef = useRef<number | null>(null);
  const smoothedHeights = useRef<number[]>([4, 6, 8, 6, 4]);

  useEffect(() => {
    if (!isActive || !analyserNode) {
      setFrequencies([4, 6, 8, 6, 4]);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      return;
    }

    const bufferLength = analyserNode.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const updateWaveform = () => {
      analyserNode.getByteFrequencyData(dataArray);

      // 5 ana vokal frekans bandını örnekle
      const binSize = Math.floor(bufferLength / 8);
      const bins = [
        dataArray[binSize * 1] || 0,
        dataArray[binSize * 2] || 0,
        dataArray[binSize * 3] || 0,
        dataArray[binSize * 4] || 0,
        dataArray[binSize * 5] || 0,
      ];

      // Ses genliğini 4px - 28px aralığında akıcı yumuşat (lerp)
      const newHeights = bins.map((val, idx) => {
        const target = Math.max(4, Math.min(28, (val / 255) * 32));
        const current = smoothedHeights.current[idx] || 4;
        const smoothed = current + (target - current) * 0.4;
        smoothedHeights.current[idx] = smoothed;
        return smoothed;
      });

      setFrequencies([...newHeights]);
      animationFrameRef.current = requestAnimationFrame(updateWaveform);
    };

    animationFrameRef.current = requestAnimationFrame(updateWaveform);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isActive, analyserNode]);

  if (!isActive) return null;

  return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-md animate-in fade-in zoom-in-95 duration-200">
      <span className="text-[11px] font-semibold text-indigo-300 mr-1 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
        Dinleniyor...
      </span>
      <div className="flex items-center gap-0.5 h-6">
        {frequencies.map((height, idx) => (
          <span
            key={idx}
            style={{
              height: `${Math.max(4, height)}px`,
              transition: 'height 50ms cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            className={`w-1 rounded-full ${
              idx === 2
                ? 'bg-gradient-to-t from-indigo-500 via-purple-400 to-cyan-300 shadow-[0_0_8px_rgba(168,85,247,0.8)]'
                : idx === 1 || idx === 3
                ? 'bg-gradient-to-t from-indigo-500 to-purple-400 shadow-[0_0_6px_rgba(99,102,241,0.6)]'
                : 'bg-indigo-400/80 shadow-[0_0_4px_rgba(99,102,241,0.4)]'
            }`}
          />
        ))}
      </div>
    </div>
  );
};
