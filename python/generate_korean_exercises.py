#!/usr/bin/env python3
"""Generate Korean verb-conjugation drill exercises for korean-speech-drill.html.

Mirrors the Japanese tense drill: one verb across eight spoken forms
(polite 해요체, formal 합니다, connective -고). Scoring accepts Hangul
with or without object particles; romanization is a pronunciation hint only.

Output:
    python/output/korean_exercises.json
    python/output/korean_definitions.json
"""
from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

random.seed(42)

# ── Eight drilled forms ──────────────────────────────────────────────────────
FORMS = {
    "yo":       ("Polite present (–요)",        "Polite 해요체 present: 가요, 먹어요, 해요."),
    "an_yo":    ("Polite negative (안 –요)",    "Polite negative: 안 + 해요체 (안 가요)."),
    "ss_yo":    ("Polite past (–었어요)",       "Polite past: 았/었 + 어요 (갔어요, 먹었어요, 했어요)."),
    "an_ss_yo": ("Polite past neg. (안 –었어요)", "Polite past negative: 안 + past (안 갔어요)."),
    "da":       ("Dictionary (–다)",            "Dictionary / citation form (가다, 먹다, 하다)."),
    "nida":     ("Formal present (–습니다)",    "Formal 합니다체: no batchim → ㅂ니다; batchim → 습니다; ㄹ drops."),
    "seyo":     ("Honourific (–세요)",          "Request / honourific: stem + 세요 (batchim takes 으세요)."),
    "go":       ("Connective (–고)",            "Connective -고: 가고, 먹고, 하고."),
}
ALL_FORMS = list(FORMS.keys())

# group: hada | oda | deu | eu | i | u | l | regular
VERBS = [
    dict(lemma="하다", romaji="hada", gloss="do", group="hada",
         objects=["숙제", "운동", "요리"]),
    dict(lemma="공부하다", romaji="gongbu-hada", gloss="study", group="hada",
         objects=["한국어", "영어", "수학"]),
    dict(lemma="말하다", romaji="malhada", gloss="speak", group="hada",
         objects=["한국어", "영어"]),
    dict(lemma="가다", romaji="gada", gloss="go", group="regular",
         objects=["학교", "집", "시장"]),
    dict(lemma="오다", romaji="oda", gloss="come", group="oda",
         objects=[]),
    dict(lemma="보다", romaji="boda", gloss="see / watch", group="regular",
         objects=["영화", "텔레비전", "책"]),
    dict(lemma="먹다", romaji="meokda", gloss="eat", group="regular",
         objects=["밥", "빵", "사과"]),
    dict(lemma="읽다", romaji="ikda", gloss="read", group="regular",
         objects=["책", "신문", "편지"]),
    dict(lemma="마시다", romaji="masida", gloss="drink", group="i",
         objects=["물", "커피", "차"]),
    dict(lemma="쓰다", romaji="sseuda", gloss="write", group="eu",
         objects=["편지", "이름", "이메일"]),
    dict(lemma="주다", romaji="juda", gloss="give", group="u",
         objects=["선물", "돈", "책"]),
    dict(lemma="자다", romaji="jada", gloss="sleep", group="regular",
         objects=[]),
    dict(lemma="살다", romaji="salda", gloss="live", group="l",
         objects=[]),
    dict(lemma="듣다", romaji="deutda", gloss="listen / hear", group="deu",
         objects=["음악", "라디오"]),
    dict(lemma="배우다", romaji="baeuda", gloss="learn", group="u",
         objects=["한국어", "영어"]),
]

TIME = ["오늘", "매일", "어제", "내일", "지금"]

# Jungseong indices in the Hangul syllable table (21 medials, including ㅖ).
V_A, V_AE, V_YA, V_YAE, V_EO, V_E, V_YEO, V_YE = 0, 1, 2, 3, 4, 5, 6, 7
V_O, V_WA, V_WAE, V_OE, V_YO = 8, 9, 10, 11, 12
V_U, V_WO, V_WE, V_WI, V_YU, V_EU, V_UI, V_I = 13, 14, 15, 16, 17, 18, 19, 20
JONG_SSANGSIOT = 20  # ㅆ
JONG_BIEUP = 17      # ㅂ
JONG_RIEUL = 8       # ㄹ
JONG_DIGEUT = 7      # ㄷ
JONG_NIEUN = 4       # ㄴ


def split_syl(ch: str) -> tuple[int, int, int]:
    o = ord(ch) - 0xAC00
    return o // 588, (o % 588) // 28, o % 28


def join_syl(cho: int, jung: int, jong: int) -> str:
    return chr(0xAC00 + cho * 588 + jung * 28 + jong)


def has_batchim(ch: str) -> bool:
    return split_syl(ch)[2] != 0


def is_hangul(ch: str) -> bool:
    o = ord(ch)
    return 0xAC00 <= o <= 0xD7A3


def bright(jung: int) -> bool:
    return jung in (V_A, V_YA, V_O, V_WA, V_YO)


def obj_with_particle(noun: str) -> str:
    last = noun[-1]
    if is_hangul(last) and has_batchim(last):
        return noun + "을"
    return noun + "를"


def _stem(lemma: str) -> str:
    if not lemma.endswith("다"):
        raise ValueError(lemma)
    return lemma[:-1]


def _set_jong(syl: str, jong: int) -> str:
    c, v, _ = split_syl(syl)
    return join_syl(c, v, jong)


def _set_jung(syl: str, jung: int) -> str:
    c, _, f = split_syl(syl)
    return join_syl(c, jung, f)


def _drop_jong(syl: str) -> str:
    return _set_jong(syl, 0)


def yo_form(lemma: str) -> str:
    """Polite present 해요체."""
    stem = _stem(lemma)
    if stem.endswith("하"):
        return stem[:-1] + "해요"
    last = stem[-1]
    head = stem[:-1]
    c, v, f = split_syl(last)
    if lemma == "듣다":
        return "들어요"
    if f == 0:
        if v == V_A:
            return stem + "요"
        if v == V_O:
            return head + _set_jung(last, V_WA) + "요"
        if v == V_U:
            return head + _set_jung(last, V_WO) + "요"
        if v == V_I:
            return head + _set_jung(last, V_YEO) + "요"
        if v == V_EU:
            return head + _set_jung(last, V_EO) + "요"
        if v in (V_EO, V_AE, V_E, V_YEO, V_YE):
            return stem + "요"
        return stem + "어요"
    # batchim
    return stem + ("아요" if bright(v) else "어요")


def past_form(lemma: str) -> str:
    """Polite past 했어요체."""
    stem = _stem(lemma)
    if stem.endswith("하"):
        return stem[:-1] + "했어요"
    last = stem[-1]
    head = stem[:-1]
    c, v, f = split_syl(last)
    if lemma == "듣다":
        return "들었어요"
    if f == 0:
        if v == V_A:
            return head + _set_jong(last, JONG_SSANGSIOT) + "어요"
        if v == V_O:
            return head + join_syl(c, V_WA, JONG_SSANGSIOT) + "어요"
        if v == V_U:
            return head + join_syl(c, V_WO, JONG_SSANGSIOT) + "어요"
        if v == V_I:
            return head + join_syl(c, V_YEO, JONG_SSANGSIOT) + "어요"
        if v == V_EU:
            return head + join_syl(c, V_EO, JONG_SSANGSIOT) + "어요"
        if v == V_EO:
            return head + _set_jong(last, JONG_SSANGSIOT) + "어요"
        return stem + "었어요"
    return stem + ("았어요" if bright(v) else "었어요")


def nida_form(lemma: str) -> str:
    stem = _stem(lemma)
    last = stem[-1]
    head = stem[:-1]
    c, v, f = split_syl(last)
    if f == 0 or f == JONG_RIEUL:
        return head + join_syl(c, v, JONG_BIEUP) + "니다"
    return stem + "습니다"


def seyo_form(lemma: str) -> str:
    stem = _stem(lemma)
    last = stem[-1]
    head = stem[:-1]
    c, v, f = split_syl(last)
    if lemma == "듣다":
        return "들으세요"
    if f == JONG_RIEUL:
        return head + _drop_jong(last) + "세요"
    if f == 0:
        return stem + "세요"
    return stem + "으세요"


def go_form(lemma: str) -> str:
    return _stem(lemma) + "고"


def conjugate(lemma: str, form: str) -> str:
    if form == "yo":
        return yo_form(lemma)
    if form == "an_yo":
        return "안 " + yo_form(lemma)
    if form == "ss_yo":
        return past_form(lemma)
    if form == "an_ss_yo":
        return "안 " + past_form(lemma)
    if form == "da":
        return lemma
    if form == "nida":
        return nida_form(lemma)
    if form == "seyo":
        return seyo_form(lemma)
    if form == "go":
        return go_form(lemma)
    raise ValueError(form)


# ── romanization (Revised Romanization, good enough for "Say: …") ───────────
_CHO = "g kk n d tt r m b pp s ss - j jj ch k t p h".split()
_JUNG = (
    "a ae ya yae eo e yeo ye o wa wae oe yo u wo we wi yu eu ui i"
).split()
_JONG = (
    [""] +
    "g kk gs n nj nh d r rg rm rb rs rt rp rh m b bs s ss ng j ch k t p h".split()
)
_CHO[11] = ""  # ㅇ initial is silent


def romanize(text: str) -> str:
    out = []
    for ch in text:
        if ch == " ":
            out.append(" ")
            continue
        if not is_hangul(ch):
            out.append(ch)
            continue
        c, v, f = split_syl(ch)
        cho = _CHO[c]
        jung = _JUNG[v]
        jong = _JONG[f]
        out.append(cho + jung + jong)
    s = "".join(out)
    return " ".join(s.split())


def generate():
    exercises, defs, counter = [], {}, 0
    for v in VERBS:
        defs[v["lemma"]] = f"{v['romaji']} — {v['gloss']}"
        transitive = bool(v["objects"])
        for form in ALL_FORMS:
            conj = conjugate(v["lemma"], form)
            # Also accept the no-space form of "안 가요"
            verb_group = sorted({conj, conj.replace(" ", "")})
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
                    key = (obj, time)
                    tries += 1
                seen.add(key)

                if transitive:
                    obj_p = obj_with_particle(obj)
                    sentence = f"{obj_p} {conj}"
                    obj_group = sorted({obj, obj_p})
                    grupos = [obj_group, verb_group]
                    ctx = f"{v['gloss']}: {romanize(obj)} {v['romaji']} → {FORMS[form][0]}"
                    say = f"{romanize(obj_p)} {romanize(conj)}"
                else:
                    sentence = f"{time} {conj}".strip() if time else conj
                    grupos = [verb_group]
                    ctx = (
                        f"{v['gloss']} ({romanize(time)}) → {FORMS[form][0]}"
                        if time else f"{v['gloss']} → {FORMS[form][0]}"
                    )
                    say = (
                        f"{romanize(time)} {romanize(conj)}".strip()
                        if time else romanize(conj)
                    )

                pista = f"{FORMS[form][1]} Say: {say}."
                exercises.append({
                    "id": f"{v['romaji']}-{form}-{counter}",
                    "verbo": v["lemma"],
                    "contexto": ctx,
                    "respuesta": sentence,
                    "pista": pista,
                    "grupos": grupos,
                })
                counter += 1
    return exercises, defs


EXPECTED = {
    "하다": dict(yo="해요", ss_yo="했어요", nida="합니다", seyo="하세요",
                 go="하고", da="하다", an_yo="안 해요", an_ss_yo="안 했어요"),
    "가다": dict(yo="가요", ss_yo="갔어요", nida="갑니다", seyo="가세요",
                 go="가고", da="가다"),
    "오다": dict(yo="와요", ss_yo="왔어요", nida="옵니다", seyo="오세요",
                 go="오고", da="오다"),
    "보다": dict(yo="봐요", ss_yo="봤어요", nida="봅니다", seyo="보세요",
                 go="보고", da="보다"),
    "먹다": dict(yo="먹어요", ss_yo="먹었어요", nida="먹습니다", seyo="먹으세요",
                 go="먹고", da="먹다"),
    "읽다": dict(yo="읽어요", ss_yo="읽었어요", nida="읽습니다", seyo="읽으세요",
                 go="읽고", da="읽다"),
    "마시다": dict(yo="마셔요", ss_yo="마셨어요", nida="마십니다", seyo="마시세요",
                   go="마시고", da="마시다"),
    "쓰다": dict(yo="써요", ss_yo="썼어요", nida="씁니다", seyo="쓰세요",
                 go="쓰고", da="쓰다"),
    "주다": dict(yo="줘요", ss_yo="줬어요", nida="줍니다", seyo="주세요",
                 go="주고", da="주다"),
    "자다": dict(yo="자요", ss_yo="잤어요", nida="잡니다", seyo="자세요",
                 go="자고", da="자다"),
    "살다": dict(yo="살아요", ss_yo="살았어요", nida="삽니다", seyo="사세요",
                 go="살고", da="살다"),
    "듣다": dict(yo="들어요", ss_yo="들었어요", nida="듣습니다", seyo="들으세요",
                 go="듣고", da="듣다"),
    "배우다": dict(yo="배워요", ss_yo="배웠어요", nida="배웁니다", seyo="배우세요",
                   go="배우고", da="배우다"),
    "공부하다": dict(yo="공부해요", ss_yo="공부했어요", nida="공부합니다",
                     seyo="공부하세요", go="공부하고", da="공부하다"),
    "말하다": dict(yo="말해요", ss_yo="말했어요", nida="말합니다",
                   seyo="말하세요", go="말하고", da="말하다"),
}


class ConjugationTests(unittest.TestCase):
    def test_known_forms(self):
        for lemma, forms in EXPECTED.items():
            for form, want in forms.items():
                got = conjugate(lemma, form)
                self.assertEqual(got, want, f"{lemma} {form}: {got!r} != {want!r}")

    def test_particle(self):
        self.assertEqual(obj_with_particle("밥"), "밥을")
        self.assertEqual(obj_with_particle("사과"), "사과를")
        self.assertEqual(obj_with_particle("한국어"), "한국어를")


def main():
    unittest.main(argv=["generate_korean_exercises"], exit=False, verbosity=2)
    exercises, defs = generate()
    out = Path(__file__).parent / "output"
    out.mkdir(exist_ok=True)
    (out / "korean_exercises.json").write_text(
        json.dumps(exercises, indent=2, ensure_ascii=False))
    (out / "korean_definitions.json").write_text(
        json.dumps(defs, indent=2, ensure_ascii=False))
    print(f"Generated {len(exercises)} exercises -> python/output/korean_exercises.json")
    print(f"Generated {len(defs)} definitions -> python/output/korean_definitions.json")


if __name__ == "__main__":
    main()
