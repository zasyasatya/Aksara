import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ProgressState {
  xp: number
  streak: number
  completedLessons: string[]
  currentLesson: string | null
  level: number
  addXP: (amount: number) => void
  completeLesson: (lessonId: string) => void
  setCurrentLesson: (lessonId: string) => void
  reset: () => void
}

export const useProgressStore = create<ProgressState>()(
  persist(
    (set, get) => ({
      xp: 0,
      streak: 1,
      completedLessons: [],
      currentLesson: null,
      level: 1,
      addXP: (amount) => set((state) => {
        const newXP = state.xp + amount
        const newLevel = Math.floor(newXP / 200) + 1
        return { xp: newXP, level: newLevel }
      }),
      completeLesson: (lessonId) => set((state) => {
        if (state.completedLessons.includes(lessonId)) return state
        return {
          completedLessons: [...state.completedLessons, lessonId],
          xp: state.xp + 50,
          level: Math.floor((state.xp + 50) / 200) + 1
        }
      }),
      setCurrentLesson: (lessonId) => set({ currentLesson: lessonId }),
      reset: () => set({ xp: 0, streak: 1, completedLessons: [], currentLesson: null, level: 1 })
    }),
    {
      name: 'aksara-progress',
    }
  )
)

interface QuizState {
  currentQuizIndex: number
  answers: Record<string, any>
  score: number
  showFeedback: boolean
  lastResult: any | null
  setAnswer: (quizId: string, answer: any) => void
  setResult: (result: any) => void
  nextQuiz: () => void
  reset: () => void
}

export const useQuizStore = create<QuizState>((set) => ({
  currentQuizIndex: 0,
  answers: {},
  score: 0,
  showFeedback: false,
  lastResult: null,
  setAnswer: (quizId, answer) => set((state) => ({
    answers: { ...state.answers, [quizId]: answer }
  })),
  setResult: (result) => set({
    lastResult: result,
    showFeedback: true,
    score: result.correct ? 1 : 0
  }),
  nextQuiz: () => set((state) => ({
    currentQuizIndex: state.currentQuizIndex + 1,
    showFeedback: false,
    lastResult: null
  })),
  reset: () => set({
    currentQuizIndex: 0,
    answers: {},
    score: 0,
    showFeedback: false,
    lastResult: null
  })
}))

interface TranslateState {
  input: string
  output: string
  direction: "latin-to-bali" | "bali-to-latin"
  isLoading: boolean
  breakdown: any[]
  setInput: (input: string) => void
  setOutput: (output: string) => void
  setDirection: (dir: "latin-to-bali" | "bali-to-latin") => void
  setLoading: (loading: boolean) => void
  setBreakdown: (breakdown: any[]) => void
}

export const useTranslateStore = create<TranslateState>((set) => ({
  input: "",
  output: "",
  direction: "latin-to-bali",
  isLoading: false,
  breakdown: [],
  setInput: (input) => set({ input }),
  setOutput: (output) => set({ output }),
  setDirection: (direction) => set({ direction }),
  setLoading: (isLoading) => set({ isLoading }),
  setBreakdown: (breakdown) => set({ breakdown })
}))
