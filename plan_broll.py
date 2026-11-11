"""Arma el plan.json de b-roll (Kie grok-imagine, 9:16, 6 s) y el montaje.json desde un guion VOZ con líneas [B: ...].
Uso: python plan_broll.py <guion.md> <carpeta_videos> <prefijo> <nombre> "<estilo en inglés>"
Cada [B:] distinto = un clip. Las [B:] que dicen "mockup" se reemplazan por MOCKUP en el montaje."""
import json, os, re, sys

guion, vdir, pref, nombre, estilo = sys.argv[1:6]
sec_map = {"HOOK": "H01", "RE-HOOK": "H01", "CUERPO": "CUERPO", "CTA": "CUERPO"}
clips, montaje, cur, idx = [], {}, None, {}
for l in open(guion, encoding="utf-8"):
    l = l.strip()
    if l.startswith("## "):
        t = l[3:]
        m = re.match(r"VARIANTE (H\d\d)", t)
        cur = m.group(1) if m else sec_map.get(t)
        continue
    b = re.match(r"\[B: (.*)\]$", l)
    if cur and b:
        d = b.group(1)
        if "mockup" in d.lower():
            montaje.setdefault(cur, []).append("MOCKUP")
            continue
        if d not in idx:
            idx[d] = f"b{len(idx) + 1:02d}"
            clips.append({"id": idx[d], "duracion": 6, "estado": "pendiente",
                          "input": {"prompt": f"{d}. {estilo}", "aspect_ratio": "9:16", "mode": "normal", "duration": "6", "resolution": "720p"}})
        montaje.setdefault(cur, []).append(idx[d])
bdir = os.path.join(vdir, f"{pref}broll")
os.makedirs(bdir, exist_ok=True)
viejo = os.path.join(bdir, "plan.json")
if os.path.exists(viejo):  # conserva task_id y descargas de los clips que ya existían (mismo prompt)
    prev = {c["input"]["prompt"]: c for c in json.load(open(viejo, encoding="utf-8"))["clips"]}
    for c in clips:
        o = prev.get(c["input"]["prompt"])
        if o and o["id"] == c["id"]:
            c.update({k: v for k, v in o.items() if k != "input"})
        if c["estado"] == "fallo":
            c["estado"] = "pendiente"; c.pop("task_id", None); c.pop("error", None)
plan = {"oferta": os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(vdir)))), "proveedor": "kie", "modelo": "grok-imagine/text-to-video",
        "costo_seg_usd": 0.012, "piloto": "b01", "piloto_aprobado": True, "clips": clips}
json.dump(plan, open(os.path.join(bdir, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({"nombre": nombre, "clips": montaje}, open(os.path.join(vdir, f"montaje-{pref.strip('-')}-clips.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(clips)} clips · {sum(c['duracion'] for c in clips)} s · secciones {list(montaje)}")
