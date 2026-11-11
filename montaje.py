"""Montaje VO: voz en off (hook + cuerpo) + b-roll por frase + subtítulos por palabra + textos [T:] + mockup final.

Uso: python montaje.py <config.json>
config: guion, voz_dir, broll_dir, portada (png para la pantalla verde), mockup (png del libro),
        fondo_mockup (hex), clips {"H01": ["b01","b02"], "CUERPO": [...], ...}, salida_dir, fonts_dir
Cada frase hablada del guion usa el clip de la lista en orden; "MOCKUP" = placa del producto; "PANTALLA" = clip con verde croma + portada.
"""
import json, os, re, subprocess, sys

W, H, FPS = 1080, 1920, 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit("ffmpeg falló:\n" + r.stderr[-1500:])


def guion_frases(path):
    """{seccion: [{"texto", "T"}]} en el orden de habla."""
    sec, cur, t_pend = {}, None, None
    for l in open(path, encoding="utf-8"):
        l = l.strip()
        if l.startswith("## "):
            t = l[3:]
            m = re.match(r"VARIANTE (H\d\d)", t)
            cur = m.group(1) if m else {"HOOK": "H01", "RE-HOOK": "H01", "CUERPO": "CUERPO", "CTA": "CUERPO"}.get(t)
            if t == "Notas":
                cur = None
            continue
        if not cur or not l or l.startswith(("#", "-")):
            continue
        if l.startswith("[T:"):
            t_pend = l[3:-1].strip()
        elif l.startswith("["):
            pass
        else:
            sec.setdefault(cur, []).append({"texto": l, "T": t_pend})
            t_pend = None
    return sec


def tiempos(frases, voz):
    """Asigna inicio/fin a cada frase contando palabras sobre los timestamps de la voz."""
    ws, i = voz["palabras"], 0
    for f in frases:
        n = len(f["texto"].split())
        bloque = ws[i:i + n]
        f["s"], f["e"], f["w"] = bloque[0]["s"], bloque[-1]["e"], bloque
        i += n
    for a, b in zip(frases, frases[1:]):  # sin huecos: cada frase dura hasta que arranca la siguiente
        a["e"] = b["s"]
    frases[-1]["e"] = voz["dur"] + 0.35
    return frases


def ass_time(t):
    h, t = divmod(t, 3600); m, s = divmod(t, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass(frases, off_cuerpo, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Poppins Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,560,1
Style: Txt,Poppins Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,1,0,0,0,100,100,0,0,3,18,0,8,70,70,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for f in frases:
        o = f["off"]
        if f["T"]:
            txt = f["T"].upper()
            txt = re.sub(r"\*(.+?)\*", r"{\\c&H00D7FF&}\1{\\c&HFFFFFF&}", txt)
            ev.append(f"Dialogue: 1,{ass_time(o + f['s'])},{ass_time(o + f['e'])},Txt,,0,0,0,,{{\\fad(120,80)}}{txt}")
        ws = f["w"]
        for i in range(0, len(ws), 3):  # bloques de 3 palabras, la activa en amarillo
            grupo = ws[i:i + 3]
            for j, w in enumerate(grupo):
                ini = o + w["s"]
                fin = o + (grupo[j + 1]["s"] if j + 1 < len(grupo) else (ws[i + 3]["s"] if i + 3 < len(ws) else f["e"]))
                partes = [(r"{\c&H00D7FF&}" + x["w"].upper() + r"{\c&HFFFFFF&}") if k == j else x["w"].upper() for k, x in enumerate(grupo)]
                ev.append(f"Dialogue: 0,{ass_time(ini)},{ass_time(fin)},Sub,,0,0,0,,{' '.join(partes)}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")


def tramo(cfg, clip, dur, out, i):
    bd = cfg["broll_dir"]
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
    zoom = f"zoompan=z='min(1+0.0009*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}"
    foto = cfg.get("mockup_foto") if clip == "MOCKUP" else (cfg.get("pantalla_foto") if clip == cfg.get("clip_pantalla") else None)
    if foto:
        # foto nítida al centro + la misma foto desenfocada de fondo (formato vertical) + zoom suave
        fil = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.06[bg];"
               f"[0:v]scale={W-80}:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-40,fps={FPS},"
               f"zoompan=z='min(1+0.0008*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", foto, "-filter_complex", fil, "-t", f"{dur:.3f}", "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out])
        return
    if clip == "MOCKUP" and cfg.get("mockup_full"):
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", cfg["mockup"], "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},{zoom}", "-t", f"{dur:.3f}", "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out])
        return
    if clip == "MOCKUP":
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={cfg['fondo_mockup']}:s={W}x{H}:r={FPS}", "-loop", "1", "-i", cfg["mockup"],
             "-filter_complex", f"[1:v]crop=600:640:240:220,scale=920:-1[m];[0:v][m]overlay=(W-w)/2:(H-h)/2-60,{zoom}", "-t", f"{dur:.3f}", "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out])
        return
    src = os.path.join(bd, clip + ".mp4")
    largo = 6.0
    vel = f",setpts={largo/dur:.4f}*PTS" if dur > largo - 0.1 else ""  # si la frase es más larga que el clip, cámara lenta suave
    if clip == cfg.get("clip_pantalla"):
        cx, cy = cfg["pantalla_centro"]
        fil = (f"[2:v]scale=-1:860[p];[1:v][p]overlay={cx}-w/2:{cy}-h/2[bg];"
               f"[0:v]{base},chromakey=0x00FF00:0.22:0.08[fg];[bg][fg]overlay{vel}")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-f", "lavfi", "-i", f"color=c={cfg['color_portada']}:s={W}x{H}:r={FPS}",
             "-loop", "1", "-i", cfg["portada"], "-filter_complex", fil, "-t", f"{dur:.3f}", "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out])
        return
    ss = "0.4" if dur < largo - 0.5 else "0"
    run(["ffmpeg", "-v", "error", "-y", "-ss", ss, "-i", src, "-vf", base + vel, "-t", f"{dur:.3f}", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out])


def main(cfg_path):
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    sec = guion_frases(cfg["guion"])
    vd, out_dir = cfg["voz_dir"], cfg["salida_dir"]
    os.makedirs(out_dir + "/prod", exist_ok=True)
    cuerpo_voz = json.load(open(f"{vd}/CUERPO.json", encoding="utf-8"))
    for hk in [k for k in sec if k.startswith("H")]:
        hv = json.load(open(f"{vd}/{hk}.json", encoding="utf-8"))
        fh = tiempos([dict(x) for x in sec[hk]], hv)
        fc = tiempos([dict(x) for x in sec["CUERPO"]], cuerpo_voz)
        off_c = hv["dur"] + 0.35
        for f in fh: f["off"] = 0
        for f in fc: f["off"] = off_c
        frases = fh + fc
        clips = cfg["clips"][hk] + cfg["clips"]["CUERPO"]
        assert len(clips) == len(frases), f"{hk}: {len(frases)} frases y {len(clips)} clips"
        pid = f"{cfg['prefijo']}{hk[1:]} {cfg['nombre']}_{hk}_v1".replace(" ", "_")
        prod = f"{out_dir}/prod/{hk}"
        os.makedirs(prod, exist_ok=True)
        lista = []
        for i, (f, c) in enumerate(zip(frases, clips)):
            dur = (f["e"] - f["s"]) if f is not frases[-1] else (f["e"] - f["s"])
            if f is fh[-1]:
                dur = off_c - f["s"]
            seg = f"{prod}/t{i:02d}.mp4"
            tramo(cfg, c, dur, seg, i)
            lista.append(seg)
        open(f"{prod}/lista.txt", "w").write("".join(f"file '{os.path.abspath(x)}'\n" for x in lista))
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{prod}/lista.txt", "-c", "copy", f"{prod}/video.mp4"])
        # audio: hook + 0,35 s + cuerpo, normalizado a -14 LUFS
        run(["ffmpeg", "-v", "error", "-y", "-i", f"{vd}/{hk}.mp3", "-i", f"{vd}/CUERPO.mp3", "-filter_complex",
             f"[0:a]apad,atrim=0:{off_c:.3f}[a0];[a0][1:a]concat=n=2:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[a]", "-map", "[a]", "-ar", "48000", f"{prod}/voz.wav"])
        ass(frases, off_c, f"{prod}/subs.ass")
        fonts = cfg["fonts_dir"].replace("\\", "/").replace(":", "\\:")
        subs = os.path.abspath(f"{prod}/subs.ass").replace("\\", "/").replace(":", "\\:")
        final = f"{out_dir}/{pid}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", f"{prod}/video.mp4", "-i", f"{prod}/voz.wav", "-vf", f"subtitles='{subs}':fontsdir='{fonts}'",
             "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final])
        print(f"OK {final}")


if __name__ == "__main__":
    main(sys.argv[1])
