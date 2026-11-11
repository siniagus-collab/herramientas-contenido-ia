"""Arma un recetario HTML (A4, listo para imprimir a PDF desde el navegador) desde un recetas.txt + un meta.json.

Formato de recetas.txt:
  # CAP | Título del capítulo | Bajada
  ## Nombre | minutos | proteína g | costo ($, $$, $$$)
  I: ingrediente; ingrediente
  P: pasos
  T: tip (opcional)

meta.json: titulo, subtitulo, kicker, marca, colores {primario, acento, papel, caja},
           intro_html (antes del índice de recetas), final_html (bonus y cierre), nota_proteina.
Uso: python ebook.py recetas.txt meta.json salida.html
"""
import html, json, os, re, sys


def parsear(path):
    caps, rec = [], None
    for raw in open(path, encoding="utf-8"):
        l = raw.rstrip("\n")
        if l.startswith("# CAP"):
            _, t, b = [x.strip() for x in l.split("|", 2)]
            caps.append({"titulo": t, "bajada": b, "recetas": []})
        elif l.startswith("## "):
            n, m, p, c = [x.strip() for x in l[3:].split("|")]
            rec = {"nombre": n, "min": m, "prot": p, "costo": c, "I": [], "P": "", "T": ""}
            caps[-1]["recetas"].append(rec)
        elif l[:2] in ("I:", "P:", "T:") and rec:
            k, v = l[0], l[2:].strip()
            rec[k] = [x.strip() for x in re.split(r";(?![^()]*\))", v)] if k == "I" else v
    return caps


def main(rec_path, meta_path, out):
    caps = parsear(rec_path)
    m = json.load(open(meta_path, encoding="utf-8"))
    c = m["colores"]
    total = sum(len(x["recetas"]) for x in caps)
    e = html.escape
    css = f"""
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Inter:wght@400;600;700&display=swap');
:root{{--primario:{c['primario']};--acento:{c['acento']};--papel:{c['papel']};--tinta:#1D1D1B;--suave:#6B6B66;--caja:{c['caja']};}}
@page{{size:A4;margin:1.8cm 1.8cm 2cm 1.8cm;@bottom-center{{content:counter(page);font:9pt Inter,sans-serif;color:#8a8a85;}}}}
@page portada{{margin:0;@bottom-center{{content:none;}}}}
*{{box-sizing:border-box}} html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{margin:0;font-family:Inter,Arial,sans-serif;font-size:10.5pt;line-height:1.55;color:var(--tinta)}}
h1,h2,h3{{font-family:Fraunces,Georgia,serif;color:var(--primario);line-height:1.15;break-after:avoid}}
h2{{font-size:19pt;margin:1.2em 0 .4em}} h3{{font-size:13pt;margin:0 0 .3em}}
.portada{{page:portada;break-after:page;width:210mm;height:297mm;padding:30mm 22mm;display:flex;flex-direction:column;justify-content:space-between;background:var(--primario);color:#fff}}
.portada .kicker{{letter-spacing:.14em;text-transform:uppercase;font-size:10pt;color:var(--acento);font-weight:700}}
.portada h1{{color:#fff;font-size:46pt;margin:.2em 0}} .portada .sub{{font-size:15pt;max-width:150mm;opacity:.93}}
.portada .big{{font-family:Fraunces,serif;font-size:120pt;color:var(--acento);line-height:1}}
.seccion{{break-before:page}} .capitulo{{break-before:page}}
.capitulo .num{{font-family:Fraunces,serif;font-size:56pt;color:var(--acento);line-height:1}}
.capitulo h1{{font-size:26pt;margin:.1em 0 .2em}} .bajada{{color:var(--suave);font-size:12pt;margin-bottom:1.2em}}
.receta{{border:1px solid #e4dfd3;border-radius:8px;padding:10pt 12pt;margin:0 0 10pt;break-inside:avoid;background:#fff}}
.meta{{display:flex;gap:6pt;flex-wrap:wrap;margin:2pt 0 6pt}}
.chip{{font-size:8.5pt;font-weight:700;padding:2pt 7pt;border-radius:20pt;background:var(--caja);color:var(--primario)}}
.chip.p{{background:var(--primario);color:#fff}}
.receta ul{{margin:3pt 0 5pt;padding-left:14pt}} .receta li{{margin:1pt 0}}
.tip{{font-size:9.5pt;background:var(--caja);border-left:3px solid var(--acento);padding:5pt 8pt;margin-top:5pt}}
.caja{{background:var(--caja);border-left:4px solid var(--primario);padding:10pt 12pt;margin:12pt 0;break-inside:avoid}}
table{{width:100%;border-collapse:collapse;font-size:9.5pt;margin:8pt 0}} th,td{{border-bottom:1px solid #e4dfd3;padding:5pt 6pt;text-align:left}} th{{background:var(--caja)}}
.indice ol{{columns:2;column-gap:14pt;font-size:9.5pt;padding-left:16pt}} .indice li{{margin:1pt 0;break-inside:avoid}}
.nota{{font-size:8.5pt;color:var(--suave)}}
.rpag{{break-before:page;break-inside:avoid}}
.rpag .foto{{width:100%;height:132mm;object-fit:cover;border-radius:10pt;display:block;margin-bottom:10pt}}
.rnum{{font-size:8.5pt;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--acento)}}
.rpag{{font-size:11.5pt}} .capfoto{{width:100%;height:170mm;object-fit:cover;border-radius:12pt;margin-top:14pt}}
.rt{{font-size:22pt;margin:2pt 0 4pt}}
.cols{{display:flex;gap:14pt;margin-top:8pt}} .ing{{flex:0 0 40%;background:var(--caja);border-radius:8pt;padding:9pt 11pt}}
.pas{{flex:1}} h4{{font-family:Fraunces,Georgia,serif;color:var(--primario);font-size:12pt;margin:0 0 4pt}}
.ing ul{{padding-left:13pt;margin:0}} .pas ol{{padding-left:16pt;margin:0}} .pas li{{margin:0 0 5pt}}
"""
    fotos = m.get("fotos")
    extra = {}
    if m.get("pasos"):
        pp = os.path.join(os.path.dirname(os.path.abspath(meta_path)), m["pasos"])
        for l in open(pp, encoding="utf-8"):
            if l[:1].isdigit():
                k, *ps = [x.strip() for x in l.split("|")]
                extra[int(k)] = [x.rstrip(".") for x in ps if x]
    out_html = [f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'><title>{e(m['titulo'])}</title><style>{css}</style></head><body>"]
    out_html.append(f"<section class='portada'><div><div class='kicker'>{e(m['kicker'])}</div><div class='big'>{m.get('numero', total)}</div>"
                    f"<h1>{e(m['titulo'])}</h1><div class='sub'>{e(m['subtitulo'])}</div></div><div class='nota' style='color:#fff;opacity:.8'>{e(m['marca'])}</div></section>")
    out_html.append(f"<section>{m['intro_html']}</section>")
    sin = m.get("sin_recetas")
    idx = ["<section class='seccion indice'><h2>Índice de recetas</h2>"]
    n = 0
    for i, cap in enumerate(caps, 1):
        idx.append(f"<h3>{i}. {e(cap['titulo'])}</h3><ol start='{n+1}'>")
        for r in cap["recetas"]:
            n += 1
            idx.append(f"<li>{e(r['nombre'])} · {e(r['prot'])} g</li>")
        idx.append("</ol>")
    idx.append("</section>")
    if not sin:
        out_html += idx
    n = 0
    for i, cap in enumerate([] if sin else caps, 1):
        cf = os.path.join(fotos, f"r{n+1:03d}.jpg") if fotos else ""
        cimg = f"<img class='capfoto' src='{cf}'>" if cf and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(out)), cf)) else ""
        out_html.append(f"<section class='capitulo'><div class='num'>{i:02d}</div><h1>{e(cap['titulo'])}</h1><div class='bajada'>{e(cap['bajada'])}</div>{cimg}")
        for r in cap["recetas"]:
            n += 1
            ing = "".join(f"<li>{e(x)}</li>" for x in r["I"])
            tip = f"<div class='tip'>💡 {e(r['T'])}</div>" if r["T"] else ""
            if fotos:
                pasos = extra.get(n) or [p.strip().rstrip(".") for p in re.split(r"(?<=\.)\s+", r["P"]) if p.strip()]
                pas = "".join(f"<li>{e(p)}.</li>" for p in pasos).replace("?.</li>","?</li>")
                foto = os.path.join(fotos, f"r{n:03d}.jpg")
                img = f"<img class='foto' src='{foto}'>" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(out)), foto)) else ""
                out_html.append(f"<div class='rpag'>{img}<div class='rnum'>Receta {n} · {e(cap['titulo'])}</div><h3 class='rt'>{e(r['nombre'])}</h3>"
                                f"<div class='meta'><span class='chip p'>≈ {e(r['prot'])} g de proteína</span><span class='chip'>⏱ {e(r['min'])} min</span>"
                                f"<span class='chip'>Costo {e(r['costo'])}</span></div><div class='cols'><div class='ing'><h4>Ingredientes</h4><ul>{ing}</ul></div>"
                                f"<div class='pas'><h4>Paso a paso</h4><ol>{pas}</ol></div></div>{tip}</div>")
                continue
            out_html.append(f"<div class='receta'><h3>{n}. {e(r['nombre'])}</h3><div class='meta'><span class='chip p'>≈ {e(r['prot'])} g de proteína</span>"
                            f"<span class='chip'>{e(r['min'])} min</span><span class='chip'>Costo {e(r['costo'])}</span></div><ul>{ing}</ul><div>{e(r['P'])}</div>{tip}</div>")
        out_html.append("</section>")
    nums = {r["nombre"]: i for i, r in enumerate((r for cap in caps for r in cap["recetas"]), 1)}
    def ref(mt):
        nombre = mt.group(1)
        if nombre not in nums:
            sys.exit(f"Receta no encontrada en el plan: {nombre}")
        return f"{nums[nombre]} · {e(nombre)}"
    final = re.sub(r"\{\{(.+?)\}\}", ref, m["final_html"])
    out_html.append(f"<section class='{'' if sin else 'seccion'}'>{final}<p class='nota' style='margin-top:20pt'>{e(m['nota_proteina'])}</p></section></body></html>")
    open(out, "w", encoding="utf-8").write("\n".join(out_html))
    print(f"OK: {0 if sin else total} recetas en {len(caps)} capítulos → {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
