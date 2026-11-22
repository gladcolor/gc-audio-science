"""Inventory pronunciation and pacing risks in local transcript send strings.

Run: python -B textscan.py
Inputs and outputs are relative to this script. Uses only the standard library.
"""
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Optional


ROOT = Path(__file__).resolve().parent
LANGUAGES = ("zh", "en")
HAN = r"\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF"
LAT = r"A-Za-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u024F"
NUM = r"(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?"
UNIT = r"km|cm|mm|nm|µm|μm|mL|ml|kg|mg|kJ|GHz|MHz|kHz|Hz|mph|rpm|BPM|ft|mi|AU|KB|MB|GB|TB|TEU|kWh|kW|MW|Pa|kPa|MPa|mol|kcal|cal|ms|min|hr|[ghsmLuNJWVAK]|°[CF]|[℃℉]"
ELEMENT = r"H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Ag|Sn|I|Au|Hg|Pb|U"
ARROW = re.compile(r"[←→↔↑↓↗↘⇒⇌⇄⟶⟷➜]|(?:<=>|->|<-|=>)")
SUP = r"⁰¹²³⁴⁵⁶⁷⁸⁹"
COORD_VALUE = r"(?:negative\s*|负\s*|[-−]\s*)?(?:[0-9]+(?:\.[0-9]+)?|[a-z])"
MONTH = r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
CODE = r"(?:https?://[^\s”’\"）),，。]*|www\.[^\s”’\"）),，。]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
CLOCK = r"(?:[01]?[0-9]|2[0-3])[:：][0-5][0-9](?::[0-5][0-9])?"
ISO = r"(?<![A-Za-z0-9-])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![A-Za-z0-9-])"
NUM_CHAIN = r"(?<![A-Za-z0-9-])[0-9]+(?:[-–—][0-9]+){2,}(?![A-Za-z0-9-])"


@dataclass(frozen=True)
class Clip:
    lesson: str
    lang: str
    key: str
    send: str
    display: str


def expand(pattern):
    for token, value in (
        ("@HAN@", HAN), ("@LAT@", LAT), ("@NUM@", NUM), ("@UNIT@", UNIT),
        ("@SUP@", SUP), ("@CV@", COORD_VALUE), ("@MONTH@", MONTH),
        ("@CODE@", CODE), ("@CLOCK@", CLOCK), ("@ISO@", ISO),
        ("@ELEMENT@", ELEMENT),
    ):
        pattern = pattern.replace(token, value)
    return pattern


def span(pattern, s):
    match = re.search(expand(pattern), s)
    return match.span() if match else None


def whole(s):
    return (0, len(s))


def valid_iso(s):
    for match in re.finditer(ISO, s):
        try:
            date.fromisoformat(match.group())
        except ValueError:
            continue
        return match.span()
    return None


def iso_date(clip):
    return valid_iso(clip.send)


def long_request(clip):
    limit = 150 if clip.lang == "zh" else 400
    return whole(clip.send) if len(clip.send) > limit else None


def dense_han(clip):
    if clip.lang == "zh" and len(re.findall(f"[{HAN}]", clip.send)) > 150:
        return whole(clip.send)
    return None


def mixed(clip):
    han = span(r"[@HAN@]+", clip.send)
    latin = span(r"[@LAT@]+", clip.send)
    return (latin if clip.lang == "zh" else han) if han and latin else None


def wrong_script(clip):
    s = clip.send
    latin = span(r"[@LAT@]", s)
    han = span(r"[@HAN@]", s)
    if (clip.lang == "zh" and latin and not han) or (clip.lang == "en" and han and not latin):
        return whole(s)
    return None


def single_glyph(clip):
    s = clip.send
    return whole(s) if re.fullmatch(expand(r"\s*[@LAT@@HAN@][。.!！?？]?\s*"), s) else None


def short_label(clip):
    s = clip.send.strip()
    if clip.lang == "zh":
        pattern = expand(r"[@HAN@]{2,5}[。.!！?？]?")
    else:
        word = expand(r"[@LAT@]{2,}(?:[’'-][@LAT@]+)*")
        pattern = rf"{word}(?: {word})?[.?!]?"
    return whole(clip.send) if re.fullmatch(pattern, s) else None


# Protect abbreviations and decimals when measuring period-delimited headings.
ABBR = re.compile(r"(?:\b[A-Za-z]\.){2,}|\b(?:Dr|Mr|Mrs|Ms|St|Mt|Jr|Sr|vs|etc|c)\.", re.I)


def mask(text, matches, fill=" "):
    chars = list(text)
    for start, end in matches:
        chars[start:end] = fill * (end - start)
    return "".join(chars)


def term_card(clip):
    s = clip.send
    if clip.lang == "en":
        clean = mask(s, [m.span() for m in ABBR.finditer(s)], "a")
        stops = [m.start() for m in re.finditer(r"(?<!\.)\.(?![\d.])", clean)]
        pos = [-1] + stops + [len(s)]
        if len(stops) < 1:
            return None
        first, second = [s[a + 1:b].strip() for a, b in zip(pos, pos[1:])][:2]
        word_count = r"[A-Za-z]+(?:[’'-][A-Za-z]+)*"
        if (not re.search(r"[:;!?]", first + second)
                and 1 <= len(re.findall(word_count, first)) <= 5
                and 1 <= len(re.findall(word_count, second)) <= 10):
            return (0, stops[1] + 1 if len(stops) > 1 else len(s))
    else:
        match = re.match(expand(r"^\s*[@HAN@]{1,10}。\s*[@HAN@、，]{2,18}(?:。|$)"), s)
        if match:
            return match.span()
    return None


def punctuation_run(clip):
    s = clip.send
    protected = [m.span() for m in ABBR.finditer(s)]
    clean = mask(s, protected, "a")
    return span(r"(?:[。．.!！?？，,、：:；;][ \t]*){2,}", clean)


def unbalanced(clip):
    s = clip.send
    pairs = {"(": ")", "（": "）", "[": "]", "［": "］", "{": "}", "【": "】",
             "《": "》", "〈": "〉", "“": "”", "「": "」", "『": "』"}
    stack = []
    for pos, ch in enumerate(s):
        if ch in pairs:
            stack.append((pairs[ch], pos))
        elif ch in pairs.values():
            if not stack or stack[-1][0] != ch:
                return (pos, pos + 1)
            stack.pop()
    return (stack[0][1], stack[0][1] + 1) if stack else None


def clock_candidate(clip):
    s = clip.send
    for match in re.finditer(rf"(?<![0-9+:：]){CLOCK}(?![0-9]|[:：][0-9])", s):
        # Explicit evidence avoids treating a bare ratio as a clock.
        left = s[max(0, match.start() - 19):match.start()]
        right = s[match.end():match.end() + 12]
        if (re.search(r"(?:[0-9]{4}-[0-9]{2}-[0-9]{2}(?: at)?|学校|时间|at|by|from|around)\s*$", left, re.I)
                or re.match(r"\s*(?:a\.?m\.?|p\.?m\.?|上课|下课|起床|：)", right, re.I)):
            return match.span()
    return None


def colon_ratio(clip):
    s = clip.send
    for match in re.finditer(r"(?<![0-9:：])[0-9]+(?:[ \t]*[:：][ \t]*[0-9]+)+(?![0-9:：])", s):
        left = s[max(0, match.start() - 30):match.start()]
        right = s[match.end():match.end() + 28]
        if re.search(r"\bUTC[+\-−]\s*$", left):
            continue
        if (match.group().count(":") + match.group().count("：") > 1
                and " " in match.group()):
            return match.span()
        if re.search(r"比(?:是|为)?|节奏|比例|\b(?:ratio|rhythm|octave|fifth)\b", left[-24:] + right, re.I):
            if " " in match.group() or not re.fullmatch(CLOCK, match.group()):
                return match.span()
    return None


def signed_literal(clip):
    s = clip.send
    for match in re.finditer(rf"(?<![A-Za-z0-9_])[-−﹣－+＋]\s*{NUM}", s):
        left = s[max(0, match.start() - 24):match.start()]
        right = s[match.end():match.end() + 16]
        if (re.search(r"[-+−]\s*$|[0-9]\s*(?:度|°)?\s*$|碳$|铀$|开普勒$", left)
                or re.match(r"[-–—]\d", right)):
            continue
        return match.span()
    return None


def dash_range(clip):
    s = clip.send
    for match in re.finditer(rf"(?<![A-Za-z0-9_.-]){NUM}[ \t]*[-‑–—~～][ \t]*{NUM}(?![A-Za-z0-9_.-])", s):
        if re.search(r"\s[-−]\s", match.group()) and clip.lesson.startswith(("math/", "physics/")):
            continue
        return match.span()
    return None


def numeric_chain(clip):
    for m in re.finditer(NUM_CHAIN, clip.send):
        if not valid_iso(m.group()):
            return m.span()
    return None


def glyph_residue(clip):
    p = r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2300-\u23FF\u2500-\u25FF\uFE0E\uFE0F\u200D]"
    for m in re.finditer(p, clip.send):
        if m.group() not in "−÷×√←→↑↓⇒⇌✓✗":
            return m.span()
    return None


def control_character(clip):
    for i, ch in enumerate(clip.send):
        if unicodedata.category(ch) in ("Cc", "Cf", "Cs") and ch not in "\t\n\r\u200d":
            return (i, i + 1)
    return None


def en_upper_emphasis(clip):
    if clip.lang != "en":
        return None
    return span(r"\b(?:OUTSIDE|INSIDE|OUT|IN|ONE|ALL|ONLY|SAME|BEHIND|AHEAD|MEAN|AND|NOT|DO|MORE|LESS|NOW|BEFORE|AFTER|WHY|WHAT)\b", clip.send)


def ipa_or_pinyin(clip):
    return span(r"[āēīōūǖǎěǐǒǔǚǜǘ]|(?:dài|gē|cí|ěrjītǐ)|[\u0250-\u02AF]|[\u0300-\u036F]", clip.send)


def missing_source_arrow(clip):
    source_arrows = list(ARROW.finditer(clip.display))
    if len(source_arrows) <= len(ARROW.findall(clip.send)):
        return None
    alignment = SequenceMatcher(None, clip.display, clip.send, autojunk=False)
    for tag, i, j, a, b in alignment.get_opcodes():
        if tag != "equal" and any(i <= match.start() < j for match in source_arrows):
            return (a, b)
    return whole(clip.send)


CUSTOM = {
    "long": (long_request, "len(send) > 150 for zh or > 400 for en. Python Unicode code points include spaces, punctuation and Latin text."),
    "dense_han": (dense_han, "lang == zh and count of characters in HAN > 150."),
    "mixed": (mixed, "send contains at least one HAN character and at least one LAT character. The excerpt anchors on the other script relative to lang."),
    "wrong_script": (wrong_script, "zh has a LAT character and no HAN, or en has a HAN character and no LAT."),
    "single": (single_glyph, "After optional outer whitespace, exactly one HAN or LAT character and optionally one terminal 。.!！?？."),
    "short": (short_label, "Trimmed zh consists of 2–5 HAN plus optional stop. Trimmed en consists of one or two words of at least two LAT letters each, with optional internal apostrophe/hyphen or terminal .?!"),
    "card": (term_card, "zh starts with a 1–10 Han heading and a 2–18 character Han/、/， gloss, separated by 。. en has a 1–5 word heading and a 1–10 word fragment after a period, with no colon, semicolon, question or exclamation marks in either. English stop detection masks ABBR and skips decimal dots and ellipses."),
    "punct": (punctuation_run, "Two or more marks from 。．.!！?？，,、：:；; (optional intermark spaces/tabs), after masking ABBR dotted abbreviations and titles."),
    "unbalanced": (unbalanced, "Stack check for (), （）, [], ［］, {}, 【】, 《》, 〈〉, “”, 「」 and 『』. Flag first unmatched/crossed delimiter."),
    "iso": (iso_date, "ASCII-boundary YYYY-MM-DD, validated with date.fromisoformat."),
    "clock": (clock_candidate, "24-hour H:MM or HH:MM[:SS] with colon boundary and local clock cues (date, at/by/from/around, 学校/时间, AM/PM, 上课/下课/起床, or trailing Chinese colon)."),
    "ratio": (colon_ratio, "Colon-separated integers with nearby ratio/rhythm cues, or a spaced chain of three or more integers. Remove UTC offsets and clock-shaped unspaced two-part tokens."),
    "signed": (signed_literal, "Plus/minus glyph followed by an Arabic number at a non-ASCII-alphanumeric boundary. Skip preceding numeric/degree operands, leading signs, 碳/铀/开普勒 and trailing numeric dash segments."),
    "range": (dash_range, "Two standalone numbers joined by -, ‑, –, —, ~ or ～. Exclude alphanumeric ID/date-chain boundaries and spaced ASCII subtraction in math/physics."),
    "chain": (numeric_chain, "Standalone chain of ≥3 ASCII integers joined by -, – or —. Exclude valid ISO dates."),
    "pictograph": (glyph_residue, "First character in U+1F000–1FAFF, U+2600–27BF, U+2300–23FF, U+2500–25FF, or U+FE0E/U+FE0F/U+200D, excluding listed mathematical and direction symbols."),
    "control": (control_character, "Unicode category Cc, Cf or Cs, excluding tab, newline, CR and U+200D."),
    "pinyin": (ipa_or_pinyin, "Pinyin-specific macron/caron vowels, selected observed grave/acute pinyin tokens, IPA block U+0250–02AF, or a combining diacritic U+0300–036F."),
    "emphasis": (en_upper_emphasis, "en includes a standalone all-caps token in the scanner's emphasis list, such as OUTSIDE, BEHIND, ONE or MEAN."),
    "arrow_diff": (
        missing_source_arrow,
        f"Count tokens matching {ARROW.pattern!r} in the clip's display text and its send. "
        "Flag if send has fewer. Align the strings to choose an excerpt near a removed arrow.",
    ),
}


# One row per public class: id, name, severity, handling, detector, reading, risk.
# @name selects a named logic detector. Otherwise the detector is a Python regex.
RULES = r"""
length§Long model request§5§Fixed§@long§Split at complete sentence boundaries, after rewrites. Send each segment in order. Keep quoted speech, clauses, numbers, formulas and their units intact. E.g. end one sky segment after the Moon sentence, then start “Planets above the horizon…” as a new request.§These are supplied approximate limits. Crossing them flags truncation risk, and no audio was tested. Some long clipped examples begin at the opening of the request.
han_length§Dense Mandarin request§5§Fixed§@dense_han§Apply the same sentence-aware chunking as for long requests. E.g. end a chunk after “水星（西南二度）、土星（北十一度）。” then start “这张星图上有约五千颗真实恒星。”§A strict Han count is a diagnostic subset of the 150-character Mandarin rule. Do not add the counts together.
corrupt_exponent§Exponent damaged by normalization§5§Context§(?:[0-9]+[@SUP@]*\s*(?:squared|的平方)\s*[@SUP@]+)§10 squared ⁶ → ten to the twenty-sixth power. 2¹ 的平方 ⁸ → 二的一百二十八次方. Restore the exponent from the display/source before speaking it.§Matches the observed split pattern. Never infer missing exponent digits from the send alone.
lost_relation§Missing equation relation§5§Context§(?:二氧化碳|carbon dioxide).{0,44}\+.{0,32}(?:，|,)\s*(?:有机物|glucose|sugar)|(?:H[⁺+]\s*\+\s*OH[⁻−]\s*[,，]\s*H[2₂]O)|(?:酸\s*\+\s*碱\s*[,，]\s*盐|acid\s*\+\s*base\s*,\s*salt)|(?:H2\s*\+\s*(?:[0-9]+\s*)?O2|CH4\s*\+\s*(?:[0-9]+\s*)?O2|HCl\s*\+\s*NaOH)\s*[,，]\s*(?:[0-9]+\s*)?(?:CO2|H2O|NaCl)|(?:water molecules|水分子)[,，]\s*[0-9]+\s*(?:个\s*)?H[2₂]\s*(?:\+|加)\s*[0-9]+\s*(?:个\s*)?O[2₂]|O\s*(?:等于|equals)\s*O\s*(?:键|bonds?)§“二氧化碳 + 水 —（光能），有机物（葡萄糖）+ 氧气” → 在光能作用下，二氧化碳和水生成葡萄糖和氧气. “O equals O bonds” → oxygen–oxygen double bonds, or “双键” in Mandarin.§Phrase signatures catch known cases. A comma can simply separate a list. Confirm reaction direction, bonds, coefficients and terms using the original.
lost_math_scope§Ambiguous fraction or expression scope§5§Context§(?:[xy]2\s*(?:minus|减)\s*[xy]1\s*(?:over|分之)\s*[xy]2\s*(?:minus|减)\s*[xy]1)|(?:\b[0-9]+\s+over\s+[0-9]+\s+[xy]\b)|(?:[0-9]+\s*分之\s*[0-9]+\s*[xy](?![A-Za-z]))|Delta\s*x\s*分之\s*Delta\s*y|\bDelta\s+y\s+over\s+Delta\s+x\b§“y2 minus y1 over x2 minus x1” → subtract y sub one from y sub two. Divide that difference by x sub two minus x sub one. “3分之2 x” → 三分之二乘以 x.§Check grouping against the source. A letter can belong in the denominator, and Chinese fraction order differs from English.
joined_tokens§Fused math words and operands§4§Fixed§(?<![A-Za-z])(?:negative|minus|plus|times|over|equals|to)(?=[0-9])|(?<![A-Za-z])(?:negative|minus|plus|times|equals)(?=[A-Za-z](?![A-Za-z]))§negative5 → negative five. negativea → negative a. “4 to6” → four to six, or “four to six” as a ratio once the surrounding construction establishes that meaning.§Safe to tokenize the observed word and operand in English math. Check the reading of “to” in the surrounding expression. Regex skips ordinary words such as “negative”.
signed_numbers§Raw signed number§4§Context§@signed§“太阳高度 -34 度” → 太阳高度为负三十四度. “changed by +16.8 percent” → increased by sixteen point eight percent, where the metric actually increased.§A sign can encode direction, a signed change, a time-zone offset or an ID. Some binary minus forms require a math parser.
stars_and_marks§Star or shorthand mark§4§Context§(?<![A-Za-z0-9])A\*|\*{1,3}|#[ \t]*[0-9]+|[✓✔✕✖✗✘]§Sagittarius A* → Sagittarius A star. 人马座 A* → 人马座 A 星. “#1 climate control” → the main factor controlling climate.§Asterisks can mark multiplication, footnotes or emphasis. Number sign can be rank, number or sharp.
absolute_value§Bars used as absolute value§4§Context§[|｜]\s*[^|｜\r\n]{1,36}\s*[|｜]§“|负5| 等于 5” → 负五的绝对值等于五. “|a|” → the absolute value of a.§Paired bars may denote a determinant, cardinality, norm or divisibility elsewhere. Apply a fixed expansion only after the expression type is known.
blank§Fill-in blank§4§Fixed§_{2,}|＿{2,}|□{2,}§“钠钾____消耗 ATP” → 钠钾，空格，消耗 A T P. In English say “blank” once for each answer slot.§Runs can be horizontal decoration or part of code. Restrict the expansion to exercise fields when metadata is available. A single underscore is handled separately.
single_character§Single letter or Han character§4§Context§@single§马 → 马，马匹的马. 骤 → 骤，步骤的骤. For a letter card use “the letter A” or “字母 A”.§A model may pronounce some single characters correctly. Use the lesson’s intended word or tone and preserve quiz design where the character is the prompt.
wrong_script§Clip entirely in the other script§4§Context§@wrong_script§For a Mandarin-track English label, speak an approved Chinese name or deliberately voice its English pronunciation. For a Chinese-only quotation on the English track, use a Mandarin segment or the approved English gloss.§This is a script heuristic. “kiwi”, a formula, a unit and a name do not identify the language by themselves.
plus§Plus between terms§4§Context§(?<=[A-Za-z0-9@HAN@)）])\s*[+＋]\s*(?=[A-Za-z0-9@HAN@(（])§“花药 + 花丝” → 雄蕊由花药和花丝组成. “color + white” → mix the color with white. “H2 + O2” in a reaction → hydrogen reacts with oxygen, with coefficients voiced where present.§Also hits true addition, UTC offsets and compound abbreviations. Replacing every plus with “and” can change meaning.
relations§Comparison, relation or signed operator glyph§4§Context§(?:[<>≤≥≠≈≃≡=＝＜＞±∓]|&(?:lt|gt|le|ge);)§“< 200 years” → less than two hundred years. Use 小于、约等于、正负 where the source distinguishes them. State open or closed bounds explicitly.§Angle brackets can be markup. An equals sign can be a bond or a label pairing.
binary_math§Raw multiplication, division or subtraction§4§Context§[×÷∙⋅]|(?<=[0-9@HAN@)）])\s*−\s*(?=[0-9A-Za-z@HAN@(（])|(?:[0-9]\s*度)\s+-\s*[0-9]|(?<=[0-9)])\s+-\s+(?=[0-9(])§“180 度 - 115 度” → 一百八十度减去一百一十五度. Say “multiplied by” or “divided by” with operand boundaries.§A dash can mark a range or prose aside. Preserve unary signs and mathematical scope.
power§Powers and superscript digits§4§Context§[0-9A-Za-zΑ-ω]\^[-+]?\s*(?:[0-9]+|[A-Za-z]|\([^)]+\))|[@SUP@]|(?:[-0-9a-z]\s*的\s*负?[0-9a-z]+\s*次方)|\b(?:to the power of|raised to)\s+(?:negative\s*)?[0-9a-z]§“2⁸” → two to the eighth power / 二的八次方. “Theta¹ Orionis C” → Theta one Orionis C, using the catalog reading.§Superscripts also represent star labels and footnotes. Damaged powers have their own class. Spoken “to the power of” can already be fine.
root§Roots and radical grouping§4§Context§[√∛∜]|\b(?:square|cube|nth) root of\b|(?:平方根|立方根|根号)\s*(?:[0-9A-Za-z(（])§“square root of 2” → the square root of two. For a sum say “the square root of the quantity …” and mark its ending when needed.§This includes already verbalized roots. Only group what was under the radical.
fraction§Fraction glyph or numeric fraction§4§Context§[¼½¾⅐-⅞]|(?<![0-9/])[0-9]+\s*/\s*[0-9]+(?![0-9/])|[0-9]+\s*分之\s*[0-9]+|\b[0-9]+\s+over\s+[0-9]+\b§“7½ minutes” → seven and a half minutes. “3分之2” → 三分之二. “6 over 36” → six thirty-sixths, or six divided by thirty-six where division is being taught.§Slash can mark calendar dates, ratios or a unit. Numeric verbal fractions may already work. Preserve whole-number parts and grouping.
math_group§Implicit multiplication, subscript or function grouping§4§Context§(?:[₀-₉ₐₑₒₓ]|(?<![A-Za-z0-9])[A-Za-z]_[A-Za-z0-9]+|\b(?:ln|log|sin|cos|tan)\s*[(（]|(?<![A-Za-z0-9])[0-9]+\s*[(（]\s*[0-9a-z]|(?<![A-Za-z0-9])[a-z][0-9](?![A-Za-z0-9])|[A-Za-z]\([\s\S]{1,20}?[)）])§“2(3x 加 1)” → 二乘以括号内三乘以 x 加一. “ln(m0 除以 m_f)” → the natural logarithm of the ratio of initial mass to final mass. “P(7)” → the probability of rolling a total of seven when that is the given event.§Parentheses can be coordinates, ordinary asides or a function call. Subscript-looking strings can be model numbers.
math_variable§Algebraic letters and juxtapositions§3§Context§(?<![A-Za-z0-9.])(?:[0-9]+\s*[xy](?![A-Za-z0-9])|(?:mx|kx|bh|lw|lh|wh|xy)(?![A-Za-z0-9])|[A-Za-z]\s*(?:加|减|乘|除以|等于|plus\b|minus\b|times\b|equals\b))§“y 等于 mx 加 b” → y 等于 m 乘以 x，再加 b. “3x plus 6” → three times x plus six.§Some letter strings are units, labels or acronyms. Equality can be used as a mnemonic, especially outside mathematics.
coordinates§Ordered pair, interval or point prime§4§Context§[（(\[]\s*@CV@\s*[,，]\s*@CV@\s*[)）\]]|(?<![A-Za-z0-9])[A-Z]['′]\s*[(（]§“B'(负1, 4)” → B 撇，坐标是负一、四. “(3, negative2)” → the point with x-coordinate three and y-coordinate negative two.§Parentheses may mark an open interval, a tuple or an aside. Preserve open and closed endpoints when the text describes an interval.
greek§Greek letters and delta shorthand§3§Context§[Α-Ωα-ωϕϵ]|\bDelta\s+[a-z]\b§Δv → change in velocity / 速度变化量. When the lesson names the symbol, say “delta v”. “λ” → lambda or 波长 lambda, when it means wavelength.§Greek letters can also be star labels, prefixes or constants. Distinguish μ as a variable from the micro unit prefix.
ratio_colon§Colon in ratio§3§Context§@ratio§“1 : 2 : 4” → one to two to four / 一比二比四. “octave 2:1” → an octave has a two-to-one frequency ratio.§Timestamp-like ratios can evade the cue filter. Colons in a year/value label or exercise numbering should get a pause instead.
number_dash§Numeric dash or tilde range§3§Context§@range§“5–6 million years” → five to six million years. “2015—2022 年” → 从二零一五年到二零二二年.§Inspect dates, scorelines, binned values, subtraction, labels and units before using “to”. In BCE, preserve date order and the era.
numeric_sequence§Hyphenated numeric sequence§3§Context§@chain§“3-4-5 triangle” → a triangle with sides of lengths three, four and five. “2-8-8 规律” → 三层电子数的上限依次是二、八、八.§A three-part sequence could be a date outside ISO format, phone number, code or subtraction.
iso_date§ISO calendar date§3§Fixed§@iso§“2026-11-18” → 二零二六年十一月十八日 / November eighteenth, twenty twenty-six.§Validated date shape. If a field is an identifier and happens to be a valid date, preserve its identifier reading.
clock_time§Clock time with context§3§Fixed§@clock§“19:57” → 十九点五十七分 / nineteen fifty-seven. “7:45” → seven forty-five. Preserve a.m./p.m. only when shown or entailed by the selected convention.§Only numbers with clock cues match. Ambiguous bare colons and UTC offsets are handled elsewhere.
utc§UTC abbreviations and offsets§4§Fixed§(?<![A-Za-z])UTC\s*(?:(?:[+＋\-−]|加|减|plus\b|minus\b)\s*[0-9]{1,2}(?::[0-9]{2})?)?(?![A-Za-z])§“UTC+5:30” → coordinated universal time plus five hours and thirty minutes / 协调世界时加五小时三十分. “UTC减4” → 协调世界时减四小时.§Expand within a time-zone template. Do not read a UTC offset as a local time or add an unstated direction.
clock_or_ratio§Unresolved numeric colon§2§Context§(?<![0-9])(?:[0-9]{1,3}[ \t]*[:：][ \t]*[0-9]+)(?![0-9])§“7:45” can be seven forty-five in a school schedule. “2 : 1 ratio” is a two-to-one ratio. In “Fiscal 2021: 5.3 million” pause at the label boundary.§Broad fallback includes known clocks, ratios, offsets and a few label/quantity boundaries. Use higher-specificity matches first.
years§Historical year, date, decade or century§2§Context§(?:公元前?\s*[0-9]+|[0-9]{1,4}\s*年\s*[0-9]{1,2}\s*月(?:\s*[0-9]{1,2}\s*[日号])?|(?<![0-9])[0-9]{3,4}\s*年|[0-9]{1,2}\s*世纪|[0-9]{2}\s*年代|\b(?:[0-9]{1,4}\s*(?:BCE|CE|BC|AD)|(?:BCE|CE|BC|AD)\s*[0-9]{1,4}|(?:1[0-9]{3}|20[0-9]{2})(?:s)?|[0-9]{1,2}(?:st|nd|rd|th)\s+century)\b|(?i:\b(?:@MONTH@)\.?\s+[0-9]{1,2}(?:st|nd|rd|th)?(?:,?\s+[0-9]{4})?\b)|(?i:\b[0-9]{1,2}\s+(?:@MONTH@)\b))§“1848年” → 一八四八年. “551–479 BCE” → from five hundred fifty-one to four hundred seventy-nine before the Common Era. “the 1800s” → the eighteen hundreds.§Bare four-digit English numbers can be quantities or IDs. A number plus 年 can be a duration. Year convention differs from cardinal reading.
durations§Compact duration or short time unit§2§Context§(?:[0-9]+\s*(?:小时|分钟|分|秒)\s*[0-9]+\s*(?:分钟|分|秒)|(?<![A-Za-z0-9])@NUM@\s*(?:h|hr|hrs|min|ms|s)(?![A-Za-z0-9/])|\b[0-9]+\s*(?:hours?|minutes?)\s+[0-9]+\s*(?:minutes?|seconds?)\b|\b[0-9]+\s*(?:a\.m\.|p\.m\.|am\b|pm\b))§“8 分 20 秒” → 八分二十秒. “24 hours 50 minutes” → twenty-four hours and fifty minutes. “45 min” → forty-five minutes.§s may be a variable, h a height, and 分 may be a score or angle minute. Some durations are already fluent.
decimal§Decimal and precision§2§Context§(?<![A-Za-z0-9])(?:[0-9]+\.[0-9]+|\.[0-9]+)(?![A-Za-z0-9])§“1.06” → one point zero six / 一点零六. “38.0” → thirty-eight point zero / 三十八点零 if precision is pedagogically relevant.§Decimals in coordinates, prices, version numbers and scientific notation need their own reading rules. Ordinary decimals may already be clear.
grouped_numeric§Grouped digits and large-number scale§3§Context§(?<![0-9.,])[0-9]{1,3}(?:,[0-9]{3})+(?![0-9])|(?<![0-9.,])[0-9]{5,}(?![0-9])|[0-9]+(?:\.[0-9]+)?\s*(?:万亿|亿|万)|(?i:\b@NUM@\s+(?:million|billion|trillion)\b)§“384,400 千米” → 三十八万四千四百千米. “5.3 million” → five point three million. Keep the correct scale, such as a hundred million for 亿.§Long strings can be IDs. A comma can divide coordinates or list values if written without a space. Already spoken magnitudes are audit candidates.
scientific§Scientific notation and exponent base§4§Context§@NUM@\s*(?:[×x·]\s*10\s*(?:\^[-+]?[0-9]+|[@SUP@]+)|[eE][+-][0-9]+)|(?:乘以?\s*10\s*(?:的|平方)|\btimes 10 (?:to the power of|squared|cubed))|10\s*(?:squared|的平方)\s*[@SUP@]§“8 times 10 to the power of 5 km” → eight times ten to the fifth power kilometers. Pause so kilometers applies to the complete quantity.§Includes readable versions. Corrupt exponent matches must be resolved first. The letter x can be a variable.
unit_symbol§Abbreviated measurement unit§3§Fixed§(?<![A-Za-z0-9])@NUM@\s*(?:@UNIT@)(?![A-Za-z0-9])§“500 m” → five hundred meters / 五百米. “3 GHz” → three gigahertz / 三吉赫兹. “1.06 g” → one point zero six grams / 一点零六克.§Use a case-sensitive unit dictionary in measured fields, plus English number agreement. m, g, N and u can be variables, mass units or labels. Do not expand ambiguous tokens globally.
rate§Slash unit or density§4§Fixed§(?<![A-Za-z])(?:km|cm|mm|mi|ft|m|kg|mg|g|N|r|人|次|克|千米|公里|米)\s*[/／]\s*(?:square\s+kilometers?|cubic\s+centimeters?|立方厘米|平方千米|平方公里|厘米\s*的立方|千米|小时|分钟|秒|时|毫升|km|kg|cm[²³23]?|m[²³23]|s|h|min|L|mL)(?![A-Za-z0-9])§“7.7 千米/秒” → 每秒七点七千米. “0.79 g/ cubic centimeters” → zero point seven nine grams per cubic centimeter. “3923 人/平方千米” → 每平方千米三千九百二十三人.§Use a whitelist of compound units and require quantity/lesson context for ambiguous short units. Preserve dimensions and say “per” for the denominator.
area_volume_unit§Squared/cubed unit or malformed unit§4§Fixed§(?:[0-9]\s*(?:km|cm|mm|m|ft)[²³23](?![0-9])|(?:厘米|千米|米|英尺)\s*的\s*(?:平方|立方)|(?:km|cm|m|ft)\s*\^\s*[23]\b|\b(?:square|cubic) (?:meters?|centimeters?|kilometers?|feet)\b|(?:平方|立方)(?:毫米|厘米|千米|公里|米))§“克/厘米 的立方” → 每立方厘米多少克, with the measured value supplied. “10 cm²” → ten square centimeters / 十平方厘米.§Common fully verbalized units are included. Do not force a unit interpretation in algebra or in an object identifier.
temperature§Temperature scale symbols§4§Fixed§[℃℉]|°\s*[CF](?![A-Za-z])|度\s+[CF](?![A-Za-z])§“-4 °C” → negative four degrees Celsius / 零下四摄氏度. “负4 度 C” → 零下四摄氏度.§Bare ° can be an angle. F and C can be direction or point labels. Keep the scale only where known.
degree_geo§Degree, latitude/longitude or bearing§3§Fixed§[-−]?[0-9]+(?:\.[0-9]+)?\s*°(?!\s*[CF]\b)(?:\s*[NSEW]\b)?|(?:北纬|南纬|东经|西经|纬度|经度|方位角)\s*[-−]?\s*@NUM@\s*度§“45.6°N, 150.7°W” → forty-five point six degrees north, one hundred fifty point seven degrees west. “北纬 38.0 度” → 北纬三十八点零度.§Fixed in a coordinate/bearing field. Bare degrees may be temperature, angle or solar altitude. Match directional suffixes before handling generic degrees.
angular_prime§Angular minute and second primes§4§Fixed§[′″]|[0-9]\s*°\s*[0-9]+\s*['"]§“33°42′” → thirty-three degrees, forty-two arcminutes. “0.768″” → zero point seven six eight arcseconds. “33 度 42′” → 三十三度四十二分.§Same primes can mean feet/inches, arc units or transformed points. Fixed only for known angular fields.
percent§Percent, permille and spoken-percent artifact§3§Fixed§[%％‰‱]|百分之\s*[0-9]+|\b[0-9]+(?:\.[0-9]+)?\s+percent\b§“百分之0.0084” → 百分之零点零零八四. “月球被照亮 百分之66” → 月球受光面积占百分之六十六. “5‰” → five per thousand / 千分之五.§Already verbalized percentages are candidates. Keep percent changes distinct from percentage points and per mille. Some Mandarin sentences need sentence-level agreement.
currency§Money and currency signs§3§Fixed§[$¥￥€£₹]\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|\b(?:USD|CNY|RMB|EUR|GBP)\s*@NUM@|\b@NUM@\s*(?:USD|CNY|RMB|EUR|GBP)\b§“$1.87” → one dollar and eighty-seven cents. “$2.1 billion” → two point one billion dollars.§Identify currency from the field or lesson. A dollar sign or yen/yuan glyph is not globally unambiguous. Handle scale words before splitting cents.
chem_ion§Chemical ion or signed charge§4§Fixed§(?<![A-Za-z0-9])(?:H|OH|Na|Cl|NH[4₄]|Ca|Mg|Fe|K|Cu|SO[4₄]|O|NO[3₃]|HCO[3₃])(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]|[0-9]*[+-](?!\s*[A-Za-z0-9]))§Na⁺ → sodium ion / 钠离子. OH⁻ → hydroxide ion / 氢氧根离子. In lessons on charge, add “with a single negative charge” or “带一个单位的负电荷”.§Use a case-sensitive formula and charge dictionary in chemistry context. Plus or minus can connect operands and can be part of a grade.
chem_formula§Chemical formula and coefficients§4§Context§(?<![A-Za-z0-9])(?:(?:H[2₂]O[2₂]?|CO[2₂]|O[2₂]|N[2₂]|H[2₂]|Cl[2₂]|CH[4₄]|NH[3₃]|NaCl|HCl|NaOH|H[2₂]SO[4₄]|CaCO[3₃]|NaHCO[3₃]|C[6₆]H(?:12|₁₂)O[6₆]|Fe[2₂]O[3₃])|(?:[A-Z][a-z]?[0-9₀-₉]*){2,}[₀-₉]+)(?![A-Za-z0-9])§H2O → water / 水 when naming the substance, or “H two O” to teach notation. “2 H2 + 1 O2” → two hydrogen molecules react with one oxygen molecule when describing that step.§A token can be an ID. Distinguish coefficients, subscripts and names. The formula list covers observed common compounds and future canonical patterns.
chem_bond§Bond or base-pair dash§4§Context§(?<![A-Za-z0-9])(?:[ATUCG]\s*[–−-]\s*[ATUCG]|[HONC]\s*[–=≡-]\s*[HONC])(?![A-Za-z0-9])§“G–C pair” → a guanine–cytosine pair / 鸟嘌呤与胞嘧啶配对. “H–H 键” → 两个氢原子之间的单键.§A–B could be generic labels. Decide from lesson context whether a dash expresses a pair, bond or span.
arrow§Arrow, progression or reaction glyph§4§Context§[←→↔↑↓↗↘⇒⇌⇄⟶⟷➜]|(?:->|<-|=>|<=>)§In a reaction say “yields” / “生成”. In a derivation say “therefore” / “因此”. Read reversible arrows as two-way where the source makes that claim.§No observed arrows may mean the export strips them, as shown by the missing-relation class. Arrow direction and purpose cannot be guessed from the glyph alone.
slash§General slash with uncertain meaning§3§Context§[/／\\]§“鼻/口” → 鼻子或嘴巴. “swells/bursts” → swells and may burst. For measurements, “km/h” → kilometers per hour.§Also hits URLs, fractions, chemical alternatives, bilingual glosses and duplicate units. Use those specific parses first.
bar§Bar separators outside confirmed absolute value§3§Context§[|｜¦]§If used between UI fields, insert a short pause or connective phrase. If it marks absolute value, speak the full mathematical relation.§Includes the observed absolute-value bars. Boolean OR, divisibility and layout separators have different readings.
middot§Middle dot in separated fields, names or products§3§Context§[·・•‧]§“北半球 · 西半球” → 位于北半球和西半球. “卡尔·冯·弗里希” → speak the name continuously. “1.4·n·log2n” → 一点四乘以 n，再乘以以二为底的 n 的对数.§A middle dot may also be a decimal marker or a bullet. Separate name handling from field and multiplication handling.
template_join§Missing pause between generated fields§4§Fixed§(?<![。.!！?？:：])(?:[A-Za-z0-9°）)@HAN@])\s+(?:(?:This zone|Planets above the horizon|On this sky map)\b|这个时区|地平线以上的行星|这张星图)§“加拿大 这个时区比 UTC 晚” → 加拿大。这个时区比协调世界时晚. “Canada This zone is …” → Canada. This time zone is …§Insert the missing boundary in the identified field template. Generic letter-plus-space detection would damage normal sentences.
spaced_stop§Space before punctuation§2§Fixed§[ \t]+(?=[。．.!！?？，,、：:；;])§“7.5 。” → “7.5。” and speak “七点五”. “equals 12 .” → “equals 12.”§Strip for confirmed punctuation boundaries. A space before a decimal-leading dot, an ellipsis or a teaching example can be intentional.
duplicate_marks§Repeated or conflicting punctuation§2§Fixed§@punct§“焦耳，J，,1 J” → “焦耳，字母 J。一个焦耳……” where the source has two statements. Collapse accidental duplicate sentence stops in prose.§Constructs such as “?!” and intentional ASCII ellipses need their own handling. Mixed separators can indicate a lost sentence boundary, so choose the surviving mark using the template.
ellipsis§Ellipsis or continuation§2§Context§…|⋯|\.{3,}§“1, 2, 4, 8 …” → one, two, four, eight, and so on. A trailing literary ellipsis should usually become a deliberate pause.§An ellipsis can mean an omission, a series, suspense or a placeholder. Preserve quotations when exact wording is required.
dash§Prose dash or dash-joined term§2§Context§—+|(?<=[A-Za-z@HAN@])–(?=[A-Za-z@HAN@])|[ \t]–[ \t]§“没养宠物——可……” → use a pause and keep the conjunction, or use a sentence break. “Earth–Sun distance” → the distance from Earth to the Sun.§The pattern also hits names, ranges, objects and chemical bonds. Normal punctuation may already read well.
quotes§Quoted term or title with explicit boundaries§1§Context§“[^”]+”|‘[^’]+’|《[^》]+》|「[^」]+」|『[^』]+』|"[^"\r\n]{2,}"§“《记承天寺夜游》” → “苏轼的《记承天寺夜游》” with a title pause or title cue. Keep contrastive terms distinct in “blue-green”, “green-blue”.§Includes in-line quotations already supported by TTS. Quotation marks signal boundaries but need no spoken “quote” in ordinary narration.
parentheses§Parenthetical or bracketed aside§1§Context§[（(][^）)\r\n]{2,}[）)]|[【\[][^\]】\r\n]+[\]】]§“oxidation (a reaction with oxygen)” can be voiced “oxidation, which is a reaction with oxygen”. For “110 米（120 码）” say “一百一十米，约合一百二十码”.§A parenthesis may carry a unit conversion, formula grouping, coordinate or translation. Preserve grouping and avoid saying punctuation by default.
unbalanced§Mismatched delimiter§3§Context§@unbalanced§Verify the intended span, then close the correct quote/bracket or recast the sentence to make grouping explicit.§Outer delimiters can deliberately open in one clip and close in another. Halfwidth/fullwidth pairs can be visually equivalent.
list_marker§Enumeration and list markers§3§Context§(?:^|[。.!?！？]\s+|[；;：:]\s*|\n)\s*(?:[1-9][0-9]?[.)）](?![0-9])|[一二三四五六七八九十]+、|[（(][1-9][0-9]?[)）]|[①-⑳]|[-•]\s+)|(?:^|\s)[A-D][.)）]\s+(?=[A-Z@HAN@])§“1. Ribosome builds it: … 2. Inside the ER: …” → “Step one. A ribosome builds the protein. Step two. It enters the E R.”§Digits may start sentences that are not list items. A. can be an initial, and “一、” can occur in a quotation.
ordinal§Numeric ordinal and rank§2§Fixed§(?<![A-Za-z0-9])[0-9]+(?:st|nd|rd|th)(?![A-Za-z0-9])|第\s*[0-9]+§“5th” → fifth. “第 48 名” → 第四十八名. In a date, use the chosen date-reading style.§Some ordinals are product or military unit names. Expanding digits is safe inside a known ordinal field. Preserve the name and context.
roman§Roman numeral candidate§3§Context§(?<![A-Za-z0-9])[IVXLCDM]{2,6}(?![A-Za-z0-9])|[Ⅰ-Ⅼ]|\b(?:quadrants?|World War|Act|Part|Chapter|Type)\s+[IVX]\b§World War II → World War Two. Louis XIV → Louis the Fourteenth. Apple II → Apple Two. “quadrants I to IV” → quadrants one through four.§IV and CD can be abbreviations. A numeral can be read as an ordinal, cardinal or letters according to the name.
dotted_abbrev§Dotted abbreviation or shortened title§3§Context§(?:(?<![A-Za-z])(?:[A-Za-z]\.){2,}|\b(?:Dr|Mr|Mrs|Ms|St|Mt|Jr|Sr|vs|etc|c)\.)§“e.g.” → “for example”. “St. John’s” → Saint John’s. “Washington, D.C.” → Washington, D C. “R.E.M.” → R E M.§St. can mean Saint or Street. c. can signal circa. Protect these periods before sentence splitting.
acronym§Acronym or letter-by-letter sequence§3§Context§(?<![A-Za-z0-9])(?:[A-Z]{2,}|[A-Z](?:[ \t]+[A-Z]){1,}|pH|mRNA|tRNA|rRNA)(?![A-Za-z0-9])§“pH 8.3” → p H eight point three / p H 八点三. DNA → D N A or 脱氧核糖核酸 when appropriate. NASA and NATO use their customary pronunciations.§Caps include emphasis and chemical strings, and spaced letters can be variables or music notes. Approved acronym readings can be dictionary-driven.
caps_emphasis§All-caps emphasis in English prose§2§Fixed§@emphasis§“the solution OUTSIDE” → “the solution outside”, with stress on outside if desired. “4 hours BEHIND UTC” → “four hours behind UTC”.§Uppercase on these common words can trigger spelling or exaggerated stress. Confirm the token is an ordinary word before lowercasing.
mixed_script§Han/Latin code switch§3§Context§@mixed§“文房四宝：笔、墨、纸、砚” can be a separately voiced Mandarin segment inside the English paragraph, or use “brush, ink, paper and inkstone” when the Chinese words are unnecessary. “Columbia 县” → use the approved Mandarin place-name reading or an English name segment plus 县.§This catches true bilingual text plus math, unit and acronym switches. A mixed-script hit does not establish a pronunciation failure.
pinyin§Pinyin, phonetic notation or detached reading hint§4§Context§@pinyin§“龟兹（读 cí）” → pronounce 龟兹 as Qiūcí, then omit the inline hint unless teaching it. “高尔基体’ěrjītǐ” → speak 高尔基体 smoothly. “行省 xíngshěng” → pronounce xíngshěng intentionally in a Mandarin segment.§Some Latin diacritics belong to foreign names. A detached hint can be a fragment of a full reading. Preserve intentional pinyin instruction.
diacritics§Latin name or word with diacritics§2§Context§[À-ÖØ-öø-ÿĀ-žǍ-ǔǖ-ǜʻ]§“Reykjavík” → use the approved pronunciation of Reykjavík. “Guð…” and transliterated names need a pronunciation lexicon, with language and named sense when applicable.§Some English loans already read well. This overlaps pinyin and excludes transliterations spelled entirely in ASCII.
polyphonic_zh§Mandarin polyphonic phrase watchlist§4§Context§龟兹|朝歌|行省|银行|行走|执行|重庆|重阳|重量|重心|重新|重复|长安|长乐|长城|长江|长大|成长|等长|西藏|宝藏|藏在|音乐|乐器|乐山|单于|尉迟|参差|参见|漂白|漂亮|湖泊|停泊|迫降|投降|降落|看守|出没|模样|模型|结实|打结|中弹|命中|划船|计划|得了|为了|数一数|数不清|乘车|千乘|咽喉|咽下|呜咽|血液|鲜血|殷墟|燕国|燕子|燕然|柏林|吐蕃|番禺|蚌埠|六安|厦门|秘鲁|华山|济南|济宁|宿迁|星宿|蒭藁|怒号|阴风怒号|颠沛|薄暮|单薄|系住|关系|数学|数轴|转身|转圈|转动|勒石|勒紧§“行省” → xíngshěng. “朝歌” → Zhāogē. “西藏” → Xīzàng. “阴风怒号” → yīnfēng nùháo. Use a pronunciation lexicon or controlled paraphrase and listen to the result.§Auditable phrase watchlist. Several common senses are low risk and will read correctly. Unlisted words and senses still require linguistic review.
homograph_en§English pronunciation depends on sense§3§Context§(?i:\b(?:lead|leads|live|lives|read|reads|record|records|close|wind|winds|wound|bow|bows|bass|minute|content|object|produce|conduct|present|project|tear|desert|row|use|does)\b)|\bPolish\b§“lead” as a metal → /lɛd/, or “the metal lead”. “wind” as moving air → /wɪnd/. “read” in the past tense → /rɛd/, or recast with “had read” where grammatical.§A watchlist hit is a review candidate. Most are ordinary occurrences whose surrounding syntax may already resolve the pronunciation.
identifier§Catalog, model, road or alphanumeric label§3§Context§(?<![A-Za-z0-9])(?:(?:[A-Z]{1,8}-)+(?:[A-Za-z]*[0-9][A-Za-z0-9-]*|[a-z][0-9][A-Za-z0-9-]*)|(?:HIP|HD|NGC|IC|GJ|TOI|CFC|DDT|I|U|F|B|M|L)\s?[0-9]{1,8}[a-z]?(?![A-Za-z0-9])|[A-Za-z]{1,10}[0-9]{2,}[A-Za-z][0-9A-Za-z]*)|开普勒[-–][0-9]+[a-z]?§“HIP 59774” → H I P, five nine seven seven four. “开普勒-452b” → 开普勒四五二 B. Confirm a catalog’s conventional grouping before using it.§Matches can include unit or math tokens, laptop names or flight names. Do not blindly treat hyphens as “minus”.
note§Musical note, octave or clef symbol§4§Context§[𝄞𝄢𝄡♪♫♩♬♭♯♮]|(?<![A-Za-z0-9])[A-G][#♯♭b]?[0-8](?![A-Za-z0-9])|\b[A-G]\s+[A-G]\s+[A-G]\b§“高音谱号 𝄞 绕着 G4” → 高音谱号绕着第四组的 G 音所在的线. “C D E F G” → “C, D, E, F and G”, with a short pause between notes.§A–G with a digit can be a grid label, highway, abbreviation or algebraic variable. Clef names already present may only need the decorative glyph omitted.
url§URL, protocol or email§4§Context§@CODE@§“https://” → say “H T T P S” when teaching the secure protocol. If an address itself is required, speak the domain with “dot” / “点” and spell ambiguous parts.§Read verbatim structure only when students need to reproduce it. Keep URLs out of ordinary prose where the site can show them.
pictograph§Emoji or other pictographic symbol§3§Context§@pictograph§Speak the meaning if it carries information, such as “warning” or “correct”. In “高音谱号 𝄞”, use the clef name and omit a redundant glyph.§Unicode range heuristic includes some UI ornamentation and misses some composite sequences. Music clefs are caught by the note class.
visible_control§Invisible control or format character§3§Fixed§@control§Normalize unexpected zero-width spaces or embedded markers at confirmed word boundaries before submission.§Some controls encode bidi, accessibility, spelling or grapheme structure. Preserve relevant content and avoid removing a meaningful separator blindly.
short_label§Very short label or response§2§Context§@short§“细胞质。” → “细胞质，细胞内部的物质。” if a definition belongs in the exercise. “vacuole.” → “The vacuole.” For names, use a brief approved carrier phrase if playback clips the name.§Short place names and vocabulary cards can already sound fine. Keep answer-only items short and avoid giving away a response.
term_card§Full stops between heading and brief gloss§2§Context§@card§“立冬。冬季开始。” → “立冬，表示冬季开始。” “Electron shell. Energy levels where electrons are found.” → “Electron shells are the energy levels where electrons are found.”§Common within lesson cards. May match two complete sentences. Avoid merging actual dialogue turns or steps.
fragment_end§Clip ends at phrase punctuation§2§Context§[,，:：;；—–]\s*$§“浮光跃金，静影沉璧，” → finish with the intended short pause, or join it to the next phrase when the interface allows uninterrupted playback.§Classical reading exercises can intentionally end mid-sentence. Do not rewrite a source quotation to replace its punctuation.
no_spoken_text§Empty or punctuation-only request§4§Fixed§\A[^\w]*\Z§Skip synthesis for an empty UI-only item. If a symbol or blank is the actual prompt, substitute the spoken label.§Punctuation-only prompts can represent meaningful signs. A symbol that will be voiced belongs in its specific class too.
"""

# Additional patterns target pronunciation choices that need a local lexicon,
# plus lower-frequency notation that may appear in future publishes.
RULES += r"""
symbolic_label§Isolated letter in subject notation§3§Context§(?<![A-Za-z0-9])(?:[A-Za-z]\s*(?:轴|点|键|基因|型|级|调|音)|(?:点|字母|基因|选项)\s*[A-Z](?![A-Za-z0-9])|[xy]\s+-\s*axis|\b(?:[A-Z] value|(?:gene|allele|point) [A-Z])\b)§“跟着 B(4, 1) 看” where B is a point → 观察 B 点，坐标是四、一. “x -axis” → the x axis. For “A 基因” say “字母 A 所代表的基因” when distinguishing the label matters.§Sometimes the letter is part of an abbreviation or a notation students must hear exactly. Verify the subject’s conventional pronunciation.
element_symbol§Chemical element symbol with local cue§3§Context§(?:元素符号|元素|原子)\s*[（(]?\s*(?:@ELEMENT@)(?![A-Za-z0-9])|(?<![A-Za-z0-9])(?:@ELEMENT@)(?:\s*(?:原子|元素)|\s+atoms?\b)|(?i:\b(?:symbol(?: for)?|atoms? of)\s+)(?:@ELEMENT@)(?![A-Za-z0-9])|(?:[0-9]+\s*个\s*(?:@ELEMENT@)[、，]|(?i:\b(?:Count|each side):\s*)[0-9]+\s+(?:@ELEMENT@)\s+(?:and|on)\b)§“4 H and 2 O atoms” → four hydrogen atoms and two oxygen atoms. When teaching the symbol, say “hydrogen, symbol H”.§Some symbols may be coordinates or exercise variables. The regex uses an element allowlist. Distinguish a letter label from the name of the element.
isotope§Isotope mass number§3§Fixed§(?:碳|铀|氢|氦|氧|铯|钴)\s*[-–]\s*[0-9]{1,3}|(?i:\b(?:carbon|uranium|hydrogen|helium|oxygen|cesium|cobalt)[-–][0-9]{1,3}\b)|[@SUP@]+[A-Z][a-z]?(?![A-Za-z0-9])§“碳-14 测定” → 碳十四测定. “carbon-14” → carbon fourteen.§Fixed for confirmed isotope names. A superscript before a capital also occurs in labels, so validate the element and context.
direction_tokens§Compass abbreviation without a degree suffix§3§Fixed§(?<![A-Za-z])(?:in the|to the|from the|[Uu]p in the)\s+(?:NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW|NE|NW|SE|SW|N|E|S|W)\b|(?<![A-Za-z])(?:NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW|NE|NW|SE|SW|N|E|S|W)\s+[0-9]{1,3}°§“up in the W” → above the western horizon. “NW 33°” → northwest, thirty-three degrees above the horizon if the value expresses altitude.§N can be a force unit and W can be a unit or a name initial. Apply direction expansions in the sky/compass template.
proper_names§Transliterated or specialized names on a pronunciation watchlist§3§Context§(?i:\b(?:Xiongnu|Xianbei|Qomolangma|Qaidam|Qin|Qinghai|Dujiangyan|Wuzhishan|Tsiolkovsky|Pleiades|Oort|Kuiper|Ocmulgee|Chattahoochee|Oconee|Etowah|Yazoo|Keweenaw|Xiaogang|Qufu|Qu Yuan|Zhang Qian|Shanhaiguan|Chicxulub|Aldebaran)\b)|克孜尔|蒭藁增二|乞力马扎罗|基奥尔科夫斯基|齐奥尔科夫斯基|可汗|大宛|月氏|阏氏§Approve the name-specific pronunciation. E.g. “Kuiper” as KYE-per, “Pleiades” as PLEE-uh-deez, and “大宛” as Dàyuān in the relevant historical passage.§A proper name may already sound right, and alternative pronunciations can be valid. The explicit watchlist is not a complete name inventory.
text_literal§Language example or spelling being mentioned§3§Context§(?i:\b(?:prefix|suffix|root word|cognate|homophone|pronounced|sounds like|spelled|the letter|the word)\b)|读作|读音|这个字|拼写|词根|词缀§“the prefix re-” → the prefix R E, meaning again, if spelling the prefix is central. If a lesson names a character’s pronunciation, use a reviewed pronunciation sample for that character.§Many hits already read fluently. Preserve the exact example and avoid substituting its definition where students need to hear its sounds.
verbal_glue§Flattened sentence connectors around normalized math§3§Context§(?:[。.!?]\s*|^)(?:[A-Za-z@HAN@ ]{1,20})(?:\s等于\s|\sequals\s)(?=[A-Za-z@HAN@][A-Za-z@HAN@ ]{2,}(?:\s*[+,;，。]))§“岩石圈 等于 地壳 + 上地幔顶部” → 岩石圈由地壳和上地幔顶部组成. When “equals” introduces a mnemonic or title, use a natural connective that conveys the same relationship.§Includes literal equations and some partly rewritten prose. Do not replace “equals” in a formal equality unless the replacement preserves it.
programming§Code-like inline construction§3§Context§\b(?:O\s*\(\s*n[^)]{0,24}\)|log[0-9]+[a-z]|\w+_\w+|[A-Za-z]0[xX][0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|[0-9][01]{5,}\s*(?:binary|二进制))\b|O\(n[^)]{0,24}\)§“O(n log n)” → big O of n log n. “log2n” in the sorting example → the base-two logarithm of n. “v_end” → final velocity or v sub end, depending on the instructional goal.§Underscores can mark subscripts instead of code. Spell source characters only if the lesson teaches what to type.
arrow_source_gap§Arrow removed between display and narration§3§Context§@arrow_diff§“2 water molecules, 2 H2 + 1 O2” → two water molecules split to form two hydrogen molecules and one oxygen molecule. “A, D, B, E…” in a letter-mapping exercise → A maps to D, B maps to E, and so on.§Some arrows were safely replaced by a sentence or natural pause. The difference counts removals, and a reviewer decides whether a relation or sequence must be restored.
repeat_decimal§Repeating-decimal notation flattened§5§Context§(?:repeat(?:s|ing)?|循环小数)\s*[（(][^）)\r\n]{0,80}(?:equals|等于)\s*[0-9]+\.[0-9]{3,}§“1 over 7 equals 0.142857” in the repeating-decimal example → one seventh equals zero point one four two eight five seven, with those six digits repeating. Mandarin → 七分之一等于零点一四二八五七，这六位数字不断循环。§A rounded or finite decimal is different. Confirm which digits repeat against the source and preserve the distinction.
"""


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    severity: int
    handling: str
    detect: Callable[[Clip], Optional[tuple[int, int]]]
    detection: dict
    reading: str
    risk: str


def rules():
    ids = set()
    for line in filter(str.strip, RULES.splitlines()):
        rule_id, name, severity, handling, detector, reading, risk = line.split("§")
        if rule_id in ids:
            raise ValueError(f"Duplicate class ID: {rule_id}")
        ids.add(rule_id)
        if detector.startswith("@") and detector[1:] in CUSTOM:
            detect, description = CUSTOM[detector[1:]]
            detection = {"kind": "logic", "function": detect.__name__, "rule": description}
        else:
            pattern = re.compile(expand(detector))
            # Bind this compiled pattern to its rule, rather than closing over the loop variable.
            def detect(clip, compiled=pattern):
                match = compiled.search(clip.send)
                return match.span() if match else None

            detection = {"kind": "regex", "engine": "Python re", "pattern": pattern.pattern}
        yield Rule(rule_id, name, int(severity), handling, detect, detection, reading, risk)


def read_transcripts():
    directory = ROOT / "transcripts"
    if directory.resolve() != directory:
        raise ValueError(f"Transcript directory resolves outside its expected path: {directory}")
    files = sorted(directory.glob("*.json"))
    if not files:
        raise ValueError(f"No JSON files in {directory}")
    clips = []
    lesson_ids = set()
    keys = set()
    skipped = []
    for path in files:
        if path.resolve() != path:
            raise ValueError(f"Transcript path resolves outside its expected path: {path}")
        record = json.loads(path.read_text(encoding="utf-8-sig"))
        if path.name == "index.json" and isinstance(record, dict) and "clips" not in record:
            if not isinstance(record.get("lessons"), list):
                raise ValueError(f"Malformed index in {path}")
            skipped.append(path.name)
            continue
        if not isinstance(record, dict) or not isinstance(record.get("clips"), list):
            raise ValueError(f"Expected lesson record with clips in {path}")
        lesson = record.get("id")
        if not isinstance(lesson, str) or not lesson or lesson in lesson_ids:
            raise ValueError(f"Missing or duplicate lesson ID {lesson!r} in {path}")
        lesson_ids.add(lesson)
        for row in record["clips"]:
            if not isinstance(row, dict):
                raise ValueError(f"Expected a clip object in {path}: {row!r}")
            lang, key, send, display = (row.get(field) for field in ("lang", "key", "send", "text"))
            if lang not in LANGUAGES or not isinstance(key, str) or not key:
                raise ValueError(f"Invalid clip identity in {path}: {(lang, key)!r}")
            if not isinstance(send, str) or not isinstance(display, str):
                raise ValueError(f"Expected string send and text fields in {path}: {(lang, key)!r}")
            identity = (lesson, lang, key)
            if identity in keys:
                raise ValueError(f"Duplicate clip identity in {path}: {identity!r}")
            keys.add(identity)
            clips.append(Clip(*identity, send, display))
    return files, lesson_ids, clips, skipped


def counts(clips):
    return {"clips": len(clips), "lessons": len({clip.lesson for clip in clips})}


def counts_by_language(clips):
    return {lang: counts([clip for clip in clips if clip.lang == lang]) for lang in LANGUAGES}


def snippet(clip, match_span, limit=156):
    # Keep enough local context on both sides of a match. For whole-clip
    # matches, show the start of the request.
    s = clip.send
    start, _ = match_span
    if len(s) <= limit:
        return s, False
    start = max(0, min(start - 40, len(s) - limit))
    end = start + limit
    value = ("…" if start else "") + s[start:end] + ("…" if end < len(s) else "")
    return value, True


PREFERRED_KEYS = {
    "corrupt_exponent": ("e4cae1fa", "a07c0cd8", "6401a64e", "095aafc6"),
    "lost_relation": ("7188d0f6", "0bee50ab", "b451d8c6", "eb0314ac", "305a540e"),
    "arrow_source_gap": ("eb0314ac", "7188d0f6", "43aa993e", "c3d06dfb", "c18423c8"),
    "lost_math_scope": ("9b4f639d", "d61950e9", "718cec80", "30c0d499"),
    "length": ("1bf74c57", "fe38e0d4", "f0c7f057", "cb81d9ca", "e296885c"),
    "joined_tokens": ("d463eb2b", "794fcba8", "74250628"),
    "signed_numbers": ("05a3adf1", "30c6b2d9", "fed3c817"),
    "term_card": ("73b4765e", "40f843c2", "2037d1aa", "9d89dd0d"),
    "math_group": ("8ce9900c", "639c8e48", "e4af34a8", "feee2224"),
    "fraction": ("557bd85b", "70161592", "378a3dad", "1fb4fc80"),
    "polyphonic_zh": ("9b2f1b9c", "f42c004d", "e5147749", "2d0664a6"),
    "single_character": ("4f373ead",),
    "pinyin": ("066a7390", "9b2f1b9c", "f42c004d", "2d0664a6", "1023c07b"),
    "number_dash": ("ec6cbf02", "9aa23cd2"),
    "binary_math": ("f204dcbc",),
    "template_join": ("8959e4b0", "b8a63ad4"),
    "temperature": ("94e41fa0",),
    "note": ("90fa16bf", "75d56b2f"),
    "rate": ("b801a4f7", "ffba656a", "f596cdf0", "f8c44ff0"),
    "roman": ("0012b614", "267b4567", "6bad617f", "06499546"),
    "programming": ("3038d644", "8ebf16ef", "9a44a9aa"),
    "identifier": ("d8aa0ba0", "91b95507", "57ddfec8"),
    "unit_symbol": ("a5954471", "ffba656a", "c5b172d4"),
    "dotted_abbrev": ("3aa96199", "56afbc0c"),
    "quotes": ("8f4a6c0e",),
    "blank": ("404470e3",),
    "degree_geo": ("9a00d032", "35200f3f"),
}


def examples(rule, matches):
    if len(matches) <= 5:
        selected = matches
    else:
        preferred = PREFERRED_KEYS.get(rule.id, ())
        by_key = {key: index for index, key in enumerate(preferred)}
        selected = []
        # Keep the languages represented and favor distinct subjects and lessons.
        # Specific observed cases above outrank the general diversity heuristic.
        pools = {}
        for lang in LANGUAGES:
            pools[lang] = [pair for pair in matches if pair[0].lang == lang]
        lang_order = sorted(LANGUAGES, key=lambda lang: len(pools[lang]), reverse=True)
        seen = set()
        subjects = Counter()
        lessons = Counter()
        for lang in (lang_order[0], lang_order[1], lang_order[0], lang_order[1], lang_order[0]):
            available = [pair for pair in pools[lang] if pair[0].send not in seen]
            if not available:
                available = [pair for pair in matches if pair[0].send not in seen]
            if not available:
                break

            def order(pair):
                clip, match_span = pair
                return (by_key.get(clip.key, len(by_key)),
                        lessons[clip.lesson], subjects[clip.lesson.split("/")[0]],
                        clip.lesson == "_shared", -min(match_span[1] - match_span[0], 28))

            pair = min(available, key=order)
            clip = pair[0]
            selected.append(pair)
            seen.add(clip.send)
            lessons[clip.lesson] += 1
            subjects[clip.lesson.split("/")[0]] += 1

    result = []
    for clip, match_span in selected:
        excerpt, shortened = snippet(clip, match_span)
        result.append({
            "lesson": clip.lesson,
            "lang": clip.lang,
            "key": clip.key,
            "send_excerpt": excerpt,
            "shortened": shortened,
            "first_match": clip.send[slice(*match_span)] if match_span[1] - match_span[0] <= 90 else None,
        })
    return result


def scan():
    files, lesson_ids, clips, skipped = read_transcripts()
    classes = []
    union = set()
    for rule in rules():
        matches = [(clip, result) for clip in clips if (result := rule.detect(clip)) is not None]
        matching_clips = [clip for clip, _ in matches]
        hits = [{"lesson": clip.lesson, "lang": clip.lang, "key": clip.key} for clip in matching_clips]
        union.update((item["lesson"], item["lang"], item["key"]) for item in hits)
        classes.append({
            "id": rule.id,
            "name": rule.name,
            "detection": rule.detection,
            "severity": rule.severity,
            "impact": len(hits) * rule.severity,
            "handling": rule.handling,
            "counts": {"total": counts(matching_clips), "by_language": counts_by_language(matching_clips)},
            "examples": examples(rule, matches),
            "narrator_reading": rule.reading,
            "risk_notes": rule.risk,
            "hits": hits,
        })
    classes.sort(key=lambda c: (-c["impact"], -c["severity"], c["id"]))
    matched = [clip for clip in clips if (clip.lesson, clip.lang, clip.key) in union]
    return {
        "schema_version": 1,
        "scope": {
            "source": "transcripts/*.json",
            "scanned_field": "send",
            "reference_field_for_arrow_comparison": "text",
            "json_files": len(files),
            "transcript_files": len(lesson_ids),
            "metadata_files_excluded": skipped,
            "shared_bucket_is_one_transcript": "_shared" in lesson_ids,
            "clips": len(clips),
            "by_language": counts_by_language(clips),
            "clips_in_at_least_one_class": {"total": counts(matched), "by_language": counts_by_language(matched)},
            "max_request_code_points": {"zh": 150, "en": 400},
        },
        "method": {
            "identity": ["lesson", "lang", "key"],
            "overlap": "A clip counts once per class. Classes overlap. Lessons are unique IDs within each count.",
            "observed_vs_estimated": "Counts are detector hits. Severity is a qualitative estimate based on the consequence if misread. This is a text audit without audio testing.",
            "severity_scale": {
                5: "Possible truncation or change to instructional meaning.",
                4: "A symbol, term or value can disappear or change, or the request can become unintelligible.",
                3: "Pronunciation, grouping or interpretation can be ambiguous.",
                2: "Pacing or conventional numeric reading can sound awkward.",
                1: "Low-priority prosody candidate.",
            },
            "impact": "Total matched clips across languages multiplied by severity.",
            "handling": {
                "Fixed": "Use a deterministic rule within the stated field or guard.",
                "Context": "Review or rewrite in context, with human approval of LLM output.",
            },
        },
        "classes": classes,
    }


def markdown_code(value):
    value = value.replace("\r", "␍").replace("\n", "␊").replace("\t", "␉")
    size = max((len(item) for item in re.findall(r"\x60+", value)), default=0) + 1
    fence = chr(96) * size
    return f"{fence} {value} {fence}" if value else f"{fence}(empty){fence}"


def report(data):
    scope = data["scope"]
    classes = data["classes"]
    class_by_id = {item["id"]: item for item in classes}
    by_lang = scope["by_language"]
    matched = scope["clips_in_at_least_one_class"]["total"]
    lines = [
        "# TTS transcript audit",
        "",
        f"Scanned **{scope['clips']:,} clips** in **{scope['transcript_files']} transcript files** — "
        f"{by_lang['zh']['clips']:,} Mandarin clips in {by_lang['zh']['lessons']} files and "
        f"{by_lang['en']['clips']:,} English clips in {by_lang['en']['lessons']} files — using the exact "
        "text in " + markdown_code("send") + ". "
        + "The arrow-removal rule also compares the corresponding display field. "
        + ("The index is metadata. " if scope["metadata_files_excluded"] else "")
        + ("The " + markdown_code("_shared") + " bucket counts as one transcript ID in the lesson totals."
           if scope["shared_bucket_is_one_transcript"] else ""),
        "",
        f"**{matched['clips']:,} clips** match at least one of the {len(classes)} classes. "
        "Counts measure detector hits. A hit can be a correctly written candidate for review. "
        "The same clip can match multiple classes. This audit did not synthesize or listen to audio.",
        "",
        "The ranking multiplies total matched clips by estimated severity. "
        "Severity 5 covers possible truncation or a change to instructional meaning. Severity 4 covers "
        "likely loss or distortion of a term, symbol or value. Severity 3 covers ambiguity. Severity 2 "
        "covers pacing or conventional number readings. Severity 1 covers low-priority prosody. "
        "Inspect the severity column as well as the ranking when triaging rare errors.",
        "",
        "## Summary",
        "",
        "The table shows the ten highest-impact classes. All classes and their counts appear below.",
        "",
        "| Class | Mandarin clips / lessons | English clips / lessons | Severity | Impact | Handling |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in classes[:10]:
        counts_by_lang = item["counts"]["by_language"]
        zh, en = (counts_by_lang[lang] for lang in LANGUAGES)
        lines.append(
            f"| [{item['name']}](#{item['id']}) | {zh['clips']:,} / {zh['lessons']:,} | "
            f"{en['clips']:,} / {en['lessons']:,} | {item['severity']} | "
            f"{item['impact']:,} | {item['handling']} |"
        )
    lines.extend([
        "",
        f"The high-severity checks also found **{class_by_id['corrupt_exponent']['counts']['total']['clips']}** "
        "clips with [damaged exponents](#corrupt_exponent), "
        f"**{class_by_id['lost_relation']['counts']['total']['clips']}** with "
        "[missing or distorted equation relations](#lost_relation), and "
        f"**{class_by_id['repeat_decimal']['counts']['total']['clips']}** with "
        "[flattened repeating-decimal notation](#repeat_decimal).",
        "",
        "## Applying the findings",
        "",
        "- Fixed means deterministic within the field or guard described below. Context means review in context "
        "and, where helpful, use an LLM rewrite with human approval.",
        "- Resolve corrupted expressions and lost relations against the source. Apply specialized rules for formulas, "
        "units, dates and fields before general symbol and punctuation handling. Run the length check after rewrites.",
        "- Pass exact names, quotations and teaching notation through the approved pronunciation or segmentation "
        "path. Verify any split preserves clip order and every word.",
        "- The Mandarin request cutoff uses 150 Unicode code points. Its strict Han-only companion count shows "
        "what a 150-Han cutoff would flag. English uses 400 code points. Exact cutoff values are allowed.",
        "- Each class has up to five real examples. Classes with fewer than three observed clips show all available "
        "examples. Zero-hit rules are included so the scanner can catch those forms after a future publish. "
        "An added ellipsis indicates shortening.",
        "",
        "## Classes",
        "",
    ])
    for item in classes:
        zh, en = (item["counts"]["by_language"][lang] for lang in LANGUAGES)
        total = item["counts"]["total"]
        definition = item["detection"]
        if definition["kind"] == "regex":
            detection_text = (
                "**Detection** uses the following Python regex against the exact "
                + markdown_code("send") + " field.\n\n"
                + "\x60\x60\x60regex\n" + definition["pattern"] + "\n\x60\x60\x60"
            )
        else:
            detection_text = f"**Detection** uses the following logic. {definition['rule']}"
        lines.extend([
            f'<a id="{item["id"]}"></a>',
            f"### {item['name']}",
            "",
            f"**Hits** — {item['severity']}/5 severity, {item['impact']:,} impact — "
            f"{zh['clips']:,} Mandarin clips in {zh['lessons']:,} lessons and "
            f"{en['clips']:,} English clips in {en['lessons']:,} lessons. "
            f"{total['clips']:,} clips across {total['lessons']:,} distinct lesson IDs.",
            "",
            detection_text,
            "",
            f"**Reading and handling ({item['handling']})**  ",
            item["narrator_reading"],
            "",
            "**False positives and limits**  ",
            item["risk_notes"],
            "",
        ])
        if item["examples"]:
            lines.extend(["**Observed examples**", ""])
            for entry in item["examples"]:
                lines.append(
                    f"- {markdown_code(entry['lesson'])} · {entry['lang']} · "
                    f"{markdown_code(entry['key'])} · {markdown_code(entry['send_excerpt'])}"
                )
            lines.append("")
        else:
            lines.extend(["No matching clips in this export.", ""])
    lines.extend([
        "## Reproduce",
        "",
        "Run " + markdown_code("python -B textscan.py") + " with Python 3.10 or later. "
        "The scanner reads the adjacent transcript directory and regenerates this report and "
        + markdown_code("textscan_classes.json") + ". The JSON includes every matched "
        + markdown_code("(lesson, lang, key)") + " along with the rules, counts, examples and handling guidance.",
        "",
    ])
    return "\n".join(lines)


def main():
    data = scan()
    encoded = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    rendered = report(data)
    (ROOT / "textscan_classes.json").write_text(encoded, encoding="utf-8", newline="\n")
    (ROOT / "textscan_report.md").write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Scanned {data['scope']['clips']:,} clips against {len(data['classes'])} classes.")


if __name__ == "__main__":
    main()

