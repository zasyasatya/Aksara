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

// ── Machine Learning (Panel Admin → Model ML) ───────────────────────────

export type MlSplit = "train" | "val" | "test"
export type MlSource = "synthetic" | "upload" | "canvas" | "import"
export type MlSampleStatus = "labeled" | "unlabeled" | "review"
export type MlJobStatus = "queued" | "running" | "done" | "failed" | "cancelled"

export interface MlClass {
  label: string
  glyph: string
  name: string
  latin: string
  group: string
  active?: boolean
}

export interface MlHyperparamSpec {
  key: string
  label: string
  type: "int" | "float"
  default: number
  min: number
  max: number
}

export interface MlArchitecture {
  id: string
  name: string
  family: string
  trainable: boolean
  description: string
  pros: string[]
  cons: string[]
  hyperparams: MlHyperparamSpec[]
}

export interface MlSample {
  id: string
  label: string | null
  status: MlSampleStatus
  split: MlSplit
  source: MlSource
  note: string
  meta: Record<string, any>
  created_at: string
  updated_at: string
  bytes: number
  feature_preview?: string | null
}

export interface MlBundledDataset {
  name: string
  folder: string
  description: string
  version: number | null
  created_at: string | null
  license: { images?: string; font?: string } | null
  generator: { seed?: number; strength?: number; per_class?: number; groups?: string[] } | null
  total: number
  per_split: Record<MlSplit, number>
  n_classes: number
  labels: string[]
  classes: MlClass[]
  readme: boolean
}

export interface MlDatasetStats {
  total: number
  labeled: number
  unlabeled: number
  review: number
  per_split: Record<MlSplit, number>
  per_source: Record<string, number>
  per_label: Record<string, { train: number; val: number; test: number; total: number }>
  n_classes: number
  min_per_class: number
  max_per_class: number
  classes_without_data: string[]
  updated_at?: string
  version: number
}

export interface MlMetricsSummary {
  accuracy: number
  macro_precision: number
  macro_recall: number
  macro_f1: number
  weighted_precision: number
  weighted_recall: number
  weighted_f1: number
  top3_accuracy?: number
  log_loss?: number
  n_samples: number
  train_accuracy?: number
}

export interface MlEpochRecord {
  epoch: number
  loss: number | null
  train_acc: number | null
  val_acc: number | null
  seconds?: number
}

export interface MlModelEntry {
  id: string
  name: string
  notes: string
  arch: string
  arch_name: string
  hyperparams: Record<string, number>
  classes: string[]
  n_classes: number
  n_params: number
  size_bytes: number
  created_at: string
  promoted_at?: string
  train_seconds: number
  dataset_version?: number
  dataset_size: { train: number; val: number; test: number }
  eval_split: string
  metrics: MlMetricsSummary
  job_id?: string
  is_production: boolean
}

export interface MlPerClass {
  label: string
  precision: number
  recall: number
  f1: number
  support: number
  predicted: number
  tp: number
  fp: number
  fn: number
}

export interface MlReport extends MlMetricsSummary {
  error_rate: number
  n_classes_present: number
  per_class: MlPerClass[]
  confusion_matrix: number[][]
  class_names: string[]
  top_confusions: { true: string; pred: string; count: number }[]
  mean_confidence?: number
  confident_rate?: number
  confident_accuracy?: number | null
  eval_split: string
  train_samples: number
  val_samples: number
  test_samples: number
  train_seconds: number
  history: MlEpochRecord[]
  misclassified: { sample_id: string | null; true: string; pred: string; confidence: number }[]
}

export interface MlJob {
  id: string
  status: MlJobStatus
  arch: string
  arch_name: string
  hyperparams: Record<string, number>
  name: string
  notes: string
  auto_promote: boolean
  created_at: number
  started_at: number | null
  finished_at: number | null
  progress: number
  epoch: number
  total_epochs: number
  history: MlEpochRecord[]
  message: string
  error: string | null
  model_id: string | null
  metrics: MlMetricsSummary | null
  cancel_requested: boolean
  dataset: { labeled: number; n_classes: number; per_split: Record<MlSplit, number> }
}

export interface MlPrediction {
  model_id: string
  model_name: string
  arch: string
  is_production: boolean
  label: string
  glyph: string
  name: string
  latin: string
  confidence: number
  margin: number
  confident: boolean
  top: { label: string; glyph: string; name: string; latin: string; probability: number }[]
  preview: string
  error?: string
}

export interface MlStatus {
  mode: "dev" | "prod"
  is_admin: boolean
  production_model: MlModelEntry | null
  dataset: { total: number; labeled: number; unlabeled: number; review: number; per_split: Record<MlSplit, number>; n_classes: number; version: number }
  models_total: number
  active_job: { id: string; status: MlJobStatus; arch: string; progress: number; message: string } | null
  font_available: boolean
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

  // ── Machine Learning (retraining, dataset, labeling, registry) ──
  ml: {
    status: () => fetchAPI<MlStatus>("/ml/status", { headers: authHeaders() }),
    architectures: () => fetchAPI<{ architectures: MlArchitecture[] }>("/ml/architectures"),
    classes: () => fetchAPI<{ active: MlClass[]; available: MlClass[] }>("/ml/classes"),
    setClasses: (labels: string[]) =>
      fetchAPI<{ active: MlClass[]; message: string }>("/ml/classes", {
        method: "PUT",
        body: JSON.stringify({ labels }),
        headers: authHeaders(),
      }),

    // Dataset
    datasetStats: () => fetchAPI<MlDatasetStats>("/ml/dataset/stats", { headers: authHeaders() }),
    listSamples: (params: { label?: string; split?: string; source?: string; status?: string; q?: string; limit?: number; offset?: number; order?: "newest" | "oldest" } = {}) => {
      const sp = new URLSearchParams()
      Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== "") sp.set(k, String(v)) })
      const qs = sp.toString() ? `?${sp.toString()}` : ""
      return fetchAPI<{ samples: MlSample[]; total: number; offset: number; limit: number }>(`/ml/dataset/samples${qs}`, { headers: authHeaders() })
    },
    getSample: (id: string) => fetchAPI<MlSample>(`/ml/dataset/samples/${id}`, { headers: authHeaders() }),
    sampleImageUrl: (id: string) => `${API_BASE}/ml/dataset/samples/${id}/image`,
    addSample: (body: { image: string; label?: string | null; source?: MlSource; split?: MlSplit; note?: string }) =>
      fetchAPI<MlSample>("/ml/dataset/samples", { method: "POST", body: JSON.stringify(body), headers: authHeaders() }),
    addSamplesBulk: (items: { image: string; label?: string | null; source?: MlSource; split?: MlSplit; note?: string }[]) =>
      fetchAPI<{ added: number; skipped: number; samples: MlSample[] }>("/ml/dataset/samples/bulk", {
        method: "POST", body: JSON.stringify({ items }), headers: authHeaders(),
      }),
    updateSample: (id: string, body: { label?: string; clear_label?: boolean; split?: MlSplit; status?: MlSampleStatus; note?: string }) =>
      fetchAPI<MlSample>(`/ml/dataset/samples/${id}`, { method: "PATCH", body: JSON.stringify(body), headers: authHeaders() }),
    deleteSample: (id: string) =>
      fetchAPI<{ message: string }>(`/ml/dataset/samples/${id}`, { method: "DELETE", headers: authHeaders() }),
    bulkLabel: (body: { ids: string[]; label?: string; split?: MlSplit; status?: MlSampleStatus }) =>
      fetchAPI<{ updated: number; message: string }>("/ml/dataset/bulk-label", { method: "POST", body: JSON.stringify(body), headers: authHeaders() }),
    bulkDelete: (ids: string[]) =>
      fetchAPI<{ removed: number; message: string }>("/ml/dataset/bulk-delete", { method: "POST", body: JSON.stringify({ ids }), headers: authHeaders() }),
    generateSynthetic: (body: { per_class: number; seed?: number; strength?: number; replace_existing?: boolean }) =>
      fetchAPI<{ added: number; removed: number; seconds: number; stats: MlDatasetStats; message: string }>("/ml/dataset/generate-synthetic", {
        method: "POST", body: JSON.stringify(body), headers: authHeaders(),
      }),
    bundledDatasets: () =>
      fetchAPI<{ root: string | null; datasets: MlBundledDataset[] }>("/ml/dataset/bundled", { headers: authHeaders() }),
    importBundled: (body: { name: string; activate_classes?: boolean; replace_existing?: boolean; keep_split?: boolean }) =>
      fetchAPI<{ name: string; added: number; removed: number; skipped: number; classes: string[]; seconds: number; stats: MlDatasetStats; message: string }>(
        "/ml/dataset/import-bundled", { method: "POST", body: JSON.stringify(body), headers: authHeaders() },
      ),
    rebalance: (body: { val_ratio: number; test_ratio: number; seed?: number }) =>
      fetchAPI<{ per_split: Record<MlSplit, number>; message: string }>("/ml/dataset/rebalance", { method: "POST", body: JSON.stringify(body), headers: authHeaders() }),
    clearDataset: (source?: MlSource) =>
      fetchAPI<{ removed: number; message: string }>(`/ml/dataset/clear${source ? `?source=${source}` : ""}`, { method: "POST", headers: authHeaders() }),

    // Training
    train: (body: { arch: string; hyperparams?: Record<string, number>; name?: string; notes?: string; auto_promote?: boolean }) =>
      fetchAPI<MlJob>("/ml/train", { method: "POST", body: JSON.stringify(body), headers: authHeaders() }),
    jobs: () => fetchAPI<{ jobs: MlJob[]; active: MlJob | null }>("/ml/train/jobs", { headers: authHeaders() }),
    job: (id: string) => fetchAPI<MlJob>(`/ml/train/jobs/${id}`, { headers: authHeaders() }),
    cancelJob: (id: string) => fetchAPI<{ message: string }>(`/ml/train/jobs/${id}`, { method: "DELETE", headers: authHeaders() }),

    // Registry
    models: () => fetchAPI<{ models: MlModelEntry[]; production_model_id: string | null }>("/ml/models", { headers: authHeaders() }),
    model: (id: string) => fetchAPI<{ model: MlModelEntry; report: MlReport | null }>(`/ml/models/${id}`, { headers: authHeaders() }),
    updateModel: (id: string, body: { name?: string; notes?: string }) =>
      fetchAPI<MlModelEntry>(`/ml/models/${id}`, { method: "PATCH", body: JSON.stringify(body), headers: authHeaders() }),
    deleteModel: (id: string) => fetchAPI<{ message: string }>(`/ml/models/${id}`, { method: "DELETE", headers: authHeaders() }),
    setProduction: (model_id: string | null) =>
      fetchAPI<{ production_model_id: string | null; message: string }>("/ml/models/production", {
        method: "PUT", body: JSON.stringify({ model_id }), headers: authHeaders(),
      }),

    // Prediksi
    predict: (body: { image: string; model_id?: string | null; top_k?: number }) =>
      fetchAPI<MlPrediction>("/ml/predict", { method: "POST", body: JSON.stringify(body) }),
    compare: (image: string, model_ids: string[]) =>
      fetchAPI<{ results: MlPrediction[] }>("/ml/predict/compare", { method: "POST", body: JSON.stringify({ image, model_ids }), headers: authHeaders() }),
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
export const SITE_HASHTAGS = "#AKSA #AksaraBali #MelestarikanBudaya"
