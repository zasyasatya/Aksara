"use client"

import { useEffect, useMemo, useState } from "react"
import { api, LessonIn, AksaraRefGroup } from "@/lib/api"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Field, TextInput, TextArea, Select, MiniToggle, ConfirmDelete, Flash, TabHeader } from "@/components/guru/ui"
import { BaliInput } from "@/components/guru/bali-input"
import { BookOpen, ChevronDown, Loader2, Pencil, Plus, X } from "lucide-react"

const CATEGORIES = [
  { value: "wresastra", label: "Wresastra (18 aksara)" },
  { value: "pangangge", label: "Pangangge (tanda)" },
  { value: "gantungan", label: "Gantungan (cluster)" },
  { value: "swalalita", label: "Swalalita (Sanskerta/Kawi)" },
  { value: "kalimat", label: "Kalimat" },
  { value: "umum", label: "Umum" },
]

const LEVELS = [
  { value: 1, label: "1 — Pemula" },
  { value: 2, label: "2 — Pangangge Suara" },
  { value: 3, label: "3 — Tengenan" },
  { value: 4, label: "4 — Gantungan" },
  { value: 5, label: "5 — Swalalita" },
  { value: 6, label: "6 — Kalimat" },
]

const EMPTY: LessonIn = {
  title: "",
  level: 1,
  order: 0,
  category: "wresastra",
  aksara_ids: [],
  pangangge_ids: [],
  estimated_minutes: 10,
  xp_reward: 50,
  prerequisites: [],
  quiz_ids: [],
  is_published: true,
}

export function TabsMateri({ token }: { token: string | null }) {
  const [lessons, setLessons] = useState<any[]>([])
  const [aksara, setAksara] = useState<AksaraRefGroup[]>([])
  const [quizList, setQuizList] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<LessonIn | null>(null)
  const [editId, setEditId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [flash, setFlash] = useState<{ kind: "ok" | "err"; text: string } | null>(null)

  const load = () => {
    Promise.all([
      api.manage.listLessons(token),
      api.manage.aksaraReference(),
      api.manage.listQuizzes(token),
    ])
      .then(([l, a, q]) => {
        setLessons(l.lessons)
        setAksara(a.groups)
        setQuizList(q.quizzes)
      })
      .catch((e) => setFlash({ kind: "err", text: (e as Error).message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [token])

  const startCreate = () => {
    setEditId(null)
    setEditing({ ...EMPTY, order: lessons.length + 1 })
  }

  const startEdit = (l: any) => {
    setEditId(l.id)
    setEditing({
      title: l.title ?? "",
      slug: l.slug,
      description: l.description ?? "",
      story: l.story ?? "",
      level: l.level ?? 1,
      order: l.order ?? 0,
      category: l.category ?? "wresastra",
      aksara_ids: l.aksara_ids ?? [],
      pangangge_ids: l.pangangge_ids ?? [],
      estimated_minutes: l.estimated_minutes ?? 10,
      xp_reward: l.xp_reward ?? 50,
      prerequisites: l.prerequisites ?? [],
      quiz_ids: l.quiz_ids ?? [],
      is_published: l.is_published ?? true,
      thumbnail: l.thumbnail ?? "",
    })
  }

  const toggleIn = (key: "aksara_ids" | "pangangge_ids" | "quiz_ids", id: string) => {
    if (!editing) return
    const arr = editing[key]
    setEditing({ ...editing, [key]: arr.includes(id) ? arr.filter(x => x !== id) : [...arr, id] })
  }

  const save = async () => {
    if (!editing) return
    if (!editing.title.trim()) {
      setFlash({ kind: "err", text: "Judul materi wajib diisi." })
      return
    }
    setSaving(true)
    try {
      if (editId) {
        await api.manage.updateLesson(editId, editing, token)
        setFlash({ kind: "ok", text: `Materi “${editing.title}” diperbarui.` })
      } else {
        await api.manage.createLesson(editing, token)
        setFlash({ kind: "ok", text: `Materi “${editing.title}” ditambahkan.` })
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
      const r = await api.manage.deleteLesson(id, token)
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
          <Loader2 className="h-5 w-5 animate-spin" /> Memuat materi…
        </div>
      ) : (
        <>
          <Card className="overflow-hidden bg-white shadow-soft">
            <TabHeader
              title="Materi Pembelajaran"
              subtitle={`${lessons.length} materi · urutan & level menentukan alur belajar murid`}
              onAdd={startCreate}
              addLabel="+ Tambah Materi"
            />

            <ul className="divide-y divide-sand">
              {lessons.map((l) => (
                <li key={l.id} className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-sand/70 font-bali text-lg text-deep-brown">
                    {l.thumbnail || <BookOpen className="h-5 w-5" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-deep-brown">{l.title}</span>
                      <Badge variant="outline">Level {l.level}</Badge>
                      <Badge variant="default">Lv urut {l.order}</Badge>
                      {!l.is_published && <Badge variant="warning">Nonaktif</Badge>}
                    </div>
                    <div className="mt-0.5 truncate text-xs text-charcoal/50">
                      {l.description || "—"} · {l.aksara_ids?.length ?? 0} aksara · {l.estimated_minutes} mnt · {l.xp_reward} XP
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => startEdit(l)}
                      className="inline-flex items-center gap-1 rounded-full border border-sand bg-white px-3 py-1.5 text-xs font-semibold text-charcoal/70 hover:border-sage/60 hover:text-sage"
                    >
                      <Pencil className="h-3 w-3" /> Edit
                    </button>
                    <ConfirmDelete onConfirm={() => remove(l.id)} />
                  </div>
                </li>
              ))}
            </ul>
          </Card>

          {editing && (
            <LessonForm
              editing={editing}
              isEdit={!!editId}
              setEditing={setEditing}
              aksara={aksara}
              quizList={quizList}
              toggleIn={toggleIn}
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

function LessonForm({
  editing, isEdit, setEditing, aksara, quizList, toggleIn, save, saveCancel, saving,
}: {
  editing: LessonIn
  isEdit: boolean
  setEditing: (l: LessonIn) => void
  aksara: AksaraRefGroup[]
  quizList: any[]
  toggleIn: (key: "aksara_ids" | "pangangge_ids" | "quiz_ids", id: string) => void
  save: () => void
  saveCancel: () => void
  saving: boolean
}) {
  const set = <K extends keyof LessonIn>(key: K, val: LessonIn[K]) => setEditing({ ...editing, [key]: val })

  return (
    <Card className="overflow-hidden bg-white shadow-medium">
      <div className="flex items-center justify-between border-b border-sand px-6 py-4">
        <h2 className="font-display text-lg font-bold text-deep-brown">
          {isEdit ? "Edit Materi" : "Materi Baru"}
        </h2>
        <button type="button" onClick={saveCancel} className="text-charcoal/40 hover:text-terracotta">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-5 p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Judul materi" className="sm:col-span-2">
            <TextInput value={editing.title} onChange={(e) => set("title", e.target.value)} placeholder="mis. Ha Na Ca Ra Ka" />
          </Field>
          <Field label="Level">
            <Select value={editing.level} onChange={(e) => set("level", Number(e.target.value))}>
              {LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </Select>
          </Field>
          <Field label="Kategori">
            <Select value={editing.category} onChange={(e) => set("category", e.target.value)}>
              {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </Select>
          </Field>
          <Field label="Urutan (order)" hint="Angka kecil = lebih dulu">
            <TextInput type="number" min={0} value={editing.order} onChange={(e) => set("order", Number(e.target.value))} />
          </Field>
          <Field label="Durasi (menit)">
            <TextInput type="number" min={1} value={editing.estimated_minutes} onChange={(e) => set("estimated_minutes", Number(e.target.value))} />
          </Field>
          <Field label="Reward XP">
            <TextInput type="number" min={0} value={editing.xp_reward} onChange={(e) => set("xp_reward", Number(e.target.value))} />
          </Field>
          <div className="flex items-end pb-1">
            <MiniToggle checked={editing.is_published} onChange={(v) => set("is_published", v)} label={editing.is_published ? "Tampil ke murid" : "Disembunyikan"} />
          </div>
        </div>

        <Field label="Deskripsi singkat">
          <TextArea rows={2} value={editing.description ?? ""} onChange={(e) => set("description", e.target.value)} placeholder="Ringkasan untuk kartu materi" />
        </Field>
        <Field label="Cerita / narasi (story)">
          <TextArea rows={3} value={editing.story ?? ""} onChange={(e) => set("story", e.target.value)} placeholder="Narasi yang tampil di detail materi" />
        </Field>
        <Field label="Thumbnail (aksara, opsional)">
          <BaliInput value={editing.thumbnail ?? ""} onChange={(v) => set("thumbnail", v)} placeholder="mis. ᬳᬦᬘᬓ" />
        </Field>

        <AksaraPicker
          title="Aksara dalam materi"
          hint="Pilih aksara yang diajarkan materi ini (tampil di detail pelajaran)"
          groups={aksara.filter(g => ["wresastra", "swalalita_extra", "suara"].includes(g.category))}
          selected={editing.aksara_ids}
          onToggle={(id) => toggleIn("aksara_ids", id)}
        />
        <AksaraPicker
          title="Pangangge (tanda, opsional)"
          hint="Pangangge terkait jika ada"
          groups={aksara.filter(g => g.category.startsWith("pangangge"))}
          selected={editing.pangangge_ids}
          onToggle={(id) => toggleIn("pangangge_ids", id)}
        />
        <QuizPicker
          title="Kuis terkait"
          quizList={quizList}
          selected={editing.quiz_ids}
          onToggle={(id) => toggleIn("quiz_ids", id)}
        />
      </div>

      <div className="flex justify-end gap-3 border-t border-sand px-6 py-4">
        <button type="button" onClick={saveCancel} className="rounded-full border border-sand bg-white px-5 py-2 text-sm font-semibold text-charcoal/60">
          Batal
        </button>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="rounded-full bg-saffron px-6 py-2 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-saffron-dark disabled:opacity-60"
        >
          {saving ? "Menyimpan…" : isEdit ? "Simpan Perubahan" : "Tambah Materi"}
        </button>
      </div>
    </Card>
  )
}

function AksaraPicker({
  title, hint, groups, selected, onToggle,
}: {
  title: string
  hint: string
  groups: AksaraRefGroup[]
  selected: string[]
  onToggle: (id: string) => void
}) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-2xl border border-sand">
      <button type="button" onClick={() => setOpen(v => !v)} className="flex w-full items-center justify-between px-4 py-3 text-left">
        <span>
          <span className="text-sm font-semibold text-deep-brown">{title}</span>
          <span className="ml-2 text-xs text-charcoal/45">{hint}</span>
        </span>
        <span className="flex items-center gap-2">
          <Badge variant="saffron">{selected.length} dipilih</Badge>
          <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </span>
      </button>
      {open && (
        <div className="border-t border-sand p-4">
          {groups.map((g) => (
            <div key={g.category} className="mb-3 last:mb-0">
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-charcoal/40">{g.category}</div>
              <div className="flex flex-wrap gap-2">
                {g.items.map((it) => {
                  const on = selected.includes(it.id)
                  return (
                    <button
                      key={it.id}
                      type="button"
                      onClick={() => onToggle(it.id)}
                      className={`flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs transition-colors ${
                        on ? "border-saffron bg-saffron/10 text-saffron-dark" : "border-sand bg-cream text-charcoal/70 hover:border-saffron/40"
                      }`}
                    >
                      <span className="font-bali text-base">{it.bali}</span>
                      <span>{it.latin}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function QuizPicker({
  title, quizList, selected, onToggle,
}: {
  title: string
  quizList: any[]
  selected: string[]
  onToggle: (id: string) => void
}) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-2xl border border-sand">
      <button type="button" onClick={() => setOpen(v => !v)} className="flex w-full items-center justify-between px-4 py-3 text-left">
        <span className="text-sm font-semibold text-deep-brown">{title}</span>
        <span className="flex items-center gap-2">
          <Badge variant="saffron">{selected.length} dipilih</Badge>
          <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </span>
      </button>
      {open && (
        <div className="max-h-64 overflow-y-auto border-t border-sand p-3">
          {quizList.length === 0 && <div className="p-2 text-sm text-charcoal/50">Belum ada kuis.</div>}
          <div className="grid gap-1.5 sm:grid-cols-2">
            {quizList.map((q) => {
              const on = selected.includes(q.id)
              return (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => onToggle(q.id)}
                  className={`rounded-xl border px-3 py-2 text-left text-xs transition-colors ${
                    on ? "border-saffron bg-saffron/10" : "border-sand bg-cream hover:border-saffron/40"
                  }`}
                >
                  <div className="font-semibold text-deep-brown">{q.type === "write_aksara" ? "Menulis aksara" : q.type} · {q.difficulty}</div>
                  <div className="truncate text-charcoal/55">{q.question?.text || q.id}</div>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
