"use client"

import { useEffect, useState } from "react"
import { api, QuizIn, QuizQuestionIn, QuizOptionIn } from "@/lib/api"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Field, TextInput, TextArea, Select, MiniToggle, ConfirmDelete, Flash, TabHeader } from "@/components/guru/ui"
import { BaliInput } from "@/components/guru/bali-input"
import { Gamepad2, Loader2, Pencil, Plus, Trash2, X } from "lucide-react"

const QUIZ_TYPES = [
  { value: "multiple_choice", label: "Pilihan Ganda — pilih aksara yang benar" },
  { value: "true_false", label: "Benar/Salah — cocokkan Latin ↔ Aksara" },
  { value: "gantungan_choice", label: "Pilihan Gantungan — cluster konsonan" },
  { value: "write_aksara", label: "Menulis Aksara — murid menulis kata" },
]

const EMPTY_Q: QuizQuestionIn = { text: "", latin: "", bali: "", hint: "" }

/** Id pilihan huruf (a, b, …) yang belum terpakai. */
function nextOptionId(existing: QuizOptionIn[]): string {
  const used = new Set(existing.map(o => o.id))
  for (let i = 0; i < 26; i++) {
    const id = String.fromCharCode(97 + i)
    if (!used.has(id)) return id
  }
  return `opt-${existing.length + 1}`
}

export function TabsKuis() {
  const [quizzes, setQuizzes] = useState<any[]>([])
  const [lessons, setLessons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<QuizIn | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [flash, setFlash] = useState<{ kind: "ok" | "err"; text: string } | null>(null)

  const load = () => {
    Promise.all([api.manage.listQuizzes(), api.manage.listLessons()])
      .then(([q, l]) => { setQuizzes(q.quizzes); setLessons(l.lessons) })
      .catch((e) => setFlash({ kind: "err", text: (e as Error).message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const startCreate = () => {
    setEditId(null)
    setEditing({
      lesson_id: lessons[0]?.id ?? "",
      type: "multiple_choice",
      difficulty: "easy",
      question: { ...EMPTY_Q },
      options: [],
      correct_answer: "",
      explanation: "",
      xp: 10,
    })
  }

  const startEdit = (q: any) => {
    setEditId(q.id)
    setEditing({
      lesson_id: q.lesson_id ?? "",
      type: q.type ?? "multiple_choice",
      difficulty: q.difficulty ?? "easy",
      question: {
        text: q.question?.text ?? "",
        latin: q.question?.latin ?? "",
        bali: q.question?.bali ?? "",
        hint: q.question?.hint ?? "",
      },
      options: (q.options ?? []).map((o: any, i: number) => ({ id: o.id ?? String.fromCharCode(97 + i), label: o.label ?? "", latin: o.latin ?? "", bali: o.bali ?? "", is_correct: o.is_correct ?? false })),
      correct_answer: q.correct_answer ?? "",
      explanation: q.explanation ?? "",
      xp: q.xp ?? 10,
    })
  }

  const save = async () => {
    if (!editing) return
    if (!editing.lesson_id) return setFlash({ kind: "err", text: "Pilih materi untuk kuis ini." })
    if (!editing.question.text.trim()) return setFlash({ kind: "err", text: "Teks soal wajib diisi." })
    if (editing.type === "write_aksara") {
      if (!(editing.question.latin ?? "").trim()) return setFlash({ kind: "err", text: "Kuis menulis: kolom Latin (kata soal) wajib diisi." })
      if (!(editing.question.bali ?? "").trim()) return setFlash({ kind: "err", text: "Kuis menulis: kunci jawaban (aksara) wajib diisi." })
    } else if (editing.type !== "true_false") {
      if (!editing.options.some(o => o.is_correct)) return setFlash({ kind: "err", text: "Tandai satu jawaban benar pada pilihan." })
    }
    setSaving(true)
    try {
      if (editId) {
        await api.manage.updateQuiz(editId, editing)
        setFlash({ kind: "ok", text: `Kuis ${editId} diperbarui.` })
      } else {
        const r = await api.manage.createQuiz(editing)
        setFlash({ kind: "ok", text: `Kuis ${r.id} ditambahkan.` })
      }
      setEditing(null)
      setEditId(null)
      load()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id: string) => {
    try {
      const r = await api.manage.deleteQuiz(id)
      setFlash({ kind: "ok", text: r.message })
      load()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    }
  }

  return (
    <div className="space-y-4">
      {flash && <Flash kind={flash.kind} text={flash.text} onDone={() => setFlash(null)} />}

      {loading ? (
        <div className="flex items-center justify-center gap-3 py-16 text-charcoal/50">
          <Loader2 className="h-5 w-5 animate-spin" /> Memuat kuis…
        </div>
      ) : (
        <>
          <Card className="overflow-hidden bg-white shadow-soft">
            <TabHeader
              title="Bank Kuis"
              subtitle={`${quizzes.length} kuis · semua tipe termasuk “Menulis Aksara”`}
              onAdd={startCreate}
              addLabel="+ Tambah Kuis"
            />
            <ul className="divide-y divide-sand">
              {quizzes.map((q) => (
                <li key={q.id} className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sand/70 text-deep-brown">
                    <Gamepad2 className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-deep-brown">{q.question?.text || q.id}</span>
                      <Badge variant="outline">{q.type === "write_aksara" ? "Menulis Aksara" : q.type}</Badge>
                      <Badge variant={q.difficulty === "easy" ? "success" : q.difficulty === "hard" ? "warning" : "default"}>{q.difficulty}</Badge>
                    </div>
                    <div className="mt-0.5 truncate text-xs text-charcoal/50">
                      {q.lesson_id} · {q.options?.length ?? 0} pilihan · {q.xp} XP
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => startEdit(q)}
                      className="inline-flex items-center gap-1 rounded-full border border-sand bg-white px-3 py-1.5 text-xs font-semibold text-charcoal/70 hover:border-sage/60 hover:text-sage"
                    >
                      <Pencil className="h-3 w-3" /> Edit
                    </button>
                    <ConfirmDelete onConfirm={() => remove(q.id)} />
                  </div>
                </li>
              ))}
            </ul>
          </Card>

          {editing && (
            <QuizForm
              editing={editing}
              isEdit={!!editId}
              lessons={lessons}
              setEditing={setEditing}
              save={save}
              saveCancel={() => { setEditing(null); setEditId(null) }}
              saving={saving}
            />
          )}
        </>
      )}
    </div>
  )
}

function QuizForm({
  editing, isEdit, lessons, setEditing, save, saveCancel, saving,
}: {
  editing: QuizIn
  isEdit: boolean
  lessons: any[]
  setEditing: (q: QuizIn) => void
  save: () => void
  saveCancel: () => void
  saving: boolean
}) {
  const set = <K extends keyof QuizIn>(key: K, val: QuizIn[K]) => setEditing({ ...editing, [key]: val })
  const setQ = <K extends keyof QuizQuestionIn>(key: K, val: string) =>
    setEditing({ ...editing, question: { ...editing.question, [key]: val } })

  const isWrite = editing.type === "write_aksara"
  const isTrueFalse = editing.type === "true_false"
  const needsOptions = !isWrite && !isTrueFalse

  const addOption = () =>
    set("options", [...editing.options, { id: nextOptionId(editing.options), label: "", latin: "", bali: "", is_correct: false }])
  const updateOption = (i: number, patch: Partial<QuizOptionIn>) =>
    set("options", editing.options.map((o, j) => (j === i ? { ...o, ...patch } : o)))
  const removeOption = (i: number) => set("options", editing.options.filter((_, j) => j !== i))
  const markCorrect = (i: number) =>
    set("options", editing.options.map((o, j) => ({ ...o, is_correct: j === i })))

  return (
    <Card className="overflow-hidden bg-white shadow-medium">
      <div className="flex items-center justify-between border-b border-sand px-6 py-4">
        <h2 className="font-display text-lg font-bold text-deep-brown">{isEdit ? "Edit Kuis" : "Kuis Baru"}</h2>
        <button type="button" onClick={saveCancel} className="text-charcoal/40 hover:text-terracotta"><X className="h-5 w-5" /></button>
      </div>

      <div className="space-y-5 p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Materi terkait">
            <Select value={editing.lesson_id} onChange={(e) => set("lesson_id", e.target.value)}>
              {lessons.map((l) => <option key={l.id} value={l.id}>{l.title} (Level {l.level})</option>)}
            </Select>
          </Field>
          <Field label="Tipe soal">
            <Select value={editing.type} onChange={(e) => set("type", e.target.value)}>
              {QUIZ_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </Select>
          </Field>
          <Field label="Kesulitan">
            <Select value={editing.difficulty} onChange={(e) => set("difficulty", e.target.value as QuizIn["difficulty"])}>
              <option value="easy">Mudah</option>
              <option value="medium">Sedang</option>
              <option value="hard">Sulit</option>
            </Select>
          </Field>
          <Field label="Reward XP">
            <TextInput type="number" min={0} value={editing.xp} onChange={(e) => set("xp", Number(e.target.value))} />
          </Field>
        </div>

        <Field label="Teks soal" hint="mis. “Tulis aksara untuk kata berikut” atau “Aksara apa untuk kata berikut?”">
          <TextArea rows={2} value={editing.question.text} onChange={(e) => setQ("text", e.target.value)} />
        </Field>

        {isWrite ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Kata soal (Latin)" hint="Kata yang tampil untuk ditulis murid">
              <TextInput value={editing.question.latin ?? ""} onChange={(e) => setQ("latin", e.target.value)} placeholder="mis. bali" />
            </Field>
            <Field label="Kunci jawaban (Aksara)" hint="Tulisan murid divalidasi otomatis terhadap kunci ini">
              <BaliInput value={editing.question.bali ?? ""} onChange={(v) => setQ("bali", v)} placeholder="mis. ᬩᬮᬶ" />
            </Field>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Kata / frasa (Latin)">
              <TextInput value={editing.question.latin ?? ""} onChange={(e) => setQ("latin", e.target.value)} placeholder="mis. saka" />
            </Field>
            <Field label="Aksara penampil (opsional)" hint="Tampil di soal; untuk Benar/Salah ini adalah pasangan yang dinilai">
              <BaliInput value={editing.question.bali ?? ""} onChange={(v) => setQ("bali", v)} placeholder="mis. ᬲᬓ" />
            </Field>
          </div>
        )}

        <Field label="Petunjuk (hint, opsional)">
          <TextInput value={editing.question.hint ?? ""} onChange={(e) => setQ("hint", e.target.value)} placeholder="mis. Huruf ‘s’ memakai aksara S" />
        </Field>

        {needsOptions && (
          <div className="rounded-2xl border border-sand p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-semibold text-deep-brown">Pilihan jawaban</span>
              <button type="button" onClick={addOption} className="inline-flex items-center gap-1 rounded-full bg-sage/15 px-3 py-1.5 text-xs font-semibold text-sage hover:bg-sage/25">
                <Plus className="h-3 w-3" /> Tambah Pilihan
              </button>
            </div>
            <div className="space-y-2">
              {editing.options.map((o, i) => (
                <div key={i} className={`grid gap-2 rounded-xl border p-3 sm:grid-cols-[1fr_1fr_auto_auto] ${o.is_correct ? "border-sage/60 bg-sage/5" : "border-sand bg-cream/40"}`}>
                  <TextInput
                    value={o.label}
                    onChange={(e) => updateOption(i, { label: e.target.value })}
                    placeholder={`Pilihan ${String.fromCharCode(65 + i)}`}
                    className="text-sm"
                  />
                  <BaliInputMini value={o.bali} onChange={(v) => updateOption(i, { bali: v })} placeholder="aksara (opsional)" />
                  <button
                    type="button"
                    onClick={() => markCorrect(i)}
                    className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                      o.is_correct ? "bg-sage text-white" : "border border-sand bg-white text-charcoal/50 hover:border-sage/50"
                    }`}
                  >
                    {o.is_correct ? "✓ Benar" : "Jawaban benar?"}
                  </button>
                  <button
                    type="button"
                    onClick={() => removeOption(i)}
                    className="rounded-full border border-sand bg-white px-2.5 py-1.5 text-terracotta hover:border-terracotta/40"
                    title="Hapus pilihan"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
              {editing.options.length === 0 && (
                <p className="text-sm text-charcoal/50">Belum ada pilihan — klik “Tambah Pilihan”.</p>
              )}
            </div>
          </div>
        )}

        <Field label="Penjelasan (explanation)" hint="Tampil setelah murid menjawab">
          <TextArea rows={2} value={editing.explanation ?? ""} onChange={(e) => set("explanation", e.target.value)} />
        </Field>
      </div>

      <div className="flex justify-end gap-3 border-t border-sand px-6 py-4">
        <button type="button" onClick={saveCancel} className="rounded-full border border-sand bg-white px-5 py-2 text-sm font-semibold text-charcoal/60">Batal</button>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="rounded-full bg-saffron px-6 py-2 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-saffron-dark disabled:opacity-60"
        >
          {saving ? "Menyimpan…" : isEdit ? "Simpan Perubahan" : "Tambah Kuis"}
        </button>
      </div>
    </Card>
  )
}

/** BaliInput ringkas untuk baris pilihan (tanpa keyboard, opsional). */
function BaliInputMini({ value, onChange, placeholder }: { value?: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-xl border border-sand bg-cream/50 px-3 py-2 font-bali text-base outline-none focus:border-saffron focus:bg-white"
    />
  )
}
