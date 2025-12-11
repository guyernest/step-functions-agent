import { create } from 'zustand'

export interface ElementInfo {
  tag: string
  text: string
  attributes: Record<string, string>
  boundingBox: {
    x: number
    y: number
    width: number
    height: number
  }
  xpath: string
  cssSelector: string
  parentHtml: string
}

interface BrowserState {
  isRecording: boolean
  currentUrl: string
  pageTitle: string
  screenshot: string | null  // base64
  selectedElement: ElementInfo | null
  hoveredElement: ElementInfo | null

  setRecording: (recording: boolean) => void
  setIsRecording: (recording: boolean) => void
  setPageInfo: (url: string, title: string) => void
  setCurrentUrl: (url: string) => void
  setScreenshot: (screenshot: string | null) => void
  setSelectedElement: (element: ElementInfo | null) => void
  setHoveredElement: (element: ElementInfo | null) => void
  reset: () => void
}

export const useBrowserStore = create<BrowserState>((set) => ({
  isRecording: false,
  currentUrl: '',
  pageTitle: '',
  screenshot: null,
  selectedElement: null,
  hoveredElement: null,

  setRecording: (recording) => set({ isRecording: recording }),

  setIsRecording: (recording) => set({ isRecording: recording }),

  setPageInfo: (url, title) => set({ currentUrl: url, pageTitle: title }),

  setCurrentUrl: (url) => set({ currentUrl: url }),

  setScreenshot: (screenshot) => set({ screenshot }),

  setSelectedElement: (element) => set({ selectedElement: element }),

  setHoveredElement: (element) => set({ hoveredElement: element }),

  reset: () => set({
    isRecording: false,
    currentUrl: '',
    pageTitle: '',
    screenshot: null,
    selectedElement: null,
    hoveredElement: null,
  }),
}))
