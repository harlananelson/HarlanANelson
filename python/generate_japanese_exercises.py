#!/usr/bin/env python3
"""Generate Japanese verb-conjugation drill exercises for japanese-speech-drill.html.

Mirrors the English tense drill: one verb conjugated across eight polite/plain
forms. Conjugation is done by rule on the hiragana reading (ichidan / godan /
irregular), and the kanji form is derived by swapping the invariant kanji root
back in. Each answer group accepts BOTH the kana and kanji form, because ja-JP
speech recognition may return either.

Output:
    python/output/japanese_exercises.json     (exercise corpus)
    python/output/japanese_definitions.json   (verbo -> "romaji - gloss")
"""

import json
import random
from pathlib import Path

random.seed(42)

# ── The eight drilled forms: key -> (display name, learner hint) ─────────────
FORMS = {
    "masu":          ("Polite present (–masu)",        "Polite present/future: stem + ます."),
    "masen":         ("Polite negative (–masen)",      "Polite negative: stem + ません."),
    "mashita":       ("Polite past (–mashita)",        "Polite past: stem + ました."),
    "masen_deshita": ("Polite past neg. (–masendeshita)", "Polite past negative: stem + ませんでした."),
    "te":            ("Te-form (–te)",                 "Te-form: connective / requests. Godan verbs take onbin (って/んで/いて)."),
    "plain":         ("Plain / dictionary",            "Plain (dictionary) form — casual present/future."),
    "nai":           ("Plain negative (–nai)",         "Plain negative: a-row + ない (godan う→わ)."),
    "ta":            ("Plain past (–ta)",              "Plain past: te-form with て→た / で→だ."),
}
ALL_FORMS = list(FORMS.keys())

# ── Verbs. group: ichidan | godan | suru | kuru ─────────────────────────────
# kanji_prefix / reading_prefix = the invariant leading kanji and its reading,
# used to rebuild the kanji form from a conjugated kana form.
# objects: natural-script noun phrases (katakana loanwords are recognizer-stable).
VERBS = [
    # ichidan (ru-verbs): drop る, add ending
    dict(kanji="食べる", kana="たべる", romaji="taberu", group="ichidan",
         gloss="eat", kanji_prefix="食", reading_prefix="た",
         objects=["パンを", "ケーキを", "りんごを"]),
    dict(kanji="見る", kana="みる", romaji="miru", group="ichidan",
         gloss="see / watch", kanji_prefix="見", reading_prefix="み",
         objects=["テレビを", "えいがを", "メールを"]),
    dict(kanji="教える", kana="おしえる", romaji="oshieru", group="ichidan",
         gloss="teach", kanji_prefix="教", reading_prefix="おし",
         objects=["にほんごを", "えいごを", "すうがくを"]),
    dict(kanji="起きる", kana="おきる", romaji="okiru", group="ichidan",
         gloss="wake up / get up", kanji_prefix="起", reading_prefix="お",
         objects=[]),  # intransitive
    # godan (u-verbs)
    dict(kanji="飲む", kana="のむ", romaji="nomu", group="godan",
         gloss="drink", kanji_prefix="飲", reading_prefix="の",
         objects=["コーヒーを", "みずを", "おちゃを"]),
    dict(kanji="書く", kana="かく", romaji="kaku", group="godan",
         gloss="write", kanji_prefix="書", reading_prefix="か",
         objects=["てがみを", "なまえを", "メールを"]),
    dict(kanji="話す", kana="はなす", romaji="hanasu", group="godan",
         gloss="speak / talk", kanji_prefix="話", reading_prefix="はな",
         objects=["にほんごを", "えいごを"]),
    dict(kanji="買う", kana="かう", romaji="kau", group="godan",
         gloss="buy", kanji_prefix="買", reading_prefix="か",
         objects=["パンを", "ほんを", "プレゼントを"]),
    dict(kanji="読む", kana="よむ", romaji="yomu", group="godan",
         gloss="read", kanji_prefix="読", reading_prefix="よ",
         objects=["ほんを", "しんぶんを", "メールを"]),
    dict(kanji="聞く", kana="きく", romaji="kiku", group="godan",
         gloss="listen / hear", kanji_prefix="聞", reading_prefix="き",
         objects=["おんがくを", "ラジオを"]),
    dict(kanji="待つ", kana="まつ", romaji="matsu", group="godan",
         gloss="wait", kanji_prefix="待", reading_prefix="ま",
         objects=["タクシーを", "バスを", "ともだちを"]),
    dict(kanji="泳ぐ", kana="およぐ", romaji="oyogu", group="godan",
         gloss="swim", kanji_prefix="泳", reading_prefix="およ",
         objects=[]),  # intransitive
    # irregular
    dict(kanji="する", kana="する", romaji="suru", group="suru",
         gloss="do", kanji_prefix="", reading_prefix="",
         objects=["べんきょうを", "しごとを", "テニスを"]),
    dict(kanji="来る", kana="くる", romaji="kuru", group="kuru",
         gloss="come", kanji_prefix="", reading_prefix="",
         objects=[]),  # intransitive
]

# time words (optional flavour; never a required match group)
TIME = ["きょう", "まいにち", "きのう", "あした", "いま"]

# ── Godan conjugation tables (final-kana transforms) ────────────────────────
I_ROW = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち",
         "ぬ": "に", "ぶ": "び", "む": "み", "る": "り"}
A_ROW = {"う": "わ", "く": "か", "ぐ": "が", "す": "さ", "つ": "た",
         "ぬ": "な", "ぶ": "ば", "む": "ま", "る": "ら"}
# te-form / ta-form euphonic (onbin): final kana -> (te, ta)
ONBIN = {
    "う": ("って", "った"), "つ": ("って", "った"), "る": ("って", "った"),
    "ぬ": ("んで", "んだ"), "ぶ": ("んで", "んだ"), "む": ("んで", "んだ"),
    "く": ("いて", "いた"), "ぐ": ("いで", "いだ"), "す": ("して", "した"),
}

# hardcoded irregulars: form -> kana
SURU = {"masu": "します", "masen": "しません", "mashita": "しました",
        "masen_deshita": "しませんでした", "te": "して", "plain": "する",
        "nai": "しない", "ta": "した"}
KURU_KANA = {"masu": "きます", "masen": "きません", "mashita": "きました",
             "masen_deshita": "きませんでした", "te": "きて", "plain": "くる",
             "nai": "こない", "ta": "きた"}
KURU_KANJI = {"masu": "来ます", "masen": "来ません", "mashita": "来ました",
              "masen_deshita": "来ませんでした", "te": "来て", "plain": "来る",
              "nai": "来ない", "ta": "来た"}


def conjugate_kana(v, form):
    """Return the hiragana conjugation of verb v in the given form."""
    g, kana = v["group"], v["kana"]
    if g == "suru":
        return SURU[form]
    if g == "kuru":
        return KURU_KANA[form]

    stem = kana[:-1]           # drop final kana
    last = kana[-1]

    if g == "ichidan":
        endings = {"masu": "ます", "masen": "ません", "mashita": "ました",
                   "masen_deshita": "ませんでした", "te": "て", "plain": "る",
                   "nai": "ない", "ta": "た"}
        return stem + endings[form]

    # godan
    if form in ("masu", "masen", "mashita", "masen_deshita"):
        polite_stem = stem + I_ROW[last]
        suffix = {"masu": "ます", "masen": "ません", "mashita": "ました",
                  "masen_deshita": "ませんでした"}[form]
        return polite_stem + suffix
    if form == "plain":
        return kana
    if form == "nai":
        return stem + A_ROW[last] + "ない"
    if form in ("te", "ta"):
        # 行く is the classic irregular te/ta
        if kana == "いく":
            return "いって" if form == "te" else "いった"
        te, ta = ONBIN[last]
        return stem + (te if form == "te" else ta)
    raise ValueError(form)


def conjugate_kanji(v, form, kana_form):
    """Rebuild the kanji form by swapping the invariant kanji root back in."""
    g = v["group"]
    if g == "suru":
        return kana_form                      # する has no kanji here
    if g == "kuru":
        return KURU_KANJI[form]
    rp, kp = v["reading_prefix"], v["kanji_prefix"]
    if rp and kana_form.startswith(rp):
        return kp + kana_form[len(rp):]
    return kana_form


def romaji_reading(kana):
    """Rough hiragana/katakana -> romaji, good enough as a pronunciation aid."""
    two = {
        "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo", "しゃ": "sha", "しゅ": "shu",
        "しょ": "sho", "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho", "にゃ": "nya",
        "にゅ": "nyu", "にょ": "nyo", "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
        "みゃ": "mya", "みゅ": "myu", "みょ": "myo", "りゃ": "rya", "りゅ": "ryu",
        "りょ": "ryo", "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo", "じゃ": "ja",
        "じゅ": "ju", "じょ": "jo", "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    }
    one = {
        "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
        "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
        "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
        "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
        "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
        "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
        "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
        "や": "ya", "ゆ": "yu", "よ": "yo",
        "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
        "わ": "wa", "を": "o", "ん": "n",
        "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
        "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
        "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
        "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
        "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    }
    # katakana share the same phonetics: fold to hiragana by codepoint offset
    def kata_to_hira(ch):
        o = ord(ch)
        if 0x30A1 <= o <= 0x30F6:
            return chr(o - 0x60)
        return ch

    src = "".join(kata_to_hira(c) for c in kana)
    out, i = [], 0
    while i < len(src):
        pair = src[i:i + 2]
        if pair in two:
            out.append(two[pair]); i += 2; continue
        ch = src[i]
        if ch == "っ":  # sokuon: double next consonant
            nxt = src[i + 1] if i + 1 < len(src) else ""
            r = two.get(src[i + 1:i + 3], one.get(nxt, ""))
            if r:
                out.append(r[0])
            i += 1; continue
        if ch == "ー":  # long vowel: repeat previous vowel
            if out and out[-1] and out[-1][-1] in "aeiou":
                out.append(out[-1][-1])
            i += 1; continue
        out.append(one.get(ch, ch)); i += 1
    return "".join(out)


def strip_particle(obj):
    """Drop a trailing を/は/に particle to also accept the bare noun."""
    return obj[:-1] if obj and obj[-1] in "をはにへがも" else obj


def generate():
    exercises, defs, counter = [], {}, 0
    for v in VERBS:
        defs[v["kana"]] = f"{v['romaji']} — {v['gloss']}"
        transitive = bool(v["objects"])
        for form in ALL_FORMS:
            kana_v = conjugate_kana(v, form)
            kanji_v = conjugate_kanji(v, form, kana_v)
            verb_group = sorted({kana_v, kanji_v})
            seen = set()
            n_variants = 3 if transitive else 2
            for _ in range(n_variants):
                obj = random.choice(v["objects"]) if transitive else ""
                time = random.choice(TIME) if not transitive else ""
                key = (obj, time)
                tries = 0
                while key in seen and tries < 10:
                    obj = random.choice(v["objects"]) if transitive else ""
                    time = random.choice(TIME) if not transitive else ""
                    key = (obj, time); tries += 1
                seen.add(key)

                if transitive:
                    sentence = f"{obj}{kana_v}"
                    obj_group = sorted({obj, strip_particle(obj)})
                    grupos = [obj_group, verb_group]
                    ctx = f"{v['gloss']}: {romaji_reading(obj)} {v['romaji']} → {FORMS[form][0]}"
                    say = f"{romaji_reading(obj)} {romaji_reading(kana_v)}"
                else:
                    sentence = f"{time}{kana_v}" if time else kana_v
                    grupos = [verb_group]
                    ctx = f"{v['gloss']} ({romaji_reading(time)}) → {FORMS[form][0]}" if time \
                        else f"{v['gloss']} → {FORMS[form][0]}"
                    say = f"{romaji_reading(time)} {romaji_reading(kana_v)}".strip() if time \
                        else romaji_reading(kana_v)

                pista = f"{FORMS[form][1]} Say: {say}."
                exercises.append({
                    "id": f"{v['romaji']}-{form}-{counter}",
                    "verbo": v["kana"],
                    "contexto": ctx,
                    "respuesta": sentence,
                    "pista": pista,
                    "grupos": grupos,
                })
                counter += 1
    return exercises, defs


def main():
    exercises, defs = generate()
    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)
    (out / "japanese_exercises.json").write_text(
        json.dumps(exercises, indent=2, ensure_ascii=False))
    (out / "japanese_definitions.json").write_text(
        json.dumps(defs, indent=2, ensure_ascii=False))
    print(f"Generated {len(exercises)} exercises -> python/output/japanese_exercises.json")
    print(f"Generated {len(defs)} definitions -> python/output/japanese_definitions.json")


if __name__ == "__main__":
    main()
