/**
 * TreeCanvas — The core visual engine for TalkingTrees.
 *
 * Canvas 2D renderer with:
 * - Category-tinted gradient node fills
 * - Animated connection wires with flow particles during simulation
 * - Hover/select glow effects
 * - Dot grid with subtle cross pattern at intersections
 * - Smooth connection port interactions
 * - Box selection
 * - Grid snapping
 */

import { useRef, useEffect, useCallback, useState } from 'react';
import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';
import { useSimStore } from '../../store/simulationStore';
import { getNodeTypeInfo } from '../Palette/nodeRegistry';
import type { CanvasNode } from '../../types/tree';

// ── Dimensions ──
const W = 196;
const H = 76;
const R = 10;       // corner radius
const PORT = 7;     // port radius
const BAR_H = 5;    // accent bar height

// ── Colors ──
const FILLS: Record<string, { bg: string; accent: string }> = {
  composite: { bg: '#152b28', accent: '#56d4b8' },
  decorator: { bg: '#2a2718', accent: '#e2d87a' },
  action:    { bg: '#152333', accent: '#5b9cf6' },
  condition: { bg: '#281d2d', accent: '#d08ed0' },
  custom:    { bg: '#2a2218', accent: '#d4956c' },
};

const STATUS: Record<string, { color: string; bg: string; glow: string }> = {
  SUCCESS: { color: '#5ccf8a', bg: '#152b1e', glow: 'rgba(92,207,138,0.35)' },
  FAILURE: { color: '#f06868', bg: '#2b1515', glow: 'rgba(240,104,104,0.35)' },
  RUNNING: { color: '#f0b848', bg: '#2b2215', glow: 'rgba(240,184,72,0.35)' },
};

const TYPE_ACCENT: Record<string, string> = {
  SubTreeRef: '#b07cd8', AsyncAction: '#e89840', RemoteSubtree: '#b07cd8',
  RateLimiter: '#f07070', AcquireResource: '#5ccf8a', ReleaseResource: '#5ccf8a',
  Debounce: '#f0b848', WindowedAggregator: '#5b9cf6',
};

function getStyle(node: CanvasNode) {
  const info = getNodeTypeInfo(node.nodeType);
  const cat = info?.category || 'action';
  const base = FILLS[cat] || FILLS.action;
  const accent = TYPE_ACCENT[node.nodeType] || base.accent;

  if (node.status && STATUS[node.status]) {
    return { bg: STATUS[node.status].bg, accent: STATUS[node.status].color, glow: STATUS[node.status].glow };
  }
  return { bg: base.bg, accent, glow: '' };
}

export function TreeCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef(0);

  const store = useTreeStore;
  const { nodes, selectedIds, selectNode, clearSelection, addNode, setParent, updateNode } = store();
  const { zoom, panX, panY, setZoom, setPan, showGrid, showDataflow } = useUIStore();
  const simRunning = useSimStore(s => s.running);
  const simTick = useSimStore(s => s.tick);

  const [drag, setDrag] = useState<{ id: string; ox: number; oy: number } | null>(null);
  const [pan, setPan_] = useState<{ sx: number; sy: number } | null>(null);
  const [conn, setConn] = useState<{ from: string; mx: number; my: number } | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [box, setBox] = useState<{ sx: number; sy: number; ex: number; ey: number } | null>(null);

  const world = useCallback((sx: number, sy: number) => ({
    x: (sx - panX) / zoom, y: (sy - panY) / zoom,
  }), [panX, panY, zoom]);

  const nl = Object.values(nodes);

  const hitN = useCallback((wx: number, wy: number) => {
    for (let i = nl.length - 1; i >= 0; i--) {
      const n = nl[i];
      if (wx >= n.x && wx <= n.x + W && wy >= n.y && wy <= n.y + H) return n;
    }
    return null;
  }, [nl]);

  const hitPort = useCallback((wx: number, wy: number, bottom: boolean) => {
    for (const n of nl) {
      const px = n.x + W / 2, py = bottom ? n.y + H : n.y;
      if (Math.hypot(wx - px, wy - py) < PORT + 6) return n;
    }
    return null;
  }, [nl]);

  // ═══════════════════════════════════════════
  //                  RENDER
  // ═══════════════════════════════════════════
  const render = useCallback(() => {
    const cvs = canvasRef.current;
    if (!cvs) return;
    const ctx = cvs.getContext('2d')!;
    const dpr = window.devicePixelRatio || 1;
    const rect = cvs.getBoundingClientRect();
    cvs.width = rect.width * dpr;
    cvs.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const cw = rect.width, ch = rect.height;

    // ── Background ──
    ctx.fillStyle = '#0c0e14';
    ctx.fillRect(0, 0, cw, ch);

    // Subtle vignette
    const vig = ctx.createRadialGradient(cw / 2, ch / 2, cw * 0.2, cw / 2, ch / 2, cw * 0.8);
    vig.addColorStop(0, 'rgba(25,30,48,0.25)');
    vig.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, cw, ch);

    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(zoom, zoom);

    const vx = -panX / zoom, vy = -panY / zoom;
    const vw = cw / zoom, vh = ch / zoom;

    // ── Dot grid ──
    if (showGrid) {
      const gs = 28;
      const sx0 = Math.floor(vx / gs) * gs;
      const sy0 = Math.floor(vy / gs) * gs;
      for (let gx = sx0; gx < vx + vw + gs; gx += gs) {
        for (let gy = sy0; gy < vy + vh + gs; gy += gs) {
          const isCross = Math.round(gx / gs) % 4 === 0 && Math.round(gy / gs) % 4 === 0;
          ctx.fillStyle = isCross ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.045)';
          ctx.beginPath();
          ctx.arc(gx, gy, isCross ? 1.2 : 0.7, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    // ── Connections ──
    const t = performance.now() * 0.001;
    for (const node of nl) {
      for (const cid of node.childIds) {
        const child = nodes[cid];
        if (!child) continue;
        const x1 = node.x + W / 2, y1 = node.y + H;
        const x2 = child.x + W / 2, y2 = child.y;
        const cp = Math.max(40, (y2 - y1) * 0.45);
        const sel = selectedIds.has(node.id) || selectedIds.has(cid);
        const style = getStyle(node);

        // Shadow
        ctx.strokeStyle = 'rgba(0,0,0,0.4)';
        ctx.lineWidth = sel ? 5 : 3.5;
        ctx.beginPath();
        ctx.moveTo(x1, y1); ctx.bezierCurveTo(x1, y1 + cp, x2, y2 - cp, x2, y2);
        ctx.stroke();

        // Wire
        const wireGrad = ctx.createLinearGradient(x1, y1, x2, y2);
        wireGrad.addColorStop(0, sel ? '#5b9cf6' : style.accent + '60');
        wireGrad.addColorStop(1, sel ? '#5b9cf680' : getStyle(child).accent + '40');
        ctx.strokeStyle = wireGrad;
        ctx.lineWidth = sel ? 2.5 : 1.8;

        if (simRunning && node.status) {
          ctx.setLineDash([10, 6]);
          ctx.lineDashOffset = -t * 80;
        }
        ctx.beginPath();
        ctx.moveTo(x1, y1); ctx.bezierCurveTo(x1, y1 + cp, x2, y2 - cp, x2, y2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Flow particles during simulation
        if (simRunning && node.status === 'SUCCESS') {
          for (let p = 0; p < 3; p++) {
            const pt = ((t * 0.6 + p * 0.33) % 1);
            const px = bezierPoint(x1, x1, x2, x2, pt);
            const py = bezierPoint(y1, y1 + cp, y2 - cp, y2, pt);
            ctx.fillStyle = style.accent;
            ctx.globalAlpha = 0.6 * (1 - Math.abs(pt - 0.5) * 2);
            ctx.beginPath();
            ctx.arc(px, py, 2.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
          }
        }
      }
    }

    // ── Dataflow ──
    if (showDataflow) {
      for (const n of nl) {
        if (!n.blackboardOutput) continue;
        for (const o of nl) {
          if (o.id === n.id || !o.blackboardInput) continue;
          const shared = Object.keys(n.blackboardOutput!).filter(k => o.blackboardInput![k]);
          if (shared.length > 0) {
            ctx.strokeStyle = 'rgba(91,156,246,0.2)';
            ctx.lineWidth = 1.2;
            ctx.setLineDash([6, 3]);
            ctx.beginPath();
            ctx.moveTo(n.x + W, n.y + H / 2);
            ctx.lineTo(o.x, o.y + H / 2);
            ctx.stroke();
            ctx.setLineDash([]);

            // Arrowhead
            ctx.fillStyle = 'rgba(91,156,246,0.2)';
            ctx.beginPath();
            ctx.moveTo(o.x, o.y + H / 2);
            ctx.lineTo(o.x - 7, o.y + H / 2 - 4);
            ctx.lineTo(o.x - 7, o.y + H / 2 + 4);
            ctx.fill();
          }
        }
      }
    }

    // ── Connection drag line ──
    if (conn) {
      const from = nodes[conn.from];
      if (from) {
        ctx.strokeStyle = '#5b9cf6';
        ctx.lineWidth = 2.5;
        ctx.setLineDash([8, 5]);
        ctx.lineDashOffset = -t * 60;
        ctx.beginPath();
        ctx.moveTo(from.x + W / 2, from.y + H);
        ctx.lineTo(conn.mx, conn.my);
        ctx.stroke();
        ctx.setLineDash([]);

        // Target indicator
        ctx.fillStyle = 'rgba(91,156,246,0.15)';
        ctx.beginPath();
        ctx.arc(conn.mx, conn.my, 12, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // ── Box selection ──
    if (box) {
      const bx = Math.min(box.sx, box.ex), by = Math.min(box.sy, box.ey);
      const bw = Math.abs(box.ex - box.sx), bh = Math.abs(box.ey - box.sy);
      ctx.fillStyle = 'rgba(91,156,246,0.06)';
      ctx.strokeStyle = 'rgba(91,156,246,0.35)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 3]);
      ctx.fillRect(bx, by, bw, bh);
      ctx.strokeRect(bx, by, bw, bh);
      ctx.setLineDash([]);
    }

    // ── Nodes ──
    for (const node of nl) {
      renderNode(ctx, node, selectedIds.has(node.id), hover === node.id, simRunning, t);
    }

    // ── Empty state ──
    if (nl.length === 0) {
      ctx.restore();
      ctx.textAlign = 'center';
      // Large icon
      ctx.fillStyle = 'rgba(255,255,255,0.06)';
      ctx.font = "60px sans-serif";
      ctx.fillText('🌳', cw / 2, ch / 2 - 30);
      // Title
      ctx.fillStyle = 'rgba(255,255,255,0.2)';
      ctx.font = "600 16px Inter, sans-serif";
      ctx.fillText('Drag nodes from the palette to start building', cw / 2, ch / 2 + 20);
      // Subtitle
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.font = "12px Inter, sans-serif";
      ctx.fillText('Right-click for context menu  ·  Ctrl+Shift+P for commands  ·  F1 for shortcuts', cw / 2, ch / 2 + 44);
      return;
    }

    ctx.restore();
  }, [nodes, nl, selectedIds, zoom, panX, panY, showGrid, showDataflow, conn, hover, simRunning, simTick, box]);

  // Render loop
  useEffect(() => {
    let active = true;
    const loop = () => { if (active) { render(); frameRef.current = requestAnimationFrame(loop); } };
    frameRef.current = requestAnimationFrame(loop);
    return () => { active = false; cancelAnimationFrame(frameRef.current); };
  }, [render]);

  // Resize
  useEffect(() => {
    const c = containerRef.current;
    if (!c) return;
    const obs = new ResizeObserver(() => render());
    obs.observe(c);
    return () => obs.disconnect();
  }, [render]);

  // ═══════════════════════════════════════════
  //              MOUSE HANDLERS
  // ═══════════════════════════════════════════
  const handleDown = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const s = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    const w = world(s.x, s.y);

    // Pan
    if (e.button === 1 || (e.button === 0 && e.altKey)) {
      setPan_({ sx: e.clientX, sy: e.clientY }); return;
    }
    if (e.button !== 0) return;

    // Port
    const p = hitPort(w.x, w.y, true);
    if (p) { setConn({ from: p.id, mx: w.x, my: w.y }); return; }

    // Node
    const hit = hitN(w.x, w.y);
    if (hit) {
      selectNode(hit.id, e.shiftKey);
      setDrag({ id: hit.id, ox: w.x - hit.x, oy: w.y - hit.y });
    } else {
      clearSelection();
      setBox({ sx: w.x, sy: w.y, ex: w.x, ey: w.y });
    }
  };

  const handleMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const w = world(e.clientX - rect.left, e.clientY - rect.top);

    setHover(hitN(w.x, w.y)?.id || null);

    if (pan) {
      setPan(panX + e.clientX - pan.sx, panY + e.clientY - pan.sy);
      setPan_({ sx: e.clientX, sy: e.clientY }); return;
    }
    if (conn) { setConn({ ...conn, mx: w.x, my: w.y }); return; }
    if (box) { setBox({ ...box, ex: w.x, ey: w.y }); return; }
    if (drag) {
      let nx = w.x - drag.ox, ny = w.y - drag.oy;
      if (useUIStore.getState().showGrid) { nx = Math.round(nx / 28) * 28; ny = Math.round(ny / 28) * 28; }
      updateNode(drag.id, { x: nx, y: ny });
    }
  };

  const handleUp = (e: React.MouseEvent) => {
    if (conn) {
      const rect = canvasRef.current!.getBoundingClientRect();
      const w = world(e.clientX - rect.left, e.clientY - rect.top);
      const target = hitPort(w.x, w.y, false) || hitN(w.x, w.y);
      if (target && target.id !== conn.from) setParent(target.id, conn.from);
      setConn(null); return;
    }
    if (box) {
      const bx = Math.min(box.sx, box.ex), by = Math.min(box.sy, box.ey);
      const bw = Math.abs(box.ex - box.sx), bh = Math.abs(box.ey - box.sy);
      if (bw > 5 && bh > 5) {
        for (const n of nl) {
          if (n.x + W > bx && n.x < bx + bw && n.y + H > by && n.y < by + bh) selectNode(n.id, true);
        }
      }
      setBox(null); return;
    }
    setDrag(null); setPan_(null);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const rect = canvasRef.current!.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const f = e.deltaY > 0 ? 0.92 : 1.08;
    const nz = Math.max(0.1, Math.min(5, zoom * f));
    const wx = (mx - panX) / zoom, wy = (my - panY) / zoom;
    setPan(mx - wx * nz, my - wy * nz);
    setZoom(nz);
  };

  const handleCtx = (e: React.MouseEvent) => {
    e.preventDefault();
    const rect = canvasRef.current!.getBoundingClientRect();
    const w = world(e.clientX - rect.left, e.clientY - rect.top);
    const hit = hitN(w.x, w.y);
    window.dispatchEvent(new CustomEvent('tree-context-menu', {
      detail: { x: e.clientX, y: e.clientY, nodeId: hit?.id || null, worldX: w.x, worldY: w.y },
    }));
  };

  const handleDbl = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const w = world(e.clientX - rect.left, e.clientY - rect.top);
    const hit = hitN(w.x, w.y);
    if (hit) {
      const name = prompt('Rename node:', hit.name);
      if (name?.trim()) updateNode(hit.id, { name: name.trim() });
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const data = e.dataTransfer.getData('application/json');
    if (!data) return;
    try {
      const info = JSON.parse(data);
      const rect = canvasRef.current!.getBoundingClientRect();
      const w = world(e.clientX - rect.left, e.clientY - rect.top);
      addNode({ nodeType: info.type, name: info.displayName, config: { ...info.defaultConfig }, x: w.x - W / 2, y: w.y - H / 2 });
    } catch { /* */ }
  };

  const cursor = pan ? 'grabbing' : conn ? 'crosshair' : drag ? 'move' : hover ? 'pointer' : 'default';

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', cursor }}
        onMouseDown={handleDown} onMouseMove={handleMove} onMouseUp={handleUp}
        onMouseLeave={() => { setDrag(null); setPan_(null); setConn(null); setBox(null); setHover(null); }}
        onWheel={handleWheel} onContextMenu={handleCtx} onDoubleClick={handleDbl}
        onDrop={handleDrop} onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════
//              NODE RENDERER
// ═══════════════════════════════════════════════
function renderNode(ctx: CanvasRenderingContext2D, node: CanvasNode, sel: boolean, hov: boolean, _sim: boolean, t: number) {
  const { x, y } = node;
  const { bg, accent, glow } = getStyle(node);
  const info = getNodeTypeInfo(node.nodeType);

  // ── Drop shadow ──
  ctx.shadowColor = sel ? 'rgba(91,156,246,0.3)' : glow || 'rgba(0,0,0,0.5)';
  ctx.shadowBlur = sel ? 20 : glow ? 22 : 10;
  ctx.shadowOffsetY = sel ? 0 : 3;

  // ── Body gradient ──
  const bodyGrad = ctx.createLinearGradient(x, y, x, y + H);
  bodyGrad.addColorStop(0, hov && !sel ? lighten(bg, 12) : bg);
  bodyGrad.addColorStop(1, darken(bg, 8));
  ctx.fillStyle = bodyGrad;

  // Border
  ctx.strokeStyle = sel ? '#5b9cf6' : hov ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.04)';
  ctx.lineWidth = sel ? 2 : 1;

  rr(ctx, x, y, W, H, R);
  ctx.fill();
  ctx.stroke();

  ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;

  // ── Accent bar (gradient) ──
  ctx.save();
  rr(ctx, x, y, W, BAR_H + R, R);
  ctx.clip();
  const barGrad = ctx.createLinearGradient(x, y, x + W, y);
  barGrad.addColorStop(0, accent);
  barGrad.addColorStop(1, accent + '60');
  ctx.fillStyle = barGrad;
  ctx.fillRect(x, y, W, BAR_H);
  ctx.restore();

  // ── Inner highlight line ──
  ctx.strokeStyle = 'rgba(255,255,255,0.03)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x + R, y + BAR_H + 0.5);
  ctx.lineTo(x + W - R, y + BAR_H + 0.5);
  ctx.stroke();

  // ── Ports ──
  drawPort(ctx, x + W / 2, y, accent, hov, sel);       // input (top)
  drawPort(ctx, x + W / 2, y + H, accent, hov, sel);   // output (bottom)

  // ── Icon ──
  if (info?.icon) {
    ctx.fillStyle = accent;
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(info.icon, x + 14, y + BAR_H + (H - BAR_H) / 2 - 4);
  }

  // ── Name ──
  ctx.fillStyle = '#eceff4';
  ctx.font = "600 13px Inter, sans-serif";
  ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillText(trunc(node.name, 15), x + 40, y + BAR_H + 18);

  // ── Type ──
  ctx.fillStyle = accent + '70';
  ctx.font = "500 10px Inter, sans-serif";
  ctx.fillText(node.nodeType, x + 40, y + BAR_H + 36);

  // ── Status badge ──
  if (node.status) {
    const sc = STATUS[node.status];
    if (sc) {
      // Pulsing glow
      const pulse = 0.6 + 0.4 * Math.sin(t * 4);
      ctx.fillStyle = sc.color;
      ctx.globalAlpha = pulse;
      ctx.beginPath(); ctx.arc(x + W - 16, y + 16, 6, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
      // Solid inner
      ctx.fillStyle = sc.color;
      ctx.beginPath(); ctx.arc(x + W - 16, y + 16, 3.5, 0, Math.PI * 2); ctx.fill();
    }
  }

  // ── Macro badge ──
  if (node.macro) {
    const mc = node.macro.color || accent;
    ctx.fillStyle = mc + '25';
    ctx.strokeStyle = mc + '60';
    ctx.lineWidth = 1;
    rr(ctx, x + W - 42, y + H - 20, 34, 16, 4);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = mc;
    ctx.font = "bold 9px Inter, sans-serif";
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('MACRO', x + W - 25, y + H - 12);
  }

  // ── BB port dots ──
  if (node.blackboardInput) {
    ctx.fillStyle = '#5b9cf6'; ctx.beginPath(); ctx.arc(x + 5, y + H / 2, 3, 0, Math.PI * 2); ctx.fill();
  }
  if (node.blackboardOutput) {
    ctx.fillStyle = '#5ccf8a'; ctx.beginPath(); ctx.arc(x + W - 5, y + H / 2, 3, 0, Math.PI * 2); ctx.fill();
  }

  // ── Child count ──
  if (node.childIds.length > 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.font = "500 10px 'JetBrains Mono', monospace";
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(`${node.childIds.length}`, x + W - 12, y + H - 14);
  }

  ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
}

function drawPort(ctx: CanvasRenderingContext2D, x: number, y: number, accent: string, hov: boolean, sel: boolean) {
  // Outer ring
  ctx.fillStyle = '#12151e';
  ctx.strokeStyle = sel ? '#5b9cf6' : hov ? accent : accent + '50';
  ctx.lineWidth = sel ? 2 : hov ? 1.8 : 1.2;
  ctx.beginPath(); ctx.arc(x, y, PORT, 0, Math.PI * 2);
  ctx.fill(); ctx.stroke();

  // Inner fill
  const inner = hov || sel ? accent : accent + '30';
  ctx.fillStyle = inner;
  ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
}

// ── Helpers ──
function rr(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}

function trunc(s: string, max: number) { return s.length > max ? s.slice(0, max - 1) + '\u2026' : s; }

function lighten(hex: string, n: number) {
  const c = parseInt(hex.replace('#', ''), 16);
  return `rgb(${Math.min(255, (c >> 16) + n)},${Math.min(255, ((c >> 8) & 0xff) + n)},${Math.min(255, (c & 0xff) + n)})`;
}
function darken(hex: string, n: number) { return lighten(hex, -n); }

function bezierPoint(p0: number, p1: number, p2: number, p3: number, t: number) {
  const u = 1 - t;
  return u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3;
}
