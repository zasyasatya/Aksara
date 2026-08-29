# Test Plan - Aksara Platform

## Overview

Testing fokus pada akurasi transliterasi (core value) dan UX quiz validation.

## Test Pyramid

- 60% Unit (backend transliterator, classifier, frontend utils)
- 20% Integration (API endpoints)
- 15% E2E (critical user flows)
- 5% Manual (cultural accuracy, font rendering)

## Backend Tests

### Unit: Transliterator

File: `backend/app/tests/test_transliterator.py`

**Latin → Bali Cases (from research papers & common words):**

```python
# Basic Wresastra
assert transliterate("ha", "latin-to-bali") == "ᬳ"
assert transliterate("na", "latin-to-bali") == "ᬦ"
assert transliterate("bali", "latin-to-bali") == "ᬩᬮᬶ"  # ba + la + ulu
assert transliterate("saka", "latin-to-bali") == "ᬲᬓ"

# Pangangge Suara
assert transliterate("bali", "latin-to-bali") == "ᬩᬮᬶ" # ulu
assert transliterate("buku", "latin-to-bali") == "ᬩᬸᬓᬸ" # suku
assert transliterate("sate", "latin-to-bali") == "ᬲᬢᬾ" # taleng
assert transliterate("soto", "latin-to-bali") == "ᬲᭀᬢᭀ" # taleng tedong? Actually o
# Pepet: bleganjur -> ᬩᬼᬕᬜ᭄ᬚᬸᬃ (special)
# Note: pepet handling: "e" as in "bleganjur" vs "e" as in "sate" (taleng) - need context

# Pangangge Tengenan
assert transliterate("nah", "latin-to-bali") contains bisah
assert transliterate("sur", "latin-to-bali") contains surang
assert transliterate("ang", "latin-to-bali") contains cecek OR "ang" special

# Gantungan
assert transliterate("dharma", "latin-to-bali") == "ᬤᬃᬫ" # surang + ma gantungan
assert transliterate("karma", "latin-to-bali") has gantungan
assert transliterate("bajra", "latin-to-bali") == "ᬩᬚ᭄ᬭ" ? Actually need check

# Special words from dictionary
assert transliterate("angklung", "latin-to-bali") == "ᬅᬗ᭄ᬓ᭄ᬮᬸᬂ"
assert transliterate("aksara", "latin-to-bali") == "ᬅᬓ᭄ᬱᬭ" # sa sapa

# Bali → Latin
assert transliterate("ᬩᬮᬶ", "bali-to-latin") == "bali"
assert transliterate("ᬳ", "bali-to-latin") == "ha"
assert transliterate("ᬅᬓ᭄ᬱᬭ", "bali-to-latin") == "aksara"

# Tumpuk Telu Prevention
# Should not produce 2 gantungan on same base
result = transliterate("kstra", "latin-to-bali")
assert not has_tumpuk_telu(result)

# Pepet + Cakra forbidden
# "kret" with pepet + cakra should be handled alternatively
```

**Test Data Sources:**
- 100+ words from paper "Accuracy Analysis of Latin-to-Balinese Transliteration"
- 50 common Balinese words: Om Swastyastu, Rahajeng, Matur Suksma, etc
- Edge: empty string, only spaces, numbers, mixed latin-bali, very long (5000 chars)

### Unit: Classifier

```python
assert classify("ᬳ")["type"] == "wresastra"
assert classify("ᬅ")["type"] == "suara"
assert classify("ᬶ")["type"] == "pangangge_suara"
assert classify("ᬄ")["type"] == "pangangge_tengenan"
assert classify("᭄ᬭ")["type"] == "pangangge_aksara"
```

### Integration: API

```python
# Test /api/translate
client.post("/api/translate", json={"text": "bali", "direction": "latin-to-bali"}).status_code == 200
# Check response structure
# Check rate limiting (61st request should 429)
# Check max length (5001 chars should 400)

# Test /api/classify
# Test /api/lessons
# Test /api/quiz/check
```

## Frontend Tests

### Unit: Utils

- transliterate client mirror
- cn() utility
- store actions

### Component

- AksaraCard renders correct char
- QuizCard shows options
- Translate page: input -> output debounced
- AksaraKeyboard: click inserts char

### E2E (Playwright)

```ts
test("translate flow", async ({ page }) => {
  await page.goto("/translate");
  await page.fill("[data-testid=translate-input]", "bali");
  await expect(page.locator("[data-testid=translate-output]")).toContainText("ᬩᬮᬶ");
});

test("quiz validation - correct", async ({ page }) => {
  await page.goto("/quiz");
  await page.click("[data-testid=option-a]");
  await page.click("[data-testid=submit]");
  await expect(page.locator("[data-testid=feedback]")).toContainText("Benar");
});

test("quiz validation - incorrect shows explanation", async ({ page }) => {
  // ...
  await expect(page.locator("[data-testid=explanation]")).toBeVisible();
});

test("dashboard progress", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.locator("[data-testid=xp]")).toBeVisible();
});

test("responsive - mobile bottom nav", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto("/dashboard");
  await expect(page.locator("[data-testid=bottom-nav]")).toBeVisible();
});
```

## Performance Tests

- Lighthouse CI: LCP <2.5s, CLS <0.1
- API load: 100 RPS for translate, p95 <300ms
- Font loading: Noto Sans Balinese <100KB subset

## Accessibility Tests

- axe-core: no violations
- Keyboard nav: tab through all interactive
- Screen reader: aria-label for aksara

## Cultural Accuracy Tests (Manual)

- Review by Balinese language teacher (simulated checklist):
  - [ ] Wresastra 18 correct?
  - [ ] Swalalita 33 correct?
  - [ ] Pangangge mapping correct?
  - [ ] Gantungan examples correct?
  - [ ] Special words (Angklung, Aksara) correct?
  - [ ] No tumpuk telu violations?
  - [ ] Pepet+Cakra forbidden handled?
- Compare output with komangputra.com for 100 words, measure accuracy

## Test Execution

### Backend
```bash
cd backend
pytest -v --cov=app --cov-report=html
```

### Frontend
```bash
cd frontend
npm run test:unit
npm run test:e2e
npm run lighthouse
```

### CI
GitHub Actions:
- On push: run backend pytest, frontend vitest
- On PR: run e2e + lighthouse
- Block merge if coverage <80% or accuracy <95%

## Test Data

- `backend/app/data/test_cases.json`: 200+ cases with expected latin↔bali
- `frontend/tests/fixtures/quiz.json`: mock quizzes

## Bug Reporting

Template:
- Title: [Module] Brief
- Steps to reproduce
- Expected: ...
- Actual: ...
- Screenshot / API response
- Severity: Critical/High/Medium/Low
- Cultural impact: Yes/No

## Done Criteria for Testing

- All unit tests pass
- Integration tests pass
- E2E critical flows pass
- Accuracy >95% on test_cases.json
- No axe violations
- Lighthouse >90
- Manual cultural checklist passed
