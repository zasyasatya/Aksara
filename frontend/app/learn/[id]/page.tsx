"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { useProgressStore } from "@/lib/store"
import { PanganggeFormula, PanganggeItem } from "@/components/aksara/pangangge-formula"
import Link from "next/link"
import { ArrowLeft, Clock, Trophy, CheckCircle2, Play, BookOpen, Volume2, ChevronRight, Check } from "lucide-react"

export default function LessonDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [lesson, setLesson] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const { completeLesson, completedLessons } = useProgressStore()
  const [copiedGlyph, setCopiedGlyph] = useState("")

  useEffect(() => {
    if (!id) return
    api.getLesson(id).then(res => {
      setLesson(res)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])
  
  if (loading) {
    return (
      <div className="min-h-screen bg-cream">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center">
          <div className="h-10 w-10 rounded-full border-2 border-saffron border-t-transparent animate-spin mx-auto" />
        </div>
      </div>
    )
  }
  
  if (!lesson) {
    return (
      <div className="min-h-screen bg-cream">
        <Header />
        <div className="container mx-auto px-4 py-20 text-center">
          <h1 className="text-2xl font-bold">Pelajaran tidak ditemukan</h1>
          <Link href="/learn"><Button className="mt-4">Kembali</Button></Link>
        </div>
      </div>
    )
  }
  
  const isCompleted = completedLessons.includes(lesson.id)

  const insertPangangge = (text: string) => {
    navigator.clipboard?.writeText(text).catch(() => {})
    setCopiedGlyph(text)
    setTimeout(() => setCopiedGlyph(""), 1500)
  }
  
  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      
      <div className="container mx-auto px-4 lg:px-8 py-6">
        <Link href="/learn" className="inline-flex items-center gap-2 text-sm text-charcoal/60 hover:text-deep-brown mb-6">
          <ArrowLeft className="h-4 w-4" /> Kembali ke Daftar
        </Link>
        
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-8 bg-white relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-saffron via-terracotta to-sage" />
              
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <Badge variant="default">Level {lesson.level}</Badge>
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />{lesson.estimated_minutes} menit
                    </Badge>
                    <Badge variant="saffron" className="flex items-center gap-1">
                      <Trophy className="h-3 w-3" />{lesson.xp_reward} XP
                    </Badge>
                  </div>
                  <h1 className="font-display text-3xl lg:text-4xl font-bold mb-2">{lesson.title}</h1>
                  <p className="text-charcoal/70">{lesson.description}</p>
                </div>
                <div className="font-bali text-6xl text-sand hidden lg:block">
                  {lesson.thumbnail}
                </div>
              </div>
              
              {lesson.story && (
                <div className="p-4 rounded-2xl bg-sand/30 border border-sand mb-6">
                  <h3 className="font-semibold text-sm mb-2 flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-saffron" />
                    Cerita Hanacaraka
                  </h3>
                  <p className="text-sm text-charcoal/70 italic">"{lesson.story}"</p>
                </div>
              )}
              
              <div className="prose prose-sm max-w-none">
                <h3 className="font-semibold text-lg mb-4">Aksara dalam pelajaran ini</h3>
              </div>
              
              <div className="grid md:grid-cols-2 gap-4">
                {lesson.aksara_details?.map((aksara: any) => (
                  <Card key={aksara.id} className="p-5 bg-cream border-sand hover:shadow-medium transition-all group">
                    <div className="flex gap-4">
                      <div className="h-20 w-20 rounded-2xl bg-white border border-sand shadow-soft flex items-center justify-center font-bali text-4xl group-hover:text-saffron group-hover:scale-110 transition-all">
                        {aksara.bali}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold">{aksara.name}</h4>
                          <span className="text-xs bg-deep-brown text-cream rounded-full px-2 py-0.5">{aksara.latin}</span>
                        </div>
                        <p className="text-xs text-charcoal/60 mt-1 line-clamp-3">{aksara.description}</p>
                        {aksara.gantungan && (
                          <div className="mt-2 text-xs">
                            <span className="text-charcoal/40">Gantungan:</span> <span className="font-bali">{aksara.gantungan}</span>
                          </div>
                        )}
                        <div className="mt-2 flex gap-1">
                          <Button variant="ghost" size="sm" className="h-7 text-xs rounded-full">
                            <Volume2 className="h-3 w-3 mr-1" /> Dengar
                          </Button>
                        </div>
                      </div>
                    </div>
                    {aksara.examples && aksara.examples.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-sand/50">
                        <div className="text-[10px] font-semibold tracking-widest text-charcoal/40 uppercase mb-2">Contoh</div>
                        <div className="space-y-1">
                          {aksara.examples.slice(0, 2).map((ex: any, i: number) => (
                            <div key={i} className="flex justify-between text-xs">
                              <span className="font-bali">{ex.bali}</span>
                              <span className="text-charcoal/60">{ex.latin} - {ex.meaning}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>

              {lesson.pangangge_details && lesson.pangangge_details.length > 0 && (
                <div className="mt-8 pt-6 border-t border-sand/60">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-lg">Pangangge dalam pelajaran ini</h3>
                    {copiedGlyph && (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-sage">
                        <Check className="h-3.5 w-3.5" /> Tersalin <span className="font-bali">{copiedGlyph}</span>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-charcoal/50 mb-4">
                    Titik bulat (◌) adalah posisi aksara dasar. Pilih aksara di bawah untuk{" "}
                    <em>mengisi</em>-nya — seperti mengisi angka ke formula pangkat/kurung.
                  </p>
                  <PanganggeFormula
                    items={lesson.pangangge_details as PanganggeItem[]}
                    onInsert={insertPangangge}
                  />
                </div>
              )}
            </Card>
            
            {lesson.content?.learning_points && (
              <Card className="p-6 bg-white">
                <h3 className="font-semibold mb-4">Poin Pembelajaran</h3>
                <ul className="space-y-2">
                  {lesson.content.learning_points.map((point: string, i: number) => (
                    <li key={i} className="flex gap-3 text-sm">
                      <CheckCircle2 className="h-5 w-5 text-sage flex-shrink-0" />
                      <span className="text-charcoal/70">{point}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
          
          <div className="space-y-6">
            <Card className="p-6 bg-deep-brown text-cream border-0 sticky top-24">
              <h3 className="font-semibold mb-4">Lanjutkan</h3>
              
              {isCompleted ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sage">
                    <CheckCircle2 className="h-5 w-5" />
                    <span className="font-medium">Sudah selesai!</span>
                  </div>
                  <p className="text-sm text-cream/70">Kamu sudah menyelesaikan pelajaran ini. Ulangi quiz atau lanjut ke berikutnya.</p>
                  <div className="space-y-2">
                    <Link href={`/quiz?lesson_id=${lesson.id}`} className="block">
                      <Button className="w-full bg-cream text-deep-brown hover:bg-white">
                        <Play className="h-4 w-4 mr-2" />
                        Ulangi Quiz
                      </Button>
                    </Link>
                    {lesson.next_lesson && (
                      <Link href={`/learn/${lesson.next_lesson}`} className="block">
                        <Button variant="ghost" className="w-full text-cream hover:bg-cream/10">
                          Lanjut: {lesson.next_lesson}
                          <ChevronRight className="h-4 w-4 ml-2" />
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-cream/60">Progress</span>
                      <span>0/{lesson.quiz_ids?.length || 0} quiz</span>
                    </div>
                    <div className="h-2 bg-cream/10 rounded-full">
                      <div className="h-full bg-saffron rounded-full w-0" />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Link href={`/quiz?lesson_id=${lesson.id}`} className="block">
                      <Button className="w-full bg-saffron hover:bg-saffron-dark text-cream">
                        <Play className="h-4 w-4 mr-2" />
                        Mulai Quiz ({lesson.quiz_ids?.length || 0} soal)
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      className="w-full text-cream hover:bg-cream/10"
                      onClick={() => {
                        completeLesson(lesson.id)
                        // Show confetti or toast
                      }}
                    >
                      Tandai Selesai
                    </Button>
                  </div>
                  
                  <div className="pt-4 border-t border-cream/10 text-xs text-cream/60">
                    Selesaikan quiz untuk mendapatkan {lesson.xp_reward} XP dan unlock pelajaran berikutnya.
                  </div>
                </div>
              )}
            </Card>
            
            <Card className="p-6 bg-white">
              <h3 className="font-semibold mb-4">Bantuan</h3>
              <div className="space-y-3 text-sm">
                <Link href="/translate" className="flex items-center justify-between p-3 rounded-xl bg-sand/30 hover:bg-sand/50 transition-colors">
                  <span>Coba Translate</span>
                  <ChevronRight className="h-4 w-4" />
                </Link>
                <Link href="/playground" className="flex items-center justify-between p-3 rounded-xl bg-sand/30 hover:bg-sand/50 transition-colors">
                  <span>Playground AKSA</span>
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
      
      <BottomNav />
    </div>
  )
}
