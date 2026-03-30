import { create } from 'zustand';

type Theme = 'dark' | 'light';

interface UIState {
  theme: Theme;
  showPalette: boolean;
  showProperties: boolean;
  showMinimap: boolean;
  showBlackboard: boolean;
  showTimeline: boolean;
  showGrid: boolean;
  showDataflow: boolean;
  zoom: number;
  panX: number;
  panY: number;
  searchQuery: string;

  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  togglePanel: (panel: 'palette' | 'properties' | 'minimap' | 'blackboard' | 'timeline' | 'grid' | 'dataflow') => void;
  setZoom: (zoom: number) => void;
  setPan: (x: number, y: number) => void;
  setSearchQuery: (q: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'dark',
  showPalette: true,
  showProperties: true,
  showMinimap: true,
  showBlackboard: false,
  showTimeline: true,
  showGrid: false,
  showDataflow: false,
  zoom: 1,
  panX: 0,
  panY: 0,
  searchQuery: '',

  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },
  toggleTheme: () => set((s) => {
    const next = s.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    return { theme: next };
  }),
  togglePanel: (panel) => set((s) => {
    const key = `show${panel.charAt(0).toUpperCase() + panel.slice(1)}` as keyof UIState;
    return { [key]: !s[key] } as Partial<UIState>;
  }),
  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),
  setPan: (panX, panY) => set({ panX, panY }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
}));
