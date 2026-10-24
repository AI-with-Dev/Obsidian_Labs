/**
 * Advanced Multi-Dialect Hindi, Haryanvi & Regional Accented Spoken Amount Parser.
 * Supports:
 * - Standard Hindi (खड़ी बोली)
 * - Haryanvi (हरियाणवी: "च्यार सै", "डेढ सै", "रुपै आग्ये", "देग्या", "अर", "ताऊ के 500 जोड़ ले")
 * - Bhojpuri & Purvanchali ("दू सौ पचास रुपया", "मिलल", "देलक")
 * - Rajasthani / Marwari ("दोय सौ", "रिपिया", "रोकड़")
 * - Hinglish & colloquial retail slang ("chai 40 ar 20 biscuit", "cash 500", "likh le 600")
 * - Devanagari numerals (०, १, २, ३, ४, ५, ६, ७, ८, ९)
 * - Scale multipliers (सौ, सै, हजार, हज्यार, लाख, करोड़)
 * - Colloquial Indian fractions (डेढ़/डेढ, ढाई, साढ़े/साढे, सवा, पौने/पौणे)
 * - Intelligent customer / payer name extraction (e.g. "ताऊ रामफल 800 देग्या" -> "ताऊ रामफल")
 */

const DEVANAGARI_DIGITS = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९']

export function convertDevanagariDigits(str: string): string {
  return str.replace(/[०-९]/g, d => String(DEVANAGARI_DIGITS.indexOf(d)))
}

export function normalizeDialectWords(text: string): string {
  let s = text
  // Convert Haryanvi 'सै' / 'sai' to 'सौ' (hundred) when preceded by numerals or fractions
  // e.g. 'दो सै' -> 'दो सौ', 'च्यार सै' -> 'च्यार सौ', 'डेढ सै' -> 'डेढ सौ', '500 सै' -> '500 सौ'
  s = s.replace(
    /((?:एक|दो|दू|दोय|तीन|तीन्या|चार|च्यार|चयार|पांच|पाँच|छे|छह|छी|सात|आठ|नौ|नू|दस|ग्यारह|ग्यारा|बारह|बारा|तेरह|तेरा|चौदह|चौदा|पंद्रह|पंदरा|सोलह|सोला|सत्रह|सतरा|अठारह|अठारा|उन्नीस|उगणीस|उगनीस|गुणीस|बीस|पच्चीस|पचीस|तीस|चालीस|चाली|पचास|साठ|सत्तर|अस्सी|नब्बे|\d+))\s*(?:सै|sai)(?=[\s,.]|$|[^\u0900-\u097Fa-zA-Z0-9])/gi,
    '$1 सौ'
  )
  s = s.replace(
    /((?:डेढ़|डेढ|डैढ|ढाई|साढ़े|साढे|साढै|सवा|सवाय|पौने|पौणे|पोने))\s*(?:सै|sai)(?=[\s,.]|$|[^\u0900-\u097Fa-zA-Z0-9])/gi,
    '$1 सौ'
  )
  return s
}

export function preprocessFractions(text: string): string {
  return text
    // Dedh (1.5) & Dhai (2.5) with multipliers in Hindi & Haryanvi
    .replace(/(?:डेढ़|डेढ|डैढ|dedh|dadh)\s*(?:हज़ार|हजार|हज्यार|hazar|hazaar|thousand)/gi, ' 1500 ')
    .replace(/(?:ढाई|ढ़ाई|dhai)\s*(?:हज़ार|हजार|हज्यार|hazar|hazaar|thousand)/gi, ' 2500 ')
    .replace(/(?:डेढ़|डेढ|डैढ|dedh|dadh)\s*(?:सौ|sau|hundred)/gi, ' 150 ')
    .replace(/(?:ढाई|ढ़ाई|dhai)\s*(?:सौ|sau|hundred)/gi, ' 250 ')
    .replace(/(?:डेढ़|डेढ|डैढ|dedh|dadh)\s*(?:लाख|lakh|lac)/gi, ' 150000 ')
    .replace(/(?:ढाई|ढ़ाई|dhai)\s*(?:लाख|lakh|lac)/gi, ' 250000 ')
    .replace(/(?:डेढ़|डेढ|डैढ|dedh|dadh)/gi, ' 1.5 ')
    .replace(/(?:ढाई|ढ़ाई|dhai)/gi, ' 2.5 ')
    // Saadhe (+0.5) with hundreds in Hindi & Haryanvi accents
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:एक|ek|1)\s*(?:सौ|sau)/gi, ' 150 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:दो|दू|दोय|do|2)\s*(?:सौ|sau)/gi, ' 250 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:तीन|teen|3)\s*(?:सौ|sau)/gi, ' 350 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:चार|च्यार|चयार|chaar|char|4)\s*(?:सौ|sau)/gi, ' 450 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:पांच|पाँच|paanch|5)\s*(?:सौ|sau)/gi, ' 550 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:छह|छः|छे|chhe|6)\s*(?:सौ|sau)/gi, ' 650 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:सात|saat|7)\s*(?:सौ|sau)/gi, ' 750 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:आठ|aath|8)\s*(?:सौ|sau)/gi, ' 850 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:नौ|nau|9)\s*(?:सौ|sau)/gi, ' 950 ')
    // Saadhe (+0.5) with thousands
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:एक|ek|1)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 1500 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:दो|दू|दोय|do|2)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 2500 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:तीन|teen|3)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 3500 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:चार|च्यार|चयार|chaar|char|4)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 4500 ')
    .replace(/(?:साढ़े|साढे|साढै|saadhe|sadhe)\s*(?:पांच|पाँच|paanch|5)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 5500 ')
    // Sawa (1.25)
    .replace(/(?:सवा|सवाय|sawa)\s*(?:सौ|sau)/gi, ' 125 ')
    .replace(/(?:सवा|सवाय|sawa)\s*(?:दो|दू|दोय|do|2)\s*(?:सौ|sau)/gi, ' 225 ')
    .replace(/(?:सवा|सवाय|sawa)\s*(?:तीन|teen|3)\s*(?:सौ|sau)/gi, ' 325 ')
    .replace(/(?:सवा|सवाय|sawa)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 1250 ')
    // Paune (0.75)
    .replace(/(?:पौने|पौणे|पोने|paune|pone)\s*(?:सौ|sau)/gi, ' 75 ')
    .replace(/(?:पौने|पौणे|पोने|paune|pone)\s*(?:दो|दू|दोय|do|2)\s*(?:सौ|sau)/gi, ' 175 ')
    .replace(/(?:पौने|पौणे|पोने|paune|pone)\s*(?:तीन|teen|3)\s*(?:सौ|sau)/gi, ' 275 ')
    .replace(/(?:पौने|पौणे|पोने|paune|pone)\s*(?:चार|च्यार|चयार|chaar|char|4)\s*(?:सौ|sau)/gi, ' 375 ')
    .replace(/(?:पौने|पौणे|पोने|paune|pone)\s*(?:हज़ार|हजार|हज्यार|hazar)/gi, ' 750 ')
}

export const MULTIPLIERS: Record<string, number> = {
  'करोड़': 10000000, 'करोड़': 10000000, 'crore': 10000000, 'cr': 10000000, 'crs': 10000000,
  'लाख': 100000, 'lakh': 100000, 'lac': 100000, 'lacs': 100000, 'lakhs': 100000,
  'हज़ार': 1000, 'हजार': 1000, 'हज्यार': 1000, 'हजार्या': 1000, 'hazar': 1000, 'hazaar': 1000, 'thousand': 1000, 'k': 1000,
  'सौ': 100, 'sau': 100, 'hundred': 100,
}

export const UNITS: Record<string, number> = {
  // 0 - 10 (Hindi, Haryanvi, Bhojpuri, Rajasthani)
  'शून्य': 0, 'zero': 0, 'shunya': 0, 'सिफर': 0,
  'एक': 1, 'ek': 1, 'one': 1, 'इक्क': 1,
  'दो': 2, 'दू': 2, 'दोय': 2, 'do': 2, 'two': 2, 'du': 2, 'doy': 2,
  'तीन': 3, 'तीन्या': 3, 'teen': 3, 'tin': 3, 'three': 3,
  'चार': 4, 'च्यार': 4, 'चयार': 4, 'chaar': 4, 'char': 4, 'four': 4, 'chyaar': 4,
  'पांच': 5, 'पाँच': 5, 'paanch': 5, 'panch': 5, 'five': 5, 'पंज': 5,
  'छह': 6, 'छः': 6, 'छे': 6, 'छी': 6, 'chhe': 6, 'chhah': 6, 'six': 6,
  'सात': 7, 'saat': 7, 'sat': 7, 'seven': 7,
  'आठ': 8, 'aath': 8, 'ath': 8, 'eight': 8,
  'नौ': 9, 'नू': 9, 'nau': 9, 'no': 9, 'nine': 9,
  'दस': 10, 'दहे': 10, 'das': 10, 'ten': 10,
  // 11 - 20 (Regional pronunciations: ग्यारा, बारा, तेरा, चौदा, पंदरा, सोला, सतरा, अठारा, उगणीस)
  'ग्यारह': 11, 'ग्यारा': 11, 'ग्यारे': 11, 'gyarah': 11, 'gyara': 11, 'eleven': 11,
  'बारह': 12, 'बारा': 12, 'बारे': 12, 'barah': 12, 'bara': 12, 'twelve': 12,
  'तेरह': 13, 'तेरा': 13, 'terah': 13, 'tera': 13, 'thirteen': 13,
  'चौदह': 14, 'चौदा': 14, 'chaudah': 14, 'chauda': 14, 'fourteen': 14,
  'पंद्रह': 15, 'पंदरा': 15, 'pandrah': 15, 'pandra': 15, 'fifteen': 15,
  'सोलह': 16, 'सोला': 16, 'solah': 16, 'sola': 16, 'sixteen': 16,
  'सत्रह': 17, 'सतरा': 17, 'satrah': 17, 'satra': 17, 'seventeen': 17,
  'अठारह': 18, 'अठारा': 18, 'atharah': 18, 'athara': 18, 'eighteen': 18,
  'उन्नीस': 19, 'उगणीस': 19, 'उगनीस': 19, 'गुणीस': 19, 'गुनीस': 19, 'unnees': 19, 'unnis': 19, 'ugnees': 19, 'ugnis': 19, 'nineteen': 19,
  'बीस': 20, 'bees': 20, 'bis': 20, 'twenty': 20,
  // 21 - 30
  'इक्कीस': 21, 'ikkees': 21, 'ikkis': 21,
  'बाईस': 22, 'baees': 22, 'bais': 22,
  'तेईस': 23, 'teees': 23, 'teis': 23,
  'चौबीस': 24, 'chaubees': 24, 'chaubis': 24,
  'पच्चीस': 25, 'पचीस': 25, 'pachchees': 25, 'pachis': 25, 'pachees': 25,
  'छब्बीस': 26, 'chhabbees': 26,
  'सत्ताईस': 27, 'sattaees': 27,
  'अट्ठाईस': 28, 'atthaees': 28,
  'उनतीस': 29, 'untees': 29, 'untis': 29,
  'तीस': 30, 'tees': 30, 'tis': 30, 'thirty': 30,
  // 31 - 40
  'इकत्तीस': 31, 'ikattees': 31,
  'बत्तीस': 32, 'battees': 32,
  'तैंतीस': 33, 'taintees': 33,
  'चौंतीस': 34, 'chauntees': 34,
  'पैंतीस': 35, 'paintees': 35, 'paintis': 35,
  'छत्तीस': 36, 'chhattees': 36,
  'सैंतीस': 37, 'saintees': 37,
  'अड़तीस': 38, 'adatees': 38,
  'उनतालीस': 39, 'untalees': 39,
  'चालीस': 40, 'चाली': 40, 'chalees': 40, 'chalis': 40, 'forty': 40,
  // 41 - 50
  'इकतालीस': 41, 'iktalees': 41,
  'बयालीस': 42, 'bayalees': 42,
  'तैंतालीस': 43, 'taintalees': 43,
  'चवालीस': 44, 'chawalees': 44,
  'पैंतालीस': 45, 'paintalees': 45, 'paintalis': 45,
  'छियालीस': 46, 'chhiyalees': 46,
  'सैंतालीस': 47, 'saintalees': 47,
  'अड़तालीस': 48, 'adtalees': 48,
  'उनचास': 49, 'unchas': 49,
  'पचास': 50, 'पचासे': 50, 'pachas': 50, 'pachaas': 50, 'fifty': 50,
  // 51 - 60
  'इक्यावन': 51, 'ikyawan': 51,
  'बावन': 52, 'bawan': 52,
  'तिरपन': 53, 'tirpan': 53,
  'चौवन': 54, 'chauwan': 54,
  'पचपन': 55, 'pachpan': 55,
  'छप्पन': 56, 'chhappan': 56,
  'सत्तावन': 57, 'sattawan': 57,
  'अट्ठावन': 58, 'atthawan': 58,
  'उनसठ': 59, 'unsath': 59,
  'साठ': 60, 'saath': 60, 'sath': 60, 'sixty': 60,
  // 61 - 70
  'इकसठ': 61, 'iksath': 61,
  'बासठ': 62, 'baasath': 62,
  'तिरसठ': 63, 'tirsath': 63,
  'चौंसठ': 64, 'chaunsath': 64,
  'पैंसठ': 65, 'painsath': 65,
  'छियासठ': 66, 'chhiyasath': 66,
  'सरसठ': 67, 'sarsath': 67,
  'अड़सठ': 68, 'adsath': 68,
  'उनहत्तर': 69, 'unhattar': 69,
  'सत्तर': 70, 'sattar': 70, 'seventy': 70,
  // 71 - 80
  'इकहत्तर': 71, 'ikhattar': 71,
  'बहत्तर': 72, 'bahattar': 72,
  'तिहत्तर': 73, 'tihattar': 73,
  'चौहत्तर': 74, 'chauhattar': 74,
  'पचहत्तर': 75, 'pachhattar': 75,
  'छिहत्तर': 76, 'chhihattar': 76,
  'सतहत्तर': 77, 'sathattar': 77,
  'अठहत्तर': 78, 'athahattar': 78,
  'उन्यासी': 79, 'uniyasi': 79,
  'अस्सी': 80, 'assi': 80, 'assee': 80, 'eighty': 80,
  // 81 - 90
  'इक्यासी': 81, 'ikyasi': 81,
  'बयासी': 82, 'bayasi': 82,
  'तिरासी': 83, 'tirasi': 83,
  'चौरासी': 84, 'chaurasi': 84,
  'पचासी': 85, 'pachasi': 85,
  'नब्बे': 90, 'nabbe': 90, 'ninety': 90,
  // 91 - 99
  'इक्यानवे': 91, 'ikyanwe': 91,
  'बानवे': 92, 'banwe': 92,
  'तिरानवे': 93, 'tiranwe': 93,
  'चौरानवे': 94, 'chauranwe': 94,
  'पचानवे': 95, 'pachanwe': 95,
  'छियानवे': 96, 'chhiyanwe': 96,
  'सत्तानवे': 97, 'sattanwe': 97,
  'अट्ठानवे': 98, 'atthanwe': 98,
  'निन्यानवे': 99, 'ninyanwe': 99,
}

export function parseSingleNumberExpression(text: string): number {
  const cleaned = convertDevanagariDigits(text)
    .replace(/₹|rs\.?|inr/gi, ' ')
    .replace(/([0-9]+(?:\.[0-9]+)?)/g, ' $1 ')

  const tokens = cleaned.trim().toLowerCase().split(/\s+/).filter(Boolean)
  let total = 0
  let current = 0
  let matchedAny = false

  for (const t of tokens) {
    if (MULTIPLIERS[t] !== undefined) {
      const mult = MULTIPLIERS[t]
      if (current === 0) current = 1
      current = current * mult
      matchedAny = true
      if (mult >= 1000) {
        total += current
        current = 0
      }
    } else if (UNITS[t] !== undefined) {
      current += UNITS[t]
      matchedAny = true
    } else if (!isNaN(Number(t))) {
      current += Number(t)
      matchedAny = true
    }
  }
  total += current
  return matchedAny ? total : 0
}

export interface ParsedAudioResult {
  total: number
  breakdown: string
  payer: string
  rawTranscript: string
}

export function parseSpokenHindiAudio(text: string, defaultPayer = 'दुकान आवक'): ParsedAudioResult {
  if (!text || !text.trim()) {
    return { total: 0, breakdown: '', payer: defaultPayer, rawTranscript: text }
  }

  let converted = convertDevanagariDigits(text)
  converted = normalizeDialectWords(converted)
  converted = preprocessFractions(converted)

  // Split on addition conjunctions including Haryanvi 'अर', 'अरु', 'गैल'
  const rawSegments = converted.split(/\s*(?:aur|and|plus|और|अर|अरु|गैल|तथा|जमा|\+)\s*/i)
  let grandTotal = 0
  const itemParts: string[] = []

  for (const seg of rawSegments) {
    // Check if segment has quantity x item x rate pattern: e.g. "2 register 40 rupai"
    const mMatch = seg.match(
      /(?:(\d+)\s+([a-zA-Z\u0900-\u097F]+)\s+(\d+)\s*(?:रुपये|रुपए|रुपै|रूपै|रिपिए|रपिए|रुपिया|rupees|rupaye|rupai)?)/i
    )
    if (mMatch && Number(mMatch[1]) > 0 && Number(mMatch[3]) > 0) {
      const qty = Number(mMatch[1])
      const itemName = mMatch[2]
      const rate = Number(mMatch[3])
      const lineTotal = qty * rate
      grandTotal += lineTotal
      itemParts.push(`${qty}x ${itemName} (₹${rate}) = ₹${lineTotal}`)
      continue
    }

    const val = parseSingleNumberExpression(seg)
    if (val > 0) {
      grandTotal += val
      itemParts.push(`₹${val}`)
    }
  }

  // Extract clean payer / customer name by stripping numbers, currency words & transaction verbs
  let payer = convertDevanagariDigits(text)
  payer = normalizeDialectWords(payer)
  payer = preprocessFractions(payer)
  payer = payer.replace(/[0-9]+(?:\.[0-9]+)?/g, ' ')
  payer = payer.replace(/₹|\$|\+|\-|\*|\//g, ' ')

  const allWordKeys = [
    ...Object.keys(MULTIPLIERS),
    ...Object.keys(UNITS),
    'डेढ़', 'डेढ', 'डैढ', 'dedh', 'ढाई', 'ढ़ाई', 'dhai', 'साढ़े', 'साढे', 'साढै', 'saadhe', 'sadhe', 'सवा', 'sawa', 'पौने', 'पौणे', 'paune'
  ]
  for (const w of allWordKeys) {
    const reg = new RegExp('(^|\\s+)' + w + '(?=[\\s,.:;!?()]|$|[^\u0900-\u097Fa-zA-Z0-9])', 'gi')
    payer = payer.replace(reg, ' ')
  }

  // Dialect transaction verbs, prepositions & stop words (Haryanvi, Bhojpuri, Rajasthani, Hindi)
  const stopWords =
    /(?:^|\s+)(?:rupees|rupaye|rupay|rupai|रुपये|रुपए|रुपया|रुपै|रूपै|रिपिए|रपिए|रुपिया|रिपिया|टका|रु|रू|rs|inr|aur|and|plus|और|अर|अरु|गैल|तथा|जमा|का|की|के|से|सूं|ने|पै|पे|माँ|म्ह|भीतर|मिला|मिले|मिल्या|मिलगे|मिलग्या|पागे|आया|आए|आये|आयगे|आग्ये|आगे|आयग्या|आग्या|आयले|देग्या|देगे|दिए|दीया|दे\s+गया|दे\s+गए|देलक|देहलक|मिलल|आयल|आगिल|लिख\s+ले|लिख\s+दो|लिख\s+लेई|जोड़\s+ले|जोड़\s+दो|जोड़\s+दे|जोड़\s+ले|चढ़ा\s+ले|चढ़ा\s+दे|धर\s+दे|धर\s+ले|खाता|खाते|गल्ला|गल्ले|दुकान|cash|नकद|नगद|नगदी|रोकड़|रोकड़ा|पेमेंट|payment)(?=[\s,.:;!?()]|$|[^\u0900-\u097Fa-zA-Z0-9])/gi

  payer = payer.replace(stopWords, ' ').replace(stopWords, ' ').replace(stopWords, ' ').replace(/\s+/g, ' ').trim()

  return {
    total: grandTotal,
    breakdown: itemParts.length > 1 ? itemParts.join(' + ') : (itemParts[0] || ''),
    payer: payer.length > 1 ? payer : defaultPayer,
    rawTranscript: text
  }
}
