#!/usr/bin/env python3
"""Gera apresentacao.html e notas.md a partir dos slides em slides/.

Uso: python apresentacao/build_deck.py apresentacao/slides apresentacao
"""
import json, re, sys, html
from pathlib import Path
deck_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
deck = json.loads((deck_dir / "deck.json").read_text())
slide_dir = deck_dir / "slides" if (deck_dir / "slides").is_dir() else deck_dir
fonts = "".join(f'<link rel="stylesheet" href="{f["href"]}">' for f in deck["faces"].values())
warn = ('<svg viewBox="0 0 24 24" style="{s};flex:none" aria-label="Aviso"><path d="M12 2 1 21h22L12 2z" fill="none" '
        'stroke="{c}" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v5M12 17v1" stroke="{c}" stroke-width="2" stroke-linecap="round"/></svg>')
def icon(m):
    style = m.group(2); color = re.search(r"color:([^;\"]+)", style).group(1)
    return warn.format(s=style.replace(f"color:{color};", ""), c=color)
assets_file = slide_dir / "assets.json"
assets = json.loads(assets_file.read_text()) if assets_file.exists() else {}
def connector(m):
    style = m.group(1)
    w = int(re.search(r"width:(\d+)px", style).group(1)); h = int(re.search(r"height:(\d+)px", style).group(1))
    color = re.search(r"color:([^;\"]+)", style).group(1)
    if h > w:  # seta para baixo
        return (f'<svg viewBox="0 0 24 {h}" style="width:24px;height:{h}px;align-self:center;flex:none" aria-hidden="true">'
                f'<path d="M12 0V{h - 2}M5 {h - 9}l7 7 7-7" fill="none" stroke="{color}" stroke-width="3"/></svg>')
    return (f'<svg viewBox="0 0 {w} 24" style="width:{w}px;height:24px;align-self:center;flex:none" aria-hidden="true">'
            f'<path d="M0 12H{w - 2}M{w - 9} 5l7 7-7 7" fill="none" stroke="{color}" stroke-width="3"/></svg>')
slides, notes = [], []
for i, sid in enumerate(deck["order"], 1):
    s = (slide_dir / f"{sid}.html").read_text()
    a = re.search(r"<aside>(.*?)</aside>", s, re.S)
    notes.append(f"## {i}. {sid}\n\n{html.unescape(a.group(1).strip()) if a else ''}\n")
    s = re.sub(r"<aside>.*?</aside>", "", s, flags=re.S)
    s = re.sub(r'<x-icon name="(\w+)" style="([^"]*)"></x-icon>', icon, s)
    s = re.sub(r'<x-connector[^>]*style="([^"]*)"></x-connector>', connector, s)
    for blob, local in assets.items():
        s = s.replace(f'src="{blob}"', f'src="{local}"')
    s = s.replace("<section ", '<section class="slide" ', 1)
    slides.append(f'<div class="frame">{s}</div>')
page = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{deck['title']}</title>{fonts}
<style>
*{{box-sizing:border-box;margin:0}} body{{background:#2b2f38;padding:24px 0}}
.frame{{width:1920px;height:1080px;margin:0 auto 24px;overflow:hidden;position:relative;transform-origin:top left}}
.slide{{width:1920px;height:1080px;position:relative}}
h1,h2,h3,p{{margin:0}} ul,ol{{padding-left:1.2em;margin:0}}
th,td{{text-align:left;padding:.35em .6em;border-bottom:1px solid #DEDCD3}} table{{border-collapse:collapse}}
@media screen and (max-width:1960px){{.frame{{zoom:calc(100vw / 2000px)}}}}
@page{{size:1920px 1080px;margin:0}}
@media print{{body{{background:none;padding:0}} .frame{{margin:0;page-break-after:always;zoom:1}}}}
</style></head><body>
{"".join(slides)}
</body></html>"""
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "apresentacao.html").write_text(page)
(out_dir / "notas.md").write_text(f"# {deck['title']}: notas do apresentador\n\n> Conteúdo gerado por IA (Claude). Revise antes de usar.\n\n" + "\n".join(notes))
