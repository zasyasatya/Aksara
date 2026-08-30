// Same-origin by default: next.config.js mem-proxy /api ke FastAPI di server
// side, sehingga browser tidak pernah memanggil localhost backend secara langsung.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api"

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

// ── Dokumentasi & Admin ─────────────────────────────────────────────────

export type DocsRole = "murid" | "guru" | "admin" | "metodologi"

export interface DocsPageMeta {
  slug: string
  title: string
  subtitle: string
  role: DocsRole
  icon: string
  is_public: boolean
  order: number
  updated_at: string
}

export interface DocsPagesResponse {
  mode: "dev" | "prod"
  is_admin: boolean
  pages: DocsPageMeta[]
}

export interface VisibilityResponse {
  slug: string
  is_public: boolean
  message: string
}

// ── Manajemen konten (Guru) ─────────────────────────────────────────────

export interface ManageStatus {
  mode: "dev" | "prod"
  is_guru: boolean
  is_admin: boolean
}

export interface LessonIn {
  id?: string
  title: string
  slug?: string
  description?: string
  story?: string
  level: number
  order: number
  category?: string
  aksara_ids: string[]
  pangangge_ids: string[]
  estimated_minutes: number
  xp_reward: number
  prerequisites: string[]
  quiz_ids: string[]
  is_published: boolean
  thumbnail?: string
}

export interface QuizQuestionIn {
  text: string
  latin?: string
  bali?: string
  hint?: string
}

export interface QuizOptionIn {
  id: string
  bali?: string
  latin?: string
  label?: string
  is_correct?: boolean
}

export interface QuizIn {
  id?: string
  lesson_id?: string
  type: string
  difficulty: "easy" | "medium" | "hard"
  question: QuizQuestionIn
  options: QuizOptionIn[]
  correct_answer?: string
  explanation?: string
  xp: number
}

export interface DictEntry {
  latin: string
  bali: string
  meaning?: string
  note?: string
}

export interface AksaraRefGroup {
  category: string
  items: { id: string; bali: string; latin: string; name: string }[]
}

const ADMIN_TOKEN_KEY = "aksara_admin_token"
const GURU_TOKEN_KEY = "aksara_guru_token"

/** Ambil token admin tersimpan (null bila belum login). Hanya jalan di browser. */
export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(ADMIN_TOKEN_KEY)
}

/** Simpan atau hapus token admin. */
export function setAdminToken(token: string | null): void {
  if (typeof window === "undefined") return
  if (token) window.localStorage.setItem(ADMIN_TOKEN_KEY, token)
  else window.localStorage.removeItem(ADMIN_TOKEN_KEY)
}

/** Ambil token guru tersimpan (null bila belum login). */
export function getGuruToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(GURU_TOKEN_KEY)
}

/** Simpan atau hapus token guru. */
export function setGuruToken(token: string | null): void {
  if (typeof window === "undefined") return
  if (token) window.localStorage.setItem(GURU_TOKEN_KEY, token)
  else window.localStorage.removeItem(GURU_TOKEN_KEY)
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
  health: () => fetchAPI<{status: string; version?: string; service?: string}>("/health"),
  
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
    }),

  // ── Dokumentasi ──
  getDocsPages: (adminToken: string | null = null) =>
    fetchAPI<DocsPagesResponse>("/docs/pages", {
      headers: adminToken ? { "X-Admin-Token": adminToken } : {},
    }),

  setDocVisibility: (slug: string, isPublic: boolean, adminToken: string | null = null) =>
    fetchAPI<VisibilityResponse>(`/docs/pages/${slug}/visibility`, {
      method: "PATCH",
      body: JSON.stringify({ is_public: isPublic }),
      headers: adminToken ? { "X-Admin-Token": adminToken } : {},
    }),

  // ── Manajemen konten (Guru) ──
  manage: {
    status: (guruToken: string | null = null) =>
      fetchAPI<ManageStatus>("/manage/status", {
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),

    // Materi
    listLessons: (guruToken: string | null = null) =>
      fetchAPI<{ lessons: any[]; total: number }>("/manage/lessons", {
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    createLesson: (body: LessonIn, guruToken: string | null = null) =>
      fetchAPI<any>("/manage/lessons", {
        method: "POST",
        body: JSON.stringify(body),
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    updateLesson: (id: string, body: LessonIn, guruToken: string | null = null) =>
      fetchAPI<any>(`/manage/lessons/${id}`, {
        method: "PUT",
        body: JSON.stringify(body),
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    deleteLesson: (id: string, guruToken: string | null = null) =>
      fetchAPI<{ message: string }>(`/manage/lessons/${id}`, {
        method: "DELETE",
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),

    // Kuis
    listQuizzes: (guruToken: string | null = null) =>
      fetchAPI<{ quizzes: any[]; total: number }>("/manage/quizzes", {
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    createQuiz: (body: QuizIn, guruToken: string | null = null) =>
      fetchAPI<any>("/manage/quizzes", {
        method: "POST",
        body: JSON.stringify(body),
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    updateQuiz: (id: string, body: QuizIn, guruToken: string | null = null) =>
      fetchAPI<any>(`/manage/quizzes/${id}`, {
        method: "PUT",
        body: JSON.stringify(body),
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    deleteQuiz: (id: string, guruToken: string | null = null) =>
      fetchAPI<{ message: string }>(`/manage/quizzes/${id}`, {
        method: "DELETE",
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),

    // Kamus
    listDictionary: (guruToken: string | null = null) =>
      fetchAPI<{ entries: DictEntry[]; total: number }>("/manage/dictionary", {
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    upsertDict: (body: { latin: string; bali: string; meaning?: string; note?: string }, guruToken: string | null = null) =>
      fetchAPI<DictEntry>("/manage/dictionary", {
        method: "POST",
        body: JSON.stringify(body),
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),
    deleteDict: (latin: string, guruToken: string | null = null) =>
      fetchAPI<{ message: string }>(`/manage/dictionary/${encodeURIComponent(latin)}`, {
        method: "DELETE",
        headers: guruToken ? { "X-Admin-Token": guruToken } : {},
      }),

    // Referensi aksara untuk form
    aksaraReference: () =>
      fetchAPI<{ groups: AksaraRefGroup[] }>("/manage/aksara"),
  },
}
