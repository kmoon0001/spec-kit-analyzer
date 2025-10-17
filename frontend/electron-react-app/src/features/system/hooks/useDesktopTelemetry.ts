import { useEffect, useMemo, useState } from 'react';

const MAX_HISTORY = 90;

const isDesktopRuntime = () => typeof window !== 'undefined' && Boolean(window.desktopApi?.tasks);

type DerivedTelemetryMetrics = {
  cpuPercent: number | null;
  memoryMb: number | null;
  eventLoopP99: number | null;
  activeCount: number;
  queueSize: number;
};

export const useDesktopTelemetry = () => {
  const [snapshot, setSnapshot] = useState<DesktopTelemetrySnapshot | null>(null);
  const [history, setHistory] = useState<DesktopTelemetrySnapshot[]>([]);

  useEffect(() => {
    if (!isDesktopRuntime()) {
      return undefined;
    }

    const unsubscribe = window.desktopApi!.tasks.on('telemetry', (payload) => {
      setSnapshot(payload);
      setHistory((prev) => {
        const next = [...prev, payload];
        if (next.length > MAX_HISTORY) {
          next.splice(0, next.length - MAX_HISTORY);
        }
        return next;
      });
    });

    return () => {
      try {
        unsubscribe?.();
      } catch (error) {
        console.warn('Failed to unsubscribe telemetry listener', error);
      }
    };
  }, []);

  const metrics: DerivedTelemetryMetrics = useMemo(() => {
    const cpuPercent = snapshot?.cpu
      ? snapshot.cpu.normalizedPercent ?? snapshot.cpu.percent ?? null
      : null;
    const memoryMb = snapshot?.memory?.rss ? snapshot.memory.rss / 1024 / 1024 : null;
    const eventLoopP99 = snapshot?.eventLoop?.p99 ?? null;
    const activeCount = snapshot?.activeCount ?? 0;
    const queueSize = snapshot?.queueSize ?? 0;
    return { cpuPercent, memoryMb, eventLoopP99, activeCount, queueSize };
  }, [snapshot]);

  return {
    snapshot,
    history,
    metrics,
    lastUpdatedAt: snapshot?.timestamp ?? null,
    isSupported: isDesktopRuntime(),
  };
};
