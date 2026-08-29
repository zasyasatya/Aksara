# BRANDING - Aksara Platform

## Brand Essence

**Name:** Aksara  
**Full:** Aksara - Platform Belajar Aksara Bali  
**Tagline ID:** "Melestarikan Warisan, Menulis Masa Depan"  
**Tagline Bali:** "Ngajegang Warisan, Nyurat Masa Depan"  
**Tagline EN:** "Preserve Heritage, Write Future"

**Brand Story:**
Aksara Bali adalah jantung identitas Bali. Dari lontar kuno hingga canang sehari-hari, aksara ini membawa doa, cerita, dan kebijaksanaan leluhur. Namun di era digital, ia terancam punah. Aksara hadir bukan sekadar aplikasi, tapi gerakan: membuat generasi muda jatuh cinta lagi pada hurufnya sendiri, dengan cara yang modern, menyenangkan, dan relevan.

**Personality:**
- **Bijaksana tapi Gaul:** Seperti kakek yang jago TikTok
- **Hangat & Membumi:** Warna tanah Bali, tekstur lontar
- **Cerdas & Akurat:** Tidak main-main soal aturan gantungan
- **Playful & Gamified:** Belajar seperti main game

---

## Visual Identity

### Logo Concept

**Primary Logo:** Wordmark "AKSARA" dengan aksen Aksara Bali ᬅᬓ᭄ᬱᬭ di atas atau sebagai ligature.

- **Logotype:** Custom sans-serif bold, rounded, dengan potongan terinspirasi ukiran
- **Symbol:** ᬅ (Akara) stylized sebagai icon app - bentuknya seperti gunung + ombak
- **Construction:** Grid 8px, clear space = height of ᬅ

**Variations:**
- Horizontal: [Icon ᬅ] AKSARA
- Stacked: ᬅ di atas AKSARA
- Icon only: ᬅ dalam lingkaran

**Usage:** 
- Jangan stretch, jangan ganti warna sembarangan
- Minimum size 24px

### Color Palette - "Tanah Bali"

Inspired by: Pura, sawah, kayu, kain endek, canang, laut.

**Primary:**
- **Saffron / Jingga Suci:** #FF6B35 - CTA, accent, energy (dari bunga marigold canang)
- **Deep Brown / Kayu Cendana:** #2C1810 - Text primary, header (dari kayu lontar)
- **Cream / Lontar:** #FFF8E7 - Background utama (dari daun lontar kering)
- **Terracotta / Tanah Liat:** #C45A3C - Secondary, card border

**Secondary:**
- **Sage / Daun Bali:** #7A9E7E - Success, nature, calm
- **Ocean / Segara:** #2A6F8E - Info, link, depth
- **Sand / Pasir:** #F4E4BC - Background secondary, muted
- **Charcoal / Arang:** #1A1A1A - Text secondary

**Semantic:**
- Success: #2E7D32
- Warning: #F9A825
- Error: #C62828
- Info: #2A6F8E

**Gradients:**
- Sunrise: linear-gradient(135deg, #FF6B35 0%, #F9A825 100%)
- Earth: linear-gradient(135deg, #2C1810 0%, #C45A3C 100%)
- Lontar: linear-gradient(180deg, #FFF8E7 0%, #F4E4BC 100%)

**Usage Rules:**
- 60% Cream/Sand (background)
- 30% Deep Brown (text, structure)
- 10% Saffron (CTA, highlight)
- Jangan pakai Saffron untuk text panjang

### Typography

**Primary UI Font:** Plus Jakarta Sans (modern, rounded, highly legible, Indonesian foundry!)
- Weights: 400 Regular, 500 Medium, 600 SemiBold, 700 Bold
- Usage: Semua UI, heading, body
- Fallback: Inter, system sans

**Aksara Font:** Noto Sans Balinese (Google, best Unicode support)
- Usage: Display aksara, 24px+ minimum
- Loading: via Google Fonts with `display=swap`, subset Balinese
- Fallback: "Noto Sans Balinese", sans-serif
- Size scale: Aksara harus 1.5x lebih besar dari Latin untuk readability

**Accent / Display (optional):** Fraunces (serif untuk heading hero, nuansa lontar)

**Type Scale (Mobile → Desktop):**
- Display: 36px/40px → 60px/64px, 700
- H1: 30px/36px → 48px/52px, 700
- H2: 24px/32px → 36px/40px, 600
- H3: 20px/28px → 24px/32px, 600
- Body Large: 18px/28px, 400
- Body: 16px/24px, 400
- Small: 14px/20px, 400
- Caption: 12px/16px, 500, uppercase, tracking 0.05em

**Aksara Scale:**
- Aksara Display: 48px → 72px
- Aksara Body: 32px → 40px
- Aksara Small: 24px

### Iconography

- **Style:** Rounded, 2px stroke, minimal
- **Library:** Lucide React (customize stroke)
- **Aksara Icons:** Custom SVG untuk pangangge, gantungan
- **Size:** 20px default, 24px for nav

### Illustration Style

- **Style:** Flat + texture grain (lontar texture overlay 5%)
- **Elements:** Wayang-style simplified, but modern (rounded corners)
- **Characters:** Anak Bali modern dengan udeng, belajar aksara
- **Motifs:** Patra (ukiran Bali) sebagai border, tidak berlebihan
- **Usage:** Empty states, onboarding, badges

### Patterns & Textures

- **Patra Sari:** Border pattern subtle untuk card header
- **Lontar Grain:** Texture overlay untuk background (opacity 3%)
- **Subtle Dots:** Untuk background section

---

## Design System Components

### Buttons

**Primary:** Saffron bg, Cream text, rounded-full, shadow
- Hover: Darken 10%, lift 2px
- Active: Scale 0.98

**Secondary:** Transparent, Deep Brown border, rounded-full

**Ghost:** No border, Deep Brown text, hover Sand bg

**Aksara Button:** Large, with Aksara char + Latin, for keyboard

### Cards

- **Base:** White bg, 16px radius, 1px Sand border, shadow-sm
- **Hover:** shadow-md, border Saffron/20%
- **Aksara Card:** Cream bg, centered Aksara Display, Latin below, patra top border
- **Quiz Card:** White, with progress bar Saffron

### Badges & Pills

- Rounded-full, 12px text, 6px padding
- Colors: Saffron for new, Sage for completed, Ocean for info

### Navigation

- **Desktop:** Sidebar 280px, Cream bg, Deep Brown text, Saffron active indicator (4px left border)
- **Mobile:** Bottom nav 72px height, 5 items, icons + label, Saffron active
- **Header:** Sticky, 64px, backdrop-blur, with progress streak

### Forms

- Input: 48px height, 12px radius, Sand border, focus Saffron ring
- Label: Small caps, Deep Brown
- Error: Red text + icon

### Feedback

- **Correct:** Sage bg, confetti animation, "MANTAP! ᬫᬦ᭄ᬢᬧ᭄"
- **Incorrect:** Terracotta bg light, explanation card with correct answer
- **Toast:** Bottom on mobile, top-right desktop, 4s auto-dismiss

---

## Voice & Tone

**ID:**
- Santai tapi hormat: "Yuk, belajar ᬳ!" bukan "Silakan mempelajari aksara Ha"
- Pakai istilah Bali sesekali: "Rahajeng!", "Matur suksma", "Pangus!"
- Encouraging: "Dikit lagi, kamu pasti bisa!"
- Tidak kaku, tidak alay

**EN (for docs):**
- Friendly, knowledgeable, slightly playful

**Microcopy Examples:**
- CTA: "Mulai Belajar →" / "Lanjutin Belajar"
- Empty: "Belum ada tantangan. Yuk, buat yang pertama!"
- Success: "Kerenn! Kamu sudah kuasai 5 aksara 🎉"
- Error: "Ups, ada yang kurang pas. Cek lagi gantungannya ya"

---

## Brand Applications

### App Icon
- Background: Saffron gradient
- Foreground: ᬅ white, bold
- Rounded: 20% radius

### Social Media
- Template: Cream bg, Deep Brown text, Saffron accent, Patra border bottom
- Hashtags: #AksaraBali #NgajegangBali #BelajarAksara

### Merch (Future)
- Tote bag: Cream with ᬅᬓ᭄ᬱᬭ large
- Sticker pack: Aksara Wresastra 18

---

## Accessibility & Inclusivity

- Contrast ratio minimum 4.5:1 (Deep Brown on Cream = 15:1 ✅)
- Don't rely on color alone for quiz feedback (use icon + text)
- Support font scaling
- Aksara always accompanied by Latin for learning

---

## Design Tokens (for Tailwind)

```js
colors: {
  saffron: "#FF6B35",
  "deep-brown": "#2C1810",
  cream: "#FFF8E7",
  terracotta: "#C45A3C",
  sage: "#7A9E7E",
  ocean: "#2A6F8E",
  sand: "#F4E4BC",
  charcoal: "#1A1A1A"
},
fontFamily: {
  sans: ["Plus Jakarta Sans", "Inter", "sans-serif"],
  bali: ["Noto Sans Balinese", "sans-serif"],
  display: ["Fraunces", "serif"]
},
borderRadius: {
  "4xl": "2rem"
}
```

---

*Branding ini hidup, akan berkembang dengan feedback komunitas Bali.*
