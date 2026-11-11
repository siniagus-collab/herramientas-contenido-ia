"""Genera la voz en off de un guion (cuerpo+CTA y cada hook) con ElevenLabs, con timestamps por carácter.

Uso: python voz.py <guion.md> <carpeta_salida> <voice_id> [velocidad]
Salida: <carpeta>/<seccion>.mp3 + <seccion>.json (texto, palabras con inicio/fin en segundos).
Secciones: H01 (HOOK + RE-HOOK), H02..H05 (variantes), CUERPO (CUERPO + CTA).
Key: ELEVENLABS_API_KEY del entorno.
"""
import base64, json, os, re, sys, urllib.request


def secciones(path):
    sec, cur = {}, None
    for l in open(path, encoding="utf-8"):
        l = l.strip()
        if l.startswith("## "):
            t = l[3:]
            m = re.match(r"VARIANTE (H\d\d)", t)
            cur = m.group(1) if m else {"HOOK": "H01", "RE-HOOK": "H01", "CUERPO": "CUERPO", "CTA": "CUERPO"}.get(t)
            if t == "Notas":
                cur = None
            continue
        if cur and l and not l.startswith(("[", "#", "-")):
            sec.setdefault(cur, []).append(l)
    return {k: " ".join(v) for k, v in sec.items()}


def tts(texto, voz, velocidad):
    body = {"text": texto, "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3, "speed": velocidad}}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voz}/with-timestamps",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def palabras(al):
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, w, ini = [], "", None
    for c, s, e in zip(ch, st, en):
        if c.isspace():
            if w:
                out.append({"w": w, "s": ini, "e": fin})
            w, ini = "", None
        else:
            if ini is None:
                ini = s
            w += c
            fin = e
    if w:
        out.append({"w": w, "s": ini, "e": fin})
    return out


def main(guion, outdir, voz, velocidad="1.1"):
    os.makedirs(outdir, exist_ok=True)
    for k, texto in secciones(guion).items():
        r = tts(texto, voz, float(velocidad))
        open(f"{outdir}/{k}.mp3", "wb").write(base64.b64decode(r["audio_base64"]))
        ws = palabras(r["alignment"])
        json.dump({"texto": texto, "palabras": ws, "dur": ws[-1]["e"] if ws else 0},
                  open(f"{outdir}/{k}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{k}: {len(texto)} caracteres · {ws[-1]['e']:.1f} s")


if __name__ == "__main__":
    main(*sys.argv[1:])
