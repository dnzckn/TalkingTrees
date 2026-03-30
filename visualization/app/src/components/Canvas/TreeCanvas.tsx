import { useRef, useEffect, useCallback, useState } from 'react';
import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';
import { getNodeTypeInfo } from '../Palette/nodeRegistry';
import type { CanvasNode, NodeCategory } from '../../types/tree';

const NODE_W = 180;
const NODE_H = 68;
const PORT_R = 5;
const V_GAP = 100;

const CAT_COLORS: Record<string, string> = {
  composite: '#4ec9b0', decorator: '#dcdcaa', action: '#4c9eff',
  condition: '#c586c0', custom: '#ce9178',
};
const STATUS_COLORS: Record<string, string> = {
  SUCCESS: '#3dd68c', FAILURE: '#ff5c5c', RUNNING: '#ffc145',
};
const TYPE_OVERRIDE: Record<string, string> = {
  SubTreeRef: '#9b59b6', AsyncAction: '#e67e22', RemoteSubtree: '#9b59b6',
  RateLimiter: '#ff6b6b', AcquireResource: '#3dd68c', ReleaseResource: '#3dd68c',
  Debounce: '#f39c12', WindowedAggregator: '#3498db',
};

function nodeColor(n: CanvasNode): string {
  if (n.status && STATUS_COLORS[n.status]) return STATUS_COLORS[n.status];
  if (TYPE_OVERRIDE[n.nodeType]) return TYPE_OVERRIDE[n.nodeType];
  const info = getNodeTypeInfo(n.nodeType);
  return CAT_COLORS[info?.category || 'action'] || CAT_COLORS.action;
}

export function TreeCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { nodes, selectedIds, selectNode, clearSelection, addNode, setParent, updateNode } = useTreeStore();
  const { zoom, panX, panY, setZoom, setPan, showGrid, showDataflow } = useUIStore();

  const [dragging, setDragging] = useState<{ id: string; ox: number; oy: number } | null>(null);
  const [panning, setPanning] = useState<{ sx: number; sy: number } | null>(null);
  const [connecting, setConnecting] = useState<{ fromId: string; mx: number; my: number } | null>(null);

  const toWorld = useCallback((sx: number, sy: number) => ({
    x: (sx - panX) / zoom, y: (sy - panY) / zoom,
  }), [panX, panY, zoom]);

  const nodeList = Object.values(nodes);

  // ── Hit testing ──
  const hitNode = useCallback((wx: number, wy: number): CanvasNode | null => {
    for (let i = nodeList.length - 1; i >= 0; i--) {
      const n = nodeList[i];
      if (wx >= n.x && wx <= n.x + NODE_W && wy >= n.y && wy <= n.y + NODE_H) return n;
    }
    return null;
  }, [nodeList]);

  const hitBottomPort = useCallback((wx: number, wy: number): CanvasNode | null => {
    for (const n of nodeList) {
      const px = n.x + NODE_W / 2, py = n.y + NODE_H;
      if (Math.hypot(wx - px, wy - py) < PORT_R + 4) return n;
    }
    return null;
  }, [nodeList]);

  const hitTopPort = useCallback((wx: number, wy: number): CanvasNode | null => {
    for (const n of nodeList) {
      const px = n.x + NODE_W / 2, py = n.y;
      if (Math.hypot(wx - px, wy - py) < PORT_R + 4) return n;
    }
    return null;
  }, [nodeList]);

  // ── Render ──
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    // Background
    const bg = getComputedStyle(document.documentElement).getPropertyValue('--surface-0').trim() || '#0f1117';
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, rect.width, rect.height);

    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(zoom, zoom);

    // Grid
    if (showGrid) {
      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      ctx.lineWidth = 1;
      const gs = 50;
      const sx = Math.floor(-panX / zoom / gs) * gs - gs;
      const sy = Math.floor(-panY / zoom / gs) * gs - gs;
      for (let x = sx; x < sx + rect.width / zoom + gs * 2; x += gs) {
        ctx.beginPath(); ctx.moveTo(x, sy); ctx.lineTo(x, sy + rect.height / zoom + gs * 2); ctx.stroke();
      }
      for (let y = sy; y < sy + rect.height / zoom + gs * 2; y += gs) {
        ctx.beginPath(); ctx.moveTo(sx, y); ctx.lineTo(sx + rect.width / zoom + gs * 2, y); ctx.stroke();
      }
    }

    // Connections
    for (const node of nodeList) {
      for (const childId of node.childIds) {
        const child = nodes[childId];
        if (!child) continue;
        const sx = node.x + NODE_W / 2, sy = node.y + NODE_H;
        const ex = child.x + NODE_W / 2, ey = child.y;
        const my = sy + (ey - sy) * 0.5;

        ctx.strokeStyle = selectedIds.has(node.id) || selectedIds.has(childId) ? 'rgba(76,158,255,0.6)' : 'rgba(255,255,255,0.15)';
        ctx.lineWidth = selectedIds.has(node.id) || selectedIds.has(childId) ? 2 : 1.5;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.bezierCurveTo(sx, my, ex, my, ex, ey);
        ctx.stroke();
      }
    }

    // Dataflow arrows
    if (showDataflow) {
      for (const n of nodeList) {
        if (!n.blackboardOutput) continue;
        for (const other of nodeList) {
          if (other.id === n.id || !other.blackboardInput) continue;
          const shared = Object.keys(n.blackboardOutput!).filter(k => other.blackboardInput![k]);
          if (shared.length > 0) {
            ctx.strokeStyle = 'rgba(76,158,255,0.3)';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 3]);
            ctx.beginPath();
            ctx.moveTo(n.x + NODE_W, n.y + NODE_H / 2);
            ctx.lineTo(other.x, other.y + NODE_H / 2);
            ctx.stroke();
            ctx.setLineDash([]);
          }
        }
      }
    }

    // Active connection drag line
    if (connecting) {
      ctx.strokeStyle = 'rgba(76,158,255,0.8)';
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      const from = nodes[connecting.fromId];
      if (from) {
        ctx.beginPath();
        ctx.moveTo(from.x + NODE_W / 2, from.y + NODE_H);
        ctx.lineTo(connecting.mx, connecting.my);
        ctx.stroke();
      }
      ctx.setLineDash([]);
    }

    // Nodes
    for (const node of nodeList) {
      drawNode(ctx, node, selectedIds.has(node.id));
    }

    ctx.restore();
  }, [nodes, nodeList, selectedIds, zoom, panX, panY, showGrid, showDataflow, connecting]);

  useEffect(() => {
    let raf: number;
    const loop = () => { render(); raf = requestAnimationFrame(loop); };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [render]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver(() => render());
    observer.observe(container);
    return () => observer.disconnect();
  }, [render]);

  // ── Mouse handlers ──
  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const w = toWorld(sx, sy);

    if (e.button === 1 || (e.button === 0 && e.altKey)) {
      setPanning({ sx: e.clientX, sy: e.clientY });
      return;
    }
    if (e.button !== 0) return;

    // Check bottom port hit (start connection)
    const portNode = hitBottomPort(w.x, w.y);
    if (portNode) {
      setConnecting({ fromId: portNode.id, mx: w.x, my: w.y });
      return;
    }

    const hit = hitNode(w.x, w.y);
    if (hit) {
      selectNode(hit.id, e.shiftKey);
      setDragging({ id: hit.id, ox: w.x - hit.x, oy: w.y - hit.y });
    } else {
      clearSelection();
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const w = toWorld(sx, sy);

    if (panning) {
      const dx = e.clientX - panning.sx, dy = e.clientY - panning.sy;
      setPan(panX + dx, panY + dy);
      setPanning({ sx: e.clientX, sy: e.clientY });
      return;
    }

    if (connecting) {
      setConnecting({ ...connecting, mx: w.x, my: w.y });
      return;
    }

    if (dragging) {
      updateNode(dragging.id, { x: w.x - dragging.ox, y: w.y - dragging.oy });
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (connecting) {
      const rect = canvasRef.current!.getBoundingClientRect();
      const w = toWorld(e.clientX - rect.left, e.clientY - rect.top);
      const target = hitTopPort(w.x, w.y) || hitNode(w.x, w.y);
      if (target && target.id !== connecting.fromId) {
        setParent(target.id, connecting.fromId);
      }
      setConnecting(null);
      return;
    }
    setDragging(null);
    setPanning(null);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const rect = canvasRef.current!.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const factor = e.deltaY > 0 ? 0.92 : 1.08;
    const newZoom = Math.max(0.1, Math.min(5, zoom * factor));
    // Zoom toward cursor
    const wx = (mx - panX) / zoom, wy = (my - panY) / zoom;
    setPan(mx - wx * newZoom, my - wy * newZoom);
    setZoom(newZoom);
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    const rect = canvasRef.current!.getBoundingClientRect();
    const w = toWorld(e.clientX - rect.left, e.clientY - rect.top);
    const hit = hitNode(w.x, w.y);
    window.dispatchEvent(new CustomEvent('tree-context-menu', {
      detail: { x: e.clientX, y: e.clientY, nodeId: hit?.id || null, worldX: w.x, worldY: w.y },
    }));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('application/json');
    if (!data) return;
    try {
      const info = JSON.parse(data);
      const rect = canvasRef.current!.getBoundingClientRect();
      const w = toWorld(e.clientX - rect.left, e.clientY - rect.top);
      addNode({ nodeType: info.type, name: info.displayName, config: { ...info.defaultConfig }, x: w.x - NODE_W / 2, y: w.y - NODE_H / 2 });
    } catch { /* ignore */ }
  };

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', cursor: panning ? 'grabbing' : connecting ? 'crosshair' : dragging ? 'move' : 'default' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => { setDragging(null); setPanning(null); setConnecting(null); }}
        onWheel={handleWheel}
        onContextMenu={handleContextMenu}
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }}
      />
    </div>
  );
}

// ── Node rendering ──
function drawNode(ctx: CanvasRenderingContext2D, node: CanvasNode, selected: boolean) {
  const { x, y } = node;
  const color = nodeColor(node);
  const info = getNodeTypeInfo(node.nodeType);

  // Shadow
  if (selected) {
    ctx.shadowColor = 'rgba(76,158,255,0.4)';
    ctx.shadowBlur = 16;
  }

  // Body
  ctx.fillStyle = selected ? 'rgba(76,158,255,0.08)' : 'rgba(255,255,255,0.03)';
  ctx.strokeStyle = selected ? '#4c9eff' : 'rgba(255,255,255,0.08)';
  ctx.lineWidth = selected ? 1.5 : 1;
  roundRect(ctx, x, y, NODE_W, NODE_H, 6);
  ctx.fill();
  ctx.stroke();

  ctx.shadowColor = 'transparent';
  ctx.shadowBlur = 0;

  // Top color accent
  ctx.fillStyle = color;
  ctx.fillRect(x + 1, y + 1, NODE_W - 2, 3);

  // Connection ports
  // Top port (input) — small circle
  ctx.fillStyle = 'var(--surface-3)' in {} ? '#242832' : '#2c313d';
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(x + NODE_W / 2, y, PORT_R, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Bottom port (output)
  ctx.beginPath();
  ctx.arc(x + NODE_W / 2, y + NODE_H, PORT_R, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Icon
  if (info?.icon) {
    ctx.fillStyle = color;
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(info.icon, x + 10, y + 28);
  }

  // Name
  ctx.fillStyle = '#e8eaed';
  ctx.font = "600 12px 'IBM Plex Sans', sans-serif";
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(truncate(node.name, 18), x + 30, y + 26);

  // Type
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.font = "11px 'IBM Plex Sans', sans-serif";
  ctx.fillText(node.nodeType, x + 30, y + 44);

  // Status badge
  if (node.status) {
    const sc = STATUS_COLORS[node.status] || '#7c818c';
    ctx.fillStyle = sc;
    ctx.beginPath();
    ctx.arc(x + NODE_W - 14, y + 14, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  // Macro badge
  if (node.macro) {
    ctx.fillStyle = node.macro.color || color;
    const bx = x + NODE_W - 32, by = y + NODE_H - 16;
    ctx.fillRect(bx, by, 24, 12);
    ctx.fillStyle = '#fff';
    ctx.font = "bold 8px 'IBM Plex Sans', sans-serif";
    ctx.textAlign = 'center';
    ctx.fillText('M', bx + 12, by + 9);
  }

  // BB port indicators
  if (node.blackboardInput) {
    ctx.fillStyle = '#4c9eff';
    ctx.beginPath(); ctx.arc(x + 3, y + NODE_H / 2, 3, 0, Math.PI * 2); ctx.fill();
  }
  if (node.blackboardOutput) {
    ctx.fillStyle = '#3dd68c';
    ctx.beginPath(); ctx.arc(x + NODE_W - 3, y + NODE_H / 2, 3, 0, Math.PI * 2); ctx.fill();
  }

  // Child count badge for composites
  if (node.childIds.length > 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.font = "10px 'IBM Plex Mono', monospace";
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${node.childIds.length}`, x + NODE_W - 10, y + 56);
  }

  ctx.textAlign = 'start';
  ctx.textBaseline = 'alphabetic';
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max - 1) + '…' : s;
}
