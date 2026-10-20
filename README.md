# Kontrola izbora · Opština Žabari

Mapa 37 biračkih mesta sa rezultatima parlamentarnih izbora 2023, sastavom biračkih odbora za izbore 25. 10. 2026 i rezultatima 2026 (povlače se sa RIK-a).

- `public/index.html` – aplikacija (statična, Cloudflare Workers static assets)
- `public/data/rez2026.json` – rezultati 2026 po BM, zapisnici, upozorenja (piše zakazani zadatak)
- `public/data/dnevnik.json` – dnevnik promena u biračkim odborima (piše zakazani zadatak)
- `public/data/odbori_izmene.json` – izmenjeni sastavi odbora
- `public/zapisnici/` – kopije zapisnika sa RIK-a
- `tools/` – skripte zakazanih zadataka

Svaki push na `main` Cloudflare automatski objavljuje.
