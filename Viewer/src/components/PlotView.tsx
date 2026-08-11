import { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import type { Figure } from '../lib/buildTraces.ts';

const CONFIG = {
  displaylogo: false,
  responsive: false, // handled by the ResizeObserver below, which also covers sidebar-driven resizes
  toImageButtonOptions: { format: 'png', filename: 'sdp-bounds', scale: 2 },
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
};

export function PlotView({ figure }: { figure: Figure }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    void Plotly.react(el, figure.data, figure.layout, CONFIG);
  }, [figure]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new ResizeObserver(() => Plotly.Plots.resize(el));
    observer.observe(el);
    return () => {
      observer.disconnect();
      Plotly.purge(el);
    };
  }, []);

  return <div className="plot" ref={ref} />;
}
