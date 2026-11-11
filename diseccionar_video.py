"""Disecciona videos: tira de fotogramas (1 cada 2 s) y transcripción con ElevenLabs (scribe).
Uso: python diseccionar_video.py video1.mp4 [video2.mp4 ...]  → deja <video>.jpg y <video>.transcripcion.txt
Key: ELEVENLABS_API_KEY."""
import json, os, subprocess, sys, urllib.request, uuid


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def tira(p):
    d = dur(p)
    n = max(1, min(24, int(d // 2)))
    cols = 8
    rows = (n + cols - 1) // cols
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", p, "-vf",
                    f"fps=1/2,scale=200:-2,tile={cols}x{rows}", "-frames:v", "1", p[:-4] + ".jpg"], check=True)
    return d


def transcribir(p):
    key = os.environ["ELEVENLABS_API_KEY"]
    b = uuid.uuid4().hex
    audio = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "mp3", "-"], capture_output=True).stdout
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"model_id\"\r\n\r\nscribe_v1\r\n"
            f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode() + audio + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read()).get("text", "")


for p in sys.argv[1:]:
    d = tira(p)
    try:
        t = transcribir(p)
    except Exception as e:
        t = f"— (sin transcripción: {e})"
    open(p[:-4] + ".transcripcion.txt", "w", encoding="utf-8").write(t)
    print(f"{os.path.basename(p)} · {d:.0f} s · {t[:160]}")
