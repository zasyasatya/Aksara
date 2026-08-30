"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { api } from "@/lib/api"
import { ArrowRight, Sparkles, BookOpen, Languages, Gamepad2, CheckCircle2, Users, Award, Zap, GraduationCap, Globe2, Stamp } from "lucide-react"
import { motion } from "framer-motion"

export default function LandingPage() {
  const [visits, setVisits] = useState<number | null>(null)

  useEffect(() => {
    api.trackVisit()
    api.getStats().then((d) => setVisits(d.visits)).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-cream">
      <Header />
      
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-sand via-cream to-cream" />
        <div className="absolute top-20 right-10 text-[200px] font-bali text-sand/30 select-none hidden lg:block">
          ᬅᬓ᭄ᬱᬭ
        </div>
        
        <div className="container mx-auto px-4 lg:px-8 py-12 lg:py-20 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-8"
            >
              <div className="space-y-4">
                <Badge variant="saffron" className="px-4 py-1.5 text-sm">
                  <Sparkles className="h-4 w-4 mr-2" />
                  Platform #1 Belajar Aksara Bali
                </Badge>
                <h1 className="font-display text-5xl lg:text-7xl font-bold leading-[0.9] tracking-tight">
                  <span className="block text-deep-brown">Melestarikan</span>
                  <span className="block text-saffron">Warisan,</span>
                  <span className="block text-deep-brown">Menulis</span>
                  <span className="block text-deep-brown">Masa Depan</span>
                </h1>
                <p className="text-lg text-charcoal/70 leading-relaxed max-w-xl">
                  Belajar <span className="font-bali font-bold text-deep-brown">ᬅᬓ᭄ᬱᬭ ᬩᬮᬶ</span> dengan cara modern. 
                  Transliterasi canggih, quiz interaktif, dan gamifikasi yang bikin nagih.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/dashboard">
                  <Button size="lg" className="w-full sm:w-auto group">
                    Mulai Belajar Gratis
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <Link href="/translate">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    Coba Translate
                  </Button>
                </Link>
              </div>
              
              <div className="flex items-center gap-4 pt-4">
                <div className="flex items-center gap-2 rounded-full bg-white border border-sand px-4 py-2 shadow-soft">
                  <Zap className="h-4 w-4 text-saffron" />
                  <span className="text-sm font-semibold text-deep-brown">
                    {visits != null ? `${visits.toLocaleString("id-ID")} orang telah belajar di Aksara` : "Bergabunglah dengan para penjaga aksara"}
                  </span>
                </div>
                <span className="text-xs text-charcoal/50">
                  dari 3,3 juta penutur<br />bahasa Bali
                </span>
              </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="relative bg-white rounded-[2rem] p-8 shadow-large border border-sand">
                <div className="absolute top-0 left-8 right-8 h-1 bg-gradient-to-r from-saffron via-terracotta to-sage rounded-full" />
                
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">Translate Live</h3>
                    <Badge variant="success">Akurasi 95%</Badge>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="rounded-2xl bg-sand/50 p-4">
                      <div className="text-xs text-charcoal/60 mb-1">Latin</div>
                      <div className="font-medium">Om Swastyastu</div>
                    </div>
                    <div className="flex justify-center">
                      <div className="h-8 w-8 rounded-full bg-saffron text-cream flex items-center justify-center">
                        <ArrowRight className="h-4 w-4 rotate-90" />
                      </div>
                    </div>
                    <div className="rounded-2xl bg-deep-brown text-cream p-4">
                      <div className="text-xs text-cream/60 mb-1">Aksara Bali</div>
                      <div className="font-bali text-2xl">ᬑᬁ ᬲ᭄ᬯᬲ᭄ᬢ᭄ᬬᬲ᭄ᬢᬸ</div>
                      <div className="text-xs text-cream/60 mt-2"> breakdown: o + m + swa + s + tya + stu</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-3 pt-4 border-t border-sand">
                    {[
                      { bali: "ᬳ", latin: "ha" },
                      { bali: "ᬦ", latin: "na" },
                      { bali: "ᬘ", latin: "ca" },
                    ].map((item) => (
                      <div key={item.latin} className="text-center rounded-xl bg-cream p-3 border border-sand">
                        <div className="font-bali text-xl">{item.bali}</div>
                        <div className="text-xs font-medium">{item.latin}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Floating badges */}
              <div className="absolute -top-4 -right-4 bg-white rounded-2xl shadow-medium border border-sand px-4 py-2 flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-sage text-white flex items-center justify-center">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div className="text-sm font-semibold">Gantungan benar!</div>
              </div>
              
              <div className="absolute -bottom-6 -left-6 bg-deep-brown text-cream rounded-2xl shadow-large px-4 py-3">
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-saffron" />
                  <div>
                    <div className="text-xs text-cream/60">Streak</div>
                    <div className="font-bold">12 hari 🔥</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>
      
      {/* Features */}
      <section className="py-20 bg-white border-y border-sand">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <Badge variant="default" className="mb-4">Fitur Canggih</Badge>
            <h2 className="font-display text-4xl font-bold mb-4">Belajar Aksara Jadi Mudah & Menyenangkan</h2>
            <p className="text-charcoal/70">Teknologi transliterasi paling akurat dengan pendekatan gamifikasi modern</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Languages,
                title: "Translate Akurat",
                desc: "Latin ↔ Aksara Bali dengan handling gantungan, pangangge, dan tumpuk telu. Akurasi 95%+",
                color: "saffron",
                bali: "ᬢ᭄ᬭᬦ᭄ᬲ᭄ᬮᬢ᭄"
              },
              {
                icon: Gamepad2,
                title: "Quiz Validasi",
                desc: "Murid tulis aksara, sistem validasi otomatis apakah benar sesuai soal dengan feedback detail",
                color: "sage",
                bali: "ᬓᬸᬯᬶᬲ᭄"
              },
              {
                icon: BookOpen,
                title: "Belajar Bertahap",
                desc: "Dari Ha Na Ca Ra Ka hingga kalimat kompleks. 11 level dengan 100+ contoh",
                color: "ocean",
                bali: "ᬩᭂᬮᬚᬃ"
              }
            ].map((feat, i) => (
              <Card key={i} className="p-6 hover:shadow-large transition-all duration-300 group">
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div className={`h-12 w-12 rounded-2xl bg-${feat.color}/10 text-${feat.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                      <feat.icon className="h-6 w-6" />
                    </div>
                    <div className="font-bali text-2xl text-sand group-hover:text-saffron transition-colors">
                      {feat.bali}
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-2">{feat.title}</h3>
                    <p className="text-sm text-charcoal/70 leading-relaxed">{feat.desc}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>
      
      {/* Wresastra showcase */}
      <section className="py-20 bg-cream">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6 mb-12">
            <div>
              <div className="font-bali text-5xl text-saffron mb-4">ᬳᬦᬘᬭᬓ</div>
              <h2 className="font-display text-4xl font-bold">Ha Na Ca Ra Ka</h2>
              <p className="text-charcoal/70 mt-2">18 Aksara Wresastra dasar - fondasi Aksara Bali</p>
            </div>
            <Link href="/learn">
              <Button variant="outline">
                Pelajari Semua <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
          
          <div className="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-9 gap-4">
            {[
              {bali:"ᬳ", latin:"ha"}, {bali:"ᬦ", latin:"na"}, {bali:"ᬘ", latin:"ca"}, {bali:"ᬭ", latin:"ra"}, {bali:"ᬓ", latin:"ka"},
              {bali:"ᬤ", latin:"da"}, {bali:"ᬢ", latin:"ta"}, {bali:"ᬲ", latin:"sa"}, {bali:"ᬯ", latin:"wa"},
              {bali:"ᬮ", latin:"la"}, {bali:"ᬫ", latin:"ma"}, {bali:"ᬕ", latin:"ga"}, {bali:"ᬩ", latin:"ba"}, {bali:"ᬗ", latin:"nga"},
              {bali:"ᬧ", latin:"pa"}, {bali:"ᬚ", latin:"ja"}, {bali:"ᬬ", latin:"ya"}, {bali:"ᬜ", latin:"nya"},
            ].map((aksara) => (
              <Card key={aksara.latin} className="p-4 text-center hover:shadow-medium hover:-translate-y-1 transition-all cursor-pointer group">
                <div className="font-bali text-3xl group-hover:text-saffron transition-colors">{aksara.bali}</div>
                <div className="text-xs font-medium mt-1">{aksara.latin}</div>
              </Card>
            ))}
          </div>
        </div>
      </section>
      
      {/* Stats */}
      <section className="py-16 bg-deep-brown text-cream">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { value: "95%", label: "Akurasi Transliterasi (diuji 57+ kasus)", icon: Award },
              { value: "11", label: "Level Pembelajaran · 24 Kuis", icon: BookOpen },
              { value: "3,3 jt", label: "Penutur Bahasa Bali (2024)", icon: Users },
              { value: "Pergub 7/2026", label: "Bahasa & Aksara Bali wajib jadi mapel di Bali", icon: GraduationCap },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="inline-flex h-12 w-12 rounded-2xl bg-cream/10 items-center justify-center mb-3">
                  <stat.icon className="h-6 w-6 text-saffron" />
                </div>
                <div className="font-display text-3xl lg:text-4xl font-bold">{stat.value}</div>
                <div className="text-sm text-cream/60 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Sekolah & Sanggar */}
      <section className="py-16 bg-white border-t border-sand">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <Badge variant="saffron" className="mb-3">
                <GraduationCap className="h-4 w-4 mr-1.5" /> Untuk Sekolah & Sanggar
              </Badge>
              <h2 className="font-display text-3xl font-bold mb-3">
                Pergub 7/2026: Bahasa & Aksara Bali kini wajib di sekolah
              </h2>
              <p className="text-charcoal/70 leading-relaxed">
                Pemerintah Provinsi Bali mewajibkan Bahasa Bali (termasuk <strong>aksara</strong>)
                dan Kearifan Lokal Bali sebagai muatan lokal minimal 2 jam per minggu di seluruh
                satuan pendidikan formal. Aksara menyediakan media belajar digital yang
                selaras: materi terstruktur, kuis tervalidasi, dan panel guru untuk
                menyesuaikan konten dengan kelas Anda — <strong>gratis untuk murid</strong>.
              </p>
              <div className="flex flex-wrap gap-3 mt-5">
                <Link href="/sekolah">
                  <Button>Daftarkan Sekolah Anda <ArrowRight className="ml-2 h-4 w-4" /></Button>
                </Link>
                <Link href="/docs/penggunaan-guru">
                  <Button variant="outline">Panduan Guru</Button>
                </Link>
              </div>
            </div>
            <Card className="p-8 bg-gradient-to-br from-sand/60 to-cream border-sand">
              <h3 className="flex items-center gap-2 font-bold text-deep-brown mb-4">
                <Globe2 className="h-5 w-5 text-saffron" /> Aksara Nusantara — roadmap
              </h3>
              <p className="text-sm text-charcoal/70 mb-4">
                Engine transliterasi, kuis, dan studio twibbon dirancang modular — siap
                diperluas ke aksara daerah lain sebagai platform warisan Nusantara:
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="success">Aksara Bali (live)</Badge>
                <Badge variant="outline">Aksara Jawa (segera)</Badge>
                <Badge variant="outline">Lontara Bugis (segera)</Badge>
                <Badge variant="outline">Aksara Batak (segera)</Badge>
              </div>
              <div className="mt-5 pt-5 border-t border-sand text-sm text-charcoal/70 space-y-2">
                <div className="flex items-center gap-2"><Stamp className="h-4 w-4 text-saffron shrink-0" /> Studio Twibbon — konten buatan murid tersebar ke sosial media (growth organik)</div>
                <div className="flex items-center gap-2"><GraduationCap className="h-4 w-4 text-saffron shrink-0" /> Program kemitraan sekolah & sanggar — <Link href="/sekolah" className="font-semibold text-saffron-dark hover:underline">daftar di sini</Link></div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-br from-saffron to-terracotta text-cream relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.05%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-50" />
        <div className="container mx-auto px-4 lg:px-8 text-center relative">
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="font-bali text-6xl opacity-20">ᬅᬓ᭄ᬱᬭᬩᬮᬶ</div>
            <h2 className="font-display text-4xl lg:text-5xl font-bold leading-tight">
              Siap Jadi Penjaga<br />Aksara Bali?
            </h2>
            <p className="text-cream/80 text-lg">
              Bergabunglah menjadi penjaga aksara — warisan budaya Bali ditulis masa depanmu
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <Link href="/dashboard">
                <Button variant="secondary" size="lg" className="bg-cream text-deep-brown hover:bg-white w-full sm:w-auto">
                  Mulai Belajar Sekarang
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>
            <div className="text-sm text-cream/60 pt-4">
              Gratis selamanya • Tidak perlu kartu kredit • Langsung bisa dipakai
            </div>
          </div>
        </div>
      </section>
      
      <footer className="py-12 bg-cream border-t border-sand">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-deep-brown text-cream font-bali flex items-center justify-center text-xl">ᬅ</div>
              <div>
                <div className="font-bold">AKSARA</div>
                <div className="text-xs text-charcoal/60">© 2026 Aksara Platform. Ngajegang Bali.</div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-charcoal/60">
              <Link href="/sekolah" className="hover:text-saffron-dark font-semibold">Untuk Sekolah & Sanggar</Link>
              <Link href="/docs" className="hover:text-saffron-dark font-semibold">Dokumentasi</Link>
              <span>ᬫᬢᬸᬃ ᬲᬸᬓ᭄ᬱ᭄ᬫ • Matur Suksma</span>
            </div>
          </div>
        </div>
      </footer>
      
      <BottomNav />
    </div>
  )
}
