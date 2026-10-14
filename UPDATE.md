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
4. Nuovi articoli: sintesi completa riscritta con parole nuove (tradotta per le fonti estere), stesso significato, **nessun fatto inventato**: usare solo ciò che dicono titolo/descrizione dei feed (o la pagina, se letta). Nessun testo copiato.
5. `python3 scripts/compile.py && python3 build.py`
6. Verifica: `grep -rE 'href="https?://' docs` deve essere vuoto (nessun link esterno).
7. `git add -A && git diff --cached --quiet || (git commit -m "Aggiornamento $(date +%F\ %H:%M)" && git push)` — se non è cambiato nulla nei contenuti, non si committa (nota: il timestamp in `docs/` cambia a ogni build, quindi eseguire build e commit solo se `data/src` è cambiato: `git diff --quiet data/src || ...`).
8. Controllare che https://edbass1.github.io/all-news/ risponda 200.
