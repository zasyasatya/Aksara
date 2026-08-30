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

// ── Otentikasi (login username + password → sesi) ───────────────────────

export type AuthRole = "admin" | "guru"

export interface LoginResponse {
  ok: boolean
  message: string
  mode: string
  role?: AuthRole
  session_token?: string | null
}

export interface SessionInfo {
  role: AuthRole | null
  is_admin: boolean
  is_guru: boolean
  mode: string
}

export interface Session {
  token: string
  role: AuthRole
}

const SESSION_KEY = "aksara_session_token"
const SESSION_ROLE_KEY = "aksara_session_role"

/** Ambil sesi login tersimpan (null bila belum login). Hanya jalan di browser. */
export function getSession(): Session | null {
  if (typeof window === "undefined") return null
  const token = window.localStorage.getItem(SESSION_KEY)
  const role = window.localStorage.getItem(SESSION_ROLE_KEY)
  if (!token || (role !== "admin" && role !== "guru")) return null
  return { token, role: role as AuthRole }
}

/** Simpan (atau hapus) sesi login. */
export function setSession(token: string | null, role: AuthRole | null): void {
  if (typeof window === "undefined") return
  if (token && role) {
    window.localStorage.setItem(SESSION_KEY, token)
    window.localStorage.setItem(SESSION_ROLE_KEY, role)
  } else {
    window.localStorage.removeItem(SESSION_KEY)
    window.localStorage.removeItem(SESSION_ROLE_KEY)
  }
}

/** Header Authorization untuk sesi aktif (kosong bila belum login). */
function authHeaders(): Record<string, string> {
  const session = getSession()
  return session ? { Authorization: `Bearer ${session.token}` } : {}
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
  getDocsPages: () =>
    fetchAPI<DocsPagesResponse>("/docs/pages", {
      headers: authHeaders(),
    }),

  setDocVisibility: (slug: string, isPublic: boolean) =>
    fetchAPI<VisibilityResponse>(`/docs/pages/${slug}/visibility`, {
      method: "PATCH",
      body: JSON.stringify({ is_public: isPublic }),
      headers: authHeaders(),
    }),

  // ── Otentikasi (Guru & Admin) ──
  auth: {
    info: () =>
      fetchAPI<{ mode: "dev" | "prod" }>("/auth/info"),
    login: (role: AuthRole, username: string, password: string) =>
      fetchAPI<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ role, username, password }),
      }),
    logout: () =>
      fetchAPI<{ ok: boolean; message: string }>("/auth/logout", {
        method: "POST",
        headers: authHeaders(),
      }),
    session: () =>
      fetchAPI<SessionInfo>("/auth/session", {
        headers: authHeaders(),
      }),
  },

  // ── Manajemen konten (Guru) ──
  manage: {
    status: () =>
      fetchAPI<ManageStatus>("/manage/status", {
        headers: authHeaders(),
      }),

    // Materi
    listLessons: () =>
      fetchAPI<{ lessons: any[]; total: number }>("/manage/lessons", {
        headers: authHeaders(),
      }),
    createLesson: (body: LessonIn) =>
      fetchAPI<any>("/manage/lessons", {
        method: "POST",
        body: JSON.stringify(body),
        headers: authHeaders(),
      }),
    updateLesson: (id: string, body: LessonIn) =>
      fetchAPI<any>(`/manage/lessons/${id}`, {
        method: "PUT",
        body: JSON.stringify(body),
        headers: authHeaders(),
      }),
    deleteLesson: (id: string) =>
      fetchAPI<{ message: string }>(`/manage/lessons/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      }),

    // Kuis
    listQuizzes: () =>
      fetchAPI<{ quizzes: any[]; total: number }>("/manage/quizzes", {
        headers: authHeaders(),
      }),
    createQuiz: (body: QuizIn) =>
      fetchAPI<any>("/manage/quizzes", {
        method: "POST",
        body: JSON.stringify(body),
        headers: authHeaders(),
      }),
    updateQuiz: (id: string, body: QuizIn) =>
      fetchAPI<any>(`/manage/quizzes/${id}`, {
        method: "PUT",
        body: JSON.stringify(body),
        headers: authHeaders(),
      }),
    deleteQuiz: (id: string) =>
      fetchAPI<{ message: string }>(`/manage/quizzes/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
      }),

    // Kamus
    listDictionary: () =>
      fetchAPI<{ entries: DictEntry[]; total: number }>("/manage/dictionary", {
        headers: authHeaders(),
      }),
    upsertDict: (body: { latin: string; bali: string; meaning?: string; note?: string }) =>
      fetchAPI<DictEntry>("/manage/dictionary", {
        method: "POST",
        body: JSON.stringify(body),
        headers: authHeaders(),
      }),
    deleteDict: (latin: string) =>
      fetchAPI<{ message: string }>(`/manage/dictionary/${encodeURIComponent(latin)}`, {
        method: "DELETE",
        headers: authHeaders(),
      }),

    // Referensi aksara untuk form
    aksaraReference: () =>
      fetchAPI<{ groups: AksaraRefGroup[] }>("/manage/aksara"),
  },

  // ── Engagement & sekolah mitra ──
  getStats: () =>
    fetchAPI<{ visits: number; twibbons: number; schools: any[] }>("/stats"),

  trackVisit: () =>
    fetchAPI<{ message: string }>("/stats/visit", { method: "POST" }).catch(() => ({})),

  trackTwibbon: () =>
    fetchAPI<{ message: string }>("/stats/twibbon", { method: "POST" }).catch(() => ({})),

  getSchools: () =>
    fetchAPI<{ schools: any[]; total: number }>("/stats/schools"),

  applySchool: (body: { school: string; region?: string; students?: number; contact: string; note?: string }) =>
    fetchAPI<any>("/stats/schools", {
      method: "POST",
      body: JSON.stringify(body),
    }),
}

/** URL publik aplikasi (untuk teks share & meta). Bisa di-override via env. */
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://aksara.id"
export const SITE_HASHTAGS = "#AksaraBali #MelestarikanBudaya"
