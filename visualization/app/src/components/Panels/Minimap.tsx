import { useRef, useEffect } from 'react';
import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';
import { getNodeTypeInfo } from '../Palette/nodeRegistry';

const MM_W = 180;
const MM_H = 130;

const CAT_COLORS: Record<string, string> = {
  composite: '#4ec9b0', decorator: '#dcdcaa', action: '#4c9eff', condition: '#c586c0', custom: '#ce9178',
};

export function Minimap() {
  const ref = useRef<HTMLCanvasElement>(null);
  const nodes = useTreeStore(s => s.nodes);
  const { zoom, panX, panY, setPan } = useUIStore();

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = MM_W * dpr;
    canvas.height = MM_H * dpr;
    ctx.scale(dpr, dpr);

    ctx.fillStyle = 'rgba(15,17,23,0.9)';
    ctx.fillRect(0, 0, MM_W, MM_H);

    const nodeList = Object.values(nodes);
    if (nodeList.length === 0) return;

    // Calculate bounds
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of nodeList) {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.width);
      maxY = Math.max(maxY, n.y + n.height);
    }
    const pad = 40;
    minX -= pad; minY -= pad; maxX += pad; maxY += pad;

    const scaleX = MM_W / (maxX - minX);
    const scaleY = MM_H / (maxY - minY);
    const s = Math.min(scaleX, scaleY);

    // Draw nodes
    for (const n of nodeList) {
      const info = getNodeTypeInfo(n.nodeType);
      ctx.fillStyle = CAT_COLORS[info?.category || 'action'] || '#4c9eff';
      ctx.globalAlpha = 0.7;
      ctx.fillRect((n.x - minX) * s, (n.y - minY) * s, Math.max(n.width * s, 3), Math.max(n.height * s, 2));
    }
    ctx.globalAlpha = 1;

    // Draw viewport rect
    const vx = (-panX / zoom - minX) * s;
    const vy = (-panY / zoom - minY) * s;
    const vw = (window.innerWidth / zoom) * s;
    const vh = (window.innerHeight / zoom) * s;
    ctx.strokeStyle = 'rgba(76,158,255,0.6)';
    ctx.lineWidth = 1;
    ctx.strokeRect(vx, vy, vw, vh);
  }, [nodes, zoom, panX, panY]);

  const handleClick = (e: React.MouseEvent) => {
    const rect = ref.current!.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const nodeList = Object.values(nodes);
    if (nodeList.length === 0) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of nodeList) { minX = Math.min(minX, n.x); minY = Math.min(minY, n.y); maxX = Math.max(maxX, n.x + n.width); maxY = Math.max(maxY, n.y + n.height); }
    const pad = 40; minX -= pad; minY -= pad; maxX += pad; maxY += pad;
    const s = Math.min(MM_W / (maxX - minX), MM_H / (maxY - minY));

    const worldX = mx / s + minX;
    const worldY = my / s + minY;
    setPan(-worldX * zoom + window.innerWidth / 2, -worldY * zoom + window.innerHeight / 2);
  };

  return (
    <div style={{
      position: 'absolute', bottom: 8, right: 8, borderRadius: 'var(--r-md)',
      border: '1px solid var(--border-1)', overflow: 'hidden', zIndex: 50,
      boxShadow: '0 4px 16px rgba(0,0,0,0.4)', cursor: 'pointer',
    }}>
      <canvas ref={ref} width={MM_W} height={MM_H} style={{ width: MM_W, height: MM_H, display: 'block' }} onClick={handleClick} />
    </div>
  );
}
