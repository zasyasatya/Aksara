"use client"

import { useEffect, useMemo, useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Header } from "@/components/layout/header"
import { BottomNav } from "@/components/layout/bottom-nav"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api, Quiz } from "@/lib/api"
import { useProgressStore } from "@/lib/store"
import { AksaraKeyboard } from "@/components/aksara/aksara-keyboard"
import { CheckCircle2, XCircle, Trophy, Sparkles, ArrowRight, RefreshCw, PenLine, Target, Keyboard, Loader2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

const TYPE_LABELS: Record<string, string> = {
  multiple_choice: "Pilihan Ganda",
  true_false: "Benar/Salah",
  gantungan_choice: "Gantungan",
  write_aksara: "Menulis Aksara",
  arrangement: "Susun",
}

function QuizContent() {
  const searchParams = useSearchParams()
  const lessonId = searchParams.get("lesson_id")
  const initialType = searchParams.get("type")
  const [quizzes, setQuizzes] = useState<Quiz[]>([])
  const [filterType, setFilterType] = useState<string | null>(
    initialType && TYPE_LABELS[initialType] ? initialType : null
  )
  const [currentIdx, setCurrentIdx] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [writeText, setWriteText] = useState("")
  const [showKb, setShowKb] = useState(false)
  const [checking, setChecking] = useState(false)
  const [loading, setLoading] = useState(true)
  const [score, setScore] = useState(0)
  const [answered, setAnswered] = useState(0)
  const { addXP } = useProgressStore()

  useEffect(() => {
    api.getQuizzes({ lesson_id: lessonId || undefined, limit: 50 }).then(res => {
      setQuizzes(res.quizzes)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [lessonId])

  // filter tipe soal (client-side agar chip instan)
  const visibleQuizzes = useMemo(
    () => (filterType ? quizzes.filter(q => q.type === filterType) : quizzes),
    [quizzes, filterType]
  )

  const currentQuiz = visibleQuizzes[currentIdx]
  const isWriteQuiz = currentQuiz?.type === "write_aksara"

  const typeChips = useMemo(() => {
    const present = new Set(quizzes.map(q => q.type))
    return Object.entries(TYPE_LABELS).filter(([t]) => present.has(t))
  }, [quizzes])

  const handleAnswer = async (answerId: string) => {
    if (result || !currentQuiz || checking) return
    setSelected(answerId)
    setChecking(true)
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
    } finally {
      setChecking(false)
    }
  }

  /** Kuis menulis aksara: validasi tulisan murid vs kunci soal (tolerant). */
  const handleCheckWriting = async () => {
    if (result || !currentQuiz || checking || !writeText.trim()) return
    setChecking(true)
    try {
      const q = currentQuiz.question
      const res = await api.validatePair(q.latin ?? "", q.bali ?? "", writeText, "tolerant")
      const correct = !!res.is_correct
      const mapped = {
        correct,
        xp_earned: correct ? currentQuiz.xp : 0,
        explanation: currentQuiz.explanation ?? "",
        similarity: res.similarity,
        suggestions: res.suggestions ?? [],
        feedback: {
          type: correct ? "success" : "error",
          message: correct ? "Mantap! Tulisanmu benar" : "Belum tepat — perhatikan petunjuknya",
          details: (res.suggestions ?? []).join(" · "),
          correct_bali: correct ? "" : res.expected ?? q.bali ?? "",
          correct_latin: correct ? "" : q.latin ?? "",
        },
      }
      setResult(mapped)
      setAnswered(a => a + 1)
      if (correct) {
        setScore(s => s + 1)
        addXP(currentQuiz.xp)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setChecking(false)
    }
  }

  const resetState = () => {
    setSelected(null)
    setResult(null)
    setWriteText("")
    setShowKb(false)
  }

  const nextQuiz = () => {
    if (currentIdx + 1 < visibleQuizzes.length) {
      setCurrentIdx(i => i + 1)
      resetState()
    } else {
      setCurrentIdx(visibleQuizzes.length)
    }
  }

  const restart = () => {
    setCurrentIdx(0)
    resetState()
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

  if (visibleQuizzes.length === 0) {
    return (
      <div className="container mx-auto px-4 py-20 text-center max-w-md mx-auto">
        <h1 className="text-2xl font-bold mb-2">Belum ada quiz</h1>
        <p className="text-charcoal/60 mb-6">Quiz untuk filter ini belum tersedia. Coba tipe lain atau pilih pelajaran lain.</p>
        <Button onClick={() => window.location.href = "/quiz"}>Lihat Semua Quiz</Button>
      </div>
    )
  }

  if (currentIdx >= visibleQuizzes.length) {
    return (
      <div className="container mx-auto px-4 py-12 max-w-2xl">
        <Card className="p-8 text-center bg-white">
          <div className="h-20 w-20 rounded-full bg-sage/10 text-sage flex items-center justify-center mx-auto mb-6">
            <Trophy className="h-10 w-10" />
          </div>
          <h1 className="font-display text-3xl font-bold mb-2">Selesai! 🎉</h1>
          <p className="text-charcoal/60 mb-6">Kamu menjawab {score} dari {visibleQuizzes.length} dengan benar</p>

          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="p-4 rounded-2xl bg-sand/50">
              <div className="text-2xl font-bold">{score}/{visibleQuizzes.length}</div>
              <div className="text-xs text-charcoal/60">Benar</div>
            </div>
            <div className="p-4 rounded-2xl bg-sand/50">
              <div className="text-2xl font-bold">{Math.round((score / visibleQuizzes.length) * 100)}%</div>
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
      {/* Filter tipe soal */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        <button
          onClick={() => { setFilterType(null); setCurrentIdx(0); resetState() }}
          className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${!filterType ? "bg-deep-brown text-cream shadow-soft" : "bg-white border border-sand text-charcoal/70 hover:border-deep-brown"}`}
        >
          Semua Tipe
        </button>
        {typeChips.map(([t, label]) => (
          <button
            key={t}
            onClick={() => { setFilterType(t); setCurrentIdx(0); resetState() }}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${filterType === t ? "bg-deep-brown text-cream shadow-soft" : "bg-white border border-sand text-charcoal/70 hover:border-deep-brown"}`}
          >
            {t === "write_aksara" && <PenLine className="h-3.5 w-3.5 inline mr-1 -mt-0.5" />}
            {label}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Badge variant="default">{currentIdx + 1}/{visibleQuizzes.length}</Badge>
          <Badge variant="saffron">{currentQuiz.difficulty}</Badge>
          <Badge variant="outline">{TYPE_LABELS[currentQuiz.type] ?? currentQuiz.type}</Badge>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Trophy className="h-4 w-4 text-amber-500" />
          <span className="font-bold">{score}</span>
          <span className="text-charcoal/60">/ {answered}</span>
        </div>
      </div>

      <div className="h-2 bg-sand rounded-full mb-8 overflow-hidden">
        <div className="h-full bg-saffron rounded-full transition-all duration-500" style={{ width: `${(currentIdx / visibleQuizzes.length) * 100}%` }} />
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
            {/* Soal */}
            <div className="mb-8">
              <h2 className="font-display text-2xl font-bold mb-2">{currentQuiz.question.text}</h2>
              {isWriteQuiz && currentQuiz.question.latin && (
                <div className="mt-4 p-5 rounded-2xl bg-deep-brown text-cream text-center">
                  <div className="text-xs text-cream/60 uppercase tracking-wider mb-1 flex items-center justify-center gap-1.5">
                    <Target className="h-3.5 w-3.5" /> Kata yang harus ditulis
                  </div>
                  <div className="text-2xl font-bold">{currentQuiz.question.latin}</div>
                </div>
              )}
              {currentQuiz.question.hint && (
                <p className="text-sm text-charcoal/60 bg-sand/30 p-3 rounded-xl border border-sand mt-4">💡 {currentQuiz.question.hint}</p>
              )}
              {!isWriteQuiz && currentQuiz.question.bali && (
                <div className="mt-4 p-4 rounded-2xl bg-deep-brown text-cream text-center">
                  <div className="font-bali text-4xl">{currentQuiz.question.bali}</div>
                  {currentQuiz.question.latin && <div className="text-sm text-cream/60 mt-1">{currentQuiz.question.latin}</div>}
                </div>
              )}
            </div>

            {/* Area jawaban: pilihan ganda ATAU menulis aksara */}
            {isWriteQuiz ? (
              <div>
                {/* Pratinjau tulisan */}
                <div className="min-h-24 p-4 rounded-2xl bg-sand/20 border-2 border-dashed border-sand focus-within:border-saffron flex items-center justify-center">
                  <div className="font-bali text-4xl text-deep-brown break-words text-center">
                    {writeText || <span className="text-charcoal/25 text-xl">Klik keyboard di bawah atau ketik aksara di sini…</span>}
                  </div>
                </div>

                <div className="mt-3 flex gap-2">
                  <textarea
                    value={writeText}
                    onChange={(e) => setWriteText(e.target.value)}
                    placeholder="Atau ketik/paste aksara Bali langsung…"
                    rows={2}
                    className="flex-1 p-3 rounded-xl bg-cream border border-sand font-bali text-lg outline-none focus:border-saffron resize-none"
                  />
                </div>

                <button
                  type="button"
                  onClick={() => setShowKb(v => !v)}
                  className={`mt-3 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold transition-colors ${showKb ? "border-saffron bg-saffron/10 text-saffron-dark" : "border-sand bg-cream text-charcoal/60 hover:border-saffron/50"}`}
                >
                  <Keyboard className="h-3.5 w-3.5" />
                  {showKb ? "Tutup Keyboard Aksara" : "Buka Keyboard Aksara"}
                </button>

                {showKb && (
                  <div className="mt-3 rounded-2xl border border-sand bg-cream/60 p-3">
                    <AksaraKeyboard onInsert={(c) => setWriteText(t => t + c)} onBackspace={() => setWriteText(t => t.slice(0, -1))} compact />
                  </div>
                )}

                {!result && (
                  <div className="mt-5 flex justify-end">
                    <Button onClick={handleCheckWriting} disabled={checking || !writeText.trim()}>
                      {checking ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                      {checking ? "Memeriksa…" : "Cek Jawaban"}
                    </Button>
                  </div>
                )}
              </div>
            ) : (
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
                      disabled={!!result || checking}
                      className={`p-4 rounded-2xl border-2 text-left transition-all flex items-center justify-between group ${stateClass} ${checking && isSelected ? "opacity-80" : ""}`}
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
                      {checking && isSelected && <Loader2 className="h-6 w-6 animate-spin text-saffron" />}
                      {result && isCorrect && <CheckCircle2 className="h-6 w-6 text-sage" />}
                      {result && isWrongSelected && <XCircle className="h-6 w-6 text-red-500" />}
                    </button>
                  )
                })}
              </div>
            )}

            {/* Hasil */}
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
                      <h4 className="font-bold flex items-center gap-2 flex-wrap">
                        {result.feedback.message}
                        {result.correct && <span>🎉</span>}
                        {typeof result.similarity === "number" && (
                          <Badge variant={result.correct ? "success" : "warning"} className="text-[11px]">
                            {Math.round(result.similarity * 100)}% mirip
                          </Badge>
                        )}
                      </h4>
                      <p className="text-sm mt-2 leading-relaxed">{result.explanation}</p>
                      {result.feedback.details && result.feedback.details !== result.explanation && (
                        <p className="text-xs mt-2 text-charcoal/70 bg-white/50 p-3 rounded-xl border">{result.feedback.details}</p>
                      )}
                      {Array.isArray(result.suggestions) && result.suggestions.length > 0 && (
                        <ul className="mt-2 text-xs list-disc list-inside text-charcoal/70">
                          {result.suggestions.map((sg: string, i: number) => (
                            <li key={i} className="flex items-start gap-1.5"><Sparkles className="h-3 w-3 mt-0.5 text-saffron shrink-0" />{sg}</li>
                          ))}
                        </ul>
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
                          {result.feedback.correct_latin && <div className="text-xs">{result.feedback.correct_latin}</div>}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 flex justify-end">
                    <Button onClick={nextQuiz} className="rounded-full">
                      {currentIdx + 1 < visibleQuizzes.length ? "Lanjut" : "Selesai"}
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
