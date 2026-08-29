"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { api, Lesson } from "@/lib/api"
import { useProgressStore } from "@/lib/store"
import Link from "next/link"
import { Clock, Trophy, ChevronRight, BookOpen, CheckCircle2, Lock } from "lucide-react"

const levelNames: Record<number, {name: string, desc: string, color: string, bali: string}> = {
  1: { name: "Pemula", desc: "Wresastra 18 dasar", color: "bg-saffron", bali: "ᬳᬦᬘᬭᬓ" },
  2: { name: "Pangangge Suara", desc: "Vokal I, U, E, O", color: "bg-sage", bali: "ᬶᬸᬾ" },
  3: { name: "Tengenan", desc: "Akhiran H, R, NG", color: "bg-ocean", bali: "ᬄᬃᬂ" },
  4: { name: "Gantungan", desc: "Cluster konsonan", color: "bg-terracotta", bali: "᭄ᬓ᭄ᬭ" },
  5: { name: "Swalalita", desc: "Sanskerta & Kawi", color: "bg-deep-brown", bali: "ᬔᬖᬙ" },
  6: { name: "Kalimat", desc: "Merangkai kalimat", color: "bg-amber-600", bali: "ᬑᬁᬲ᭄ᬯ" },
}

export default function LearnPage() {
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [filterLevel, setFilterLevel] = useState<number | null>(null)
  const { completedLessons } = useProgressStore()
  
  useEffect(() => {
    api.getLessons({ limit: 50 }).then(res => setLessons(res.lessons))
  }, [])
  
  const filtered = filterLevel ? lessons.filter(l => l.level === filterLevel) : lessons
  const grouped = filtered.reduce((acc, lesson) => {
    if (!acc[lesson.level]) acc[lesson.level] = []
    acc[lesson.level].push(lesson)
    return acc
  }, {} as Record<number, Lesson[]>)
  
  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      
      <div className="container mx-auto px-4 lg:px-8 py-6">
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold">Belajar Aksara Bali</h1>
          <p className="text-charcoal/60 mt-1">Belajar bertahap dari dasar hingga mahir, dengan pendekatan tradisional + modern</p>
        </div>
        
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          <button
            onClick={() => setFilterLevel(null)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${!filterLevel ? "bg-deep-brown text-cream shadow-soft" : "bg-white border border-sand text-charcoal/70 hover:border-deep-brown"}`}
          >
            Semua Level
          </button>
          {[1,2,3,4,5,6].map(lvl => (
            <button
              key={lvl}
              onClick={() => setFilterLevel(lvl)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all flex items-center gap-2 ${filterLevel === lvl ? "bg-deep-brown text-cream shadow-soft" : "bg-white border border-sand hover:border-deep-brown"}`}
            >
              <span className="font-bali">{levelNames[lvl].bali}</span>
              {levelNames[lvl].name}
            </button>
          ))}
        </div>
        
        <div className="space-y-12">
          {Object.entries(grouped).sort(([a],[b]) => Number(a)-Number(b)).map(([levelStr, levelLessons]) => {
            const level = Number(levelStr)
            const info = levelNames[level]
            const completedInLevel = levelLessons.filter(l => completedLessons.includes(l.id)).length
            return (
              <div key={level}>
                <div className="flex items-center gap-4 mb-6">
                  <div className={`h-12 w-12 rounded-2xl ${info.color} text-cream flex items-center justify-center font-bali text-xl`}>
                    {info.bali}
                  </div>
                  <div>
                    <h2 className="font-display text-2xl font-bold flex items-center gap-3">
                      Level {level}: {info.name}
                      <Badge variant="default">{completedInLevel}/{levelLessons.length}</Badge>
                    </h2>
                    <p className="text-sm text-charcoal/60">{info.desc}</p>
                  </div>
                </div>
                
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(levelLessons as Lesson[]).sort((a,b) => a.order - b.order).map((lesson) => {
                    const isCompleted = completedLessons.includes(lesson.id)
                    const prevLesson = lessons.find(l => l.order === lesson.order - 1)
                    const isLocked = lesson.order > 1 && prevLesson && !completedLessons.includes(prevLesson.id)
                    
                    return (
                      <Link key={lesson.id} href={isLocked ? "#" : `/learn/${lesson.id}`} className={isLocked ? "pointer-events-none" : ""}>
                        <Card className={`p-6 h-full group hover:shadow-large hover:-translate-y-1 transition-all relative overflow-hidden ${isCompleted ? "bg-sage/5 border-sage/20" : "bg-white"} ${isLocked ? "opacity-60" : ""}`}>
                          {isCompleted && (
                            <div className="absolute top-0 right-0 bg-sage text-white text-[10px] px-3 py-1 rounded-bl-xl font-medium flex items-center gap-1">
                              <CheckCircle2 className="h-3 w-3" /> Selesai
                            </div>
                          )}
                          {isLocked && (
                            <div className="absolute top-0 right-0 bg-sand text-charcoal/60 text-[10px] px-3 py-1 rounded-bl-xl font-medium flex items-center gap-1">
                              <Lock className="h-3 w-3" /> Terkunci
                            </div>
                          )}
                          
                          <div className="flex items-start justify-between mb-4">
                            <div className="font-bali text-4xl group-hover:text-saffron transition-colors">
                              {lesson.thumbnail || "ᬅ"}
                            </div>
                            <div className={`h-8 w-8 rounded-full ${info.color} text-cream flex items-center justify-center text-xs font-bold`}>
                              {lesson.order}
                            </div>
                          </div>
                          
                          <h3 className="font-semibold text-lg mb-2 group-hover:text-saffron transition-colors">{lesson.title}</h3>
                          <p className="text-sm text-charcoal/60 line-clamp-2 mb-4">{lesson.description}</p>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 text-xs text-charcoal/60">
                              <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{lesson.estimated_minutes}m</span>
                              <span className="flex items-center gap-1"><Trophy className="h-3 w-3" />{lesson.xp_reward} XP</span>
                            </div>
                            <ChevronRight className="h-4 w-4 text-charcoal/40 group-hover:text-saffron group-hover:translate-x-1 transition-all" />
                          </div>
                        </Card>
                      </Link>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
        
        <Card className="mt-12 p-8 bg-deep-brown text-cream border-0 relative overflow-hidden">
          <div className="absolute top-0 right-0 text-[150px] font-bali text-cream/5 leading-none">ᬳᬦᬘᬭᬓ</div>
          <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <h3 className="font-display text-2xl font-bold mb-2">Butuh bantuan guru?</h3>
              <p className="text-cream/70 max-w-xl">Aksara Platform juga menyediakan dashboard guru untuk monitoring kelas dan pembuatan soal custom. Hubungi kami untuk akses sekolah.</p>
            </div>
            <Button variant="secondary" className="bg-cream text-deep-brown hover:bg-white">
              <BookOpen className="h-4 w-4 mr-2" />
              Untuk Guru
            </Button>
          </div>
        </Card>
      </div>
      
      <BottomNav />
    </div>
  )
}
