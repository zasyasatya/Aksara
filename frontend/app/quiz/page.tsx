"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api, Quiz } from "@/lib/api"
import { useProgressStore } from "@/lib/store"
import { CheckCircle2, XCircle, Trophy, Sparkles, ArrowRight, RefreshCw } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

function QuizContent() {
  const searchParams = useSearchParams()
  const lessonId = searchParams.get("lesson_id")
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [score, setScore] = useState(0)
  const [answered, setAnswered] = useState(0)
  const { addXP } = useProgressStore()
  
  useEffect(() => {
    api.getQuizzes({ lesson_id: lessonId || undefined, limit: 20 }).then(res => {
      setQuizzes(res.quizzes)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [lessonId])
  
  const currentQuiz = quizzes[currentIdx]
  
  const handleAnswer = async (answerId: string) => {
    if (result) return
    setSelected(answerId)
    
    try {
      const res = await api.checkQuiz(currentQuiz.id, answerId)
      setResult(res)
      setAnswered(a => a + 1)
      if (res.correct) {
        setScore(s => s + 1)
        addXP(res.xp_earned)
      }
    } catch (e) {
      console.error(e)
    }
  }
  
  const nextQuiz = () => {
    if (currentIdx + 1 < quizzes.length) {
      setCurrentIdx(i => i + 1)
      setSelected(null)
      setResult(null)
    } else {
      setCurrentIdx(quizzes.length)
    }
  }
  
  const restart = () => {
    setCurrentIdx(0)
    setSelected(null)
    setResult(null)
    setScore(0)
    setAnswered(0)
  }
  
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 text-center">
        <div className="h-10 w-10 rounded-full border-2 border-saffron border-t-transparent animate-spin mx-auto" />
      </div>
    )
  }
  
  if (quizzes.length === 0) {
    return (
      <div className="container mx-auto px-4 py-20 text-center max-w-md mx-auto">
        <div className="font-bali text-6xl mb-4">ᬓᬸᬯᬶᬲ᭄</div>
        <h1 className="text-2xl font-bold mb-2">Belum ada quiz</h1>
        <p className="text-charcoal/60 mb-6">Quiz untuk filter ini belum tersedia. Coba tanpa filter atau pilih pelajaran lain.</p>
        <Button onClick={() => window.location.href = "/quiz"}>Lihat Semua Quiz</Button>
      </div>
    )
  }
  
  if (currentIdx >= quizzes.length) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-2xl">
        <Card className="p-8 text-center bg-white">
          <div className="h-20 w-20 rounded-full bg-sage/10 text-sage flex items-center justify-center mx-auto mb-6">
            <Trophy className="h-10 w-10" />
          </div>
          <h1 className="font-display text-3xl font-bold mb-2">Selesai! 🎉</h1>
          <p className="text-charcoal/60 mb-6">Kamu menjawab {score} dari {quizzes.length} dengan benar</p>
          
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="p-4 rounded-2xl bg-sand/50">
              <div className="text-2xl font-bold">{score}/{quizzes.length}</div>
              <div className="text-xs text-charcoal/60">Benar</div>
            </div>
            <div className="p-4 rounded-2xl bg-sand/50">
              <div className="text-2xl font-bold">{Math.round((score/quizzes.length)*100)}%</div>
              <div className="text-xs text-charcoal/60">Akurasi</div>
            </div>
            <div className="p-4 rounded-2xl bg-saffron/10 text-saffron">
              <div className="text-2xl font-bold">+{score * 10}</div>
              <div className="text-xs">XP</div>
            </div>
          </div>
          
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={restart}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Ulangi
            </Button>
            <Button onClick={() => window.location.href = "/dashboard"}>
              Dashboard
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto px-4 lg:px-8 py-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Badge variant="default">{currentIdx + 1}/{quizzes.length}</Badge>
          <Badge variant="saffron">{currentQuiz.difficulty}</Badge>
          <Badge variant="outline">{currentQuiz.type}</Badge>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Trophy className="h-4 w-4 text-amber-500" />
          <span className="font-bold">{score}</span>
          <span className="text-charcoal/60">/ {answered}</span>
        </div>
      </div>
      
      <div className="h-2 bg-sand rounded-full mb-8 overflow-hidden">
        <div className="h-full bg-saffron rounded-full transition-all duration-500" style={{ width: `${((currentIdx) / quizzes.length) * 100}%` }} />
      </div>
      
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuiz.id}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="p-8 bg-white shadow-large">
            <div className="mb-8">
              <h2 className="font-display text-2xl font-bold mb-2">{currentQuiz.question.text}</h2>
              {currentQuiz.question.hint && (
                <p className="text-sm text-charcoal/60 bg-sand/30 p-3 rounded-xl border border-sand">💡 {currentQuiz.question.hint}</p>
              )}
              {currentQuiz.question.bali && (
                <div className="mt-4 p-4 rounded-2xl bg-deep-brown text-cream text-center">
                  <div className="font-bali text-4xl">{currentQuiz.question.bali}</div>
                  {currentQuiz.question.latin && <div className="text-sm text-cream/60 mt-1">{currentQuiz.question.latin}</div>}
                </div>
              )}
            </div>
            
            <div className="grid gap-3">
              {currentQuiz.options.map((opt) => {
                const isSelected = selected === opt.id
                const isCorrect = result && opt.id === result.correct_answer
                const isWrongSelected = result && isSelected && !result.correct
                
                let stateClass = "bg-white border-sand hover:border-saffron hover:bg-saffron/5"
                if (result) {
                  if (isCorrect) stateClass = "bg-sage/10 border-sage text-sage"
                  else if (isWrongSelected) stateClass = "bg-red-50 border-red-200 text-red-700"
                  else stateClass = "bg-white border-sand opacity-60"
                } else if (isSelected) {
                  stateClass = "bg-saffron/10 border-saffron text-saffron"
                }
                
                return (
                  <button
                    key={opt.id}
                    onClick={() => handleAnswer(opt.id)}
                    disabled={!!result}
                    className={`p-4 rounded-2xl border-2 text-left transition-all flex items-center justify-between group ${stateClass}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-bold border-2 transition-all ${isSelected ? "bg-saffron text-cream border-saffron" : "bg-sand border-sand group-hover:border-saffron"}`}>
                        {opt.id.toUpperCase()}
                      </div>
                      <div>
                        {opt.bali && <div className="font-bali text-2xl">{opt.bali}</div>}
                        <div className="font-medium">{opt.label || opt.latin || opt.bali}</div>
                        {opt.latin && opt.bali && <div className="text-xs opacity-70">{opt.latin}</div>}
                      </div>
                    </div>
                    {result && isCorrect && <CheckCircle2 className="h-6 w-6 text-sage" />}
                    {result && isWrongSelected && <XCircle className="h-6 w-6 text-red-500" />}
                  </button>
                )
              })}
            </div>
            
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-6 p-6 rounded-2xl border-2 ${result.correct ? "bg-sage/5 border-sage/20" : "bg-amber-50 border-amber-200"}`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 ${result.correct ? "bg-sage text-white" : "bg-amber-500 text-white"}`}>
                      {result.correct ? <CheckCircle2 className="h-6 w-6" /> : <XCircle className="h-6 w-6" />}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold flex items-center gap-2">
                        {result.feedback.message}
                        {result.correct && <span>🎉</span>}
                      </h4>
                      <p className="text-sm mt-2 leading-relaxed">{result.explanation}</p>
                      {result.feedback.details && result.feedback.details !== result.explanation && (
                        <p className="text-xs mt-2 text-charcoal/70 bg-white/50 p-3 rounded-xl border">{result.feedback.details}</p>
                      )}
                      {result.correct && (
                        <div className="mt-3 flex items-center gap-2 text-sm font-medium text-sage">
                          <Trophy className="h-4 w-4" />
                          +{result.xp_earned} XP
                        </div>
                      )}
                      {!result.correct && result.feedback.correct_bali && (
                        <div className="mt-3 p-3 rounded-xl bg-white border">
                          <div className="text-xs text-charcoal/60">Jawaban benar:</div>
                          <div className="font-bali text-xl">{result.feedback.correct_bali}</div>
                          <div className="text-xs">{result.feedback.correct_latin}</div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-6 flex justify-end">
                    <Button onClick={nextQuiz} className="rounded-full">
                      {currentIdx + 1 < quizzes.length ? "Lanjut" : "Selesai"}
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
          
          {currentQuiz.type === "gantungan_choice" && (
            <Card className="mt-6 p-4 bg-ocean/5 border-ocean/10">
              <h4 className="text-sm font-semibold flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-ocean" />
                Tips Gantungan
              </h4>
              <p className="text-xs text-charcoal/70">
                Ingat: gantungan untuk cluster konsonan di tengah kata, adeg-adeg untuk akhiran. Tumpuk telu (2 gantungan pada 1 aksara) dilarang! 
                La gantungan + pepet boleh (bleganjur), tapi Cakra + pepet tidak boleh.
              </p>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

export default function QuizPage() {
  return (
    <div className="min-h-screen bg-cream pb-20 lg:pb-0">
      <Header />
      <Suspense fallback={<div className="container mx-auto px-4 py-20 text-center"><div className="h-10 w-10 rounded-full border-2 border-saffron border-t-transparent animate-spin mx-auto" /></div>}>
        <QuizContent />
      </Suspense>
      <BottomNav />
    </div>
  )
}
