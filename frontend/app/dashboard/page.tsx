"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useProgressStore } from "@/lib/store"
import { api, Lesson } from "@/lib/api"
import Link from "next/link"
import { BookOpen, Flame, Trophy, Clock, ChevronRight, Sparkles, Target, Award, Play } from "lucide-react"
import { motion } from "framer-motion"

export default function DashboardPage() {
  const { xp, streak, completedLessons, level } = useProgressStore()
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    api.getLessons({ limit: 20 }).then(res => {
      setLessons(res.lessons)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])
  
  const progressPercent = (completedLessons.length / (lessons.length || 11)) * 100
  
  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      
      <div className="container mx-auto px-4 lg:px-8 py-6 lg:py-8">
        {/* Welcome */}
        <div className="mb-8">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl lg:text-4xl font-bold">Rahajeng semeng! ☀️</h1>
              <p className="text-charcoal/70 mt-1">Lanjutkan perjalanan aksara mu. Kamu sudah di level {level}!</p>
            </div>
            <div className="flex gap-3">
              <Card className="px-4 py-2 flex items-center gap-2 bg-white">
                <Flame className="h-5 w-5 text-saffron" />
                <div>
                  <div className="font-bold leading-none">{streak} hari</div>
                  <div className="text-xs text-charcoal/60">streak</div>
                </div>
              </Card>
              <Card className="px-4 py-2 flex items-center gap-2 bg-deep-brown text-cream">
                <Trophy className="h-5 w-5 text-amber-400" />
                <div>
                  <div className="font-bold leading-none">{xp} XP</div>
                  <div className="text-xs text-cream/60">poin</div>
                </div>
              </Card>
            </div>
          </motion.div>
        </div>
        
        {/* Progress */}
        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          <Card className="lg:col-span-2 p-6 bg-gradient-to-br from-deep-brown to-charcoal text-cream border-0 relative overflow-hidden">
            <div className="absolute top-0 right-0 text-[120px] font-bali text-cream/5 leading-none">ᬅᬓ᭄ᬱᬭ</div>
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Target className="h-5 w-5 text-saffron" />
                  Progress Belajar
                </h3>
                <Badge variant="saffron">{completedLessons.length}/{lessons.length || 11} selesai</Badge>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-cream/70">Level {level} - Penjaga Aksara</span>
                  <span className="font-bold">{Math.round(progressPercent)}%</span>
                </div>
                <div className="h-3 bg-cream/10 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-saffron to-amber-400 rounded-full transition-all duration-1000" style={{ width: `${progressPercent}%` }} />
                </div>
                <div className="flex gap-2 pt-2">
                  <div className="text-xs bg-cream/10 rounded-full px-3 py-1">Wresastra {completedLessons.filter(id => id.includes('wresastra')).length}/4</div>
                  <div className="text-xs bg-cream/10 rounded-full px-3 py-1">Gantungan {completedLessons.filter(id => id.includes('gantungan')).length}/2</div>
                </div>
              </div>
            </div>
          </Card>
          
          <Card className="p-6 bg-white">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Award className="h-5 w-5 text-sage" />
              Pencapaian
            </h3>
            <div className="space-y-3">
              {[
                { name: "Pemula Aksara", desc: "Selesaikan Ha Na Ca Ra Ka", done: completedLessons.includes("wresastra-01") },
                { name: "Pangus Gantungan", desc: "Kuasai gantungan", done: completedLessons.includes("gantungan-01") },
                { name: "Penjaga Budaya", desc: "10 pelajaran selesai", done: completedLessons.length >= 10 },
              ].map((badge, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${badge.done ? "bg-sage text-white" : "bg-sand text-charcoal/40"}`}>
                    <Award className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium ${badge.done ? "" : "text-charcoal/60"}`}>{badge.name}</div>
                    <div className="text-xs text-charcoal/60 truncate">{badge.desc}</div>
                  </div>
                  {badge.done && <div className="h-2 w-2 rounded-full bg-sage" />}
                </div>
              ))}
            </div>
          </Card>
        </div>
        
        {/* Continue Learning */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-2xl font-bold">Lanjutkan Belajar</h2>
            <Link href="/learn" className="text-sm font-medium text-saffron hover:underline flex items-center gap-1">
              Lihat semua <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
          
          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1,2,3].map(i => <div key={i} className="h-40 rounded-2xl bg-sand animate-pulse" />)}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {lessons.slice(0, 6).map((lesson) => {
                const isCompleted = completedLessons.includes(lesson.id)
                const isLocked = lesson.order > 1 && !completedLessons.includes(lessons[lesson.order - 2]?.id) && lesson.order !== 1
                return (
                  <Link key={lesson.id} href={isLocked ? "#" : `/learn/${lesson.id}`}>
                    <Card className={`p-5 h-full hover:shadow-medium hover:-translate-y-1 transition-all group ${isLocked ? "opacity-60" : ""} ${isCompleted ? "bg-sage/5 border-sage/20" : "bg-white"}`}>
                      <div className="flex items-start justify-between mb-3">
                        <div className="font-bali text-3xl group-hover:text-saffron transition-colors">
                          {lesson.thumbnail || "ᬅ"}
                        </div>
                        <div className="flex items-center gap-2">
                          {isCompleted ? <Badge variant="success">Selesai</Badge> : isLocked ? <Badge variant="outline">Terkunci</Badge> : <Badge variant="default">Level {lesson.level}</Badge>}
                        </div>
                      </div>
                      <h3 className="font-semibold mb-1 group-hover:text-saffron transition-colors">{lesson.title}</h3>
                      <p className="text-xs text-charcoal/60 line-clamp-2 mb-3">{lesson.description}</p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-xs text-charcoal/60">
                          <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{lesson.estimated_minutes}m</span>
                          <span className="flex items-center gap-1"><Trophy className="h-3 w-3" />{lesson.xp_reward} XP</span>
                        </div>
                        <div className="h-8 w-8 rounded-full bg-sand group-hover:bg-saffron group-hover:text-cream flex items-center justify-center transition-colors">
                          <Play className="h-4 w-4" />
                        </div>
                      </div>
                    </Card>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
        
        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-4">
          <Link href="/translate">
            <Card className="p-6 bg-gradient-to-br from-saffron to-terracotta text-cream border-0 hover:shadow-large hover:-translate-y-1 transition-all group">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">Translate</h3>
                  <p className="text-sm text-cream/80 mt-1">Latin ↔ Aksara Bali instan</p>
                </div>
                <div className="h-12 w-12 rounded-2xl bg-cream/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span className="font-bali text-2xl">ᬢ᭄ᬭ</span>
                </div>
              </div>
            </Card>
          </Link>
          
          <Link href="/quiz">
            <Card className="p-6 bg-white hover:shadow-large hover:-translate-y-1 transition-all group border-sand">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">Tantangan Harian</h3>
                  <p className="text-sm text-charcoal/60 mt-1">Uji kemampuanmu hari ini</p>
                </div>
                <div className="h-12 w-12 rounded-2xl bg-sage/10 text-sage flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Sparkles className="h-6 w-6" />
                </div>
              </div>
            </Card>
          </Link>
          
          <Link href="/playground">
            <Card className="p-6 bg-white hover:shadow-large hover:-translate-y-1 transition-all group border-sand">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">Playground</h3>
                  <p className="text-sm text-charcoal/60 mt-1">Latihan tulis bebas</p>
                </div>
                <div className="h-12 w-12 rounded-2xl bg-ocean/10 text-ocean flex items-center justify-center group-hover:scale-110 transition-transform">
                  <BookOpen className="h-6 w-6" />
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </div>
      
      <BottomNav />
    </div>
  )
}
