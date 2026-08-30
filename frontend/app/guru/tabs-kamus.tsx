"use client"

import { useEffect, useMemo, useState } from "react"
import { api, DictEntry } from "@/lib/api"
import { Card } from "@/components/ui/card"
import { Field, TextInput, ConfirmDelete, Flash, TabHeader } from "@/components/guru/ui"
import { BaliInput } from "@/components/guru/bali-input"
import { KeyRound, Loader2, Pencil, Search, X } from "lucide-react"

interface Draft {
  latin: string
  bali: string
  meaning: string
  note: string
}

const EMPTY_DRAFT: Draft = { latin: "", bali: "", meaning: "", note: "" }

export function TabsKamus() {
  const [entries, setEntries] = useState<DictEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState("")
  const [draft, setDraft] = useState<Draft | null>(null)
  const [draftKey, setDraftKey] = useState<string | null>(null) // latin lama saat edit
  const [saving, setSaving] = useState(false)
  const [flash, setFlash] = useState<{ kind: "ok" | "err"; text: string } | null>(null)

  const load = () => {
    api.manage.listDictionary()
      .then((r) => setEntries(r.entries))
      .catch((e) => setFlash({ kind: "err", text: (e as Error).message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return entries
    return entries.filter(e => e.latin.toLowerCase().includes(q) || (e.note ?? "").toLowerCase().includes(q))
  }, [entries, query])

  const save = async () => {
    if (!draft) return
    if (!draft.latin.trim()) return setFlash({ kind: "err", text: "Kata Latin wajib diisi." })
    if (!draft.bali.trim()) return setFlash({ kind: "err", text: "Aksara wajib diisi — ini hasil transliterasi kata tersebut." })
    setSaving(true)
    try {
      await api.manage.upsertDict({
        latin: draft.latin.trim().toLowerCase(),
        bali: draft.bali.trim(),
        meaning: draft.meaning || undefined,
        note: draft.note || undefined,
      })
      setFlash({
        kind: "ok",
        text: draftKey ? `Kamus “${draft.latin}” diperbarui.` : `Kamus “${draft.latin}” ditambahkan.`,
      })
      setDraft(null)
      setDraftKey(null)
      load()
    } catch (e) {
      setFlash({ kind: "err", text: (e as Error).message })
    } finally {
      setSaving(false)
    }
  }

  const remove = async (latin: string) => {
    try {
      const r = await api.manage.deleteDict(latin)
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
          <Loader2 className="h-5 w-5 animate-spin" /> Memuat kamus…
        </div>
      ) : (
        <>
          <Card className="overflow-hidden bg-white shadow-soft">
            <TabHeader
              title="Kamus Transliterasi"
              subtitle={`${entries.length} entri · kamus khusus yang dipakai mesin transliterasi untuk kata-kata sulit`}
              onAdd={() => { setDraftKey(null); setDraft({ ...EMPTY_DRAFT }) }}
              addLabel="+ Tambah Kata"
            />

            <div className="flex items-center gap-2 border-b border-sand px-6 py-3">
              <Search className="h-4 w-4 text-charcoal/40" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Cari kata…"
                className="w-full bg-transparent text-sm outline-none placeholder:text-charcoal/40"
              />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-sand text-[11px] uppercase tracking-wide text-charcoal/45">
                    <th className="px-6 py-3 font-semibold">Kata (Latin)</th>
                    <th className="px-4 py-3 font-semibold">Aksara</th>
                    <th className="px-4 py-3 font-semibold">Arti</th>
                    <th className="px-4 py-3 font-semibold">Catatan</th>
                    <th className="px-6 py-3 text-right font-semibold">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sand">
                  {filtered.map((e) => (
                    <tr key={e.latin} className="hover:bg-sand/20">
                      <td className="px-6 py-3 font-semibold text-deep-brown">{e.latin}</td>
                      <td className="px-4 py-3"><span className="font-bali text-lg text-deep-brown">{e.bali}</span></td>
                      <td className="max-w-[10rem] truncate px-4 py-3 text-charcoal/55">{e.meaning ?? "—"}</td>
                      <td className="max-w-[12rem] truncate px-4 py-3 text-charcoal/55">{e.note ?? "—"}</td>
                      <td className="px-6 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              setDraftKey(e.latin)
                              setDraft({ latin: e.latin, bali: e.bali, meaning: e.meaning ?? "", note: e.note ?? "" })
                              window.scrollTo({ top: 0, behavior: "smooth" })
                            }}
                            className="inline-flex items-center gap-1 rounded-full border border-sand bg-white px-3 py-1.5 text-xs font-semibold text-charcoal/70 hover:border-sage/60 hover:text-sage"
                          >
                            <Pencil className="h-3 w-3" /> Edit
                          </button>
                          <ConfirmDelete onConfirm={() => remove(e.latin)} />
                        </div>
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={5} className="px-6 py-8 text-center text-charcoal/50">Tidak ada entri yang cocok.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {draft && (
            <Card className="overflow-hidden bg-white shadow-medium">
              <div className="flex items-center justify-between border-b border-sand px-6 py-4">
                <h2 className="flex items-center gap-2 font-display text-lg font-bold text-deep-brown">
                  <KeyRound className="h-5 w-5" />
                  {draftKey ? `Edit “${draftKey}”` : "Kata Baru"}
                </h2>
                <button type="button" onClick={() => { setDraft(null); setDraftKey(null) }} className="text-charcoal/40 hover:text-terracotta"><X className="h-5 w-5" /></button>
              </div>
              <div className="grid gap-4 p-6 sm:grid-cols-2">
                <Field label="Kata (Latin)" hint="Kecil otomatis — jadi kunci kamus">
                  <TextInput value={draft.latin} onChange={(e) => setDraft({ ...draft, latin: e.target.value })} placeholder="mis. rahajeng" />
                </Field>
                <Field label="Aksara" hint="Tulisan Aksara Bali yang benar">
                  <BaliInput value={draft.bali} onChange={(v) => setDraft({ ...draft, bali: v })} placeholder="mis. ᬭᬳᬭᬂᬂᬾᬂ" />
                </Field>
                <Field label="Arti (opsional)">
                  <TextInput value={draft.meaning} onChange={(e) => setDraft({ ...draft, meaning: e.target.value })} placeholder="mis. selamat datang" />
                </Field>
                <Field label="Catatan transliterasi (opsional)">
                  <TextInput value={draft.note} onChange={(e) => setDraft({ ...draft, note: e.target.value })} placeholder="mis. A independent karena diawali vokal" />
                </Field>
              </div>
              <div className="flex justify-end gap-3 border-t border-sand px-6 py-4">
                <button type="button" onClick={() => { setDraft(null); setDraftKey(null) }} className="rounded-full border border-sand bg-white px-5 py-2 text-sm font-semibold text-charcoal/60">Batal</button>
                <button
                  type="button"
                  onClick={save}
                  disabled={saving}
                  className="rounded-full bg-saffron px-6 py-2 text-sm font-semibold text-cream shadow-soft transition-colors hover:bg-saffron-dark disabled:opacity-60"
                >
                  {saving ? "Menyimpan…" : "Simpan Kata"}
                </button>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
