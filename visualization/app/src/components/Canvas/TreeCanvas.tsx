import { useRef, useEffect, useCallback, useState } from 'react';
import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';
import { useSimStore } from '../../store/simulationStore';
import { getNodeTypeInfo } from '../Palette/nodeRegistry';
import type { CanvasNode } from '../../types/tree';

const NODE_W = 190;
const NODE_H = 72;
const PORT_R = 6;

// ── Color system ──
const CAT_BG: Record<string, [string, string]> = {
  // [fill, accent]
  composite: ['#1a2f2c', '#4ec9b0'],
  decorator: ['#2a2820', '#dcdcaa'],
  action:    ['#1a2535', '#4c9eff'],
  condition: ['#2a1f2d', '#c586c0'],
  custom:    ['#2a2420', '#ce9178'],
};

const STATUS_COLORS: Record<string, string> = {
  SUCCESS: '#3dd68c', FAILURE: '#ff5c5c', RUNNING: '#ffc145',
};
const STATUS_BG: Record<string, string> = {
  SUCCESS: '#1a2f22', FAILURE: '#2f1a1a', RUNNING: '#2f2a1a',
};

const TYPE_OVERRIDE: Record<string, string> = {
  SubTreeRef: '#9b59b6', AsyncAction: '#e67e22', RemoteSubtree: '#9b59b6',
  RateLimiter: '#ff6b6b', AcquireResource: '#3dd68c', ReleaseResource: '#3dd68c',
  Debounce: '#f39c12', WindowedAggregator: '#3498db',
};

function nodeAccent(n: CanvasNode): string {
  if (n.status && STATUS_COLORS[n.status]) return STATUS_COLORS[n.status];
  if (TYPE_OVERRIDE[n.nodeType]) return TYPE_OVERRIDE[n.nodeType];
  const info = getNodeTypeInfo(n.nodeType);
  return CAT_BG[info?.category || 'action']?.[1] || '#4c9eff';
}

function nodeFill(n: CanvasNode): string {
  if (n.status && STATUS_BG[n.status]) return STATUS_BG[n.status];
  const info = getNodeTypeInfo(n.nodeType);
  return CAT_BG[info?.category || 'action']?.[0] || '#1a2535';
}

export function TreeCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const store = useTreeStore();
  const { nodes, selectedIds, selectNode, clearSelection, addNode, setParent, updateNode } = store;
  const { zoom, panX, panY, setZoom, setPan, showGrid, showDataflow } = useUIStore();
  const simRunning = useSimStore(s => s.running);
  const simTick = useSimStore(s => s.tick);

  const [dragging, setDragging] = useState<{ id: string; ox: number; oy: number } | null>(null);
  const [panning, setPanning] = useState<{ sx: number; sy: number } | null>(null);
  const [connecting, setConnecting] = useState<{ fromId: string; mx: number; my: number } | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [boxSelect, setBoxSelect] = useState<{ sx: number; sy: number; ex: number; ey: number } | null>(null);

  const toWorld = useCallback((sx: number, sy: number) => ({
    x: (sx - panX) / zoom, y: (sy - panY) / zoom,
  }), [panX, panY, zoom]);

  const nodeList = Object.values(nodes);

  const hitNode = useCallback((wx: number, wy: number): CanvasNode | null => {
    for (let i = nodeList.length - 1; i >= 0; i--) {
      const n = nodeList[i];
      if (wx >= n.x && wx <= n.x + NODE_W && wy >= n.y && wy <= n.y + NODE_H) return n;
    }
    return null;
  }, [nodeList]);

  const hitBottomPort = useCallback((wx: number, wy: number): CanvasNode | null => {
    for (const n of nodeList) {
      if (Math.hypot(wx - (n.x + NODE_W / 2), wy - (n.y + NODE_H)) < PORT_R + 5) return n;
    }
    return null;
  }, [nodeList]);

  const hitTopPort = useCallback((wx: number, wy: number): CanvasNode | null => {
    for (const n of nodeList) {
      if (Math.hypot(wx - (n.x + NODE_W / 2), wy - n.y) < PORT_R + 5) return n;
    }
    return null;
  }, [nodeList]);

  // ══════════════════ RENDER ══════════════════
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

    // Background with subtle radial gradient
    ctx.fillStyle = '#0f1117';
    ctx.fillRect(0, 0, rect.width, rect.height);
    const grad = ctx.createRadialGradient(rect.width / 2, rect.height / 2, 0, rect.width / 2, rect.height / 2, rect.width * 0.7);
    grad.addColorStop(0, 'rgba(30,35,50,0.3)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, rect.width, rect.height);

    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(zoom, zoom);

    // ── Dot grid ──
    if (showGrid) {
      const gs = 30;
      const sx = Math.floor(-panX / zoom / gs) * gs;
      const sy = Math.floor(-panY / zoom / gs) * gs;
      ctx.fillStyle = 'rgba(255,255,255,0.07)';
      for (let x = sx; x < sx + rect.width / zoom + gs; x += gs) {
        for (let y = sy; y < sy + rect.height / zoom + gs; y += gs) {
          ctx.beginPath();
          ctx.arc(x, y, 0.8, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    // ── Connections ──
    for (const node of nodeList) {
      for (const childId of node.childIds) {
        const child = nodes[childId];
        if (!child) continue;
        const x1 = node.x + NODE_W / 2, y1 = node.y + NODE_H;
        const x2 = child.x + NODE_W / 2, y2 = child.y;
        const cp = (y2 - y1) * 0.45;
        const isSel = selectedIds.has(node.id) || selectedIds.has(childId);

        // Wire shadow
        ctx.strokeStyle = 'rgba(0,0,0,0.3)';
        ctx.lineWidth = isSel ? 4 : 3;
        ctx.beginPath();
        ctx.moveTo(x1, y1); ctx.bezierCurveTo(x1, y1 + cp, x2, y2 - cp, x2, y2);
        ctx.stroke();

        // Wire color
        const accent = nodeAccent(node);
        ctx.strokeStyle = isSel ? 'rgba(76,158,255,0.7)' : accent + '55';
        ctx.lineWidth = isSel ? 2.5 : 2;

        // Animated dash during simulation
        if (simRunning && node.status) {
          ctx.setLineDash([8, 4]);
          ctx.lineDashOffset = -simTick * 3;
        }

        ctx.beginPath();
        ctx.moveTo(x1, y1); ctx.bezierCurveTo(x1, y1 + cp, x2, y2 - cp, x2, y2);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.lineDashOffset = 0;
      }
    }

    // ── Dataflow arrows ──
    if (showDataflow) {
      for (const n of nodeList) {
        if (!n.blackboardOutput) continue;
        for (const other of nodeList) {
          if (other.id === n.id || !other.blackboardInput) continue;
          const shared = Object.keys(n.blackboardOutput!).filter(k => other.blackboardInput![k]);
          if (shared.length > 0) {
            ctx.strokeStyle = 'rgba(76,158,255,0.25)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([6, 3]);
            ctx.beginPath();
            ctx.moveTo(n.x + NODE_W, n.y + NODE_H / 2);
            ctx.lineTo(other.x, other.y + NODE_H / 2);
            ctx.stroke();
            ctx.setLineDash([]);
            // Arrow head
            const ax = other.x - 6, ay = other.y + NODE_H / 2;
            ctx.fillStyle = 'rgba(76,158,255,0.25)';
            ctx.beginPath();
            ctx.moveTo(other.x, ay); ctx.lineTo(ax, ay - 4); ctx.lineTo(ax, ay + 4);
            ctx.fill();
          }
        }
      }
    }

    // ── Connection drag line ──
    if (connecting) {
      const from = nodes[connecting.fromId];
      if (from) {
        ctx.strokeStyle = '#4c9eff';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 4]);
        ctx.beginPath();
        ctx.moveTo(from.x + NODE_W / 2, from.y + NODE_H);
        ctx.lineTo(connecting.mx, connecting.my);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // ── Box selection ──
    if (boxSelect) {
      ctx.fillStyle = 'rgba(76,158,255,0.08)';
      ctx.strokeStyle = 'rgba(76,158,255,0.4)';
      ctx.lineWidth = 1;
      const bx = Math.min(boxSelect.sx, boxSelect.ex), by = Math.min(boxSelect.sy, boxSelect.ey);
      const bw = Math.abs(boxSelect.ex - boxSelect.sx), bh = Math.abs(boxSelect.ey - boxSelect.sy);
      ctx.fillRect(bx, by, bw, bh);
      ctx.strokeRect(bx, by, bw, bh);
    }

    // ── Nodes ──
    for (const node of nodeList) {
      drawNode(ctx, node, selectedIds.has(node.id), hoveredId === node.id, simRunning);
    }

    // ── Empty state ──
    if (nodeList.length === 0) {
      ctx.restore();
      ctx.fillStyle = 'rgba(255,255,255,0.15)';
      ctx.font = "500 16px 'IBM Plex Sans', sans-serif";
      ctx.textAlign = 'center';
      ctx.fillText('Drag nodes from the palette or right-click to start', rect.width / 2, rect.height / 2 - 10);
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.font = "12px 'IBM Plex Sans', sans-serif";
      ctx.fillText('Ctrl+Shift+P for command palette  |  F1 for shortcuts', rect.width / 2, rect.height / 2 + 14);
      return;
    }

    ctx.restore();
  }, [nodes, nodeList, selectedIds, zoom, panX, panY, showGrid, showDataflow, connecting, hoveredId, simRunning, simTick, boxSelect]);

  useEffect(() => {
    let raf: number;
    const loop = () => { render(); raf = requestAnimationFrame(loop); };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [render]);

  useEffect(() => {
    const c = containerRef.current;
    if (!c) return;
    const obs = new ResizeObserver(() => render());
    obs.observe(c);
    return () => obs.disconnect();
  }, [render]);

  // ══════════════════ MOUSE ══════════════════
  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const w = toWorld(sx, sy);

    if (e.button === 1 || (e.button === 0 && e.altKey)) {
      setPanning({ sx: e.clientX, sy: e.clientY }); return;
    }
    if (e.button !== 0) return;

    const portNode = hitBottomPort(w.x, w.y);
    if (portNode) { setConnecting({ fromId: portNode.id, mx: w.x, my: w.y }); return; }

    const hit = hitNode(w.x, w.y);
    if (hit) {
      selectNode(hit.id, e.shiftKey);
      setDragging({ id: hit.id, ox: w.x - hit.x, oy: w.y - hit.y });
    } else {
      clearSelection();
      // Start box selection
      setBoxSelect({ sx: w.x, sy: w.y, ex: w.x, ey: w.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const w = toWorld(e.clientX - rect.left, e.clientY - rect.top);

    // Hover detection
    const hovered = hitNode(w.x, w.y);
    setHoveredId(hovered?.id || null);

    if (panning) {
      setPan(panX + e.clientX - panning.sx, panY + e.clientY - panning.sy);
      setPanning({ sx: e.clientX, sy: e.clientY }); return;
    }
    if (connecting) { setConnecting({ ...connecting, mx: w.x, my: w.y }); return; }
    if (boxSelect) { setBoxSelect({ ...boxSelect, ex: w.x, ey: w.y }); return; }
    if (dragging) {
      let nx = w.x - dragging.ox, ny = w.y - dragging.oy;
      // Snap to grid when grid is on
      if (useUIStore.getState().showGrid) {
        nx = Math.round(nx / 25) * 25;
        ny = Math.round(ny / 25) * 25;
      }
      updateNode(dragging.id, { x: nx, y: ny });
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (connecting) {
      const rect = canvasRef.current!.getBoundingClientRect();
      const w = toWorld(e.clientX - rect.left, e.clientY - rect.top);
      const target = hitTopPort(w.x, w.y) || hitNode(w.x, w.y);
      if (target && target.id !== connecting.fromId) setParent(target.id, connecting.fromId);
      setConnecting(null); return;
    }
    if (boxSelect) {
      // Select all nodes within box
      const bx = Math.min(boxSelect.sx, boxSelect.ex), by = Math.min(boxSelect.sy, boxSelect.ey);
      const bw = Math.abs(boxSelect.ex - boxSelect.sx), bh = Math.abs(boxSelect.ey - boxSelect.sy);
      if (bw > 5 && bh > 5) {
        for (const n of nodeList) {
          if (n.x + NODE_W > bx && n.x < bx + bw && n.y + NODE_H > by && n.y < by + bh) {
            selectNode(n.id, true);
          }
        }
      }
      setBoxSelect(null); return;
    }
    setDragging(null); setPanning(null);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const rect = canvasRef.current!.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const factor = e.deltaY > 0 ? 0.93 : 1.07;
    const nz = Math.max(0.1, Math.min(5, zoom * factor));
    const wx = (mx - panX) / zoom, wy = (my - panY) / zoom;
    setPan(mx - wx * nz, my - wy * nz);
    setZoom(nz);
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

  const handleDblClick = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const w = toWorld(e.clientX - rect.left, e.clientY - rect.top);
    const hit = hitNode(w.x, w.y);
    if (hit) {
      // Inline rename
      const name = prompt('Rename node:', hit.name);
      if (name !== null && name.trim()) updateNode(hit.id, { name: name.trim() });
    }
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

  const cursor = panning ? 'grabbing' : connecting ? 'crosshair' : dragging ? 'move' : hoveredId ? 'pointer' : 'default';

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', cursor }}
        onMouseDown={handleMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}
        onMouseLeave={() => { setDragging(null); setPanning(null); setConnecting(null); setBoxSelect(null); setHoveredId(null); }}
        onWheel={handleWheel} onContextMenu={handleContextMenu} onDoubleClick={handleDblClick}
        onDrop={handleDrop} onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }}
      />
    </div>
  );
}

// ══════════════════ NODE RENDERER ══════════════════
function drawNode(ctx: CanvasRenderingContext2D, node: CanvasNode, selected: boolean, hovered: boolean, simActive: boolean) {
  const { x, y } = node;
  const accent = nodeAccent(node);
  const fill = nodeFill(node);
  const info = getNodeTypeInfo(node.nodeType);

  // ── Glow for status during simulation ──
  if (node.status && simActive) {
    ctx.shadowColor = STATUS_COLORS[node.status] + '50';
    ctx.shadowBlur = 18;
  } else if (selected) {
    ctx.shadowColor = 'rgba(76,158,255,0.35)';
    ctx.shadowBlur = 14;
  }

  // ── Body fill ──
  ctx.fillStyle = hovered && !selected ? lighten(fill, 15) : fill;
  ctx.strokeStyle = selected ? '#4c9eff' : hovered ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.06)';
  ctx.lineWidth = selected ? 2 : 1;
  roundRect(ctx, x, y, NODE_W, NODE_H, 8);
  ctx.fill();
  ctx.stroke();

  ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0;

  // ── Top accent bar ──
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x + 8, y); ctx.lineTo(x + NODE_W - 8, y);
  ctx.quadraticCurveTo(x + NODE_W, y, x + NODE_W, y + 4);
  ctx.lineTo(x, y + 4);
  ctx.quadraticCurveTo(x, y, x + 8, y);
  ctx.closePath();
  ctx.clip();
  ctx.fillStyle = accent;
  ctx.fillRect(x, y, NODE_W, 4);
  ctx.restore();

  // ── Ports ──
  drawPort(ctx, x + NODE_W / 2, y, accent, hovered);         // top (input)
  drawPort(ctx, x + NODE_W / 2, y + NODE_H, accent, hovered); // bottom (output)

  // ── Icon ──
  if (info?.icon) {
    ctx.fillStyle = accent;
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(info.icon, x + 12, y + 30);
  }

  // ── Name ──
  ctx.fillStyle = '#e8eaed';
  ctx.font = "600 13px 'IBM Plex Sans', sans-serif";
  ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillText(truncate(node.name, 16), x + 34, y + 28);

  // ── Type label ──
  ctx.fillStyle = accent + '80';
  ctx.font = "500 10px 'IBM Plex Sans', sans-serif";
  ctx.fillText(node.nodeType, x + 34, y + 46);

  // ── Status dot ──
  if (node.status) {
    ctx.fillStyle = STATUS_COLORS[node.status];
    ctx.beginPath(); ctx.arc(x + NODE_W - 14, y + 14, 5, 0, Math.PI * 2); ctx.fill();
  }

  // ── Macro badge ──
  if (node.macro) {
    const mc = node.macro.color || accent;
    ctx.fillStyle = mc + '40';
    ctx.strokeStyle = mc;
    ctx.lineWidth = 1;
    roundRect(ctx, x + NODE_W - 36, y + NODE_H - 18, 28, 14, 3);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = mc;
    ctx.font = "bold 9px 'IBM Plex Sans', sans-serif";
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('M', x + NODE_W - 22, y + NODE_H - 11);
  }

  // ── BB port indicators ──
  if (node.blackboardInput) {
    ctx.fillStyle = '#4c9eff'; ctx.beginPath(); ctx.arc(x + 4, y + NODE_H / 2, 3, 0, Math.PI * 2); ctx.fill();
  }
  if (node.blackboardOutput) {
    ctx.fillStyle = '#3dd68c'; ctx.beginPath(); ctx.arc(x + NODE_W - 4, y + NODE_H / 2, 3, 0, Math.PI * 2); ctx.fill();
  }

  // ── Child count ──
  if (node.childIds.length > 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.2)';
    ctx.font = "10px 'IBM Plex Mono', monospace";
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(`${node.childIds.length}`, x + NODE_W - 10, y + 58);
  }

  ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
}

function drawPort(ctx: CanvasRenderingContext2D, x: number, y: number, color: string, hovered: boolean) {
  // Outer ring
  ctx.fillStyle = '#1c1f28';
  ctx.strokeStyle = hovered ? color : color + '60';
  ctx.lineWidth = hovered ? 2 : 1.5;
  ctx.beginPath(); ctx.arc(x, y, PORT_R, 0, Math.PI * 2);
  ctx.fill(); ctx.stroke();
  // Inner dot
  ctx.fillStyle = hovered ? color : color + '40';
  ctx.beginPath(); ctx.arc(x, y, 2.5, 0, Math.PI * 2); ctx.fill();
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
  return s.length > max ? s.slice(0, max - 1) + '\u2026' : s;
}

function lighten(hex: string, percent: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, (num >> 16) + percent);
  const g = Math.min(255, ((num >> 8) & 0xff) + percent);
  const b = Math.min(255, (num & 0xff) + percent);
  return `rgb(${r},${g},${b})`;
}
