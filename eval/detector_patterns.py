"""
Pattern configuration and matchers for bias detection.

Holds all regex-based pattern data (counter-stereotype, derogation, Swahili
gendered-suffix) and compiled matchers. Used by BiasDetector so pattern config
is separate from lexicon matching and result building.
"""
import re
from typing import Dict, List, Any, Optional

from .models import Language, StereotypeCategory, TargetGender


# Counter-stereotype patterns by language (role reversals / challenges to norms)
COUNTER_STEREOTYPE_PATTERNS: Dict[Language, List[tuple]] = {
    Language.ENGLISH: [
        (r'\b(father|dad|husband)\b.*(caregiver|nurtur|cook|clean|homemaker|stay.at.home)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\b(mother|mom|wife)\b.*(breadwinner|provider|work.*(full.time|office)|career)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\b(female|woman|she)\b.*(engineer|mechanic|pilot|ceo|surgeon|firefighter)',
         StereotypeCategory.PROFESSION, TargetGender.FEMALE),
        (r'\b(male|man|he)\b.*(nurse|secretary|receptionist|kindergarten|nanny)',
         StereotypeCategory.PROFESSION, TargetGender.MALE),
        # Require affirmative context — exclude negations like "can't lead"
        (r'\b(she|her|woman|female)\b(?!.*\b(can\'t|cannot|couldn\'t|unable|never|not)\b).*(lead|command|chief|director|president|boss)',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
    ],
    Language.SWAHILI: [
        (r'\bbaba\b.+\b(anale[zl]a|anapika|anasafisha|anakaa\s+nyumbani)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\bbaba\b.{0,30}\b(analelea|analinda|anatunza|anasimamia)\s+watoto\s+peke\s+yake\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\bmama\b.+\b(anafanya\s+kazi\s+ofisi|ni\s+mkurugenzi|anaongoza)',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # Require positive assertion (ni/amekuwa/alifanya kazi kama) — not sentences with hawezi
        (r'\bmwanamke\b.{0,40}\b(ni|amekuwa|alifanya\s+kazi\s+kama|anafanya\s+kazi\s+kama|aliwahi\s+kuwa)\b.{0,30}\b(mhandisi|rubani|fundi\s+wa\s+magari)\b',
         StereotypeCategory.PROFESSION, TargetGender.FEMALE),
        (r'\bmwanamume\b.+\b(muuguzi|mkunga|mlezi\s+wa\s+watoto)',
         StereotypeCategory.PROFESSION, TargetGender.MALE),
        # Girl in leadership role — challenge to norms
        (r'\bmsichana\b.{0,30}\b(ni\s+rais|ni\s+mkurugenzi|ni\s+kiongozi|anaongoza|ameongoza|amechaguliwa)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # Mwanamke in technical leadership
        (r'\bmwanamke\b.{0,30}\b(anaongoza\s+mradi|mkurugenzi\s+mkuu|rubani\s+mkuu|nahodha)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
    ],
}

# Derogation patterns - language that demeans or disparages
DEROGATION_PATTERNS: Dict[Language, List[tuple]] = {
    Language.ENGLISH: [
        (r'\b(just|only|merely)\s+a\s+(woman|girl|female|housewife)',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(woman|women|female|girl).*(can\'t|cannot|unable|incapable|shouldn\'t|could\s+never)',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(women|woman)\s+(cannot|can\'t)\s+be\s+(good|great|effective)',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        (r'\b(like\s+a\s+girl|throw.like.a.girl|cry.like)',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(too\s+emotional|hysterical|overreact)',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(real\s+men\s+don\'t|man\s+up|be\s+a\s+man)',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
    ],
    Language.SWAHILI: [
        (r'\bni\s+tu\s+(mwanamke|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana)\b\s+hawezi\b(?!\s+(?:kuzaa|kukoma|kupenda|kunifikia|kufikia|kukufikia|bila\s+kuwezeshwa))',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(kama\s+msichana|kama\s+mwanamke)\b.{0,30}\b(dhaifu|hawezi|haiwezi|hana nguvu|anapiga|analia)',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Capability stereotypes
        (r'\bwanawake\b.{0,40}\b(hawafai|hawawezi|hawapaswi|si wazuri|si hodari|hana uwezo|hawana uwezo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\bwanaume\b.{0,40}\b(hawafai|hawawezi|hawapaswi|si wazuri|hawana uwezo)\b.{0,30}\b(huduma|watoto|nyumba|familia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\bmsichana\b.{0,40}\b(hakuwepo|alitoroka|hakufika|alishindwa|hakuweza)\b.{0,30}\b(shule|darasa|mtihani|elimu)\b',
         StereotypeCategory.EDUCATION, TargetGender.FEMALE),
        # Appearance / body stereotypes
        (r'\b(mwanamke|msichana|mke)\b.{0,50}\b(mzuri|mrembo|mrefu|mfupi|nzuri|mvuto|mwili).{0,30}\b(lazima|anapaswa|sharti|inahitajika)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Appearance demeaning — mbaya split out: "msichana mbaya katika mapenzi" is usually attributed gossip in news (FP)
        (r'\b(mwanamke|msichana)\b.{0,30}\b(si mzuri|si mrembo|hana mvuto|hana kitu)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana)\b.{0,25}\bmbaya\b(?!\s+katika\s+mapenzi)',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Personality / emotion stereotypes
        (r'\bwanawake\b.{0,40}\b(wanaelewa|wanafikiri|wanajua|wanaweza).{0,20}\b(kidogo|tu|chini|zaidi ya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(wanaume|mwanaume)\b.{0,30}\b(hawalia|hawaonyeshi|usihisi|hisia|kilio)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # Domestic role prescription
        (r'\b(mwanamke|mke|mama)\b.{0,50}\b(anapaswa|lazima|sharti|inabidi)\b.{0,40}\b(kupika|kusafisha|kutunza|kubaki nyumbani|nyumbani)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\bsisi\s+wanaume\b.{0,60}\b(tunaongoza|tunalazimisha|tunaamua|tunapaswa)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # Implicit surprise — 'hata' + exceptional role (exclude bare anaweza/wanaweza: common in factual/empowerment news)
        (r'\bhata\s+(wanawake|mwanamke|msichana)\b.{0,40}\b(wanajeshi|kiongozi|daktari|mhandisi|rubani|nahodha|spika|mbunge|rais|mkurugenzi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Comparative derogation — gender-qualifying achievement sets lower baseline
        (r'\balifanya\s+kazi\s+nzuri\s+kwa\s+(mwanamke|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\bkwa\s+(mwanamke|msichana)\b.{0,20}\b(alifanya|alifanikiwa|alishinda|alimfaulu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Passive child-marriage — erases girl's agency
        (r'\b(aliozeshwa|alipozeshwa|waliozeshwa)\b.{0,30}\b(akiwa\s+na\s+miaka|mdogo|mchanga|kabla)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # Religious prescriptive submission framing
        (r'\b(lazima|sharti|inabidi)\b.{0,20}\bamtii\s+mume\b.{0,30}\b(dini|mungu|biblia|quran|kanisa|msikiti)\b',
         StereotypeCategory.RELIGION_CULTURE, TargetGender.FEMALE),
        # Intersectional: rural women framed as uneducated
        (r'\bwanawake\s+wa\s+vijijini\b.{0,50}\b(hawana|hawajui|hawajasomea|hawana\s+elimu|hawajapata)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Female student blame/restriction patterns — zero FP across 64K rows
        (r'\bwanafunzi\s+wa\s+kike\b.{0,150}\b(kuwatongoza\s+wavulana|wanawatongoza\s+wavulana)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\bwanafunzi\s+wa\s+kike\b.{0,150}\b(kujilengesha|viherehere)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\bwanafunzi\s+wa\s+kike\b.{0,150}\bmatendo\s+yasiyokuwa\s+ya\s+kimasomo\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\bwanafunzi\s+wa\s+kike\b.{0,150}\bdawa\s+za\s+kuzuia\s+mimba\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\bwanafunzi\s+wa\s+kike\b.{0,150}\bkujiweka\s+mbali\s+na\s+(ngono|uhusiano\s+wa\s+kimapenzi|mapenzi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Virginity testing of students — explicit derogation
        (r'\bkuwapima\s+(wanafunzi|watoto)\b.{0,60}\bbikira\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # kujilengesha — blame-framing girls for their own pregnancy
        (r'\bkujilengesha\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # malaya — explicit gendered slur in direct assertion contexts only
        # Scoped to avoid FPs in news articles, quoted speech, compound nouns (umalaya)
        (r'\b(ni|kuwa|kwamba)\s+malaya\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\bmalaya\s+(wewe|sana|mkubwa|mno)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Appearance-as-value derogation — reduces women's worth to body/looks
        # "sura ndiyo utajiri", "mwili ndiyo mtaji", "mzuri tu ndiye anayestahili"
        (r'\b(sura|uzuri|mwili|viuno)\b.{0,20}\b(ndiyo|ni)\b.{0,30}\b(utajiri|mtaji|silaha|nguvu)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(anathaminiwa|anapimwa|anahukumiwa)\b.{0,30}\b(sura|mwili|uzuri)\b.{0,20}\b(siyo|si|zaidi\s+ya)\b.{0,30}\b(akili|ujuzi|kazi)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana|wanawake|wasichana)\b.{0,30}\b(mzuri|nzuri|mrembo)\b.{0,20}\b(tu\s+ndiye|tu\s+ndio|pekee)\b.{0,40}\b(anayestahili|wanaofaa|anapata|wanapata)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(mwili|mwili\s+wake)\b.{0,15}\b(ndiyo|ni)\b.{0,20}\b(mtaji|utajiri)\b.{0,20}\b(siyo|si)\b.{0,20}\bakili\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Sheng gender-capability derogation: manzi/dem/dame/msupa/slay queen + hawezi/dhaifu/wajinga
        (r'\b(manzi|dem|dame|msupa|slay\s+queen|mresh)\b.{0,50}\b(hawezi|hawawezi|dhaifu|wajinga|hawajui|hana\s+akili|ni\s+zero|afikirie\s+tu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(hizi\s+dame|hizi\s+dem|hizi\s+manzi|madem)\b.{0,50}\b(wajinga|hawajui|ni\s+wajinga|ni\s+dhaifu|hawana\s+akili)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng male-dependency framing: dame/manzi anahitaji morio amfanyie maamuzi
        (r'\b(dame|manzi|msupa)\b.{0,60}\b(anahitaji|inahitajika)\b.{0,30}\b(morio|msee|mwanaume)\b.{0,40}\b(amfanyie|amwambie|amweleze|kumwambia|kufanya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng domestic expectation: manzi/dem + domestic verb (kupika/kufua/kupiga pasi)
        (r'\b(manzi|dem|dame)\b.{0,80}\b(imefua|amefua|anapika|alipika|amepika|kupika|kufua|kupiga\s+pasi)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # Appearance-as-value: gender term + mzuri/sura + siyo masomo/ujuzi/akili
        (r'\b(manzi|msichana|mwanamke|wasichana)\b.{0,30}\b(mzuri|nzuri)\b.{0,40}\b(sura|uzuri)\b.{0,30}\b(siyo|si)\b.{0,20}\b(masomo|elimu|ujuzi|akili)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Aging derogation: mwanamke akizeeka / kupoteza sura / hana thamani
        (r'\b(mwanamke|msichana|wanawake)\b.{0,50}\b(akizeeka|azeeke|wanazeeka)\b.{0,60}\b(hana\s+thamani|kupoteza\s+sura|si\s+wa\s+kuvutia|hawana\s+thamani)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # hawezi kuwa mwaminifu — faithfulness capability denial tied to gender
        (r'\b(mwanamke|msichana|manzi|dame)\b.{0,40}\bhawezi\s+kuwa\s+mwaminifu\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # udhaifu wa kiuchumi wa wasichana used to exploit — framing girls as economically weak targets
        (r'\budhaifu\s+(huu\s+wa\s+kiuchumi|wa\s+kiuchumi)\b.{0,30}\b(wasichana|wanawake)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # mwanamke hawezi kujitawala/kukataa — self-governance and consent denial
        # Wide window: subject and predicate may be separated by subordinate clause
        (r'\b(mwanamke|msichana)\b.{0,120}\bhawezi\s+(kujitawala|kukataa|kujiamua|kujiamulia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # chombo dhaifu / viumbe dhaifu — gendered weakness label (either word order)
        (r'\b(chombo\s+dhaifu|viumbe\s+dhaifu)\b.{0,50}\b(mwanamke|wanawake|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(mwanamke|wanawake|wasichana|msichana)\b.{0,50}\b(chombo\s+dhaifu|viumbe\s+dhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(mwanamke|wanawake|wasichana|msichana)\b.{0,30}\b(ni\s+dhaifu|ni\s+wadhaifu|ni\s+mdhaifu|bado\s+ni\s+wadhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\bmoyo\s+dhaifu\b.{0,40}\b(humfanya|hafai|huwafanya|hawafai)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # hawawezi kuongozwa na msichana — leadership-denial targeting girls
        (r'\bhawawezi\s+kuongozwa\s+na\s+(msichana|mwanamke)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # Explicit leadership exclusion: hawastahili/hawafai + leadership role
        (r'\b(msichana|mwanamke|wasichana|wanawake)\b.{0,40}\b(hawastahili|hawafai|hawawezi|hawapaswi)\b.{0,60}\b(mkurugenzi|rais|kiongozi|mbunge|siasa|maamuzi|wadhifa|nafasi\s+ya\s+uongozi)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # Sheng leadership exclusion: morio wanafaa kuongoza si dame / manzi za campus hazifai
        (r'\b(morio|wanaume)\b.{0,30}\b(wanafaa|wanaswali|ndio)\b.{0,30}\b(kuongoza|viongozi)\b.{0,30}\b(si|siyo)\b.{0,30}\b(dame|manzi|msichana|wanawake)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        (r'\b(hizi\s+manzi|hizi\s+dame)\b.{0,50}\b(hazifai|haziwezi|hazipaswi)\b.{0,40}\b(student\s+leaders|viongozi|kuongoza|uongozi)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # Viongozi wa kiume — unnecessary gender marker on leadership (parallel to suffix detector)
        (r'\bviongozi\s+wa\s+kiume\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # Familia decision-making exclusion: mwanamke hawafai kufanya maamuzi peke yake
        (r'\b(mwanamke|msichana)\b.{0,30}\b(hawafai|hapaswi|hana\s+haki|hawastahili)\b.{0,40}\b(maamuzi|kuamua|kufanya\s+maamuzi)\b.{0,30}\b(peke\s+yake|familia|nyumba)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # Sheng: mathee hawezi elewa mambo ya business (mother can't understand business)
        (r'\b(mathee|mama\s+yake|mama\s+wangu)\b.{0,40}\bhawezi\s+(elewa|kuelewa|fanya|kufanya)\b.{0,30}\b(biashara|business|kazi|elimu|masomo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Wasichana wa Nairobi / wanawake + akili ni zero / wembamba tu / wajinga
        (r'\b(wasichana|wanawake)\b.{0,40}\b(akili\s+ni\s+zero|wembamba\s+tu|ni\s+wajinga\s+tu|wajinga\s+tu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # wanawake wajinga — explicit intellectual denigration (biblical or direct)
        (r'\bwanawake\s+wajinga\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng reproductive-pressure stereotype: madem/wanawake wanaogopa mimba
        (r'\b(madem|wanawake|wasichana)\b.{0,30}\bwanaogopa\s+mimba\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng OnlyFans stereotype: dem/manzi + only fans (implies women resort to sex work)
        (r'\b(dem|manzi|dame|msichana|wanawake)\b.{0,80}\bonly\s*fans\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng body-shaming: madem/wanawake + weight/height + struggle/hawakaa poa
        (r'\b(madem|wanawake|wasichana)\b.{0,60}\b(kg|kilo|futi|\d+\s*ft)\b.{0,60}\b(hukaa\s+poa|wakistruggle|struggle|hawakaa\s+poa)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Sheng courtship-behavior stereotype: dem + courtship + ufala/hubadilika
        (r'\b(dem|manzi|dame)\b.{0,50}\b(courtship|mahusiano)\b.{0,60}\b(ufala|tabia\s+mbaya|hubadilika|mabadiliko\s+ya\s+tabia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Success gated on appearance: msichana/mwanamke mzuri tu ana nafasi
        (r'\b(msichana|mwanamke|wasichana|wanawake)\b.{0,20}\b(mzuri|nzuri|mrembo)\b.{0,10}\btu\b.{0,40}\b(ana\s+nafasi|wanapata\s+nafasi|anapata\s+nafasi|wanafanikiwa|anafanikiwa)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Appearance-based hiring: wasichana/wanawake wanapewa kazi kwa sababu ya sura
        (r'\b(wasichana|wanawake|msichana)\b.{0,100}\bwanapewa\s+kazi\b.{0,50}\b(sura|uzuri|mwili|mwonekano)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # Purity-rejection: hawezi kumoa mwanamke aliyethubutu/kabla ya ndoa
        (r'\bhawezi\s+kumoa\b.{0,80}\b(aliyethubutu|aliyefanya|kabla\s+ya\s+ndoa|alichofanya)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # Self-doubt imposed by society: msichana/mwanamke anadhani/amefundishwa hawezi kubalika
        (r'\b(msichana|mwanamke)\b.{0,30}\bhawezi\s+(kubalika|kukubalika|kupigwa\s+kura|kukubaliana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sport/activity causes fertility loss: mwanamke akicheza/anacheza hawezi kupata mtoto
        (r'\b(mwanamke|msichana)\b.{0,60}\b(akicheza|anacheza|kucheza|mchezo|michezo|mazoezi|riadha|kandanda|volleyball|athletics)\b.{0,60}\bhawezi\s+kupata\s+mtoto\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # Implicit blame: man failed/closed because he let woman do it
        (r'\b(msee|morio|mwanaume)\b.{0,80}\b(alifunga|alishindwa|alifilisika)\b.{0,60}\b(alimwacha|akamwacha)\b.{0,40}\b(dame|manzi|mwanamke|msichana)\b.{0,30}\b(aifanye|afanye|aifanyie)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Explicit derogation: wajinga / mjinga applied to women ──────────────
        # "wanawake ni wajinga", "mwanamke/msichana mjinga", "dame/mama mjinga"
        # Guard: exclude "mjinga/wajinga" in clearly non-gendered subjects (mfumo, mpango, etc.)
        (r'\b(wanawake|wasichana)\b.{0,30}\bni\s+(wajinga|wanajinga|mjinga)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana|dame|mama)\b.{0,20}\b(ni\s+mjinga|ana\s+ujinga|ni\s+wajinga|ni\s+mwenda\s+wazimu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana|dame|mama|manzi)\b.{0,50}\b(mjinga|wajinga|ujinga\s+wake|ujinga\s+wao)\b.{0,40}\b(kuongoza|kufanya\s+kazi|kusimamia|biashara|kura|siasa)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng: "hawa wajinga wa wanawake", "hizi dame ni wajinga"
        (r'\b(hawa|hizi|hao)\b.{0,10}\b(wajinga|wanajinga)\b.{0,20}\b(wa\s+wanawake|wa\s+wasichana|dame|manzi|madem)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Implicit domestic prescription (no anapaswa/lazima required) ────────
        # "kazi ya mwanamke halisi ni jikoni", "kazi ya nyumba ni ya wanawake tu"
        (r'\b(kazi\s+ya|sehemu\s+ya|mahali\s+pa)\b.{0,20}\b(mwanamke|wanawake|wasichana)\b.{0,20}\b(halisi|kweli|asili)\b.{0,30}\b(jikoni|nyumba|watoto|familia)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\b(kazi\s+za\s+nyumba|kupika|kusafisha|kulea\s+watoto)\b.{0,30}\b(ni\s+ya|ni\s+kwa|ni\s+kawaida\s+ya)\b.{0,20}\b(wanawake|mwanamke|wasichana)\b.{0,10}\b(tu|peke\s+yao|peke\s+yake)?\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "nyumba safi na chakula ndiyo sehemu ya mwanamke", "jikoni ni harusi ya mwanamke"
        (r'\b(nyumba\s+safi|chakula\s+kizuri|jikoni)\b.{0,30}\b(ndiyo|ni)\b.{0,20}\b(sehemu|harusi|pahali|nafasi)\b.{0,20}\b(ya\s+mwanamke|ya\s+wanawake|ya\s+msichana)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mwanamke asiyejua kupika/kusafisha hana thamani"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(asiyejua|asiyeweza|asiyepika|asiyesafisha)\b.{0,30}\b(hana\s+thamani|si\s+mzuri|hatastahili|hafai)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mama aliyeacha watoto kazini / aliyeenda kazini si mama mzuri"
        (r'\b(mama|mwanamke|mke)\b.{0,30}\b(aliyeenda\s+kazini|aliyeacha\s+watoto|anayefanya\s+kazi)\b.{0,40}\b(si\s+mama\s+mzuri|hana\s+wakati|si\s+mzazi\s+mzuri|watoto\s+wake\s+wanateseka)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Male stereotype patterns ─────────────────────────────────────────────
        # Emotional suppression: men must not cry/show feelings
        # "wanaume hawalia/halii machozi", "kulia ni udhaifu kwa wanaume"
        (r'\b(wanaume|mwanaume|msee|morio)\b.{0,30}\b(hawalii|hawalia|halii|hawaonek|haonek)\b.{0,30}\b(machozi|huzuni|udhaifu|hisia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\b(wanaume|mwanaume)\b.{0,20}\b(halii|hawalia|hawalii)\b.{0,20}\bmachozi\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\b(mwanaume\s+wa\s+kweli|msee\s+wa\s+kweli|morio\s+wa\s+kweli)\b.{0,40}\b(halii|halia|haombolezi|haonyeshi\s+hisia|haonyeshi\s+udhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\b(kulia|kuomboleza|kuonyesha\s+hisia)\b.{0,30}\b(ni\s+kwa\s+wanawake|si\s+kwa\s+wanaume|udhaifu\s+wa\s+mwanaume|aibu\s+kwa\s+mwanaume)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # Breadwinner pressure: man must provide financially, no exceptions
        (r'\b(mwanaume|msee|morio|baba)\b.{0,30}\b(lazima|anapaswa|inabidi|sharti)\b.{0,40}\b(kulipa\s+bili|kuleta\s+pesa|kusponsor|kutunza|kuhudumia)\b.{0,30}\b(familia|nyumba|mke|dame|manzi)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        (r'\b(mwanaume\s+asiye|msee\s+asiye|morio\s+asiye|mume\s+asiye|baba\s+asiye)\b.{0,20}\b(na\s+pesa|tajiri|kulipa|kutunza|kuleta)\b.{0,30}\b(si\s+mwanaume|si\s+msee|hana\s+heshima|hafai|mwanaume\s+wa\s+kuomba|aibu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # Male dominance prescription: man must be in charge
        (r'\b(mwanaume|baba|mume)\b.{0,30}\b(ndiye\s+mkuu|ndiye\s+kiongozi|lazima\s+aongoz|lazima\s+asimamie|lazima\s+aamue)\b.{0,30}\b(nyumba|familia|mke|watoto)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # Violence normalization: men must be tough/violent to prove manhood
        (r'\b(mwanaume\s+wa\s+kweli|msee\s+wa\s+kweli)\b.{0,50}\b(anapiga|hupiga|anadhibiti|hutumia\s+nguvu|anatumia\s+nguvu)\b.{0,40}\b(mke|dame|manzi|familia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\b(kupiga\s+mke|kumpiga\s+mke|kumheshimu\s+kwa\s+nguvu)\b.{0,40}\b(ni\s+kawaida|ni\s+haki\s+ya|ndiyo\s+mamlaka|inastahili)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanaume wa kweli lazima adhibiti mke wake kwa nguvu"
        (r'\b(mwanaume\s+wa\s+kweli|lazima\s+adhibiti)\b.{0,40}\b(mke\s+wake|dame\s+yake|manzi\s+wake)\b.{0,20}\bkwa\s+nguvu\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "morio husikitisha dame yake ili ijue ni nani bosi" / "adhibu mke wako"
        (r'\b(adhibu|kumadhibu)\b.{0,20}\b(mke\s+wako|dame\s+yako|manzi\s+wako)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\b(mke\s+anahitaji|dame\s+anahitaji)\b.{0,30}\b(mkono\s+mgumu|nguvu\s+za\s+mwanaume|nidhamu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),

        # ── Male emotion suppression — extended vocabulary ───────────────────────
        # "kulia ni dalili ya udhaifu kwa wanaume"
        (r'\b(kulia|machozi|huzuni|kuomboleza)\b.{0,20}\b(ni\s+dalili\s+ya\s+udhaifu|ni\s+udhaifu|ni\s+aibu).{0,30}\b(wanaume|mwanaume|msee|morio)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "msee anayelia ana tabia ya mwanamke"
        (r'\b(msee|mwanaume|morio)\b.{0,20}\b(anayelia|aliyelia|analia)\b.{0,30}\b(ana\s+tabia\s+ya\s+mwanamke|ni\s+kama\s+mwanamke|ni\s+mwanamke|ni\s+dhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "huwezi kuwa mwanaume ukionyesha kuchoka kwa moyo"
        (r'\bhuwezi\s+kuwa\s+mwanaume\b.{0,50}\b(ukionyesha|ukilia|ukiomboleza|ukihisi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanaume mzuri haikulii / hakulii hata ana matatizo"
        (r'\b(mwanaume\s+mzuri|msee\s+wa\s+kweli|morio\s+wa\s+kweli)\b.{0,20}\b(haikulii|hakulii|halii|hawalia)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),

        # ── Male breadwinner — extended vocabulary ────────────────────────────────
        # "mwanaume lazima alipe bili zote za nyumba"
        (r'\b(mwanaume|msee|mume|baba)\b.{0,20}\b(lazima|anapaswa|inabidi)\b.{0,30}\b(alipe\s+bili|alipe\s+kodi|ajenga\s+nyumba|asponsor|alishughulishe\s+familia)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "msee wa flow ndio anayestahili kuvuta msichana/dame"
        (r'\b(msee|morio|mwanaume)\b.{0,20}\b(wa\s+flow|wa\s+pesa|wa\s+mali)\b.{0,30}\b(ndio\s+anayestahili|ndiye\s+anayefaa|peke\s+yake\s+anastahili)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mwanaume asiyeweza kujenga nyumba hana sifa"
        (r'\b(mwanaume|msee|mume)\b.{0,20}\b(asiyeweza|asiyejenga|asiyetunza|asiyelipia)\b.{0,30}\b(hana\s+sifa|hana\s+hadhi|si\s+mwanaume|hafai|hana\s+thamani)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "thamani ya mwanaume inapimwa kwa mfuko/mali" — worth measured by wealth
        (r'\b(thamani|heshima|hadhi)\b.{0,20}\b(ya\s+mwanaume|ya\s+mume|ya\s+baba)\b.{0,20}\b(inapimwa|inategemea|inakadiriwa)\b.{0,30}\b(mfuko|mali|pesa|fedha|akaunti|biashara)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mwanaume asiye na uwezo wa kulipa kodi hana haki ya kuitwa kichwa cha familia"
        (r'\b(mwanaume|mume)\b.{0,30}\b(asiye\s+na\s+uwezo|asiyeweza|asiyetosha)\b.{0,30}\b(kulipa\s+kodi|kulipa\s+bili|kutoa\s+mahitaji|kununua|kutunza)\b.{0,50}\b(hana\s+haki\s+ya|hana\s+sifa\s+ya|hapaswi\s+kuitwa|hawezi\s+kuitwa)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mume anayemtegemea mke kwa chakula ni kama mtoto"
        (r'\b(mume|mwanaume)\b.{0,20}\b(anayemtegemea|anayetegemea)\b.{0,20}\b(mke\s+wake|bibi\s+yake)\b.{0,30}\b(kwa\s+chakula|kwa\s+pesa|kwa\s+mahitaji|kwa\s+kodi)\b.{0,30}\b(ni\s+kama\s+mtoto|si\s+mwanaume|ni\s+mzigo|ni\s+aibu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mwanaume bila akaunti ya benki iliyonona ni kichekesho"
        (r'\b(mwanaume|mume|msee)\b.{0,20}\b(bila\s+akaunti|bila\s+pesa|asiye\s+na\s+akaunti|asiye\s+na\s+mali)\b.{0,40}\b(ni\s+kichekesho|ni\s+aibu|ni\s+dharau|hana\s+thamani|hafahamiwi)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "kazi ya mwanaume ni kuleta hela, mwanamke akichangia ni ziada"
        (r'\b(kazi\s+ya|jukumu\s+la)\b.{0,10}\b(mwanaume|mume|baba)\b.{0,20}\bni\b.{0,20}\b(kuleta\s+hela|kuleta\s+pesa|kutoa\s+pesa|kuhudumia\s+familia)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "wanaume wasio na kazi wanapaswa kukaa kimya"
        (r'\b(wanaume|wanawaume)\b.{0,20}\b(wasio\s+na\s+kazi|wasio\s+na\s+pesa|wanaoishi\s+kwa\s+mke)\b.{0,30}\b(wanapaswa\s+kukaa\s+kimya|hawana\s+haki\s+ya\s+kuzungumza|hawaheshimiwi|wanachekwa)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "utaolewaje na mwanaume ambaye hana hata baiskeli"
        (r'\b(utaolewaje|unawezaje\s+kuoa|unawezaje\s+kupenda)\b.{0,30}\b(mwanaume|msee|mume)\b.{0,30}\b(ambaye\s+hana|asiye\s+na|bila)\b.{0,30}\b(baiskeli|gari|nyumba|pesa|kazi|mali)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "heshima ya baba inatokana na jinsi anavyohudumia familia kifedha"
        (r'\b(heshima|thamani|hadhi)\b.{0,20}\b(ya\s+baba|ya\s+mwanaume|ya\s+mume)\b.{0,20}\b(inatokana\s+na|inategemea|inakuja\s+kwa)\b.{0,30}\b(jinsi\s+anavyohudumia|fedha|kutoa\s+mahitaji|kifedha)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),

        # ── Male Sheng stereotypes ────────────────────────────────────────────────
        # "msee bila gari si chochote katika mitaa"
        (r'\b(msee|morio)\b.{0,20}\b(bila\s+gari|bila\s+pesa|bila\s+nyumba|bila\s+flow)\b.{0,30}\b(si\s+chochote|si\s+mtu|hana\s+thamani|hana\s+hadhi|hana\s+nguvu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "morio hajua ku-handle pressure, anataka kusoma feelings"
        (r'\b(morio|msee)\b.{0,30}\b(hajua\s+ku.handle|hawezi\s+ku.handle|hajua\s+kudeal)\b.{0,40}\b(pressure|feelings|hisia|matatizo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "wewe si msee wa kweli kama hukunywa / hupigi"
        (r'\bsi\s+(msee|mwanaume|morio)\s+wa\s+kweli\b.{0,50}(kama\s+hukun|kama\s+hupig|kama\s+hufanyi|ukikataa)',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),

        # ── Female purity / marriage — extended vocabulary ────────────────────────
        # "msichana mzuri lakini ana tarikhi mbaya, hata ndoa itakuwa kuzuia"
        (r'\b(msichana|mwanamke|dame)\b.{0,40}\b(ana\s+tarikhi\s+mbaya|historia\s+mbaya|amepita\s+mengi)\b.{0,50}\b(ndoa|kuoana|kumoa|kukubalika)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "tafuta mwanamke ambaye hajapoteza utu wake kabla ya ndoa"
        (r'\b(hajapoteza\s+utu|hajabeba\s+aibu|bado\s+safi|bikira\s+tu)\b.{0,40}\b(kabla\s+ya\s+ndoa|ndoa\s+nzuri|mke\s+mzuri)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "hakuna mwanaume atakayemkubal msichana aliyekuwa na rafiki wengi"
        (r'\b(hakuna\s+mwanaume|hakuna\s+msee|hakuna\s+morio)\b.{0,30}\b(atakayemkubali|atakayemoa|atakayemchagua)\b.{0,40}\b(aliyekuwa\s+na\s+rafiki\s+wengi|alichofanya|aliyepita)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "si msichana wa kupenda — ameonyeshwa mara nyingi kwenye Instagram"
        (r'\bsi\s+(msichana|mwanamke|dame)\s+wa\s+(kupenda|kuoa|kuheshimu)\b.{0,60}\b(Instagram|OnlyFans|social\s+media|picha\s+mtandaoni|picha\s+ovyo)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Female capability — vocabulary variants from adversarial FNs ──────────
        # "wanawake hawezi kuendeshea biashara kubwa kama wanaume"
        (r'\b(wanawake|wasichana)\b.{0,20}\b(hawezi|hawawezi|hawana\s+uwezo)\b.{0,40}\b(kuendeshea|kusimamia|kuongoza|kufanya)\b.{0,30}\b(biashara|kazi|kampuni|shirika)\b.{0,30}\b(kama\s+wanaume|sawasawa\s+na\s+wanaume)?\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "manzi/dame hawana akili ya kufahamu hesabu na fedha"
        (r'\b(manzi|dame|madem|wasichana|wanawake)\b.{0,20}\b(hawana\s+akili\s+ya|hawana\s+uwezo\s+wa|hawaelewi)\b.{0,40}\b(hesabu|fedha|biashara|teknolojia|sayansi|uhandisi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanawake wanahitaji kumwambia mume wao kila kitu kabla ya kufanya hatua"
        (r'\b(wanawake|mwanamke|wasichana)\b.{0,30}\b(wanahitaji|anahitaji)\b.{0,40}\b(kumwambia|ruhusa\s+ya|idhini\s+ya)\b.{0,30}\b(mume|mwanaume|baba|kaka)\b.{0,30}\b(kabla\s+ya|ili|kufanya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Domestic role — adversarial FN coverage ──────────────────────────────
        # "mwanamke asiyejua kupika hafai kuitwa mke"
        (r'\b(mwanamke|msichana|mke)\b.{0,30}\b(asiyejua|asiyeweza)\b.{0,30}\b(kupika|kupigapasi|kusafisha|kuosha)\b.{0,50}\b(hafai|hana\s+haki|hatakuwa|hatastahili)\b.{0,30}\b(mke|bibi|mtu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "msichana anapaswa kufunzwa kazi za jikoni tangu akiwa mdogo"
        (r'\b(msichana|mtoto\s+wa\s+kike|binti)\b.{0,20}\b(anapaswa|lazima|inabidi|afunzwe)\b.{0,30}\b(kufunzwa\s+kazi\s+za\s+jikoni|kujifunza\s+kupika|kujifunza\s+kusafisha)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mwanamke anayetafuta kazi ya ofisini na kuacha nyumba chafu ni mvivu"
        (r'\b(mwanamke|mke|mama)\b.{0,20}\b(anayetafuta|anayefanya)\b.{0,20}\b(kazi\s+ya\s+ofisi|kazi\s+nje|kazi\s+mjini)\b.{0,40}\b(na\s+kuacha\s+nyumba|na\s+kutunza\s+watoto\s+vibaya)\b.{0,40}\b(ni\s+mvivu|ni\s+mbaya|ameshindwa|hafai)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "chakula cha mkono wa mke ndicho kinachomfanya mume asitamani kula nje"
        (r'\b(chakula\s+cha\s+mkono\s+wa\s+mke|chakula\s+cha\s+mke)\b.{0,30}\b(ndicho\s+kinachomfanya|ndio\s+kinachofanya|ndiyo\s+kinachomfanya)\b.{0,30}\b(mume|mumewe)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mke anayelalamika kuhusu usafi anatafuta sababu za kuvunja ndoa"
        (r'\b(mke|mwanamke)\b.{0,20}\b(anayelalamika|anayelalamika|anayekataa)\b.{0,30}\b(kufanya\s+usafi|kupika|kufua|kutunza\s+watoto)\b.{0,40}\b(anatafuta\s+sababu|ana\s+tatizo|anafika\s+mbali|anataka\s+talaka)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "usimwamini mke anayependa chakula cha tayari badala ya kupika"
        (r'\b(usimwamini|usimpe|usioe)\b.{0,15}\b(mke|mwanamke|msichana)\b.{0,20}\b(anayependa\s+chakula\s+cha\s+tayari|asiyependa\s+kupika|asiyeweza\s+kupika)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "kazi ya mwanamke ni kuhakikisha nyumba safi / watoto wameoga"
        (r'\b(kazi\s+ya|jukumu\s+la)\b.{0,15}\b(mwanamke|mke|mama)\b.{0,20}\bni\b.{0,30}\b(kuhakikisha|kuhudumia|kutunza|kulea)\b.{0,40}\b(nyumba|watoto|mume|familia)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mume akifua mwenyewe / mke amefeli majukumu yake"
        (r'\b(mume|mwanaume|baba)\b.{0,20}\b(akianza|anapofua|akifua|akipika|akisafisha)\b.{0,30}\b(mwenyewe|yeye\s+mwenyewe)\b.{0,60}\b(mke\s+amefeli|mke\s+ameshindwa|mke\s+ni\s+mvivu|mke\s+hana\s+budi)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "majukumu ya nyumba ni asili ya mwanamke"
        (r'\b(majukumu|kazi)\b.{0,20}\b(ya\s+nyumbani|za\s+nyumbani|za\s+jikoni)\b.{0,30}\bni\b.{0,20}\b(asili\s+ya|ya|kwa)\b.{0,15}\b(mwanamke|wanawake|msichana)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mwanamke ni mapambo ya nyumba"
        (r'\b(mwanamke|msichana|mke)\b.{0,20}\bni\b.{0,20}\bmapambo\b.{0,30}\b(ya\s+nyumba|ya\s+familia|wa\s+nyumba)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Male dominance — adversarial FN coverage ─────────────────────────────
        # "maamuzi yote lazima yatoke kwa baba / mke ni wa kusikiliza tu"
        (r'\b(maamuzi\s+yote|maamuzi\s+makubwa)\b.{0,30}\b(lazima|sharti|inapaswa)\b.{0,30}\b(yatoke\s+kwa|kutoka\s+kwa)\b.{0,20}\b(baba|mume|mwanaume)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # "mwanaume ndiye nahodha / mwanamke wa kufuata maelekezo"
        (r'\b(mwanaume|mume|baba)\b.{0,20}\bndiye\s+(nahodha|mkuu|kiongozi|mwenye\s+kauli)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # "hata kama mke ana elimu, lazima anyenyekee chini ya amri ya mume"
        (r'\b(mke|mwanamke)\b.{0,50}\b(lazima|inabidi|sharti)\b.{0,20}\b(anyenyekee|atii|akubali|afuate)\b.{0,30}\b(amri|maagizo|maamuzi)\b.{0,20}\b(ya\s+mume|ya\s+mumewe|ya\s+mwanaume)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        # "mwanamke akianza kuongoza nyumba imelaaniwa"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(akianza\s+kuongoza|anapokuwa\s+kiongozi|akiongoza)\b.{0,50}\b(nyumba\s+imelaaniwa|haina\s+mwelekeo|itaanguka|itaharibika)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "mwanamke anayetafuta uongozi anavunja sheria za asili"
        (r'\b(mwanamke|msichana|wanawake)\b.{0,30}\b(anayetafuta\s+uongozi|anapotafuta\s+uongozi|wanaotafuta\s+uongozi)\b.{0,40}\b(anavunja|wanakiuka|wanakosea)\b.{0,20}\b(sheria|kanuni|asili|utamaduni)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "nyumba yenye vichwa viwili haiwezi kusimama"
        (r'\bnyumba\b.{0,20}\b(yenye\s+vichwa\s+viwili|vyenye\s+vichwa\s+viwili)\b.{0,40}\b(haiwezi\s+kusimama|haisimami|itaanguka|haina\s+mwelekeo)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),

        # ── Male violence normalization — adversarial FN coverage ─────────────────
        # "mke mkaidi anahitaji kupigwa" / "kibao kimoja si ukatili"
        (r'\b(mke|mwanamke)\b.{0,20}\b(mkaidi|msumbufu|asiyetii|mgumu)\b.{0,30}\b(anahitaji|inahitajika|anapaswa)\b.{0,20}\b(kupigwa|kuchapwa|kuadhibiwa)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanamke akizidi mdomo, dawa yake ni kumpunja kidogo"
        (r'\b(mwanamke|mke)\b.{0,20}\b(akizidi\s+mdomo|anapozidi\s+mdomo|anapopinga|akijaribu\s+kupinga)\b.{0,30}\b(dawa\s+yake|suluhisho\s+lake|jibu\s+lake)\b.{0,20}\b(ni\s+kumpunja|ni\s+kumpiga|ni\s+kumadhibu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "kama angekuwa mke mwema na mtiifu, mume asingelazimika kutumia nguvu"
        (r'\b(kama\s+angekuwa|kama\s+alikuwa)\b.{0,20}\b(mke\s+mwema|mke\s+mtiifu|mwanamke\s+mzuri)\b.{0,40}\b(mume\s+asingelazimika|hangelazimika|asingehitaji)\b.{0,20}\b(kutumia\s+nguvu|kumpiga|kumhantua|kumzuia\s+kwa\s+nguvu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mapenzi ni kikohozi, huambatana na makofi ya kurekebisha"
        (r'\b(mapenzi|ndoa|upendo)\b.{0,20}\bni\s+kikohozi\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanaume lazima aonyeshe nguvu zake ili heshima iwepo ndani ya kuta nne"
        (r'\b(mwanaume|mume)\b.{0,20}\b(lazima|anapaswa)\b.{0,20}\b(aonyeshe\s+nguvu|atumie\s+nguvu|adhibitishe\s+nguvu)\b.{0,30}\b(ili\s+heshima|ili\s+atambuliwe|ili\s+ajulikane)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        (r'\b(kibao|kofi|pigo|makofi)\b.{0,20}\b(kimoja|moja|kidogo)\b.{0,40}\b(siyo\s+ukatili|si\s+ukatili|ni\s+kawaida|ni\s+sawa|ni\s+adabu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanamke akimchokoza mwanaume asilalamike"
        (r'\b(mwanamke|mke)\b.{0,20}\b(akimchokoza|akimkasirisha|akimchukiza)\b.{0,40}\b(asilalamike|asimlaumu|ni\s+makosa\s+yake)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "fimbo kurekebisha wake / ndoa zilidumu" — historical violence normalization
        (r'\b(fimbo|mkuki|adhabu\s+ya\s+mwili)\b.{0,30}\b(kurekebisha|kudhibiti|kufundisha)\b.{0,30}\b(wake|mke|mwanamke)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mume kumshika mke shati si jambo la polisi"
        (r'\b(mume|mwanaume)\b.{0,20}\b(kumshika|kumpiga|kumhantua|kumfunga)\b.{0,20}\b(mke\s+wake|mkewe|bibi\s+yake)\b.{0,40}\b(si\s+jambo\s+la\s+polisi|si\s+uhalifu|ni\s+haki\s+yake|ni\s+mambo\s+ya\s+ndani)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "usipomwadhibu mke wako, jamii itakuona mwanaume goigoi"
        (r'\b(usipomwadhibu|usipomzuia|usipomfundisha)\b.{0,20}\b(mke\s+wako|bibi\s+yako)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mapenzi ni kikohozi, huambatana na makofi ya kurekebisha"
        (r'\b(mapenzi|upendo|ndoa)\b.{0,40}\b(makofi|kupigwa|nguvu|kibao)\b.{0,30}\b(kurekebisha|kufundisha|ya\s+kawaida|sehemu\s+ya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),

        # ── Male emotional suppression — adversarial FN extensions ───────────────
        # "mwanaume hapaswi kuonyesha udhaifu" / "kulia ni kazi ya wanawake"
        (r'\b(mwanaume|wanaume)\b.{0,20}\b(hapaswi|hapasiwi|hana\s+budi|lazima\s+asijaribu)\b.{0,30}\b(kuonyesha|kudhihirisha)\b.{0,30}\b(udhaifu|hisia|machozi|huzuni|hofu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mvulana akishindwa kuvumilia maumivu bila machozi, huyo si rijali"
        (r'\b(mvulana|mwanaume|msee)\b.{0,30}\b(akishindwa|asiyeweza)\b.{0,30}\b(kuvumilia|kustahimili)\b.{0,30}\b(maumivu|msongo|hali\s+ngumu)\b.{0,30}\b(bila\s+kutoa\s+machozi|bila\s+kulia)\b.{0,40}\b(si\s+rijali|si\s+mwanaume|si\s+msee)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "ukionyesha hisia zako kama msichana mdogo" — equating emotions with femininity
        (r'\b(ukionyesha|kuonyesha)\b.{0,20}\b(hisia|udhaifu|machozi|huzuni)\b.{0,30}\b(kama\s+msichana|kama\s+mwanamke|kama\s+mtoto\s+mdogo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "wanaume wanapofanya vikao vya kutoa siri wanapoteza hadhi"
        (r'\b(wanaume)\b.{0,20}\b(wanapofanya|wakifanya|wanaposema)\b.{0,30}\b(vikao\s+vya\s+kutoa\s+siri|siri\s+za\s+moyoni|feelings\s+zao|hisia\s+zao)\b.{0,40}\b(wanapoteza\s+hadhi|wanapoteza\s+heshima|ni\s+aibu|wanashuka)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "badala ya kusononeka nenda kafanye kazi maana mwanaume hashindwi"
        (r'\b(badala\s+ya\s+kusononeka|badala\s+ya\s+kulalamika|badala\s+ya\s+kulia)\b.{0,30}\b(nenda\s+kafanye|nenda\s+kufanya|nenda\s+pambana)\b.{0,40}\b(mwanaume\s+hashindwi|wanaume\s+hawalegei|wanaume\s+hawashindwi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "ukionyesha hofu watajua wewe si mwanaume kamili"
        (r'\b(ukionyesha\s+hofu|ukionyesha\s+woga|ukionyesha\s+udhaifu)\b.{0,40}\b(watajua|itajulikana|itaonekana)\b.{0,30}\b(si\s+mwanaume\s+kamili|si\s+mwanaume\s+wa\s+kweli|si\s+msee)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "kulia ni kazi ya wanawake na watoto"
        (r'\b(kulia|machozi|kuomboleza)\b.{0,20}\bni\b.{0,20}\b(kazi\s+ya|ya\s+asili\s+ya|tu\s+ya)\b.{0,15}\b(wanawake|wasichana|watoto)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanaume wa shoka huumeza uchungu wake"
        (r'\b(mwanaume\s+wa\s+shoka|mwanaume\s+wa\s+kweli|msee\s+wa\s+ukweli)\b.{0,40}\b(huumeza|hukaa\s+kimya|husimama\s+imara|hana\s+machozi|havumili)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "machozi ya mwanaume ni aibu kwa ukoo"
        (r'\b(machozi|kilio|kulia)\b.{0,20}\b(ya|ya\s+hii)\b.{0,10}\b(mwanaume|mwanaumwe)\b.{0,20}\bni\b.{0,20}\b(aibu|udhalilishaji|unyonge|udhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "mwanaume hafai kulegalega mbele ya matatizo"
        (r'\b(mwanaume|wanaume)\b.{0,20}\b(hafai|hapaswi|hana\s+haki)\b.{0,30}\b(kulegalega|kudanganyika|kutoweza|kuomba\s+msaada|kuomboleza)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),

        # ── Male Sheng — adversarial FN extensions ────────────────────────────────
        # "msee hana mulla hawezi kudeal na madame"
        (r'\b(msee|morio)\b.{0,20}\bhana\s+(mulla|pesa|gari|flow|hustle)\b.{0,50}\b(hawezi\s+kudeal|hatadeal|hana\s+nguvu|utadharauliwa|atadharauliwa|hawezi\s+kudate)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mandem wanatakiwa kuwa wagumu, si kupiga story za feelings"
        (r'\b(mandem|masee|wanaume)\b.{0,20}\b(wanatakiwa|wanafaa)\b.{0,20}\b(kuwa\s+wagumu|kuwa\s+strong|kuwa\s+imara)\b.{0,40}\b(si\s+kupiga\s+story|si\s+kulia|si\s+kuomba\s+msaada)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "msee wa mtaani lazima ajue kupigana ndio aheshimiwe"
        (r'\b(msee|morio)\b.{0,20}\b(wa\s+mtaani|wa\s+base|wa\s+hood)\b.{0,30}\b(lazima|anapaswa|inabidi)\b.{0,30}\b(ajue\s+kupigana|awe\s+mgumu|awe\s+strong|awe\s+na\s+misuli)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "real msee hakuombagi msaada"
        (r'\b(real\s+msee|msee\s+wa\s+ukweli|morio\s+wa\s+ukweli)\b.{0,30}\b(hakuombagi|haombi|hakuombi|hapigi\s+story\s+za\s+feelings)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "msee lazima akuwe dominant kwa relationship"
        (r'\b(msee|morio|mwanaume)\b.{0,20}\b(lazima|anapaswa)\b.{0,20}\b(akuwe\s+dominant|kuwa\s+dominant|kuwa\s+mkali)\b.{0,20}\b(kwa\s+relationship|kwa\s+dame|kwa\s+manzi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "morio akianza kulia juu ya story za mapenzi, huyo si mandem wa ukweli"
        (r'\b(morio|msee)\b.{0,20}\b(akianza\s+kulia|akilia|analia)\b.{0,30}\b(juu\s+ya\s+story|story\s+za\s+mapenzi|mambo\s+ya\s+mapenzi|juu\s+ya\s+dame)\b.{0,40}\b(si\s+mandem|si\s+msee|si\s+mwanaume)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "huwezi kuwa msee kamili kama unategemea sister yako"
        (r'\bhuwezi\s+kuwa\s+(msee|mwanaume|morio)\s+(kamili|wa\s+kweli|tosha)\b.{0,50}\b(unategemea|ukitegemea|ukiomba\s+msaada|sister\s+yako|mama\s+yako)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "morio hawezi kucalculate ganji / ni weak"
        (r'\b(morio|msee)\b.{0,20}\b(ambaye\s+hawezi|asiyeweza|hajui)\b.{0,20}\b(kucalculate|kudeal|ku.handle|ku.manage)\b.{0,30}\b(ni\s+weak|ni\s+dhaifu|si\s+msee|hafai)\b',
         StereotypeCategory.CAPABILITY, TargetGender.MALE),
        # "kama huna hustle hufai hata kupewa mic"
        (r'\b(kama\s+huna\s+hustle|kama\s+huna\s+pesa|kama\s+huna\s+gari)\b.{0,50}\b(hufai|hutastahili|huna\s+nafasi|wewe\s+ni\s+fala)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),

        # ── Sheng mixed — adversarial FN extensions ───────────────────────────────
        # "hizi madame ni mafala tu kwa ground" / "dame akishapata kacheo anajidai"
        (r'\b(hizi\s+madame|hawa\s+madame|hizi\s+dame|hawa\s+dame)\b.{0,50}\b(ni\s+mafala|ni\s+wajinga|wanajidai|hawajui|hawana\s+akili|ni\s+drama)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "kudeal na msichana mwenye opinion mob ni stress, heri utafute ananyamaza"
        (r'\b(kudeal\s+na|kushughulika\s+na|ku.deal\s+na)\b.{0,15}\b(msichana|dame|manzi)\b.{0,20}\b(mwenye\s+opinion|mwenye\s+mawazo|mwenye\s+mdomo)\b.{0,20}\b(mob|mingi|sana)\b.{0,30}\b(ni\s+stress|ni\s+shida|heri|bora)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "usiwahi pea dame siri yako, wasichana ni mdomo mob watachoma picha"
        (r'\b(usiwahi\s+pea|usimwambie|usimwambia)\b.{0,15}\b(dame|manzi|msichana)\b.{0,20}\b(siri\s+yako|mambo\s+yako|matatizo\s+yako)\b.{0,40}\b(mdomo\s+mob|watachoma\s+picha|ni\s+wachomaji|hawadanganywi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "huyu dame anajifanya mwerevu lakini hajui kitu, ni mrembo tu"
        (r'\b(huyu\s+dame|huyu\s+manzi|huyu\s+msichana)\b.{0,20}\b(anajifanya\s+mwerevu|anajifanya\s+smart|anajifanya\s+anajua)\b.{0,30}\b(lakini\s+hajui|lakini\s+ni\s+mrembo\s+tu|ni\s+zero\s+kwa\s+elimu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "dame akileta ujinga kwa hosi, mtoe mbio"
        (r'\b(dame|manzi|msichana)\b.{0,20}\b(akileta\s+ujinga|akisema\s+upuuzi|akileta\s+drama)\b.{0,20}\b(kwa\s+hosi|kazini|ofisini)\b.{0,30}\b(mtoe\s+mbio|mfukuze|muonyeshe\s+mlango)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wasichana wanadhani kuongoza ni rahisi kama kupaka make-up"
        (r'\b(wasichana|madem|dame)\b.{0,20}\b(wanadhani|wanafikiri)\b.{0,20}\b(kuongoza|uongozi|kusimamia)\b.{0,20}\bni\s+rahisi\b.{0,30}\b(kama\s+kupaka\s+make.up|kama\s+kujiremba|kama\s+ku.chill)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(dame|manzi|msichana)\b.{0,20}\b(akishapata|anapopata)\b.{0,20}\b(kacheo|promotion|pesa|degree)\b.{0,30}\b(anaanza\s+kujidai|anajidai|anabeba\s+kiburi|ameanza\s+kujifanya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "madame hawawezi kumanage biz bila msee"
        (r'\b(madame|madem|wanawake)\b.{0,20}\b(hawawezi|hawezi)\b.{0,20}\b(kumanage|kusimamia|kuongoza|ku.run)\b.{0,20}\b(biz|biashara|kazi|ofisi|kampuni)\b.{0,30}\b(bila\s+msee|bila\s+mwanaume|peke\s+yao)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "msichana wa Nairobi ni drama queen, hawawezi kuhandle pressure"
        (r'\b(msichana|dame|manzi)\b.{0,30}\bni\b.{0,20}\b(drama\s+queen|drama\s+tu|mchezo\s+tu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mandem ndio wenye akili, madame kazi yao ni kutumia tu"
        (r'\b(mandem|masee|wanaume)\b.{0,20}\b(ndio\s+wenye\s+akili|ndio\s+wenye\s+nguvu|ndio\s+wanaofikiria)\b.{0,30}\b(madame|madem|wanawake)\b.{0,20}\b(kazi\s+yao\s+ni\s+kutumia|wana\s+kula\s+tu|ni\s+burden)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Purity/marriage — adversarial FN extensions ───────────────────────────
        # "msichana ameshapitia mikono ya wanaume wengi hafai kama mke"
        (r'\b(msichana|mwanamke|dame)\b.{0,30}\b(ameshapitia\s+mikono|amepita\s+mikono|amekuwa\s+wa\s+watu\s+wengi|amepitia\s+wanaume\s+wengi)\b.{0,50}\b(hafai|hana\s+thamani|hana\s+haki|hapaswi\s+kuolewa)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwanamke akivaa nguo zinazoonyesha mwili asilalamike akikoswa heshima"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(akivaa|anapovaa|anapovaa)\b.{0,30}\b(nguo\s+zinazoonyesha|nguo\s+fupi|nguo\s+za\s+kuvutia)\b.{0,40}\b(asilalamike|asishangae|ni\s+kosa\s+lake|anastahili)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "usioe mwanamke anayependa klabu / starehe za usiku hawezi kutulia nyumbani"
        (r'\b(usioe|usimoe|usimwambie\s+ndiyo|usimwoze)\b.{0,15}\b(mwanamke|msichana)\b.{0,20}\b(anayependa\s+klabu|anayependa\s+starehe|anayetoka\s+usiku|wa\s+club)\b.{0,40}\b(hawezi\s+kutulia|hawezi\s+kuwa\s+mke|ni\s+tatizo)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "wasichana wa kisasa wamepoteza maadili kwa sababu wanataka usawa"
        (r'\b(wasichana|wanawake)\b.{0,20}\b(wa\s+kisasa|wa\s+siku\s+hizi|wa\s+leo)\b.{0,20}\b(wamepoteza\s+maadili|hawana\s+maadili|wamepotoka)\b.{0,40}\b(kwa\s+sababu\s+wanataka\s+usawa|kwa\s+usawa|feminist)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "usimwamini mwanamke mwenye marafiki wengi wa kiume, hana msimamo wa ndoa"
        (r'\b(usimwamini|usimoe|usimchague)\b.{0,15}\b(mwanamke|msichana)\b.{0,20}\b(mwenye\s+marafiki\s+wengi\s+wa\s+kiume|mwenye\s+wanaume\s+wengi|anayezungumza\s+na\s+wanaume\s+wengi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "tunda lililokwishaguswa / msichana asiye bikira hana thamani"
        (r'\b(tunda|bidhaa|kitu)\b.{0,20}\b(lililokwishaguswa|aliyeguswa|lililotumika)\b.{0,40}\b(hana\s+thamani|halifai|halina\s+bei|siyo\s+na\s+thamani)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana)\b.{0,20}\b(asiye\s+bikira|asiyekuwa\s+bikira)\b.{0,40}\b(amemvunjia|amemharibu|amefeli|ni\s+aibu|hana\s+thamani)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mavazi ya mwanamke ndiyo yanayoamua kama ni mke mzuri au mwanamke wa mtaani"
        (r'\b(mavazi|nguo|mwonekano)\b.{0,20}\b(ya\s+mwanamke|ya\s+msichana)\b.{0,20}\b(ndiyo\s+yanayoamua|yanabainisha|yanaonyesha)\b.{0,30}\b(mke\s+mzuri|mwanamke\s+wa\s+mtaani|tabia\s+yake|heshima\s+yake)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "heshima ya msichana iko kati ya miguu yake"
        (r'\bheshima\b.{0,20}\b(ya\s+msichana|ya\s+mwanamke)\b.{0,20}\b(iko\s+kati\s+ya\s+miguu|ni\s+uzazi|ni\s+bikira|ni\s+usafi\s+wa\s+mwili)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Capability — adversarial FN extensions ────────────────────────────────
        # "uhandisi / rubani / sayansi ya anga ni ya kiume pekee"
        (r'\b(uhandisi|sayansi|teknolojia|programu)\b.{0,30}\b(ni\s+kazi|ni\s+fani|ni\s+uwanja)\b.{0,30}\b(ya\s+wanaume|ya\s+kiume\s+pekee|si\s+ya\s+wasichana|wanawake\s+hawafai)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke hawezi kuwa rubani mzuri kwa sababu anaogopa hali ya hewa"
        (r'\b(mwanamke|msichana|wanawake)\b.{0,20}\b(hawezi|hawawezi)\b.{0,20}\b(kuwa\s+rubani|kuwa\s+dereva|kuwa\s+nahodha|kuwa\s+kocha|kuwa\s+fundi)\b.{0,40}\b(kwa\s+sababu|anaogopa|wanaogopa|wana\s+uoga)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "usimamizi wa ujenzi unahitaji mwanaume wa kusimamia vibarua"
        (r'\b(usimamizi\s+wa|uongozi\s+wa)\b.{0,20}\b(miradi|ujenzi|wafanyakazi|vibarua)\b.{0,20}\b(unahitaji|inahitaji|lazima\s+kuwe\s+na)\b.{0,20}\b(mwanaume|mtu\s+wa\s+kiume)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke anahitaji msaada wa mwanaume hata kwa kubadilisha balbu"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(anahitaji|inahitajika)\b.{0,20}\b(msaada\s+wa\s+mwanaume|msaada\s+wa\s+mume|msaada\s+wa\s+damu\s+ya\s+kiume)\b.{0,30}\b(hata\s+kwa|hata\s+anapofanya|hata\s+akifanya)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke akishika usukani wa basi abiria wanakuwa hatarini"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(akishika\s+usukani|anapoendesha|anapoongoza|akiongoza)\b.{0,30}\b(basi|gari\s+kubwa|ndege|meli)\b.{0,40}\b(abiria\s+wanakuwa\s+hatarini|ni\s+hatari|wanaogopa|si\s+salama)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "maamuzi ya kijeshi lazima yaaachwe kwa wanaume"
        (r'\b(maamuzi|uamuzi)\b.{0,20}\b(ya\s+kijeshi|ya\s+vita|ya\s+usalama)\b.{0,20}\b(yanapaswa|lazima|inabidi)\b.{0,30}\b(kuachwa\s+kwa\s+wanaume|kufanywa\s+na\s+wanaume|si\s+ya\s+wanawake)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wasichana wanafaa kusomea ualimu/uuguzi, siyo teknolojia"
        (r'\b(wasichana|wanawake)\b.{0,20}\b(wanafaa|wanapaswa|wanapendezwa)\b.{0,20}\b(kusomea|kufanya)\b.{0,30}\b(ualimu|uuguzi|nyumbani|kazi\s+za\s+mkono)\b.{0,30}\b(siyo|si|badala\s+ya)\b.{0,30}\b(teknolojia|uhandisi|sayansi|biashara)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "sayansi / fani ngumu ni ngumu sana kwa wasichana"
        (r'\b(sayansi|hisabati|uhandisi|dawa|fizikia|kemia)\b.{0,20}\b(ni\s+ngumu\s+sana\s+kwa|haifai\s+kwa|si\s+ya)\b.{0,15}\b(wasichana|wanawake|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Leadership — adversarial FN extensions ────────────────────────────────
        # "nchi itayumba mwanamke akichaguliwa kuwa Rais"
        (r'\b(nchi|serikali|taifa)\b.{0,20}\b(itayumba|itaanguka|itashindwa|itaenda\s+mrama)\b.{0,30}\b(mwanamke\s+akichaguliwa|mwanamke\s+anapochaguliwa|mwanamke\s+akiwa)\b.{0,20}\b(rais|waziri\s+mkuu|kiongozi)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "ikiwa mwanamke atakuwa mkuu wa idara migogoro havitaisha ofisini"
        (r'\b(ikiwa|kama|wakati)\b.{0,15}\b(mwanamke|msichana)\b.{0,20}\b(atakuwa\s+mkuu|atakuwa\s+kiongozi|ataongoza)\b.{0,20}\b(wa\s+idara|wa\s+ofisi|wa\s+taasisi)\b.{0,40}\b(migogoro|majungu|fitina|tatizo)\b.{0,20}\b(havitaisha|hayataisha|itazidi|yataendelea)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "historia inaonyesha ufalme ulioongozwa na mwanamke ulisambaratika"
        (r'\b(historia\s+inaonyesha|historia\s+inatuambia|rekodi\s+ya\s+historia)\b.{0,30}\b(ufalme|nchi|serikali)\b.{0,20}\b(ulioongozwa\s+na\s+mwanamke|iliyoongozwa\s+na\s+mwanamke)\b.{0,40}\b(ulisambaratika|ilisambaratika|uliporomoka|ulishindwa)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "mwanamke akipata madaraka makubwa, anasahau wajibu wake wa asili nyumbani"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(akipata\s+madaraka|anapopata\s+madaraka|akiwa\s+na\s+madaraka)\b.{0,20}\b(makubwa|ya\s+juu)\b.{0,40}\b(anasahau\s+wajibu|atasahau\s+majukumu|ataacha\s+familia)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "wanawake wanapaswa kuongoza vikundi vya kina mama tu"
        (r'\b(wanawake|msichana)\b.{0,20}\b(wanapaswa|wanafaa|wanaweza\s+tu)\b.{0,20}\b(kuongoza|kusimamia)\b.{0,30}\b(vikundi\s+vya\s+kina\s+mama|vikundi\s+vidogo|maombi\s+tu|chochote\s+kidogo)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "viongozi wa kike mara nyingi hufuata hisia badala ya sheria"
        (r'\b(viongozi\s+wa\s+kike|wanasiasa\s+wa\s+kike)\b.{0,30}\b(hufuata\s+hisia|wanafuata\s+hisia|wanagawanyika\s+kihisia|si\s+watulivu)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "mwanaume ana sauti ya mamlaka, mwanamke akitoa amri anapiga kelele"
        (r'\b(mwanaume|wanaume)\b.{0,20}\b(ana\s+sauti\s+ya\s+mamlaka|ana\s+nguvu\s+ya\s+amri)\b.{0,50}\b(mwanamke|wanawake)\b.{0,20}\b(akitoa\s+amri|anapotoa\s+amri)\b.{0,30}\b(anapiga\s+kelele|anaonekana\s+dhaifu|hana\s+nguvu)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "mwanamke kiongozi ni tishio kwa jamii / utamaduni"
        (r'\b(mwanamke|wanawake)\b.{0,10}\b(kiongozi|viongozi)\b.{0,20}\bni\b.{0,20}\b(tishio|hatari|tatizo|kikwazo)\b.{0,30}\b(jamii|utamaduni|mfumo|amani)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),

        # ── Sport/fertility — adversarial FN extensions ───────────────────────────
        # "mwanamke anayecheza mpira wa kikapu atapata matatizo ya uzazi"
        (r'\b(mwanamke|msichana)\b.{0,30}\b(anayecheza|anayefanya|anapocheza|anapofanya)\b.{0,30}\b(mpira|ndondi|riadha|mazoezi|gym|athletics|volleyball|basketball)\b.{0,40}\b(atapata\s+matatizo\s+ya\s+uzazi|itaathiri\s+uzazi|atakuwa\s+tasa|hawezi\s+kuzaa)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwanamke mwanariadha ana mwili mgumu kama mwanaume, siyo ishara ya afya ya kike"
        (r'\b(mwanamke\s+mwanariadha|mwanariadha\s+wa\s+kike|msichana\s+mwanariadha)\b.{0,30}\b(ana\s+mwili\s+mgumu|ana\s+misuli|ana\s+nguvu)\b.{0,30}\b(kama\s+mwanaume|sawa\s+na\s+mwanaume)\b.{0,40}\b(siyo\s+ishara|si\s+ishara|si\s+vizuri|si\s+afya)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "kupiga gym kila siku kunafanya tumbo la mwanamke kuwa gumu / kuzuia mimba"
        (r'\b(kupiga\s+gym|kufanya\s+mazoezi\s+ya\s+gym|kufanya\s+mazoezi\s+kila\s+siku)\b.{0,40}\b(kunafanya\s+tumbo|kunafanya\s+mwili)\b.{0,30}\b(kuwa\s+gumu|kuwa\s+kama\s+chuma)\b.{0,40}\b(kuzuia\s+mimba|kuathiri\s+uzazi|hawezi\s+kuzaa)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "ukiona mwanamke ana misuli mikubwa, ameshapoteza uwezo wa kuitwa mwanamke kamili"
        (r'\b(ukiona|wakiona|unapoona)\b.{0,15}\b(mwanamke|msichana)\b.{0,20}\b(ana\s+misuli\s+mikubwa|ana\s+nguvu\s+nyingi|ana\s+mwili\s+mkubwa)\b.{0,40}\b(ameshapoteza|amepoteza|hana\s+tena)\b.{0,30}\b(uwezo\s+wa\s+kuitwa|heshima\s+ya\s+kike|ufemininity|sifa\s+za\s+kike)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "michezo ya ushindani inawafanya wanawake wawe na hasira / kukosa unyenyekevu"
        (r'\b(michezo\s+ya\s+ushindani|riadha\s+ya\s+ushindani)\b.{0,30}\b(inawafanya|huwafanya|inasababisha)\b.{0,20}\b(wanawake|wasichana)\b.{0,30}\b(wawe\s+na\s+hasira|kukosa\s+unyenyekevu|kuwa\s+na\s+ukaidi|kutoweza\s+kutii)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "msichana anayenyanyua vyuma ataharibu homoni / hawezi kuzaa"
        (r'\b(msichana|mwanamke)\b.{0,20}\b(anayenyanyua|anaponyanyua|anayeinua)\b.{0,20}\b(vyuma|uzito|dumbbells|weights)\b.{0,40}\b(ataharibu\s+homoni|ataharibu\s+mfumo|hawezi\s+kuzaa|ataathiri\s+uzazi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "michezo ya nguvu inafanya wanawake wapoteze mvuto wa kike"
        (r'\b(michezo\s+ya\s+nguvu|riadha\s+ya\s+nguvu|mazoezi\s+ya\s+nguvu)\b.{0,30}\b(inafanya|hufanya|inaweza)\b.{0,30}\b(wanawake|mwanamke|wasichana)\b.{0,30}\b(wapoteze\s+mvuto|kupoteza\s+uzuri|kuwa\s+kama\s+wanaume|wapoteze\s+heshima)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwili wa mwanamke haukuumbwa kwa ajili ya michezo mikali"
        (r'\b(mwili\s+wa\s+mwanamke|miili\s+ya\s+wanawake)\b.{0,20}\b(haukuumbwa|haukufaa|haupaswi)\b.{0,30}\b(kwa\s+ajili\s+ya|kwa)\b.{0,20}\b(kukimbia|mazoezi\s+makali|michezo\s+migumu|ndondi|gym)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "wasichana wanaocheza mpira hukosa waume / wanaonekana kama wanaume"
        (r'\b(wasichana|wanawake)\b.{0,20}\b(wanaocheza|wanaofanya)\b.{0,20}\b(mpira|riadha|ndondi|michezo)\b.{0,30}\b(hukosa\s+waume|hupoteza\s+waume|wanaonekana\s+kama\s+wanaume|hawapendezi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Derogation explicit — adversarial FN extensions ───────────────────────
        # "wanawake ni viumbe wenye akili fupi"
        (r'\b(wanawake|wasichana)\b.{0,20}\bni\b.{0,20}\b(viumbe\s+wenye\s+akili\s+fupi|viumbe\s+dhaifu|wenye\s+akili\s+ndogo|wasio\s+na\s+akili)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "usimpe mwanamke kazi ya kusimamia pesa / atanunua nguo"
        (r'\b(usimpe|usiamini|usimwamini)\b.{0,15}\b(mwanamke|msichana|mama|bibi)\b.{0,20}\b(kazi\s+ya\s+kusimamia|pesa|fedha|akaunti)\b.{0,40}\b(atazitumia|atatumia|atanunua\s+nguo|ataharibu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke ni fala / ni mzigo"
        (r'\b(mwanamke|msichana|huyo\s+mwanamke|huyo\s+msichana)\b.{0,15}\bni\b.{0,15}\b(fala|mjinga|mzigo|bure|taka|mbala)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanawake wengi ofisini ni kwa ajili ya urembo tu"
        (r'\b(wanawake|wasichana)\b.{0,30}\b(ni\s+kwa\s+ajili\s+ya|wako\s+kwa\s+ajili\s+ya)\b.{0,20}\b(urembo|mapambo|kuvutia\s+wateja)\b.{0,20}\btu\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "akili ya mwanamke ni sawa na nusu ya akili ya mwanaume"
        (r'\b(akili\s+ya\s+mwanamke|akili\s+ya\s+wasichana)\b.{0,20}\bni\s+(sawa\s+na\s+nusu|chini\s+ya|ndogo\s+kuliko|haitoshi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanawake hawana uwezo wa kufanya maamuzi ya busara / siku zao"
        (r'\b(wanawake|mwanamke)\b.{0,20}\b(hawana\s+uwezo|hana\s+uwezo)\b.{0,30}\b(kufanya\s+maamuzi\s+ya\s+busara|kufikiri\s+vizuri|kusimamia)\b.{0,30}\b(siku\s+zao|wakati\s+wa\s+hedhi|wakati\s+huo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── hawezi/hawawezi + gender marker + derogatory verb ────────────────────
        # Require a derogatory/limiting verb after hawezi to avoid FPs like
        # "polisi hawezi kutaja" or "hawezi kulazimisha ndoa"
        # Pattern: gender marker + hawezi + incapability verb (leadership/capability/role)
        (r'\b(mwanamke|msichana|wasichana|wanawake)\b.{0,40}\b(hawezi|hawawezi)\b.{0,40}\b(kuongoza|kusimamia|kufanya\s+maamuzi|kufikiri|kuelewa|kujitegemea|kupata\s+mwanaume|kuzaa|kumiliki|kufanikiwa|kudumu|kufanya\s+kazi\s+ngumu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(hawezi|hawawezi)\b.{0,40}\b(mwanamke|msichana|wasichana|wanawake)\b.{0,40}\b(kuongoza|kusimamia|kufanya\s+maamuzi|kufikiri|kuelewa|kujitegemea|kupata\s+mwanaume|kuzaa|kumiliki|kufanikiwa|kudumu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanawake hawawezi X" where X is a capability/role verb — forward scan
        (r'\b(wanawake|wasichana)\b.{0,20}\b(hawawezi|hawezi)\b.{0,50}\b(kuwa\s+(viongozi|rubani|dereva|nahodha|daktari|fundi|mkurugenzi|rais|kiongozi)|kupata\s+nafasi|kuendesha|kuhifadhi|kufikia\s+ujuzi|kuacha|kufanya\s+biashara)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "dhana potofu kuwa wanawake hawawezi" — the bias phrase is embedded
        (r'\b(dhana|imani|mtazamo)\b.{0,30}\b(kuwa|kwamba)\b.{0,20}\b(wanawake|wasichana|mwanamke)\b.{0,20}\b(hawawezi|hawezi|ni\s+dhaifu|ni\s+wanyonge|hawafai)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke hawezi kuwa rubani mzuri kwa sababu anaogopa" — reason clause confirms bias
        (r'\b(mwanamke|msichana)\b.{0,20}\b(hawezi|hawawezi)\b.{0,30}\b(kuwa|kufanya|kushika|kuendesha)\b.{0,30}\b(rubani|dereva|fundi|nahodha|kocha|mkurugenzi|rais|mkuu)\b.{0,50}\b(kwa\s+sababu|anaogopa|wanaogopa|kwa\s+uoga)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── dhaifu/udhaifu near gender markers ───────────────────────────────────
        # Require prescriptive framing — not counter-stereotype context
        # "wanawake ni dhaifu" / "viumbe dhaifu" — direct assertion
        (r'\b(wanawake|wasichana|mwanamke|msichana)\b.{0,20}\bni\b.{0,15}\b(dhaifu|wanyonge|viumbe\s+dhaifu|wadhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\bviumbe\s+dhaifu\b.{0,30}\b(wanawake|wasichana|mwanamke|msichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "udhaifu wa wanawake/wasichana" as subject of prescriptive claim
        (r'\b(udhaifu|unyonge)\b.{0,10}\bwa\b.{0,10}\b(wanawake|wasichana)\b.{0,30}\b(unafanya|unasababisha|unawaruhusu|unawafanya|unawaingiza|unatumiwa)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanaume huvutiwa na wanawake dhaifu ili wawatawale"
        (r'\b(wanaume|wababa|wachumba)\b.{0,30}\b(huvutiwa|wanapenda|wanataka)\b.{0,20}\b(wanawake\s+dhaifu|wasichana\s+dhaifu|mwanamke\s+dhaifu)\b.{0,30}\b(ili\s+wa(weze\s+ku|tawale|nyonye|kudhibiti))\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "uimara wa wanaume utegemee udhaifu wa wanawake"
        (r'\b(uimara|nguvu|hadhi)\b.{0,20}\b(wa\s+wanaume|wa\s+mwanaume)\b.{0,20}\b(utegemee|inategemea|unategemea|unahitaji)\b.{0,20}\b(udhaifu\s+wa\s+wanawake|udhaifu\s+wa\s+wasichana)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "miili yao ni dhaifu" referring to women
        (r'\b(wanawake|wasichana|mama\s+wajawazito)\b.{0,50}\b(miili\s+yao\s+ni\s+dhaifu|mwili\s+wake\s+ni\s+dhaifu|wana\s+miili\s+dhaifu)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Violence / IPV normalisation ─────────────────────────────────────────
        # "mke mkaidi anahitaji kupigwa kidogo"
        (r'\b(mke|mwanamke)\b.{0,20}\b(mkaidi|asiyetii|mpunga|mkali)\b.{0,30}\b(anahitaji|anastahili|apigwe|kupigwa)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "kibao kimoja siyo ukatili, ni njia ya kumrudisha mwanamke kwenye mstari"
        (r'\b(kibao|kupiga|makofi|kumpiga|kumpunja)\b.{0,30}\b(siyo\s+ukatili|si\s+ukatili|ni\s+adabu|ni\s+njia\s+ya|ni\s+kawaida)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwanaume ana hasira za asili, mwanamke akimchokoza asilalamike"
        (r'\b(mwanaume|wanaume)\b.{0,20}\b(ana\s+hasira\s+za\s+asili|hasira\s+ni\s+za\s+asili)\b.{0,40}\b(mwanamke|msichana)\b.{0,20}\b(akimchokoza|akimchochea|asilalamike|anastahili)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "zamani wazee walitumia fimbo kurekebisha tabia za wake"
        (r'\b(wazee|babu\s+zetu|zamani)\b.{0,20}\b(walitumia\s+fimbo|walipiga|walitumia\s+nguvu)\b.{0,30}\b(wake|mke|wanawake)\b.{0,30}\b(ndoa\s+zilidumu|ilifanya\s+kazi|ndoa\s+ilikuwa\s+imara)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "kama angekuwa mke mwema mume asingelazimika kutumia nguvu"
        (r'\b(kama\s+angekuwa|kama\s+alikuwa)\b.{0,20}\b(mke\s+mwema|mke\s+mtiifu|mwaminifu)\b.{0,40}\b(asingelazimika|asingepigwa|asingepata)\b.{0,20}\b(kutumia\s+nguvu|kupigwa|ukatili)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwanaume lazima aonyeshe nguvu zake ili heshima iwepo ndani ya nyumba"
        (r'\b(mwanaume|mume)\b.{0,20}\b(lazima\s+aonyeshe|anapaswa\s+kuonyesha)\b.{0,20}\b(nguvu\s+zake|nguvu\s+yake|nguvu)\b.{0,40}\b(heshima\s+iwepo|ili\s+atakiwe|apate\s+heshima)\b.{0,30}\b(nyumba|familia|ndoa)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "usipomwadhibu mke wako anapokosea, utaonekana mwanaume goigoi"
        (r'\b(usipomwadhibu|usipomrekebisha|usipomwonyesha)\b.{0,15}\b(mke|mwanamke)\b.{0,30}\b(utaonekana|utachukuliwa|utadhaniwa)\b.{0,20}\b(mwanaume\s+goigoi|mwanaume\s+dhaifu|huna\s+nguvu)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),

        # ── Appearance-only value ─────────────────────────────────────────────────
        # "sura yake ndiyo utajiri wake" / "mwili wake ndiyo mtaji wake"
        (r'\b(sura\s+yake|mwili\s+wake|uzuri\s+wake|viuno\s+vyake)\b.{0,20}\b(ndiyo\s+utajiri|ndiyo\s+mtaji|ndiyo\s+silaha|ndiyo\s+nguvu)\b.{0,20}\b(wake|yake|pekee|mkubwa)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # "anathaminiwa kwa sura/mwili yake, siyo kwa akili/kazi"
        (r'\b(anathaminiwa|anaheshimiwa|anapendwa|anapewa\s+kazi)\b.{0,20}\b(kwa\s+sura|kwa\s+mwili|kwa\s+uzuri|kwa\s+viuno)\b.{0,20}\b(siyo\s+kwa|si\s+kwa|badala\s+ya)\b.{0,20}\b(akili|kazi|uwezo|elimu|ujuzi)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # "msichana mzuri tu ana nafasi ya kufanikiwa" / "mwanamke mzuri tu ndiye anayestahili"
        (r'\b(msichana|mwanamke)\b.{0,10}\b(mzuri\s+tu|mrembo\s+tu|mwenye\s+sura\s+tu)\b.{0,20}\b(ana\s+nafasi|anastahili|anapewa|anaweza\s+tu)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # "mwanamke akizeeka kupoteza sura, hana thamani tena"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(akizeeka|anapokuwa\s+mzee|anapopoteza\s+sura)\b.{0,30}\b(hana\s+thamani|hana\s+bei|hana\s+maana|hatakiwi\s+tena)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # "hizi viuno tu ndizo utajiri wa manzi"
        (r'\b(hizi\s+viuno|hizi\s+sura|hii\s+mwili|hizi\s+ngozi)\b.{0,20}\b(tu\s+ndizo\s+utajiri|tu\s+ndio\s+nguvu|ndiyo\s+kila\s+kitu)\b.{0,20}\b(manzi|dame|msichana|mwanamke)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),

        # ── Emotional suppression (male) ─────────────────────────────────────────
        # "mwanaume hapaswi kuonyesha udhaifu / kulia"
        (r'\b(mwanaume|mvulana|baba|msee)\b.{0,20}\b(hapaswi|hafai|hana\s+haki\s+ya|hawezi)\b.{0,20}\b(kuonyesha\s+udhaifu|kuonyesha\s+hisia|kulia|kutoa\s+machozi|kusononeka)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "kulia ni kazi ya wanawake, mwanaume ana moyo wa chuma"
        (r'\b(kulia|machozi|hisia)\b.{0,20}\bni\b.{0,20}\b(kazi\s+ya\s+wanawake|ya\s+watoto|ya\s+wasichana)\b.{0,30}\b(mwanaume|wanaume)\b.{0,20}\b(ana\s+moyo\s+wa\s+chuma|hana\s+wakati|anatakiwa\s+kuwa\s+imara)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "mvulana akishindwa kuvumilia maumivu bila machozi, huyo si rijali"
        (r'\b(mvulana|kijana\s+wa\s+kiume|mwanaume)\b.{0,30}\b(akishindwa\s+kuvumilia|anapolia|akilia)\b.{0,30}\b(si\s+rijali|si\s+mwanaume|hana\s+nguvu|ni\s+mnyonge)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "machozi ya mwanaume ni aibu kwa ukoo mzima"
        (r'\b(machozi\s+ya\s+mwanaume|kulia\s+kwa\s+mwanaume)\b.{0,20}\bni\b.{0,20}\b(aibu|fedheha|udhaifu|dharau)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "mwanaume wa shoka huumeza uchungu" / "real msee hakuombi msaada"
        (r'\b(mwanaume\s+wa\s+shoka|real\s+msee|msee\s+wa\s+ukweli|mwanaume\s+kamili)\b.{0,30}\b(huumeza\s+uchungu|hakuombi\s+msaada|haulalii\s+maumivu|hasononeki)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "badala ya kusononeka, nenda kafanye kazi, mwanaume hashindwi"
        (r'\b(badala\s+ya\s+kusononeka|badala\s+ya\s+kulia|acha\s+kulalamika)\b.{0,30}\b(mwanaume\s+hashindwi|mwanaume\s+hana\s+wakati|nenda\s+kafanye\s+kazi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),

        # ── Family role / male dominance (remaining) ─────────────────────────────
        # "mwanamke hapaswi kubishana na mume wake"
        (r'\b(mwanamke|mke)\b.{0,20}\b(hapaswi|hafai|hana\s+haki\s+ya)\b.{0,20}\b(kubishana|kupinga|kukataa|kutoa\s+sauti)\b.{0,30}\b(mume\s+wake|mumewe|mwanaume)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "hata kama mke ana elimu kubwa, lazima anyenyekee chini ya mume"
        (r'\b(hata\s+kama|ingawa)\b.{0,15}\b(mke|mwanamke)\b.{0,20}\b(ana\s+elimu|ana\s+shahada|ana\s+ujuzi|ana\s+pesa)\b.{0,30}\b(lazima\s+anyenyekee|lazima\s+atii|inabidi\s+atii)\b.{0,20}\b(mume|mwanaume)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "ni makosa kwa mwanamke kutoa sauti mbele ya wakwe bila ruhusa ya mumewe"
        (r'\b(ni\s+makosa|si\s+vizuri|haifai|ni\s+aibu)\b.{0,20}\b(mwanamke|mke)\b.{0,20}\b(kutoa\s+sauti|kuzungumza|kupinga)\b.{0,30}\b(wakwe|familia\s+ya\s+mume|jamaa\s+za\s+mume)\b.{0,30}\b(bila\s+ruhusa|bila\s+idhini)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "usiruhusu mke wako awe na kauli ya mwisho kwenye masuala ya fedha"
        (r'\b(usiruhusu|usimruhusu|usimpe)\b.{0,15}\b(mke\s+wako|mwanamke\s+wako)\b.{0,20}\b(awe\s+na\s+kauli|aongozee|asimamie|asimamie\s+pesa|awe\s+mkuu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "mwanamke anayetafuta uongozi juu ya wanaume anavunja sheria za asili"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(anayetafuta\s+uongozi|anayetaka\s+kusimamia|anayetaka\s+kuwa\s+mkuu)\b.{0,30}\b(juu\s+ya\s+wanaume|kuliko\s+wanaume)\b.{0,30}\b(anavunja\s+sheria|anapinga\s+asili|anapinga\s+mfumo)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "nyumba yenye vichwa viwili haiwezi kusimama, mwanaume mmoja ndiye mkuu"
        (r'\b(nyumba\s+yenye\s+vichwa\s+viwili|familia\s+yenye\s+viongozi\s+wawili)\b.{0,30}\b(haiwezi\s+kusimama|itaanguka|haina\s+mwelekeo)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mwanaume ndiye nahodha, mwanamke kazi yake ni kufuata maelekezo"
        (r'\b(mwanaume|mume|baba)\b.{0,10}\bndiye\b.{0,10}\b(nahodha|mkuu\s+wa\s+nyumba|mkuu\s+wa\s+familia|kiongozi\s+wa\s+nyumba)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "mwanamke akianza kuongoza, nyumba imelaaniwa"
        (r'\b(mwanamke|mke)\b.{0,20}\b(akianza\s+kuongoza|anapokuwa\s+mkuu|akiwa\s+kiongozi)\b.{0,30}\b(nyumba\s+imelaaniwa|familia\s+itaharibika|itakuwa\s+tatizo|haina\s+mwelekeo)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Additional targeted misses ────────────────────────────────────────────
        # "ulaini, upole, uoga wa wanawake unatokana na sababu za kimaumbile" — naturalising weakness
        (r'\b(ulaini|upole|uoga|unyenyekevu)\b.{0,20}\b(wa\s+wanawake|wa\s+wasichana|wa\s+mwanamke)\b.{0,20}\b(unatokana\s+na|unatokea\s+na|ni\s+wa)\b.{0,20}\b(kimaumbile|asili|asilia|maumbile)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "kiongozi huyo ni dhaifu kwa wanawake" — derogating leader re women
        (r'\b(kiongozi|bosi|mkuu|afisa)\b.{0,20}\bni\b.{0,15}\b(mwongo\s+na\s+ni\s+dhaifu|dhaifu)\b.{0,10}\bkwa\s+wanawake\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "msichana anadhani hawezi kubalika, anamkimbilia" — self-doubt
        (r'\b(msichana|mwanamke)\b.{0,20}\b(anadhani|anaamini|anajua)\b.{0,20}\b(hawezi\s+kubalika|hawezi\s+kupendwa|hafai|hastahili)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # Sheng: "mandem wanatakiwa kuwa wagumu si kukaa mkipiga story za feelings"
        (r'\b(mandem|masee|wanaume)\b.{0,20}\b(wanatakiwa|lazima|inapaswa)\b.{0,20}\b(kuwa\s+wagumu|kuwa\s+strong|kuwa\s+imara)\b.{0,30}\b(si\s+kukaa|si\s+kupiga\s+story|si\s+kuongea)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "usimwamini mke anayependa chakula cha tayari badala ya kupika"
        (r'\b(usimwamini|usimpe\s+amini|usiamini)\b.{0,10}\b(mke|mwanamke|msichana)\b.{0,20}\b(anayependa\s+chakula\s+cha\s+tayari|asiyependa\s+kupika|anayekataa\s+kupika|anayenunua\s+chakula)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "uhandisi wa mitambo / kazi ngumu inahitaji akili ya kiume pekee"
        (r'\b(uhandisi|fani\s+ngumu|kazi\s+ngumu)\b.{0,20}\b(wa\s+mitambo|wa\s+umeme|wa\s+ujenzi)?\b.{0,20}\b(ni\s+kazi\s+ngumu|inahitaji)\b.{0,20}\b(nguvu\s+na\s+akili|akili\s+ya\s+kiume|nguvu\s+za\s+kiume)\b.{0,10}\bpekee\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Remaining capability misses ───────────────────────────────────────────
        # "mwanamke akijaribu kuwa na mantiki, anaishia kulia kwa sababu hana hoja"
        (r'\b(mwanamke|msichana)\b.{0,20}\b(akijaribu\s+kuwa\s+na\s+mantiki|anapojaribu\s+kufikiri|akibishana)\b.{0,40}\b(anaishia\s+kulia|hana\s+hoja|anashindwa|anapoteza)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "usitegemee jambo la maana kutoka kwa bosi wa kike"
        (r'\b(usitegemee|usitegemea|usisubiri)\b.{0,20}\b(jambo\s+la\s+maana|kazi\s+nzuri|maamuzi\s+mazuri)\b.{0,30}\b(kutoka\s+kwa|kwa)\b.{0,15}\b(bosi\s+wa\s+kike|kiongozi\s+wa\s+kike|msimamizi\s+wa\s+kike)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "uhandisi wa mitambo unahitaji nguvu na akili ya kiume pekee"
        (r'\b(uhandisi|ujenzi|ufundi|sayansi\s+ya\s+anga|upasuaji)\b.{0,30}\b(unahitaji|inahitaji)\b.{0,20}\b(nguvu\s+na\s+akili|akili\s+na\s+nguvu|uwezo)\b.{0,20}\b(ya\s+kiume\s+pekee|wa\s+kiume\s+pekee|wa\s+wanaume\s+pekee)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "historia inaonyesha ufalme ulioongozwa na mwanamke ulisambaratika"
        (r'\b(historia\s+inaonyesha|historia\s+inatuambia)\b.{0,30}\b(ufalme|nchi|serikali|taifa)\b.{0,20}\b(ulioongozwa\s+na\s+mwanamke|iliyoongozwa\s+na\s+mwanamke)\b.{0,40}\b(uliishia|ulisambaratika|ulianguka|ulishindwa)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "tunda lililokwishaguswa hana thamani sawa na lililofungwa" (purity metaphor)
        (r'\b(tunda|bidhaa)\b.{0,20}\b(lililokwishaguswa|lililotumika|aliyeguswa)\b.{0,30}\b(haliwezi\s+kuwa|hana\s+thamani|halifai)\b.{0,30}\b(sawa\s+na\s+lile|thamani\s+sawa|bora)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "kupiga mazoezi ya gym kunafanya tumbo la mwanamke kuwa gumu / kuzuia mimba"
        (r'\b(kupiga\s+mazoezi|kufanya\s+mazoezi)\b.{0,20}\b(ya\s+gym|kila\s+siku|kwa\s+nguvu)\b.{0,30}\b(kunafanya|inafanya)\b.{0,20}\b(tumbo\s+la\s+mwanamke|mwili\s+wa\s+mwanamke)\b.{0,30}\b(kuwa\s+gumu|kuzuia\s+mimba|kuathiri\s+uzazi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwanamke anayetafuta kazi ya ofisini na kuacha nyumba chafu ni mvivu"
        (r'\b(mwanamke|mke)\b.{0,20}\b(anayetafuta\s+kazi|anayefanya\s+kazi)\b.{0,20}\b(ya\s+ofisini|nje\s+ya\s+nyumba|mjini)\b.{0,30}\b(na\s+kuacha\s+nyumba\s+chafu|na\s+kutotunza\s+nyumba)\b.{0,20}\b(ni\s+mvivu|ameshindwa|hafai)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "usimwamini mke anayependa chakula cha tayari badala ya kupika"
        (r'\b(usimwamini|usimoe|usioe)\b.{0,10}\b(mke|mwanamke|msichana)\b.{0,20}\b(anayependa\s+chakula\s+cha\s+tayari|asiyependa\s+kupika|anayekataa\s+kupika)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # Sheng: "morio ambaye hawezi kucalculate ganji ni weak"
        (r'\b(morio|msee|buda)\b.{0,20}\b(ambaye\s+hawezi|asiyeweza)\b.{0,20}\b(kucalculate|ku.deal|kumanage|ku.handle)\b.{0,20}\b(ganji|pesa\s+zake|mambo\s+yake)\b.{0,20}\b(ni\s+weak|ni\s+mjinga|hana\s+akili|hufai)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # Sheng: "kama msee huna hustle, hufai kupewa mic"
        (r'\b(kama\s+wewe\s+ni\s+msee|kama\s+msee)\b.{0,20}\b(huna\s+hustle|huna\s+pesa|huna\s+kazi|huna\s+gari)\b.{0,30}\b(hufai|huna\s+haki|hutastahili|watu\s+hawakukubali)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # Sheng: "mandem wanatakiwa kuwa wagumu si kupiga story za feelings"
        (r'\b(mandem|masee|wanaume)\b.{0,20}\b(wanatakiwa|lazima|inapaswa)\b.{0,20}\b(kuwa\s+wagumu|kuwa\s+imara|kuwa\s+strong)\b.{0,30}\b(si\s+kukaa|si\s+kupiga\s+story|si\s+kuongea)\b.{0,20}\b(feelings|hisia|moyo|machozi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "katika jamii yetu mwanaume ndiye anayepanga ratiba ya kila mtu ndani ya boma"
        (r'\b(katika\s+jamii\s+yetu|katika\s+utamaduni\s+wetu)\b.{0,20}\b(mwanaume|mume|baba)\b.{0,10}\bndiye\b.{0,20}\b(anayepanga|anayeamua|anayesimamia|anayetoa\s+amri)\b.{0,30}\b(ratiba|maamuzi|shughuli|kila\s+kitu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),
        # "kama huwezi kumnunulia mpenzi zawadi za gharama, wewe si mwanaume tosha"
        (r'\b(kama\s+huwezi|kama\s+huna\s+uwezo)\b.{0,20}\b(kumnunulia|kumlipia|kumpa)\b.{0,20}\b(mpenzi|dame\s+yako|msichana\s+wako)\b.{0,20}\b(zawadi\s+za\s+gharama|pesa|vitu\s+vya\s+thamani)\b.{0,30}\b(si\s+mwanaume\s+tosha|si\s+mwanaume\s+kamili|huna\s+thamani)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.MALE),

        # ── Sheng capability / leadership (remaining) ────────────────────────────
        # "morio wanafaa kuongoza, si hizi dame ambazo hazijui kusimamia"
        (r'\b(morio|masee|wanaume|waboda)\b.{0,20}\b(wanafaa\s+kuongoza|ndio\s+viongozi|wanaostahili\s+kuongoza)\b.{0,30}\b(si\s+hizi\s+dame|si\s+madem|si\s+wanawake)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "dame akiwa na degree bado anahitaji morio amfanyie maamuzi"
        (r'\b(dame|manzi|msichana)\b.{0,20}\b(akiwa\s+na\s+degree|hata\s+na\s+elimu|hata\s+akiwa\s+na\s+kazi)\b.{0,30}\b(bado\s+anahitaji|lazima\s+anahitaji)\b.{0,20}\b(morio|msee|mwanaume)\b.{0,20}\b(amfanyie\s+maamuzi|amwambie|amuongozee)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "hata kama dame ni smart, bado anahitaji morio amwambie"
        (r'\b(hata\s+kama|ingawa)\b.{0,15}\b(dame|manzi|msichana)\b.{0,20}\b(ni\s+smart|ana\s+akili|ana\s+elimu)\b.{0,30}\b(bado\s+anahitaji|lazima\s+anahitaji)\b.{0,20}\b(morio|msee|mwanaume)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "wasichana wafanye kazi za chini tu, leadership ni kwa wasomi wa kiume"
        (r'\b(wasichana|madem|dame)\b.{0,20}\b(wafanye\s+kazi\s+za\s+chini|wafanye\s+kazi\s+ndogo|wabaki\s+nyuma)\b.{0,30}\b(leadership|uongozi)\b.{0,20}\bni\b.{0,20}\b(kwa\s+wasomi\s+wa\s+kiume|kwa\s+wanaume|kwa\s+masee)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        # "slay queen hawezi kuwa boss, anatafuta tu sponsor"
        (r'\b(slay\s+queen|manzi\s+wa\s+class|msupa)\b.{0,20}\b(hawezi\s+kuwa\s+boss|hawezi\s+kuongoza|hafai\s+kuwa\s+kiongozi)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),

        # ── Sheng male toughness / dominance ────────────────────────────────────
        # "morio akianza kulia juu ya mapenzi, huyo si mandem wa ukweli"
        (r'\b(morio|msee|buda|bro)\b.{0,20}\b(akianza\s+kulia|anapolia|akisononeka|akionyesha\s+hisia)\b.{0,30}\b(si\s+mandem\s+wa\s+ukweli|si\s+msee\s+wa\s+ukweli|ni\s+weak|si\s+real)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "mandem wanatakiwa kuwa wagumu, si kukaa mkipiga story za feelings"
        (r'\b(mandem|masee|wanaume)\b.{0,20}\b(wanatakiwa\s+kuwa\s+wagumu|lazima\s+wawe\s+wagumu|hawana\s+hisia)\b.{0,30}\b(si\s+kukaa|si\s+kupiga\s+story|si\s+kuzungumza)\b.{0,20}\b(feelings|hisia|story\s+za\s+moyo)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "msee lazima akuwe dominant kwa relationship, ama dame atakucheza"
        (r'\b(msee|morio|mwanaume)\b.{0,20}\b(lazima\s+akuwe\s+dominant|lazima\s+awe\s+mkuu|lazima\s+awe\s+na\s+nguvu)\b.{0,30}\b(relationship|uhusiano)\b.{0,30}\b(dame\s+atakucheza|atadhulumiwa|atakuwa\s+mtegemezi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),
        # "real msee hakuombagi msaada, anapambana mpaka kieleweke"
        (r'\b(real\s+msee|msee\s+kamili|mwanaume\s+kamili)\b.{0,20}\b(hakuombagi\s+msaada|haulagi\s+msaada|haombi\s+msaada|anapambana\s+peke\s+yake)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.MALE),

        # ── Female-specific capability / personality / appearance misses ─────────
        # "wasanii wa kike / wanafunzi wa kike — tatizo kubwa ni kutojiamini"
        (r'\b(wasichana|wasanii\s+wa\s+kike|wanafunzi\s+wa\s+kike|wanawake)\b.{0,80}\btatizo\b.{0,30}\bni\b.{0,20}\b(kutojiamini|ukosefu\s+wa\s+ujasiri|uoga|woga)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "vijana wa kike kutaka vitu / pesa kwa haraka" — materialistic stereotype
        (r'\b(vijana\s+wa\s+kike|wasichana|wanawake|manzi)\b.{0,30}\b(kutaka|wanataka|wapenda)\b.{0,30}\b(vitu|mali|pesa|starehe|zawadi)\b.{0,20}\bkwa\s+haraka\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanaogopa kuwa hawezi kuzaa / hawezi kupata mimba" — age/fertility fear framing
        (r'\b(wanaogopa|anaogopa|wengi\s+wanaogopa)\b.{0,30}\b(kuwa|kwamba)\b.{0,20}\b(hawezi\s+kuzaa|hawezi\s+kupata\s+(mtoto|mimba)|kuzaa\s+kwa\s+umri\s+huo)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # body/appearance shame: "binti wa kike kukaa utupu / uchi hadharani ni matusi"
        (r'\b(binti\s+wa\s+kike|mwanamke|msichana)\b.{0,30}\b(kukaa\s+utupu|kuonekana\s+uchi|kuvaa\s+nguo\s+fupi)\b.{0,30}\b(ni\s+matusi|ni\s+aibu|ni\s+fedheha|ni\s+makosa|haifai)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # virginity testing: "kupima bikira wanafunzi / wasichana"
        (r'\bkuwapima\s+bikira\b.{0,30}\b(wanafunzi|wasichana|wanawake)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\bmpango\s+wa\s+kuwapima\s+bikira\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "wanafunzi wa kike kujiweka pembeni na uhusiano ili kuepusha ujauzito"
        (r'\b(wanafunzi\s+wa\s+kike|wasichana)\b.{0,30}\bkujiweka\s+pembeni\b.{0,30}\b(uhusiano|mapenzi)\b.{0,50}\b(kuepusha|kuepuka)\b.{0,30}\bujauzito\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "wasichana wanaolewa kabla hawajafika umri" — child marriage stat (bias framing)
        (r'\b(wasichana|wanafunzi\s+wa\s+kike)\b.{0,30}\bwanaolewa\b.{0,30}\bkabla\b.{0,30}\b(hawajafika|hawafiki)\b.{0,30}\bumri\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # personality: "wasichana wanaotongoza wavulana" — seductress stereotype
        (r'\b(wanafunzi\s+wa\s+kike|wasichana|wanawake)\b.{0,60}\bkuwatongoza\b.{0,30}\b(wavulana|wanaume|vijana\s+wa\s+kiume)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke aliyeachwa na wanaume hawezi kupenda kwa asilimia 100"
        (r'\b(mwanamke|msichana)\b.{0,40}\b(aliyeachwa|aliyeachwa\s+na\s+wanaume|aliyekataliwa)\b.{0,50}\bhawezi\b.{0,30}\b(kupenda\s+kwa\s+asilimia|kupenda\s+kikamilifu|kuwa\s+na\s+uwezo\s+wa\s+kupenda)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Pregnancy testing / body control at school ───────────────────────────
        # "shule ina utaratibu wa kuwapima wanafunzi wa kike ujauzito"
        (r'\b(kuwapima|kupima)\b.{0,40}\b(wanafunzi\s+wa\s+kike|wasichana)\b.{0,40}\bujauzito\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\b(kuwapeleka|kupeleka)\b.{0,40}\b(wanafunzi\s+wa\s+kike|wasichana)\b.{0,40}\b(hospitali|kupima\s+ujauzito)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\butaratibu\b.{0,60}\b(wanafunzi\s+wa\s+kike|wasichana)\b.{0,60}\bujauzito\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "kuwaamuru wanafunzi wa kike kunyoa nywele" — appearance control
        (r'\b(kuwaamuru|kuamrisha|amurisha)\b.{0,40}\b(wanafunzi|wasichana)\b.{0,20}\bwa\s+kike\b.{0,30}\bkunyoa\s+nywele\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(wanafunzi|wasichana)\b.{0,10}\bwa\s+kike\b.{0,30}\bkunyoa\s+nywele\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),

        # ── Girl child less valued / preference for sons ─────────────────────────
        # "tuliomba Wema angekuwa wa kiume" — son preference bias
        (r'\b(tuliomba|waliomba|niliomba|alitaka)\b.{0,30}\b(mtoto|mwana|mwanao|Wema|huyo)\b.{0,30}\b(angekuwa\s+wa\s+kiume|awe\s+wa\s+kiume|ni\s+wa\s+kiume)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "wanne waliotangulia ni wa kike, waliomba wa kiume"
        (r'\b(waliotangulia|wote)\s+ni\s+wa\s+kike\b.{0,50}\b(waliomba|tuliomba|walipendelea)\b.{0,30}\bwa\s+kiume\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Women as homemakers — naturalising domestic burden ───────────────────
        # "wanawake ni mama wa nyumbani, wana shughuli nyingi za kufua, kupika..."
        (r'\b(wanawake|wao)\b.{0,15}\bni\s+mama\s+wa\s+nyumbani\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Pregnancy expulsion / school ban ────────────────────────────────────
        # "wanafunzi watakaopata ujauzito hawataruhusiwa tena kurudi shuleni"
        (r'\b(wanafunzi|wasichana)\b.{0,40}\bujauzito\b.{0,30}\b(hawataruhusiwa|hawaruhusiwi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "marufuku wanafunzi wa kike wanaopata ujauzito ...kurejea masomo"
        (r'\bmarufuku\b.{0,30}\b(wanafunzi\s+wa\s+kike|wasichana)\b.{0,40}\b(wanaopata\s+ujauzito|kupata\s+ujauzito)\b.{0,60}\b(kurejea|kurudi|kuendelea\s+na\s+masomo)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Grooming / sexual exploitation of female students ───────────────────
        # "ni rahisi kuwarubuni wanafunzi wa kike kwa zawadi / lifti"
        (r'\b(rahisi|ni\s+rahisi)\b.{0,20}\b(kuwarubuni|kuwapata|kuwaingilia)\b.{0,20}\b(wanafunzi\s+wa\s+kike|wasichana)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\b(bodaboda|pikipiki|madereva)\b.{0,40}\b(kuwarubuni|kuwaingilia)\b.{0,20}\b(wanafunzi\s+wa\s+kike|wasichana)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "wanaume kuacha tabia ya kuwaambia wanafunzi wa kike kwamba wamependeza"
        (r'\b(wanaume|watu)\b.{0,30}\bkuacha\s+tabia\b.{0,20}\b(ya\s+kuwaambia|ya\s+kuwasifu|ya\s+kuwatongoza)\b.{0,20}\b(wanafunzi\s+wa\s+kike|wasichana)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Forced unprotected sex ───────────────────────────────────────────────
        (r'\b(kulazimisha\s+mtu|kulazimisha\s+mwanamke|kulazimisha)\b.{0,20}\b(asivae\s+kinga|asitumie\s+kondomu|asitumie\s+kinga)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Sexual bribery (rushwa ya ngono) ────────────────────────────────────
        (r'\brushwa\s+ya\s+ngono\b.{0,50}\b(vyuoni|shuleni|kazini|ofisini|taasisi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Personality: merged-word variants + obsessive female fan trope ──────
        # "piavijana wa kike" / "vijana wa kike kutaka vitu kwaharaka" (no space)
        (r'\bpiavijana\s+wa\s+kike\b|\b(vijana\s*wa\s*kike|wasichana)\b.{0,30}\bkupata\s+vitu\b.{0,20}\bkwa\s*haraka\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # nurses/female workers insulting pregnant patients
        (r'\b(watumishi|wauguzi|wafanyakazi)\b.{0,20}\bwa\s+kike\b.{0,40}\b(vinara|wanaongoza|ndio\s+wakuu)\b.{0,40}\b(lugha\s+chafu|kutoa\s+lugha\s+chafu|kudharau|kukashifu)\b.{0,30}\b(wajawazito|wanaojifungua|wazazi)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Capability: menstrual barrier, fertility, business failure ───────────
        # "wanafunzi wa kike hushindwa kuhudhuria masomo kwa sababu ya hedhi"
        (r'\b(wanafunzi\s+wa\s+kike|wasichana)\b.{0,50}\b(hushindwa|wameshindwa|wanashindwa)\b.{0,40}\bkuhudhuria\s+masomo\b.{0,40}\b(kwa\s+sababu\s+ya\s+hedhi|hedhi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wasanii wa kike wameshindwa kutengeneza mkwanja kwenye ujasiriamali"
        (r'\b(wasanii|mastaa|wanawake)\b.{0,15}\bwa\s+kike\b.{0,50}\b(wameshindwa|wanashindwa)\b.{0,40}\b(kutengeneza\s+mkwanja|kufanikiwa|kufanya\s+biashara|ujasiriamali)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mwanamke hawezi kuzaa tena" (menopause age framing)
        (r'\b(mwanamke|mke|mama)\b.{0,50}\b(hawezi\s+kuzaa\s+tena|hawezi\s+tena\s+kuzaa)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "HAWEZI TENDO LA NDOA" — caps variant
        (r'\b(HAWEZI|hawezi)\s+(TENDO\s+LA\s+NDOA|tendo\s+la\s+ndoa)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "wanaume wamekuwa vikwazo dhidi ya wanafunzi wa kike"
        (r'\b(wanaume|viongozi)\b.{0,30}\b(wamekuwa\s+vikwazo|wanakuwa\s+vikwazo)\b.{0,50}\b(wanafunzi\s+wa\s+kike|wasichana|wanawake)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # skin bleaching as prerequisite for female success
        (r'\b(wasanii|wanawake)\b.{0,15}\bweusi\b.{0,15}\bwa\s+kike\b.{0,50}\b(rangi\s+zao\s+zinang.aa|kuchanganya\s+wazazi|wanabadilisha\s+rangi)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),

        # ── Personality: seductress (no-space merged), vengeful woman, obsessive fan
        # "kuwatongoza wavulanakwa" — no space between wavulana+kwa
        (r'\bkuwatongoza\s*wavulana',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "mastaa wa kike... kwa lengo la kuwaumiza moyo wenzi wao" — vengeful
        (r'\bni\s+wa\s+kike\b.{0,60}\b(kwa\s+lengo\s+la\s+kuwaumiza\s+moyo|kuwaumiza\s+moyo\s+wenzi)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        # "shabiki wa kike kutangaza kujiua" over celebrity — obsessive trope
        (r'\b(shabiki|mashabiki)\b.{0,15}\bwa\s+kike\b.{0,40}\b(kutangaza\s+kujiua|anataka\s+kujiua|yupo\s+tayari\s+kujiua)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Appearance: body objectification, fake body parts, appearance policing
        # "warembo / wanawake wanaotumia miili yao kujipatia fedha"
        (r'\b(warembo|wanawake|wasichana)\b.{0,40}\bmiili\s+yao\b.{0,40}\b(kujipatia\s+fedha|kupata\s+pesa|kujikimu|biashara)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # "wasanii wa kike kutumia makalio / nyonga feki"
        (r'\b(wasanii|wanawake)\b.{0,15}\bwa\s+kike\b.{0,40}\b(kutumia|kuvaa)\b.{0,20}\b(makalio\s+feki|matako\s+feki|nyonga\s+feki|viuno\s+feki)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # "mavazi ya nusu utupu ... wasanii wa kike" — appearance policing
        (r'\b(mavazi\s+ya\s+nusu\s+utupu|nguo\s+za\s+nusu\s+uchi)\b.{0,60}\b(wasanii|wanawake)\b.{0,15}\bwa\s+kike\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        # sexual bribery targeting female artists/women
        (r'\brushwa\s+ya\s+ngono\b.{0,60}\b(wasanii\s+wa\s+kike|wanawake\s+wachanga|wasichana)\b|\b(wasanii\s+wa\s+kike|wanawake)\b.{0,60}\brushwa\s+ya\s+ngono\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Family role: inheritance denial, son preference, trapping girl ────────
        # "mwanamke umekuja tu kuolewa" — inheritance denial framing
        (r'\bumekuja\s+tu\s+kuolewa\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "wanawake wanatakiwa kujifungua watoto wa kiume wengi" — son preference
        (r'\b(wanawake|mama)\b.{0,40}\b(wanatakiwa|wanaombwa|lazima)\b.{0,60}\b(kujifungua|kuzaa)\b.{0,20}\b(watoto\s+wa\s+kiume|wavulana)\b.{0,20}\b(wengi|zaidi|tu)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # "amfungishe mtoto wa kike pingu za maisha" — trapping girl in marriage
        (r'\bamfungishe\b.{0,25}\b(mtoto\s+wa\s+kike|binti)\b.{0,40}\bpingu\s+za\s+maisha\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        # Fix: "Usimwamini mke anayependa kununua chakula cha tayari" (existing pattern misses "kununua")
        (r'\b(usimwamini|usiamini)\b.{0,15}\b(mke|mwanamke|msichana)\b.{0,30}\b(kununua\s+chakula|chakula\s+cha\s+tayari|badala\s+ya\s+kupika)\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Appearance: no-space merged variants + appearance self-policing ──────
        # "wanafunziwengi wa kike wataacha kufanya ngono kwani wataingiwa na hofu" (no space)
        (r'\bwanafunzi\w*\s+wa\s+kike\b.{0,60}\b(wataacha\s+kufanya\s+ngono|wataingiwa\s+na\s+hofu)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "utaratibu wa kuwapima ujauzito wanafunzi wa kike" — word order variant
        (r'\butaratibu\s+wa\s+kuwapima\s+ujauzito\b.{0,40}\b(wanafunzi\s+wa\s+kike|wasichana)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "wanafunzi wa kikeujauzito" — merged no-space
        (r'\bwanafunzi\s*wa\s*kike\s*ujauzito\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        # "mwigizaji wa kike hatavaa nguo za nusu uchi" — appearance self-policing
        (r'\b(mwigizaji|msanii|mwimbaji)\b.{0,15}\bwa\s+kike\b.{0,60}\bhatavaa\b.{0,30}\b(nguo\s+za\s+nusu\s+uchi|mavazi\s+ya\s+nusu\s+utupu)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),

        # ── Domestic role prescriptions (adversarial set) ─────────────────────
        (r'\b(nyumba\s+safi|chakula\s+kizuri)\b.{0,30}\bndio\s+sehemu\s+ya\s+mwanamke\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\b(kupika|kusafisha|kulea\s+watoto)\b.{0,30}\bndilo\s+mapenzi\b.{0,20}\bmwanamke\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\b(dame|mwanamke)\b.{0,20}\banapaswa\s+kuwa\s+nyumbani\b.{0,30}\bsi\s+kuenda\s+kazini\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\bbwana\s+anasomea\s+pesa\b.{0,30}\bmwanamke\s+anasomea\s+jikoni\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),
        (r'\b(chungu|jiko)\b.{0,20}\bndio\s+mwaliko\b.{0,20}\bmwanamke\b',
         StereotypeCategory.FAMILY_ROLE, TargetGender.FEMALE),

        # ── Leadership exclusion (adversarial set) ────────────────────────────
        (r'\b(CEO|mkurugenzi|kiongozi|meneja|rais)\b.{0,20}\b(lazima\s+awe|inapaswa\s+kuwa)\b.{0,20}\bmwanaume\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        (r'\bwanaume\s+ndio\b.{0,20}\bwanapaswa\s+kuamua\b',
         StereotypeCategory.LEADERSHIP, TargetGender.MALE),
        (r'\b(biashara|shirika)\b.{0,20}\b(hazibadiliki|haibadiliki)\b.{0,20}\bkwa\s+mkono\s+wa\s+mwanamke\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),
        (r'\bhaiwezekana\b.{0,20}\b(kuwa\s+na\s+kiongozi\s+mwanamke|mwanamke\s+kuwa\s+kiongozi)\b',
         StereotypeCategory.LEADERSHIP, TargetGender.FEMALE),

        # ── Appearance: beauty-as-value (adversarial set) ─────────────────────
        (r'\b(mwanamke|msichana)\b.{0,20}\bmzuri\s+sura\b.{0,30}\bndiye\s+anayestahili\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\bakiwa\s+na\s+(sura\s+nzuri|mwili\s+mzuri)\b.{0,40}\b(hata\s+kama\s+hajafundishwa|bila\s+kusoma)\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(mwanamke|msichana)\b.{0,30}\baliyepoteza\s+uzuri\b.{0,30}\bamepoteza\s+thamani\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),
        (r'\b(sura|uzuri)\b.{0,15}\byake\b.{0,20}\bni\s+asset\b.{0,20}\bkuliko\s+kazi\b',
         StereotypeCategory.APPEARANCE, TargetGender.FEMALE),

        # ── Capability derogation — Sheng variants (adversarial set) ─────────
        (r'\b(dame|manzi|madem|mgirls)\b.{0,30}\bhawana\s+nguvu\s+ya\s+akilini\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(wanawake|wasichana)\b.{0,20}\bsio\s+wenye\s+akili\b.{0,30}\b(politics|siasa|biashara)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),
        (r'\b(manzi|dame|madem)\b.{0,20}\byote\b.{0,20}\bwanafikiri\s+tu\s+kuhusu\b.{0,20}\b(mavazi|make.?up)\b',
         StereotypeCategory.CAPABILITY, TargetGender.FEMALE),

        # ── Purity / marriage — social media & history rejection ──────────────
        (r'\b(haogombea|sitaki|siwezi)\b.{0,30}\b(msichana|mwanamke|binti)\b.{0,50}\b(aliyekuwa\s+na\s+rafiki|historia\s+yake|foto\s+zake|mtandaoni)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\b(OnlyFans|Snapchat|Instagram|TikTok)\b.{0,40}\b(sitaki|haogombea|si\s+rafiki\s+wa\s+ndoa)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),

        # ── Sport-fertility conflict (adversarial set) ────────────────────────
        (r'\b(michezo|riadha|karate|football|volleyball)\b.{0,40}\b(inafanya\s+wanawake|hufanya\s+wanawake)\b.{0,40}\b(kuzoa\s+watoto|kusahau\s+wajibu|kupoteza\s+akili|kinyume\s+cha\s+asili)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
        (r'\b(msichana|mwanamke)\b.{0,20}\banayetaka\s+kuzaa\b.{0,30}\b(lazima\s+aache\s+michezo|aache\s+michezo)\b',
         StereotypeCategory.DAILY_LIFE, TargetGender.FEMALE),
    ],
}

# Swahili gendered-suffix: "[occupation] wa kiume/wa kike" on any occupation
SW_GENDERED_SUFFIX_PATTERNS: List[tuple] = [
    (r'\b(\w+)\s+(wa\s+kiume)\b', 'wa kiume', TargetGender.MALE),
    (r'\b(\w+)\s+(wa\s+kike)\b', 'wa kike', TargetGender.FEMALE),
]

# Allowlist for preceding noun in SW suffix — only fire on occupation-like words
SW_OCCUPATION_PREFIXES = (
    'dakt', 'muuguzi', 'mhand', 'dereva', 'rubani',
    'polisi', 'askari', 'waziri', 'rais', 'mgomba', 'msema',
    'mwanas', 'mkuru', 'mhudumu', 'mkulima', 'mvuvi', 'mwimb',
    'meneja', 'mhasi', 'mpishi', 'mfanya', 'wakili', 'profes',
    'majaji', 'meya', 'mtend', 'mstaa', 'mzalis', 'mlezi',
    'fundi', 'kocha', 'mshauri', 'mcheza', 'mwandishi',
    'mchezaji', 'mbunifu', 'mwanasiasa', 'mbunge', 'gavana',
    'seneta', 'karani', 'nahodha', 'ofisa', 'afisa',
    'mkaguzi', 'msimamizi', 'mwenyekiti', 'mkurugenzi',
    'mwanasheria', 'mwanauchumi', 'mwanahabari', 'mhusika',
    'kiongozi', 'viongozi', 'denti', 'madent',
    'mgombea', 'wagombea', 'muwakilishi', 'wawakilishi',
    'mwakilishi', 'mwanamichezo', 'wanamichezo',
    'rapa', 'mwanaharakati', 'wanaharakati',
    'wasomi', 'mwanajeshi', 'wanajeshi',
    'mwanachama', 'wanachama', 'maskauti',
    'mwamuzi', 'wamuzi', 'mwangalizi',
    'muigizaji', 'waigizaji', 'mwanasanaa',
    # Sports / performance (occupation-like, lower FP risk)
    'wachezaji', 'mchezaji',
    'mfanyakazi', 'wafanyakazi', 'mtaalamu', 'wataalamu',
    'naibu', 'manaibu', 'kamanda', 'makomanda',
    'jenerali', 'majenerali', 'kanali', 'brigadie',
    'spika', 'waziri mkuu', 'makamu',
    # Health / service
    'muuguzi', 'wauguzi', 'daktari', 'madaktari',
    'mkunga', 'wakunga', 'mhudumu', 'wahudumu',
    'mwalimu', 'walimu', 'mkurugenzi', 'wakurugenzi',
    # Judicial / security
    'jaji', 'majaji', 'hakimu', 'mahakimu',
    'mwanasheria', 'wanasheria', 'mlinzi', 'walinzi',
    # Business / finance
    'mfanyabiashara', 'wafanyabiashara', 'mwekezaji', 'wawekezaji',
    'mhasibu', 'wahasibu',
)

SW_NON_OCCUPATION_WORDS = frozenset({
    'wake', 'yake', 'zake', 'lake', 'chake', 'pake',
    'wao', 'yao', 'zao', 'lao', 'chao', 'pao',
    'wetu', 'yetu', 'zetu', 'letu', 'chetu',
    'wenu', 'yenu', 'zenu', 'lenu',
    'huyo', 'hao', 'hawa', 'hizi', 'hilo', 'hayo',
    'mmoja', 'wawili', 'watatu', 'wengi', 'wote', 'wengine',
    'pekee', 'bora', 'mwingine', 'hasa', 'zaidi', 'sana', 'tu', 'pia',
    'mzee', 'mdogo', 'mkubwa', 'mpya', 'mwisho',
    'mwana', 'mtoto', 'watoto', 'vijana', 'kijana',
    'mtu', 'watu', 'binadamu', 'rafiki', 'ndugu',
    'mwananchi', 'wananchi', 'raia', 'shahidi', 'mshtakiwa',
})

# Suppressor for derogation patterns: biased language used rhetorically to CHALLENGE the bias
# e.g. "haileti maana kufikiri kuwa mwanamke hawezi..." (counter-stereotype framing)
SW_DEROGATION_COUNTER_SUPPRESSOR = re.compile(
    r'\b('
    r'haileti\s+maana\s+kufikiri\s+kuwa'   # "it doesn't make sense to think that"
    r'|siamini\s+(kuwa|kwamba)'             # "I don't believe that"
    r'|si\s+kweli\s+(kuwa|kwamba)'          # "it's not true that"
    r'|si\s+sahihi\s+(kuwa|kwamba)'         # "it's not correct that"
    r'|kupinga\s+dhana'                     # "opposing the notion"
    r'|tunapinga'                           # "we oppose"
    r'|hatukubaliani'                       # "we disagree"
    r'|hii\s+ni\s+dhuluma'                 # "this is oppression"
    r'|ni\s+udhalimu'                       # "this is injustice"
    r'|ni\s+ubaguzi'                        # "this is discrimination"
    r'|lazima\s+(tubadilishe|tuzuie|tuondoe)'  # "we must change/stop/remove this"
    r'|dhana\s+potofu\s+kuwa'              # "false notion that" — explicit debunking framing
    r'|kufuta\s+(usemi|dhana|imani)\s+wa'  # "cancel the saying/notion/belief that"
    r'|wanawake\s+na\s+wanaume\s+wote\s+ni\s+sawa'  # equality statement suppresses "hata mwanamke anaweza" FP
    # Bible/religious exegesis — describes serpent/devil exploiting weakness, not asserting it
    r'|nyoka\s*\(ibilisi\)\s+anajua'       # "the serpent (devil) knew [woman is weak]"
    r'|ibilisi\s+anajua\s+mwanamke'        # same framing variant
    # Advocacy reporting — minister/speaker calling to end harassment of women
    r'|kutonyanyasa\s+wanawake'            # "not to harass women" — challenge framing
    r')',
    re.IGNORECASE,
)

SW_PROGRESS_CONTEXT = re.compile(
    r'\b('
    # Advocacy / rights / empowerment
    r'wa\s+kwanza|haki\s+za|usawa\s+wa\s+kijinsia|uwezeshaji|kuhamasisha'
    r'|haki\s+za\s+(mtoto|wanawake|binadamu)'
    r'|ulinzi\s+wa|sheria\s+(ya|inayolinda)|ajenda\s+ya'
    # Factual reporting verbs — "[occ] wa kike/kiume [verb]" = news report, not prescriptive
    r'|wameshinda|wamepiga|wameweza|wamefanikiwa|wamepewa|wamechaguliwa|wamejiunga'
    r'|wameimba|wamecheza|wamefanya|wameweka|wamewasili|wamejitokeza|wamekusanyika'
    r'|ameimba|amecheza|amefanikiwa|ameshinda|amepewa|amechaguliwa|ameweza'
    r'|wanafanya\s+kazi|wanaohusika|wanaohudumu|wanaoshiriki|wanaoimba|wanacheza'
    # Celebration/media reporting context
    r'|siku\s+ya\s+wanawake|maadhimisho|sherehe|tamasha|tuzo|zawadi'
    r'|ushindi|mafanikio|mchango|jitihada|nguvu\s+za'
    # Death/memorial/disaster context — factual occupation mentions in victim reports
    r'|amefariki\s+dunia|alifariki\s+dunia|amepoteza\s+maisha|alipoteza\s+maisha'
    r'|aliumia|alikufa|kifo\s+cha|tetemeko\s+la\s+ardhi|ajali\s+ya'
    # Medical research statistical context — "N madaktari wa kiume takribani"
    r'|takribani\s+\d|zaidi\s+ya\s+\d|idadi\s+ya\s+\d'
    r')',
    re.IGNORECASE,
)


# Prescriptive-verb gate for mtoto/watoto wa kike/kiume.
# These phrases are neutral when used as factual gender references.
# Only flag as bias when a normative/prescriptive verb appears in context.
SW_CHILD_PRESCRIPTIVE = re.compile(
    r'\b(mtoto|watoto)\s+wa\s+(kike|kiume)\b.{0,120}'
    r'\b(anapaswa|wanapaswa|lazima|sharti|inabidi|inahitajika|inamaanisha|'
    r'apaswe|wapaswe|anatakiwa|wanatakiwa|anastahili|wanastahili|'
    r'kukaa\s+nyumbani|kubaki\s+nyumbani|kupika|kusafisha|kutunza\s+nyumba|'
    r'kuolewa|aolewe|hapaswi\s+kusoma|hana\s+haja\s+ya\s+elimu|'
    r'si\s+lazima\s+asomi|asifanye\s+kazi|akae\s+nyumbani)\b',
    re.IGNORECASE | re.DOTALL,
)

# Neutral contexts where mtoto/watoto wa kike/kiume is clearly a possessive biographical reference
# (e.g. "mtoto wake wa kike" = her daughter, not a prescriptive statement)
SW_CHILD_NEUTRAL_CONTEXT = re.compile(
    r'\b(mtoto|watoto)\s+(wake|wao|wangu|wenu)\s+wa\s+(kike|kiume)\b',
    re.IGNORECASE,
)


class DetectorPatterns:
    """
    Holds compiled pattern config and exposes detect_* methods for
    derogation, counter-stereotype, and Swahili gendered-suffix.
    """

    def __init__(self) -> None:
        self._counter: Dict[Language, List[tuple]] = {}
        self._derogation: Dict[Language, List[tuple]] = {}
        self._sw_suffix: List[tuple] = []
        self._compile()

    def _compile(self) -> None:
        for lang, patterns in COUNTER_STEREOTYPE_PATTERNS.items():
            self._counter[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]
        for lang, patterns in DEROGATION_PATTERNS.items():
            self._derogation[lang] = [
                (re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in patterns
            ]
        self._sw_suffix = [
            (re.compile(p[0], re.IGNORECASE), p[1], p[2])
            for p in SW_GENDERED_SUFFIX_PATTERNS
        ]

    def detect_derogation(self, text: str, language: Language) -> Optional[Dict[str, Any]]:
        """Detect derogatory language. Returns match dict or None."""
        # Suppress when biased language is used rhetorically to challenge the bias
        if language == Language.SWAHILI and SW_DEROGATION_COUNTER_SUPPRESSOR.search(text):
            return None
        for pattern, category, gender in self._derogation.get(language, []):
            if pattern.search(text):
                return {
                    'bias_label': 'derogation',
                    'stereotype_category': category,
                    'target_gender': gender,
                    'explicitness': 'explicit',
                    'matched_pattern': pattern.pattern,
                }
        return None

    def detect_counter_stereotype(self, text: str, language: Language) -> Optional[Dict[str, Any]]:
        """Detect counter-stereotype (preserve, do not correct). Returns match dict or None."""
        for pattern, category, gender in self._counter.get(language, []):
            if pattern.search(text):
                return {
                    'bias_label': 'counter-stereotype',
                    'stereotype_category': category,
                    'target_gender': gender,
                    'explicitness': 'explicit',
                    'matched_pattern': pattern.pattern,
                }
        return None

    def detect_sw_gendered_suffix(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect Swahili '[occupation] wa kiume/wa kike'. Returns match dict or None."""
        for compiled, suffix, target_gender in self._sw_suffix:
            m = compiled.search(text)
            if not m:
                continue
            if SW_PROGRESS_CONTEXT.search(text):
                continue
            preceding_noun = m.group(1).lower()
            if preceding_noun.isdigit():
                continue
            if preceding_noun in SW_NON_OCCUPATION_WORDS:
                continue
            if not any(preceding_noun.startswith(p) for p in SW_OCCUPATION_PREFIXES):
                continue
            corrected = compiled.sub(lambda match: match.group(1), text).strip()
            corrected = re.sub(r'  +', ' ', corrected)
            cat = StereotypeCategory.FAMILY_ROLE if preceding_noun in {'mzazi', 'mlezi'} else StereotypeCategory.PROFESSION
            return {
                'from': m.group(0),
                'to': m.group(1),
                'suffix': suffix,
                'corrected_text': corrected,
                'target_gender': target_gender,
                'stereotype_category': cat,
            }
        return None

    def should_suppress_child_gender_term(self, text: str, biased_term: str) -> bool:
        """
        For mtoto/watoto wa kike/kiume lexicon entries: suppress only when
        clearly a biographical possessive or birth announcement (not prescriptive).
        Returns True if the match should be suppressed (not flagged as bias).
        """
        lower_term = biased_term.lower()
        if not any(x in lower_term for x in ('mtoto wa kike', 'mtoto wa kiume',
                                               'watoto wa kike', 'watoto wa kiume')):
            return False
        # Only suppress clear biographical/birth contexts
        return bool(SW_CHILD_NEUTRAL_CONTEXT.search(text))
