const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

type TranslateDirection = "latin-to-bali" | "bali-to-latin"

export interface TranslateResponse {
  original: string
  result: string
  direction: string
  breakdown: any[]
  confidence: number
  warnings: string[]
}

export interface ClassifyResponse {
  input: string
  classifications: any[]
  overall_type: string
  syllable_count: number
  has_gantungan: boolean
  has_pangangge: boolean
}

export interface Lesson {
  id: string
  title: string
  description: string
  level: number
  order: number
  category: string
  estimated_minutes: number
  xp_reward: number
  thumbnail?: string
  aksara_ids?: string[]
}

export interface Quiz {
  id: string
  lesson_id?: string
  type: string
  difficulty: string
  question: {
    text: string
    latin?: string
    bali?: string
    pair?: any
    hint?: string
  }
  options: {
    id: string
    bali?: string
    latin?: string
    label?: string
    is_correct?: boolean
  }[]
  correct_answer: string
  explanation?: string
  xp: number
}

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })
  
  if (!res.ok) {
    const error = await res.text()
    throw new Error(`API Error ${res.status}: ${error}`)
  }
  
  return res.json()
}

export const api = {
  health: () => fetchAPI<{status: string}>("/health"),
  
  translate: (text: string, direction: TranslateDirection, useDictionary = true) =>
    fetchAPI<TranslateResponse>("/translate", {
      method: "POST",
      body: JSON.stringify({
        text,
        direction,
        options: { use_dictionary: useDictionary }
      })
    }),
  
  translateBatch: (items: {text: string, direction: TranslateDirection}[]) =>
    fetchAPI<{results: TranslateResponse[]}>("/translate/batch", {
      method: "POST",
      body: JSON.stringify({ items })
    }),
  
  classify: (text: string) =>
    fetchAPI<ClassifyResponse>("/classify", {
      method: "POST",
      body: JSON.stringify({ text })
    }),
  
  getClassifyTypes: () =>
    fetchAPI<{types: any[]}>("/classify/types"),
  
  getLessons: (params?: {level?: number, category?: string, search?: string, limit?: number, offset?: number}) => {
    const searchParams = new URLSearchParams()
    if (params?.level) searchParams.set("level", params.level.toString())
    if (params?.category) searchParams.set("category", params.category)
    if (params?.search) searchParams.set("search", params.search)
    if (params?.limit) searchParams.set("limit", params.limit.toString())
    if (params?.offset) searchParams.set("offset", params.offset.toString())
    const query = searchParams.toString() ? `?${searchParams.toString()}` : ""
    return fetchAPI<{lessons: Lesson[], total: number, level_info: any}>(`/lessons${query}`)
  },
  
  getLesson: (id: string) =>
    fetchAPI<any>(`/lessons/${id}`),
  
  getQuizzes: (params?: {lesson_id?: string, type?: string, difficulty?: string, limit?: number}) => {
    const searchParams = new URLSearchParams()
    if (params?.lesson_id) searchParams.set("lesson_id", params.lesson_id)
    if (params?.type) searchParams.set("type", params.type)
    if (params?.difficulty) searchParams.set("difficulty", params.difficulty)
    if (params?.limit) searchParams.set("limit", params.limit.toString())
    const query = searchParams.toString() ? `?${searchParams.toString()}` : ""
    return fetchAPI<{quizzes: Quiz[], total: number}>(`/quiz${query}`)
  },
  
  checkQuiz: (quiz_id: string, answer: any, user_input?: string) =>
    fetchAPI<any>("/quiz/check", {
      method: "POST",
      body: JSON.stringify({ quiz_id, answer, user_input })
    }),
  
  validatePair: (question_latin: string, question_bali: string, user_bali: string, mode: "exact" | "tolerant" = "exact") =>
    fetchAPI<any>("/quiz/validate-pair", {
      method: "POST",
      body: JSON.stringify({ question_latin, question_bali, user_bali, mode })
    }),
  
  getGantunganRules: () =>
    fetchAPI<{rules: any[]}>("/translate/gantungan/rules"),
  
  analyzeGantungan: (text: string, direction: TranslateDirection = "latin-to-bali") =>
    fetchAPI<any>("/translate/gantungan/analyze", {
      method: "POST",
      body: JSON.stringify({ text, direction })
    })
}
