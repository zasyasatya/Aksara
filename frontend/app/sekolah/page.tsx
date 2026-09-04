"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import {
  GraduationCap, BookOpenCheck, PenSquare, Stamp, CheckCircle2,
  Users, MapPin, Loader2, ArrowRight,
} from "lucide-react"

const REGIONS = [
  "Denpasar", "Badung", "Gianyar", "Tabanan", "Jembrana",
  "Buleleng", "Karangasem", "Klungkung", "Bangli", "Luar Bali",
]

export default function SekolahPage() {
  const [schools, setSchools] = useState<any[]>([])
  const [visits, setVisits] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  // form
  const [school, setSchool] = useState("")
  const [region, setRegion] = useState("Denpasar")
  const [students, setStudents] = useState("")
  const [contact, setContact] = useState("")
  const [note, setNote] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [flash, setFlash] = useState<{ kind: "ok" | "err"; text: string } | null>(null)

  useEffect(() => {
    api.getStats().then((d) => { setSchools(d.schools); setVisits(d.visits) }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!school.trim() || !contact.trim()) return
    setSubmitting(true)
    setFlash(null)
    try {
      await api.applySchool({
        school: school.trim(),
        region,
        students: students ? Number(students) : undefined,
        contact: contact.trim(),
        note: note.trim() || undefined,
      })
      setFlash({ kind: "ok", text: `Matur suksma! Pendaftaran ${school.trim()} diterima. Tim AKSA akan menghubungi Anda via ${contact.trim()}.` })
      setSchool(""); setStudents(""); setContact(""); setNote("")
      const d = await api.getStats()
      setSchools(d.schools)
    } catch (err) {
      setFlash({ kind: "err", text: (err as Error).message })
    } finally {
      setSubmitting(false)
    }
  }

  const inputCls = "w-full rounded-xl border border-sand bg-cream/50 px-3 py-2.5 text-sm outline-none focus:border-saffron"

  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />

      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Hero */}
        <div className="max-w-3xl">
          <Badge variant="saffron" className="mb-4">
            <GraduationCap className="h-4 w-4 mr-1.5" /> Program Kemitraan Sekolah & Sanggar
          </Badge>
          <h1 className="font-display text-3xl lg:text-5xl font-bold leading-tight lg:leading-tight text-deep-brown">
            Bawa Aksara Bali ke kelas Anda — <span className="text-saffron">gratis</span>
          </h1>
          <p className="mt-4 text-charcoal/70 leading-relaxed">
            Sejak <strong>Pergub Bali Nomor 7 Tahun 2026</strong>, Bahasa Bali (termasuk{" "}
            <strong>aksara</strong>) dan Kearifan Lokal Bali wajib diajarkan minimal 2 jam per
            minggu di seluruh satuan pendidikan formal di Bali. AKSA hadir sebagai media
            digital yang selaras: <strong>11 pelajaran terstruktur</strong>, <strong>24 kuis
            tervalidasi otomatis</strong>, dan <strong>Panel Guru</strong> untuk menyesuaikan
            konten dengan silabus kelas Anda.
          </p>
          {visits != null && visits > 0 && (
            <p className="mt-3 text-sm text-charcoal/60">
              🔥 {visits.toLocaleString("id-ID")} kunjungan tercatat sejak program kemitraan dibuka.
            </p>
          )}
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-3">
          {/* Manfaat */}
          <div className="lg:col-span-2 space-y-4">
            {[
              {
                icon: BookOpenCheck,
                title: "Selaras kurikulum muatan lokal",
                body: "Urutan pembelajaran Wresastra 18 → Pangangge → Gantungan → Kalimat mengikuti perkembangan kognitif, cocok untuk alokasi 2 JP per minggu.",
              },
              {
                icon: PenSquare,
                title: "Panel Guru: konten bisa disesuaikan",
                body: "Guru menambah/mengubah materi, kuis, dan kamus langsung dari browser — termasuk membuat kuis “menulis aksara” untuk asesmen. Perubahan langsung terlihat murid.",
              },
              {
                icon: Stamp,
                title: "Studio Twibbon untuk tugas kreatif",
                body: "Murid membuat kartu ucapan & konten sosmed beraksara Bali dari foto mereka sendiri — hasil terjemahan aksara otomatis membuat tugas bisa dinilai dari ejaan, bukan sekadar desain.",
              },
            ].map((f) => (
              <Card key={f.title} className="p-6 bg-white shadow-soft flex gap-4">
                <div className="h-12 w-12 shrink-0 rounded-2xl bg-saffron/10 text-saffron-dark flex items-center justify-center">
                  <f.icon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-bold text-deep-brown">{f.title}</h3>
                  <p className="mt-1 text-sm text-charcoal/70 leading-relaxed">{f.body}</p>
                </div>
              </Card>
            ))}

            {/* Daftar sekolah */}
            <Card className="p-6 bg-white shadow-soft">
              <h3 className="flex items-center gap-2 font-bold text-deep-brown mb-1">
                <Users className="h-5 w-5 text-saffron" /> Sekolah & Sanggar Mitra
              </h3>
              <p className="text-xs text-charcoal/55 mb-4">
                Didukung secara mandiri — kami tidak meminta biaya apa pun dari sekolah.
              </p>
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-charcoal/50">
                  <Loader2 className="h-4 w-4 animate-spin" /> Memuat…
                </div>
              ) : schools.length > 0 ? (
                <ul className="divide-y divide-sand">
                  {schools.map((sc) => (
                    <li key={sc.id} className="py-3 flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-deep-brown">{sc.school}</span>
                      {sc.region && (
                        <span className="inline-flex items-center gap-1 text-xs text-charcoal/55">
                          <MapPin className="h-3 w-3" /> {sc.region}
                        </span>
                      )}
                      {sc.students && (
                        <span className="text-xs text-charcoal/55">±{sc.students} siswa</span>
                      )}
                      {sc.is_verified
                        ? <Badge variant="success">Terverifikasi</Badge>
                        : <Badge variant="warning">Verifikasi berjalan</Badge>}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="rounded-2xl border-2 border-dashed border-sand p-6 text-center">
                  <div className="font-bali text-3xl text-sand mb-2">ᬲᬓᭀᬭ</div>
                  <p className="text-sm text-charcoal/60">
                    Belum ada sekolah yang terdaftar. <strong>Jadilah yang pertama</strong> —
                    daftar lewat formulir di samping.
                  </p>
                </div>
              )}
            </Card>
          </div>

          {/* Form */}
          <div>
            <Card className="p-6 bg-white shadow-medium">
              <h3 className="font-display text-lg font-bold text-deep-brown mb-1">Daftar Sekolah</h3>
              <p className="text-xs text-charcoal/55 mb-4">
                Gratis, tanpa komitmen. Tim kami akan menghubungi untuk sesi onboarding 30 menit.
              </p>

              {flash && (
                <div className={`mb-4 rounded-2xl border px-4 py-3 text-sm ${flash.kind === "ok" ? "border-sage/50 bg-sage/10 text-deep-brown" : "border-terracotta/40 bg-terracotta/10 text-terracotta"}`}>
                  {flash.kind === "ok" && <CheckCircle2 className="h-4 w-4 inline mr-1.5 -mt-0.5 text-sage" />}
                  {flash.text}
                </div>
              )}

              <form onSubmit={submit} className="space-y-3">
                <div>
                  <label className="mb-1 block text-xs font-semibold text-charcoal/70">Nama sekolah / sanggar / pasraman *</label>
                  <input value={school} onChange={(e) => setSchool(e.target.value)} required placeholder="mis. SMP Negeri 1 Gianyar" className={inputCls} />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-charcoal/70">Wilayah</label>
                  <select value={region} onChange={(e) => setRegion(e.target.value)} className={inputCls}>
                    {REGIONS.map((r) => <option key={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-charcoal/70">Perkiraan jumlah siswa</label>
                  <input type="number" min={1} value={students} onChange={(e) => setStudents(e.target.value)} placeholder="mis. 600" className={inputCls} />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-charcoal/70">Kontak (email / WhatsApp) *</label>
                  <input value={contact} onChange={(e) => setContact(e.target.value)} required placeholder="mis. guru.bali@sekolah.sch.id" className={inputCls} />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold text-charcoal/70">Catatan (opsional)</label>
                  <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} placeholder="mis. butuh kuis khusus level 4 gantungan" className={inputCls + " resize-none"} />
                </div>
                <Button type="submit" disabled={submitting} className="w-full">
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ArrowRight className="h-4 w-4 mr-2" />}
                  {submitting ? "Mengirim…" : "Kirim Pendaftaran"}
                </Button>
              </form>

              <div className="mt-5 pt-4 border-t border-sand text-xs text-charcoal/55 space-y-2">
                <p>• Data hanya dipakai untuk menghubungi Anda terkait kemitraan.</p>
                <p>• Pertanyaan? Lihat <Link href="/docs/penggunaan-guru" className="font-semibold text-saffron-dark hover:underline">Panduan Guru</Link>.</p>
              </div>
            </Card>
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  )
}
