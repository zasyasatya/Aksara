# User Stories - Aksara Platform

## Epic 1: Translate

### US-001: Translate Latin to Bali
**As a** siswa Putu  
**I want to** mengetik teks Latin dan melihat hasil Aksara Bali secara real-time  
**So that** saya bisa menggunakannya untuk tugas atau sosial media  
**Acceptance:**
- Input latin "bali" → output "ᬩᬮᬶ" dalam <200ms
- Breakdown menunjukkan ba + la + ulu
- Copy button
- Handle gantungan otomatis

### US-002: Translate Bali to Latin
**As a** researcher Wayan  
**I want to** paste Aksara Bali dan mendapat transliterasi Latin  
**So that** saya bisa membaca lontar yang tidak saya pahami  
**Acceptance:**
- Input "ᬩᬮᬶ" → "bali"
- Handle pangangge suara & tengenan

### US-003: Gantungan Analysis
**As a** guru Ibu Ayu  
**I want to** melihat analisis gantungan pada kata  
**So that** saya bisa menjelaskan aturan ke murid  
**Acceptance:**
- API /gantungan/analyze mengembalikan clusters, has_gantungan, has_tumpuk_telu

## Epic 2: Learn

### US-004: Browse Lessons
**As a** Putu  
**I want to** melihat daftar pelajaran bertahap  
**So that** saya tahu harus mulai dari mana  
**Acceptance:**
- List lessons grouped by level
- Show progress, locked state
- Filter by level

### US-005: Lesson Detail
**As a** Putu  
**I want to** membuka detail pelajaran Ha Na Ca Ra Ka  
**So that** saya bisa belajar 5 aksara pertama dengan contoh  
**Acceptance:**
- Show aksara cards with bali, latin, name, description
- Examples: hana, hujan
- Audio button (future)
- Button to quiz

### US-006: Progress Tracking
**As a** Putu  
**I want to** melihat XP, streak, level di dashboard  
**So that** saya termotivasi belajar terus  
**Acceptance:**
- Dashboard shows xp, streak, completed count
- Progress bar
- Badges

## Epic 3: Quiz & Validation

### US-007: Multiple Choice Quiz
**As a** Putu  
**I want to** menjawab soal pilihan ganda "Pilih aksara Ha"  
**So that** saya bisa test pemahaman  
**Acceptance:**
- Show question, 4 options with bali chars
- Select → feedback correct/incorrect + explanation
- XP earned

### US-008: Validate Pair (Core)
**As a** Ibu Ayu (guru)  
**I want to** membuat soal: "Apakah ᬩᬮᬶ benar untuk bali?" dan murid jawab benar/salah  
**So that** murid bisa menentukan apakah aksara yang ditulis sudah benar sesuai soal  
**Acceptance:**
- POST /quiz/validate-pair with question_latin, question_bali, user_bali
- Return is_correct, similarity, differences, suggestions
- Suggestions like "Kehilangan ulu"

### US-009: Gantungan Quiz
**As a** Putu level 4  
**I want to** soal gantungan: "Pilih yang benar untuk dharma"  
**So that** saya paham aturan gantungan vs surang  
**Acceptance:**
- Options show different bali writings
- Explanation mentions surang + gantungan ma

### US-010: Arrangement Quiz (Future)
**As a** Putu  
**I want to** menyusun aksara acak menjadi kata benar  
**So that** belajar menulis

## Epic 4: Playground

### US-011: Virtual Keyboard
**As a** Putu  
**I want to** keyboard virtual Aksara Bali untuk ngetik bebas  
**So that** saya bisa latihan tanpa harus hafal keyboard fisik  
**Acceptance:**
- Show Wresastra 18 buttons
- Show Pangangge buttons
- Click inserts to text area
- Translate button

### US-012: Free Validation
**As a** Putu  
**I want to** tulis bebas di playground dan validasi apakah benar untuk kata tertentu  
**So that** saya bisa eksperimen

## Epic 5: Responsive & Accessibility

### US-013: Mobile Bottom Nav
**As a** Putu yang mobile-first  
**I want to** bottom navigation di HP  
**So that** mudah navigasi dengan jempol  
**Acceptance:**
- Bottom nav visible <1024px
- 5 items: Home, Belajar, Translate, Kuis, Play
- Active state with bg deep-brown

### US-014: Desktop Sidebar
**As a** Wayan di desktop  
**I want to** sidebar nav di desktop  
**So that** lebih banyak ruang konten  
**Acceptance:**
- Header with nav items horizontal
- No bottom nav on desktop

### US-015: Font Loading
**As a** user dengan internet lambat  
**I want to** Noto Sans Balinese load dengan swap  
**So that** tidak ada FOIT lama

## Epic 6: Branding & Culture

### US-016: Cultural Accuracy
**As a** budayawan  
**I want to** transliterasi mengikuti aturan tumpuk telu, pepet+cakra forbidden  
**So that** platform tidak menyebarkan kesalahan  
**Acceptance:**
- Unit tests for tumpuk telu detection
- Pepet+cakra handling
- Dictionary for special words

### US-017: Balinese Greeting
**As a** Putu  
**I want to** melihat greeting "Rahajeng!" dan "Matur Suksma"  
**So that** feel Bali-nya kuat
