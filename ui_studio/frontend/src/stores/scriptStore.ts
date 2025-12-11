import { create } from 'zustand'

export interface ScriptStep {
  id: string
  type: 'click' | 'fill' | 'navigate' | 'wait' | 'screenshot' | 'extract' | 'execute_js' | 'select' | 'hover' | 'press'
  description: string
  value?: string
  url?: string
  locators?: Array<{
    type: string
    value: string
    confidence?: number
    stability?: 'high' | 'medium' | 'low'
  }>
}

// Alias for convenience
export type Step = ScriptStep

export interface Script {
  id: string
  name: string
  version: string
  startUrl: string
  description?: string
  inputs?: Record<string, {
    type: string
    description: string
    required?: boolean
    default?: unknown
  }>
  steps: ScriptStep[]
  createdAt?: string
  updatedAt?: string
}

interface ScriptState {
  currentScript: Script | null
  isDirty: boolean

  setScript: (script: Script) => void
  addStep: (step: ScriptStep, index?: number) => void
  updateStep: (id: string, updates: Partial<ScriptStep>) => void
  removeStep: (id: string) => void
  moveStep: (fromIndex: number, toIndex: number) => void
  clearScript: () => void
  markClean: () => void
  updateScriptName: (name: string) => void
  setSteps: (steps: ScriptStep[]) => void
  setStartUrl: (url: string) => void
}

const createEmptyScript = (): Script => ({
  id: crypto.randomUUID(),
  name: 'New Script',
  version: '2.0.0',
  startUrl: '',
  steps: [],
})

export const useScriptStore = create<ScriptState>((set, get) => ({
  currentScript: null,
  isDirty: false,

  setScript: (script) => {
    set({ currentScript: script, isDirty: false })
  },

  addStep: (step, index) => {
    const { currentScript } = get()
    if (!currentScript) {
      const newScript = createEmptyScript()
      newScript.steps = [step]
      set({ currentScript: newScript, isDirty: true })
      return
    }

    const steps = [...currentScript.steps]
    if (index !== undefined) {
      steps.splice(index, 0, step)
    } else {
      steps.push(step)
    }

    set({
      currentScript: { ...currentScript, steps },
      isDirty: true,
    })
  },

  updateStep: (id, updates) => {
    const { currentScript } = get()
    if (!currentScript) return

    const steps = currentScript.steps.map((step) =>
      step.id === id ? { ...step, ...updates } : step
    )

    set({
      currentScript: { ...currentScript, steps },
      isDirty: true,
    })
  },

  removeStep: (id) => {
    const { currentScript } = get()
    if (!currentScript) return

    const steps = currentScript.steps.filter((step) => step.id !== id)

    set({
      currentScript: { ...currentScript, steps },
      isDirty: true,
    })
  },

  moveStep: (fromIndex, toIndex) => {
    const { currentScript } = get()
    if (!currentScript) return

    const steps = [...currentScript.steps]
    const [removed] = steps.splice(fromIndex, 1)
    steps.splice(toIndex, 0, removed)

    set({
      currentScript: { ...currentScript, steps },
      isDirty: true,
    })
  },

  clearScript: () => {
    set({ currentScript: null, isDirty: false })
  },

  markClean: () => {
    set({ isDirty: false })
  },

  updateScriptName: (name) => {
    const { currentScript } = get()
    if (!currentScript) {
      const newScript = createEmptyScript()
      newScript.name = name
      set({ currentScript: newScript, isDirty: true })
      return
    }
    set({
      currentScript: { ...currentScript, name },
      isDirty: true,
    })
  },

  setSteps: (steps) => {
    const { currentScript } = get()
    if (!currentScript) {
      const newScript = createEmptyScript()
      newScript.steps = steps
      set({ currentScript: newScript, isDirty: true })
      return
    }
    set({
      currentScript: { ...currentScript, steps },
      isDirty: true,
    })
  },

  setStartUrl: (url) => {
    const { currentScript } = get()
    if (!currentScript) {
      const newScript = createEmptyScript()
      newScript.startUrl = url
      set({ currentScript: newScript, isDirty: true })
      return
    }
    set({
      currentScript: { ...currentScript, startUrl: url },
      isDirty: true,
    })
  },
}))
