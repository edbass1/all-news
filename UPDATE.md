# ALL NEWS – procedura di aggiornamento orario

Struttura: `data/feeds.json` (feed RSS per gruppo) → `scripts/fetch.py` → `data/candidates.json` (cluster ordinati per prominenza) → redazione manuale in `data/src/<sezione>.txt` → `scripts/compile.py` → `data/articles.json` → `build.py` → `docs/` (GitHub Pages da main:/docs).

Sezioni (file in `data/src/`): ITALIA = `it-news` (30), `it-op` (30), `it-sport` (~15), `it-opsport` (~10); MONDO = `wo-news` (50), `wo-op` (50+); SPORT = `wo-sport` (15-20), `wo-opsport`. **Sport: escludere sport americani (NFL, NBA, MLB, NHL, college).** Fonti italiane escluse: Il Giornale, Libero, La Verità, Il Tempo.

Formato blocco in `data/src/*.txt` (blocchi separati da riga vuota, ordine = ranking):
```
@Tag|Fonte1, Fonte2|story-key(opzionale)|AAAA-MM-GG(opzionale)
Titolo
Sommario (1 frase)
Paragrafo 1
Paragrafo 2 ...
```
**Regola live/partite:** quinto campo dell'intestazione = `live` per cronache di partite, risultati, live-blog e dirette: vengono mostrati come voci brevi ("Risultati e dirette in breve") sotto la griglia, mai come notizie principali. Solo un grande evento (es. big match di Champions, finale) può avere `live-big`: va in cima ma in card ridotta (e se non è il primo della sezione diventa anch'esso breve). Es.: `@Champions League|ANSA||2026-10-14|live`.

Articoli con la stessa `story-key` sono raggruppati: il primo è la notizia principale, gli altri sono approfondimenti (intervista, analisi, retroscena) e devono avere contenuto diverso. L'ID è lo slug del titolo: **non modificare il titolo di un articolo che resta**, così ID/URL e `first_seen` restano stabili.

## Passi di ogni esecuzione (ogni ora)
1. `cd /workspace/all-news && git pull -q`
2. `python3 scripts/fetch.py` (≈20 s). Ranking: cluster per parole in comune, punteggio = n. testate distinte×10 − posizione nel feed×0,3.
3. Per ogni gruppo (`it`, `itsport`, `itop`, `world`, `worldsport`, `worldop`) confrontare i primi cluster con gli articoli esistenti:
   - storia ancora prominente → resta (eventualmente aggiorna il ranking spostando il blocco; aggiungi un approfondimento se ci sono sviluppi nuovi rilevanti);
   - storia nuova e coperta da più testate → nuovo blocco in posizione adeguata;
   - storia uscita dai feed / non più rilevante → eliminare il blocco solo se serve spazio per rispettare i conteggi.
   Le storie che restano in primo piano per giorni restano sul sito.
4. Nuovi articoli — **SEMPRE A LUNGHEZZA PIENA, MAI 2-3 RIGHE**:
   - Leggere il **testo completo** dell'articolo originale (non solo titolo/descrizione RSS): `curl -sL -A "Mozilla/5.0" URL` + `trafilatura.extract(html, favor_precision=True)` (helper: `/workspace/xp/links.py` per i link dei feed, `/workspace/xp/batch.py <sezione> [indici]` per scaricare i testi). Se la fonte è a pagamento/illeggibile, usare il testo di altre testate che coprono la stessa notizia.
   - **Lunghezza proporzionata all'originale**: articolo lungo → articolo lungo, pezzo breve (es. una nota d'agenzia di 5 righe) → articolo breve. Indicativamente almeno 3-6 paragrafi per le notizie normali.
   - Riscrittura completa con parole nuove (tradotta in italiano per le fonti estere), stesso significato, includendo dati, nomi, cifre, citazioni parafrasate e contesto presenti nella fonte. **Nessun fatto inventato, nessuna frase copiata, nessun link esterno**; fonti solo come testo nell'intestazione.
   - **Opinioni/editoriali**: leggere sempre il testo INTERO (nessun troncamento a ~1.700 caratteri) e coprire tutto l'argomento, con lunghezza proporzionata. Se la fonte di un'opinione è illeggibile (paywall/blocco: es. Le Monde, NYT, Washington Post, El País), **non pubblicare un pezzo breve**: scegliere un altro editoriale attuale e leggibile (Guardian, Irish Times, Haaretz, SCMP, Daily Maverick, Mail & Guardian, Toronto Star, Der Standard, Volkskrant, Politiken, Página/12, El Espectador, Folha, NZ Herald, SMH; per l'Italia Il Post, Linkiesta, Internazionale, Valigia Blu…). Scartare advertorial/contenuti sponsorizzati.
   - Eccezione: cronache live/live-blog di partite (`live`) restano brevi.
5. `python3 scripts/compile.py && python3 build.py`
6. Verifica: `grep -rE 'href="https?://' docs` deve essere vuoto (nessun link esterno).
7. `git add -A && git diff --cached --quiet || (git commit -m "Aggiornamento $(date +%F\ %H:%M)" && git push)` — se non è cambiato nulla nei contenuti, non si committa (nota: il timestamp in `docs/` cambia a ogni build, quindi eseguire build e commit solo se `data/src` è cambiato: `git diff --quiet data/src || ...`).
8. Controllare che https://edbass1.github.io/all-news/ risponda 200.

## URL stabili (slug)
- `data/slugs.json`: `published` = tutti gli slug mai pubblicati; `redirects` = vecchio slug → slug attuale (vuoto = pagina iniziale).
- `scripts/compile.py`: se un articolo cambia titolo, mantiene il vecchio ID/URL (match per sezione + somiglianza titolo/sommario ≥ 0,25). **Comunque: non cambiare i titoli degli articoli già pubblicati.**
- `build.py` aggiorna `slugs.json` e genera in `docs/a/<vecchio>.html` una pagina di redirect (meta refresh, link relativo) per ogni slug pubblicato che non esiste più. Committare sempre `data/slugs.json`.
- Recupero dalla storia git: `python3 scripts/slugs.py --history`.

## Testate (ITALIA, MONDO, SPORT) e TORINO
- **Config**: `data/outlets.json` – una voce per testata: `key`, `label`, `country`, `tab` (`italia`/`mondo`/`sport`/`torino`), feed `news`/`op`, opzionali `html`/`html_op` (scraping homepage con regex sul percorso), `op_match` (regex sul link per separare le opinioni dal feed news), `note` (testo mostrato se la testata è vuota), `pool:true` (fonti TORINO: niente badge, vista unica).
- ITALIA, MONDO e SPORT sono **solo per testata** (badge sotto la barra, prima testata selezionata di default, Notizie a sinistra / Opinioni a destra). TORINO è una vista unica ordinata (`to-news`, `to-op`), **senza elencare le fonti** sul sito (solo il badge per articolo).
- **Sezioni**: `data/src/so-<key>.txt` (notizie) e `data/src/so-<key>-op.txt` (opinioni); Torino `data/src/to-news.txt`, `to-op.txt`. Stesso formato blocchi (5° campo `live`/`live-big` per partite e dirette).
- **Ogni ora**: `python3 scripts/fetch_outlets.py [N] [tab]` → `data/outlet_candidates.json` (titoli, link, testo completo letto dalla pagina; scarta voci più vecchie di 4 giorni e sport americani). Per ogni testata confrontare con il suo file: aggiungere le nuove notizie principali (**obiettivo: almeno le TOP 30 notizie attuali per ogni testata**, più le opinioni dove esistono; Torino 30+). Per trovare 30 voci non basta l'RSS principale: usare anche feed di sezione e homepage/pagine sezione della testata (`python3 scripts/fetch_one.py <key> 45 <feed extra> 'html:<url>|<regex percorso>'` → `/tmp/one-<key>.txt` con testo completo). Se la testata ha davvero meno voci recenti, usare quelle che ci sono, togliere quelle sparite dalla testata, non cambiare i titoli di quelle che restano. Riscrittura in italiano con parole nuove, lunghezza proporzionale al testo letto, nessun fatto inventato (se si ha solo il sommario RSS, articolo breve).
- Testate rimosse perché non leggibili (feed vuoti/bloccati o nessun contenuto): ESPN, The Telegraph Sport, TyC Sports, Sports Illustrated, Daily News NY; per Torino Chivasso Oggi, La Nuova Periferia, Quotidiano Canavese, La Voce. Regola: una testata che non produce contenuti non va mostrata; toglierla da `data/outlets.json` (e `feeds.json`) invece di lasciare la nota. The Athletic, L'Équipe, So Foot, France Football, Kicker, Libération, Le Monde, de Volkskrant, NYT e il Manifesto: solo sommari RSS (testo a pagamento).
