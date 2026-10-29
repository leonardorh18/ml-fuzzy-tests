// Gera apresentacao/slides.pdf a partir de apresentacao/project/ (uma página 1920x1080 por slide).
// Aproxima a renderização do deck no claude.ai; o PDF oficial sai de Share > Export no próprio deck.
// Uso: node apresentacao/gerar_pdf.js   (precisa do pacote playwright com Chromium)
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const dir = path.join(__dirname, "project");
const deck = JSON.parse(fs.readFileSync(path.join(dir, "deck.json"), "utf8"));

// Ícones usados nos slides, desenhados em SVG simples (o deck usa um conjunto próprio).
const ICONS = {
  Chat: '<path d="M4 5h16v11H9l-5 4z"/>',
  Code: '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/>',
  Search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
};

function adapt(html) {
  return html
    .replace(/<aside>[\s\S]*?<\/aside>/g, "")
    .replace(/<x-icon name="(\w+)" style="([^"]*)"><\/x-icon>/g, (_, name, style) =>
      `<svg viewBox="0 0 24 24" style="${style};flex:none" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`)
    .replace(/<x-shape kind="arrow-right" style="([^"]*)"><\/x-shape>/g, (_, style) =>
      `<div style="${style};flex:none;clip-path:polygon(0 30%,60% 30%,60% 0,100% 50%,60% 100%,60% 70%,0 70%)"></div>`);
}

const fonts = Object.values(deck.faces).map((f) => `<link rel="stylesheet" href="${f.href}">`).join("\n");
const slides = deck.order.map((id) => adapt(fs.readFileSync(path.join(dir, "slides", `${id}.html`), "utf8"))).join("\n");

const page = `<!doctype html><html><head><meta charset="utf-8">${fonts}
<style>
@page { size: 1920px 1080px; margin: 0 }
* { box-sizing: border-box; margin: 0 }
html, body { padding: 0 }
section { width: 1920px; height: 1080px; position: relative; overflow: hidden; break-after: page; display: flex; flex-direction: column }
h1, h2, h3, p, li, td, th { font-family: inherit }
h1 { font-size: 96px } h2 { font-size: 64px } h3 { font-size: 44px; line-height: 1.2 } p { font-size: 32px; line-height: 1.4 }
ul { padding-left: 1.2em } li { margin-bottom: 8px }
table { border-collapse: collapse; width: 100% }
th, td { padding: 0.35em 0.6em; border-bottom: 1px solid rgba(128,128,128,0.35); vertical-align: top }
th { font-weight: 600; border-bottom: 2px solid currentColor }
</style></head><body>${slides}</body></html>`;

(async () => {
  const browser = await chromium.launch();
  const tab = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await tab.setContent(page, { waitUntil: "networkidle" });
  await tab.evaluate(() => document.fonts.ready);
  const out = path.join(__dirname, "slides.pdf");
  await tab.pdf({ path: out, width: "1920px", height: "1080px", printBackground: true });
  await browser.close();
  console.log(`PDF gerado: ${out}`);
})();
