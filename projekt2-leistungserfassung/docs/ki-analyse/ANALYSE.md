# KI-Analyse Phase 3 – Ergebnisse, Lauf 2 (UNIFR-3 / UNIFR-4 / UNIFR-5)

**Modell:** claude-fable-5 (Anthropic) · **Datum:** 2026-08-10 (Lauf 2) ·
**Input:** `probanden_export.json` (IK I–III, Import v2 – direkt aus der
korrigierten Excel, Summen-validiert gegen Blatt-Gesamt und GESAMT-Blatt) ·
**Prompt:** siehe `PROMPT.md` (Reproduzierbarkeit)

> **Lauf 2 ersetzt Lauf 1 vollständig.** Lauf 1 basierte auf dem
> Prototyp-Import, der ~110 P je Proband verlor (v. a. Prothetik) – dessen
> Kernbefund „Prothetik überall tiefrot" war ein **Datenartefakt**. Mit den
> korrigierten Daten sind die echten Lücken: **Chirurgie/Implantologie und
> KFO (0 % bei allen fünf Probanden)**.

> ⚠ **Wichtig:** Schwierigkeitsgrad/Zeitbedarf sind DEMO-Platzhalter (kein
> Lehrenden-Konsens, siehe UNIFR-16/17). Alle darauf beruhenden Aussagen sind
> entsprechend gekennzeichnet. Die Freigabe der Verläufe erfolgt erst im
> humanen Gegencheck (Phase 4, UNIFR-19 ff.).


## Stud. 1

**Fazit:** Stud. 1 hat nach IK I–III insgesamt 283,5 von 328 Zielpunkten (86 %) erbracht, aber sehr ungleich verteilt: 6 von 8 Kategorien stehen auf 'gut' (≥75 %), Chirurgie/Implantologie (0/16 P) und KFO (0/48 P) sind komplett leer – sie machen 64 der 81 fehlenden Punkte aus. Gleichzeitig wurden Endodontologie (190 %), Kinderzahnheilkunde (150 %) und Prothetik (112,5 %) übererfüllt; dieser Überschuss von 36,5 P hätte rechnerisch die Lücken in Chirurgie, Paro, ZHS und Schnittmenge vollständig decken können – die KFO-Lücke (48 P) übersteigt ihn jedoch, sie wäre selbst bei optimaler Umverteilung nicht in IK I–III schließbar gewesen (eher strukturelles Curriculum-Problem als individuelles Versäumnis). Die didaktische Reihenfolge ist auf Basis der DEMO-Schwierigkeitsgrade nicht aufsteigend (gewichtet 2,20 → 2,70 → 2,28; Totalprothese Schw. 3 bereits in IK I) – diese Aussage steht unter Vorbehalt des ausstehenden Lehrenden-Konsenses. Der prospektive IK-IV-Plan (82,5 P, unterhalb des bisherigen Semesterschnitts von 94,5 P) schließt alle Kategorien rechnerisch auf 100 %; kritischer Erfolgsfaktor ist die frühe Eröffnung der 4 KFO-Fallstrecken in den Wochen 1–3. Limitationen: Punkte je Semester aggregiert (keine Aussagen zur Reihenfolge innerhalb eines Semesters), 15 P Prothetik in IK III als nicht aufgeschlüsselte Blocksumme, Schwierigkeit/Zeit sind Demo-Platzhalter, IK IV fehlt in der Quelle (laufendes Semester).

### Befunde (Prüfung Reihenfolge & Inhalt vs. Originalstand)

| Aspekt | Schweregrad | Befund |
|---|---|---|
| luecke | KRITISCH | Zwei Kategorien nach drei Semestern komplett ohne Leistungen: Chirurgie/Implantologie (0 von 16 P, 0 %) und Kieferorthopädie (0 von 48 P, 0 %). – *In kategorien_summen fehlen beide Kategorien vollständig (keine Einträge in IK I–III). Zusammen 64 der insgesamt 81 fehlenden Punkte. KFO ist mit 48 P die mit Abstand größte Einzellücke und übersteigt sogar den gesamten Kapazitätsüberschuss der übererfüllten Kategorien (36,5 P) – sie wäre also selbst bei optimaler Umverteilung in IK I–III nicht vollständig schließbar gewesen (strukturelles, kein individuelles Versäumnis-Problem allein).* |
| reihenfolge | relevant | Keine aufsteigende didaktische Schwierigkeit über die Semester: punktgewichtete Demo-Schwierigkeit IK I = 2,20 → IK II = 2,70 → IK III = 2,28 (Peak in der Mitte statt am Ende). Bereits in IK I liegen 38 von 71,5 P (53 %) auf Schwierigkeitsstufe 3, darunter eine Totalprothese (20 P) und Endo-Aufbereitung/-Füllung. – *Berechnet aus schwierigkeit_demo × punkte_summe je Semester. ACHTUNG: Schwierigkeitsgrade sind DEMO-Platzhalter (lt. meta.bekannte_luecken, Lehrenden-Konsens steht aus) – der Befund ist vorläufig. Limitation: Punkte sind je Semester aggregiert, Aussagen zur Reihenfolge INNERHALB eines Semesters sind nicht möglich, nur der Vergleich zwischen Semestern.* |
| ausgewogenheit | relevant | Starke Klumpenbildung: Prothetik dominiert IK II mit 81 von 117,5 P (69 % der Semesterlast), davon allein 61 P Kronen (proth_krone). Endodontologie fehlt in IK II komplett (nur IK I: 10 P und IK III: 28 P), Kinderzahnheilkunde fehlt in IK I, Parodontologie fällt ab (10 → 10,5 → 5 P). – *Direkt aus kategorien_summen bzw. den Semesterlisten ablesbar. Die Prothetik-Ballung in IK II verdrängt dort fast alles andere (ZHS nur 4 P in IK II); kontinuierliches Üben über alle Semester (Spacing) wäre didaktisch günstiger als Blockbildung.* |
| mindestanforderung | relevant | Ampel Ende IK III: 6 von 8 Kategorien 'gut' (≥75 %): Endodontologie 100 % (real 190 %), Kinderzahnheilkunde 100 % (real 150 %), Prothetik 100 % (real 112,5 %), Schnittmenge 91 %, ZHS 86 %, Parodontologie 80 %. 2 Kategorien 'gering' (<50 %): Chirurgie/Implantologie 0 %, KFO 0 %. Keine Kategorie 'mittel'. – *Exakt aus kategorien_summen / mindestpunkte: Paro 25,5/32, ZHS 47,5/55, Endo 38/20, KZH 12/8, Prothetik 130,5/116, Schnittmenge 30/33, Chirurgie 0/16, KFO 0/48. Bei Paro fehlt konkret der 3. AIT-Patient (nur 2 × 8 P erbracht, Soll 3) plus UPT-Rest; bei Schnittmenge wurden schnitt_inlay und schnitt_reparatur nie erbracht (Kategorie nur über Stumpf-/Stiftaufbauten bedient).* |
| inhalt | Hinweis | Übererfüllung bindet Kapazität: Endo +18 P, KZH +4 P, Prothetik +14,5 P über Minimum = 36,5 P Überschuss, während gleichzeitig 81 P zu den Kategorien-Minima fehlen. Zudem enthält IK III eine nicht aufgeschlüsselte Prothetik-Blocksumme (proth_krone, 15 P, Feld 'hinweis') – die tatsächliche Leistungsart in diesem Block ist unbekannt. – *Überschuss/Lücken exakt aus kategorien_summen vs. mindestpunkte gerechnet. Die 36,5 P Überschuss hätten rechnerisch die Lücken in Chirurgie (16), Paro (6,5), ZHS (7,5) und Schnittmenge (3) = 33 P vollständig decken können. Die Blocksumme ist als Datenlimitation zu behandeln (Kategorienzuordnung Prothetik gilt, Leistungsart nicht); ebenso fehlt IK IV (SoSe26) in der Quelle als laufendes Semester.* |

### Optimierter Verlauf

**IK I** (retrospektiv) – Fokus: Grundlagen zuerst: Befunde, Prophylaxe, einfache Füllungen, leichte 1-P-Leistungen aus Chirurgie und KFO-Start; nur eine Schwierigkeit-3-Leistung (AIT) spät im Semester. Zielsumme 71,5 P = tatsächliche IK-I-Last. Die real in IK I erbrachte Totalprothese (Schw. 3 demo, 20 P) und die Endodontie wären nach IK II/III zu verschieben gewesen.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Wo 1–4 | Kariologischer Befund, Kariesrisiko, Therapieplanung (`zhs_befund`) | 10 | Leichter Einstieg (Schw. 1 demo), Basis für alle Folgebehandlungen. |
| Wo 1–6 | Prophylaxesitzung MuHy + PZR (`zhs_prophylaxe`) | 6 | Schw. 1, hoher Übungswert, Soll 4 Sitzungen. |
| Wo 1–6 | Systematische Untersuchung der Mundschleimhaut (`chir_msh`) | 4 | 1-P-Leistungen, ideal für den Semesterstart – real blieb die Kategorie 3 Semester leer. |
| Wo 2–5 | Unterstützende Parodontitistherapie (UPT) (`pa_upt`) | 2 | Schw. 1, kontinuierlicher Paro-Einstieg vor der AIT. |
| Wo 2–10 | Recall (Prothetik) (`proth_recall`) | 5 | Wie real erbracht – leichter Prothetik-Kontakt ohne große Fallstrecke. |
| Wo 3–6 | Plastische definitive Füllungen Klasse V (`zhs_fuell_5`) | 2 | Einfachste Füllungsklasse (Schw. 1 demo) vor Klasse I/II. |
| Wo 4–12 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 12 | Kern-Übungsleistung (Schw. 2 demo), gestreckt statt geklumpt. |
| Wo 5–8 | KZH-Befund inkl. Planung (`kzh_befund`) | 2 | KZH schon in IK I beginnen (real erst ab IK II). |
| Wo 5–8 | KZH-Prophylaxesitzung (`kzh_prophylaxe`) | 2 | Schw. 1, zusammen mit KZH-Befund am selben Patienten machbar. |
| Wo 6–10 | Planung oralchir. Eingriffe / DVT-Indikation (`chir_dvt`) | 4 | 1-P-Planungsleistungen, Soll 4 – füllt die real leere Kategorie früh. |
| Wo 7–13 | Adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 9 | Schw. 2 demo, wie real in IK I begonnen, leicht aufgestockt. |
| Wo 8–13 | Antiinfektiöse Parodontitistherapie (1. Patient) (`pa_ait`) | 8 | Einzige Schw.-3-Leistung (demo) in IK I, bewusst in die zweite Semesterhälfte gelegt. |
| Wo 10–13 | Implantat-prothetische Beratung (`chir_impl_beratung`) | 2 | 2 von 4 Soll-Beratungen bereits in IK I. |
| Wo 10–14 | KFO: Erstgespräch + Anamnese + Abformung + 1 Kontrolle (Fallstart, Codes kfo_erstgespraech/kfo_anamnese/kfo_abformung/kfo_kontrolle) (`kfo_erstgespraech`) | 3.5 | KFO-Fallstrecke früh eröffnen – die 48-P-Lücke ist zu groß, um sie einem einzigen Semester zu überlassen. (Schwierigkeit dieser Katalogleistungen ohne Demo-Wert, da nie erbracht.) |

**IK II** (retrospektiv) – Fokus: Gestufter Aufbau statt Prothetik-Klumpen: 2 Kronen (30 P) statt real 61 P Kronen, Totalprothese aus IK I hierher verschoben, Endo-Einstieg (real fehlte Endo in IK II komplett), Chirurgie weiterführen. Zielsumme 117,5 P = tatsächliche IK-II-Last; gewichtete Schwierigkeit steigt gegenüber IK I.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Wo 1–4 | Recall (Prothetik) (`proth_recall`) | 2.5 | Leichter Semesterstart. |
| Wo 1–5 | UPT-Sitzungen (`pa_upt`) | 2.5 | Paro kontinuierlich halten (real fiel Paro über die Semester ab). |
| Wo 1–6 | Kariologischer Befund / Therapieplanung (`zhs_befund`) | 4.5 | Befunde je Semester statt Ballung in IK I (real 11 P in IK I, 0 in IK II... 4 P gesamt in IK II). |
| Wo 2–6 | Aufbissbehelf inkl. FAL und Zentrikregistrat (`proth_aufbiss`) | 7 | Schw. 2 demo – sinnvolle Vorstufe vor den großen prothetischen Arbeiten (real erst IK III). |
| Wo 2–10 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 8 | Füllungsroutine fortführen (real nur 4 P in IK II). |
| Wo 3–10 | AIT (2. Patient) (`pa_ait`) | 8 | Wie real; Soll sind 3 AIT-Patienten über den Verlauf. |
| Wo 3–12 | Krone auf Zahn/Implantat (2 Kronen) (`proth_krone`) | 30 | Statt real 61 P Kronen in einem Semester: 2 Kronen hier, weitere in IK III – entzerrt den Klumpen (Schw. 3 demo). |
| Wo 4–9 | Wurzelkanalaufbereitung (2 Kanäle) (`endo_aufbereitung`) | 6 | Endo-Einstieg in IK II statt bereits in IK I (Schw. 3 demo) – real hatte IK II gar keine Endo. |
| Wo 4–12 | Adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 9 | Begleitend zu den Kronen, wie real (real 18 P – Überschuss reduziert). |
| Wo 5–13 | Totalprothese je Kiefer (`proth_totalprothese`) | 20 | Aus IK I hierher verschoben: Schw. 3 demo, 20 P – gehört nicht ins erste klinische Semester. |
| Wo 6–11 | Wurzelkanalfüllung (2 Kanäle) (`endo_fuellung`) | 4 | Folgt direkt auf die Aufbereitung derselben Kanäle. |
| Wo 6–12 | KZH non-invasive/invasive Behandlung (`kzh_behandlung`) | 4 | Schw. 2 demo, baut auf KZH-Befund aus IK I auf. |
| Wo 8–12 | Füllungen Klasse III/IV (`zhs_fuell_3_4`) | 3 | Anspruchsvollere Füllungsklasse nach Routine in Klasse I/II. |
| Wo 8–12 | Implantat-prothetische Beratung (`chir_impl_beratung`) | 2 | Restliche 2 Soll-Beratungen. |
| Wo 9–13 | Stiftaufbau (`schnitt_stiftaufbau`) | 3 | Ergänzt Stumpfaufbauten (real erst IK III). |
| Wo 9–14 | Implantatnachsorge (`chir_impl_nachsorge`) | 4 | Schließt die Chirurgie-Kategorie retrospektiv bereits Ende IK II auf 16/16 P. |

**IK III** (retrospektiv) – Fokus: Komplexe Fälle als Abschluss: zweite große Prothetik-Strecke (Teilprothese + 2 Kronen), Endo-Vervollständigung inkl. Revision, 3. AIT-Patient, Schnittmengen-Rest inkl. erstmals Kronenrand-Reparatur. Zielsumme 94,5 P = tatsächliche IK-III-Last. Ergebnis: Ende IK III wären 7 von 8 Kategorien auf 100 %, nur KFO (3,5/48 P) bliebe offen – mehr ist mit der realen Gesamtkapazität von 283,5 P rechnerisch nicht möglich (Minima-Summe 328 P).

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Wo 1–3 | Recall (Prothetik) (`proth_recall`) | 1.5 | Leichter Semesterstart, wie real. |
| Wo 1–4 | Prophylaxesitzung MuHy + PZR (`zhs_prophylaxe`) | 1.5 | ZHS-Kategorie exakt auf 55/55 P auffüllen. |
| Wo 1–6 | UPT-Sitzungen (`pa_upt`) | 3.5 | UPT-Soll (4 Sitzungen) komplettieren; Paro erreicht damit 32/32 P. |
| Wo 2–10 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 8 | Routine halten (real 15 P – leicht reduziert zugunsten der Lücken). |
| Wo 2–11 | Krone auf Zahn/Implantat (2 Kronen) (`proth_krone`) | 30 | Zweite Kronen-Strecke; zusammen mit IK II werden die real erbrachten Kronenpunkte entzerrt statt geklumpt. |
| Wo 3–7 | Wurzelkanalaufbereitung (1 Kanal) (`endo_aufbereitung`) | 3 | Endo auf exakt 20/20 P führen statt real 38 P (190 % – Überschuss von 18 P band Kapazität). |
| Wo 4–10 | AIT (3. Patient) (`pa_ait`) | 8 | Erfüllt das AIT-Soll von 3 Patienten – real fehlte der dritte. |
| Wo 4–13 | Teilprothese Doppelkrone (`proth_teilprothese`) | 20 | Große Schw.-3-Arbeit (demo) im letzten Retro-Semester, wo die Routine am größten ist. |
| Wo 5–9 | Wurzelkanalfüllung (2 Kanäle) (`endo_fuellung`) | 4 | Abschluss der aufbereiteten Kanäle. |
| Wo 5–11 | Adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 6 | Begleitend zu Kronen/Teilprothese. |
| Wo 6–11 | Stiftaufbau (`schnitt_stiftaufbau`) | 3 | Wie real in IK III. |
| Wo 8–12 | Entfernung Wurzelkanalfüllmaterial (Revision) (`endo_revision`) | 3 | Schwierigste Endo-Leistung (Schw. 3 demo) zuletzt in der Endo-Progression. |
| Wo 9–13 | Kariesbedingte Reparatur Kronenrand (`schnitt_reparatur`) | 3 | Real nie erbrachter Leistungstyp; bringt Schnittmenge auf 33/33 P. |

**IK IV** (prospektiv) – Fokus: Konkreter 14-Wochen-Plan vom REALEN Stand Ende IK III aus (nicht vom Retro-Szenario): schließt alle 81 fehlenden Punkte – KFO 48 P (4 Fallstrecken), Chirurgie/Implantologie 16 P, Parodontologie 8 P (3. AIT-Patient), ZHS 7,5 P, Schnittmenge 3 P. Plansumme 82,5 P: realistisch, da unter dem Semesterschnitt des Probanden (94,5 P; Spanne 71,5–117,5 P). Priorisierung nach Lückengröße × Machbarkeit: KFO und Chirurgie (viele kleine 1-P-Leistungen, gut planbar) starten sofort; die einzige Schw.-3-Leistung (AIT, demo) liegt in der Semestermitte.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Wo 1–2 | Systematische Untersuchung der Mundschleimhaut (4×) (`chir_msh`) | 4 | Leichter Einstieg: 1-P-Leistungen, keine Vorlaufzeit, Kategorie steht bei 0 %. |
| Wo 1–3 | Erstaufnahmegespräch / KIG-Klassifizierung (4 Fälle) (`kfo_erstgespraech`) | 4 | Größte Lücke (48 P) sofort adressieren; 4 parallele KFO-Fallstrecken eröffnen. Schwierigkeit dieser Leistungen hat keinen Demo-Wert (nie erbracht) – Annahme 'leicht' ist nicht datengestützt. |
| Wo 2–4 | KFO-Anamnese, Aufklärung, Epikrise (4 Fälle) (`kfo_anamnese`) | 4 | Direkte Fortsetzung der Fallstrecken. |
| Wo 3–5 | Abformung OK/UK, Scan, Registrat, Zielbiss (4 Fälle) (`kfo_abformung`) | 4 | Diagnostikunterlagen für alle 4 Fälle. |
| Wo 3–5 | Planung oralchir. Eingriffe / DVT-Indikation (4×) (`chir_dvt`) | 4 | Parallel zur KFO-Diagnostik terminierbar. |
| Wo 4–6 | Modellherstellung analog und digital (4 Fälle) (`kfo_modell`) | 4 | Folgt auf die Abformungen. |
| Wo 5–7 | 3D-Modellanalyse (4 Fälle) (`kfo_3d`) | 4 | Auswertung der Modelle. |
| Wo 5–9 | AIT – 3. Patient (MHT, FMS, Reevaluation) (`pa_ait`) | 8 | Schließt die Paro-Lücke (6,5 P fehlen, AIT bringt 8) und erfüllt das Soll von 3 AIT-Patienten. Einzige Schw.-3-Leistung (demo) des Plans – bewusst in der Semestermitte, nicht in den ersten Wochen. |
| Wo 6–8 | Foto/Gesichtsscan mit Auswertung (4 Fälle) (`kfo_foto`) | 4 | Fortsetzung Diagnostikstrecke. |
| Wo 7–9 | Rö-Befund OPG und FRS (4 Fälle) (`kfo_roentgen`) | 4 | Röntgendiagnostik vor Behandlungsplan. |
| Wo 7–10 | Implantat-prothetische Beratung (4×) (`chir_impl_beratung`) | 4 | Flexibel einplanbare 1-P-Leistungen als Puffer neben AIT und KFO. |
| Wo 8–10 | KFO-Behandlungsplan (4 Fälle) (`kfo_plan`) | 4 | Synthese der kompletten Diagnostik. |
| Wo 8–14 | Kontrollsitzungen (6 × 0,5 P je Fall, 4 Fälle) (`kfo_kontrolle`) | 12 | 24 kurze Sitzungen, über die zweite Semesterhälfte verteilt – terminlich gut streubar. |
| Wo 9–11 | Kariologischer Befund / Therapieplanung (`zhs_befund`) | 2.5 | Teil der ZHS-Restlücke (7,5 P); liefert zugleich Patienten für die Füllungen. |
| Wo 9–12 | Konstruktionszeichnung Gerät / ClinCheck (4 Fälle) (`kfo_konstruktion`) | 4 | Letzter 1-P-Baustein der Fallstrecken; damit KFO 48/48 P. |
| Wo 10–12 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 4 | Routineleistung (Schw. 2 demo) aus dem ZHS-Befund heraus. |
| Wo 11–13 | Kariesbedingte Reparatur Kronenrand (`schnitt_reparatur`) | 3 | Schließt die Schnittmengen-Lücke (exakt 3 P) und deckt erstmals diesen Leistungstyp ab. |
| Wo 11–14 | Implantatnachsorge (4×) (`chir_impl_nachsorge`) | 4 | Letzter Chirurgie-Baustein; damit 16/16 P. |
| Wo 13–14 | Plastische definitive Füllung Klasse V (`zhs_fuell_5`) | 1 | Kleinster Baustein zum exakten Erreichen von ZHS 55/55 P; unkritisch am Semesterende. |

### Auswirkungen auf die Kompetenzentwicklung

| Kategorie | Ende IK III (Ist) | Ende IK IV (optimiert, projiziert) | Kommentar |
|---|---|---|---|
| Parodontologie | 80 % | 100 % | 25,5/32 P = 79,7 % → 80 % (gut). Plan: +8 P (pa_ait, 3. Patient) → 33,5/32 = 104,7 %, gedeckelt 100 %. Erfüllt zugleich das AIT-Soll von 3 Patienten. |
| Zahnhartsubstanz/Prävention/Restauration | 86 % | 100 % | 47,5/55 P = 86,4 % → 86 % (gut). Plan: +7,5 P (zhs_befund 2,5 + zhs_fuell_1_2 4 + zhs_fuell_5 1) → exakt 55/55 = 100 %. |
| Endodontologie | 100 % | 100 % | 38/20 P = 190 %, gedeckelt 100 %. Keine weiteren Leistungen im IK-IV-Plan – der Überschuss von 18 P ist bereits die größte relative Übererfüllung. |
| Kinderzahnheilkunde | 100 % | 100 % | 12/8 P = 150 %, gedeckelt 100 %. Keine weiteren Leistungen geplant. |
| Prothetik | 100 % | 100 % | 130,5/116 P = 112,5 %, gedeckelt 100 %. Keine weiteren Leistungen geplant; die freiwerdende Kapazität geht in KFO/Chirurgie. Limitation: 15 P davon sind eine nicht aufgeschlüsselte Blocksumme (IK III, proth_krone mit 'hinweis'). |
| Schnittmenge Restauration/Prothetik | 91 % | 100 % | 30/33 P = 90,9 % → 91 % (gut). Plan: +3 P (schnitt_reparatur) → exakt 33/33 = 100 %; deckt zudem erstmals den Reparatur-Leistungstyp ab. |
| Chirurgie/Implantologie | 0 % | 100 % | 0/16 P = 0 % (gering, komplette Lücke). Plan: +16 P (je 4× msh, dvt, impl_beratung, impl_nachsorge à 1 P) → 16/16 = 100 %. |
| Kieferorthopädie (KFO) | 0 % | 100 % | 0/48 P = 0 % (gering, größte Lücke). Plan: +48 P über 4 komplette Fallstrecken (9 Diagnostik-/Planungsleistungen à 1 P + 6 Kontrollen à 0,5 P je Fall) → 48/48 = 100 %. Ambitioniertester Teil des Plans (58 % der Plansumme) – hängt von KFO-Patientenverfügbarkeit ab. |

## Stud. 2

**Fazit:** Stud. 2 hat nach IK I–III insgesamt 270 von 328 Zielpunkten (82 %) erbracht, jedoch stark unausgewogen: Prothetik (124 %), Kinderzahnheilkunde (150 %), Endodontologie (125 %) und die Schnittmenge (103 %) sind übererfüllt, während Chirurgie/Implantologie und KFO nach drei Semestern bei 0 % stehen und ZHS mit 48 % im roten Ampelbereich liegt. Der Prothetik-Klumpen (144 P, davon 102 P Kronen, 72 P allein in IK II) hat die Kapazität für die leeren Kategorien verdrängt. Ein einfach-zu-schwer-Aufbau über die Semester ist nicht erkennbar – schon IK I trug 58 % der Punkte auf Demo-Schwierigkeit 3; diese Aussage beruht allerdings auf den heuristischen DEMO-Platzhaltern (Lehrenden-Rating steht aus). Der vorgeschlagene IK-IV-Plan (14 Wochen, ca. 97 P – im Rahmen der bisherigen Semesterlasten von 66–108,5 P) schließt rechnerisch alle Lücken: KFO 48 P über vier gestaffelte Fälle, Chirurgie 16 P über kleinteilige 1-P-Leistungen, ZHS 29 P und PA-Rest 4 P; damit erreichen alle acht Kategorien 100 %. Der Plan ist ambitioniert, aber ohne einzige Demo-Schwierigkeit-3-Leistung machbar, da die schweren Kategorien bereits erfüllt sind. Limitationen: Punkte liegen nur semesterweise aggregiert vor (keine Aussagen zur Reihenfolge innerhalb eines Semesters), IK IV fehlt in der Quelle (laufendes Semester), und Schwierigkeit/Zeit sind Demo-Werte. Blocksummen-Einträge mit 'hinweis' kommen bei Stud. 2 – anders als bei anderen Probanden – nicht vor, diese Limitation entfällt hier.

### Befunde (Prüfung Reihenfolge & Inhalt vs. Originalstand)

| Aspekt | Schweregrad | Befund |
|---|---|---|
| luecke | KRITISCH | Kieferorthopädie (KFO) ist nach drei Semestern komplett leer: 0 von 48 Mindestpunkten (0 %). – *In kategorien_summen von Stud. 2 existiert kein KFO-Eintrag und in keinem Semester wurde eine kfo_*-Leistung dokumentiert. Mit 48 fehlenden Punkten ist dies die größte Einzellücke des Probanden – sie allein bindet rund die Hälfte einer realistischen IK-IV-Semesterlast (bisher 66–108,5 P je Semester).* |
| luecke | KRITISCH | Chirurgie/Implantologie ist ebenfalls komplett leer: 0 von 16 Mindestpunkten (0 %). – *Keine chir_*-Leistung in IK I–III. Die Lücke ist absolut kleiner als bei KFO, besteht aber aus vier 1-Punkt-Leistungsarten (je 4× soll) und wäre didaktisch früh und niederschwellig zu füllen gewesen – sie blieb dennoch drei Semester unbearbeitet.* |
| mindestanforderung | KRITISCH | Zahnhartsubstanz/Prävention/Restauration steht bei 26,5 von 55 Punkten = 48 % – Ampel 'gering' (<50 %). – *IK I 15,0 + IK II 4,0 + IK III 7,5 = 26,5 P. Der Verlauf ist zudem rückläufig statt aufbauend. Innerhalb der Kategorie wurde zhs_fuell_5 (Klasse-V-Füllung, Soll 2 Stück) in keinem Semester erbracht. Ampel gemäß Regel: >=75 % gut, 50–75 % mittel, <50 % gering.* |
| ausgewogenheit | relevant | Starke Klumpenbildung in der Prothetik: 144 von insgesamt 270 erbrachten Punkten (53 %) entfallen auf eine Kategorie; Soll-Übererfüllung 124 %. – *Allein proth_krone summiert sich auf 102 P (IK I 30 + IK II 72), davon 72 P in einem einzigen Semester (66 % der IK-II-Last). Diese Kapazität fehlt spiegelbildlich in ZHS, Chirurgie und KFO. Auch Endodontologie (125 %) und Kinderzahnheilkunde (150 %) sind übererfüllt, während zwei Kategorien bei 0 % stehen.* |
| reihenfolge | relevant | Kein einfach-zu-schwer-Verlauf über die Semester erkennbar: bereits IK I trägt 58 % der Punkte auf Demo-Schwierigkeit 3 (u. a. proth_krone 30 P), IK II sogar 71 %, IK III 59 %. – *Berechnung: IK I 38/66 P Schwierigkeit 3 (pa_ait 8 + proth_krone 30); IK II 77/108,5 (endo 5 + proth_krone 72); IK III 56/95,5 (endo 20 + pa_ait 16 + proth_totalprothese 20). Eine didaktische Progression würde den Schwierigkeit-3-Anteil ansteigen lassen – hier ist er von Beginn an hoch. ACHTUNG: Diese Aussage beruht vollständig auf den DEMO-Schwierigkeitsgraden (heuristische Platzhalter laut meta.bekannte_luecken, Lehrenden-Konsens steht aus).* |
| mindestanforderung | Hinweis | Parodontologie liegt bei 28,5 von 32 Punkten = 89 % – Ampel 'gut', aber mit kleiner Restlücke von 3,5 P. – *pa_ait ist mit 24 P (IK I 8 + IK III 16) exakt auf Soll (3 Patienten à 8 P); die Restlücke liegt allein bei pa_upt (4,5 P erbracht, Soll 4 Sitzungen à 2–3 P = 8–12 P). Mit ca. 2 UPT-Sitzungen in IK IV geschlossen – gut machbar.* |
| reihenfolge | Hinweis | Limitation: Aussagen zur Reihenfolge INNERHALB eines Semesters sind nicht möglich, da Punkte je Semester aggregiert vorliegen. – *Laut meta.bekannte_luecken existieren keine Einzeltermine. Alle Reihenfolge-Bewertungen in dieser Analyse beziehen sich daher ausschließlich auf den Vergleich ZWISCHEN den Semestern IK I → II → III; über die Abfolge innerhalb eines Semesters wird bewusst nicht spekuliert.* |
| inhalt | Hinweis | Positiv: Endodontologie (25/20 = 125 %), Kinderzahnheilkunde (12/8 = 150 %) und Schnittmenge Restauration/Prothetik (34/33 = 103 %) sind bereits vor IK IV vollständig erfüllt. Keine Blocksummen-Limitation: Stud. 2 hat keine Einträge mit Feld 'hinweis'. – *Endo wurde didaktisch sinnvoll gestaffelt (IK II 5 P Einstieg, IK III 20 P Vertiefung – auf Demo-Schwierigkeit 3). Anders als bei anderen Probanden sind alle Einträge von Stud. 2 nach Leistungsart aufgeschlüsselt; die Blocksummen-Limitation entfällt hier. Generelle Limitation bleibt: IK IV (SoSe26) fehlt in der Quelle (laufendes Semester).* |

### Optimierter Verlauf

**IK I** (retrospektiv) – Fokus: Einstiegslast entschärfen (Demo-Schwierigkeit 3 reduzieren), leere Kategorien früh anlegen – Semesterlast bleibt bei ca. 66 P

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Semester gesamt | Krone auf Zahn/Implantat (inkl. Stumpfaufbau) (`proth_krone`) | 15 | Reduktion von 30 auf 15 P: nur eine Krone (Demo-Schwierigkeit 3) im Einstiegssemester statt zwei – setzt 15 P Kapazität frei, Prothetik-Soll (116 P) bleibt über vier Semester sicher erreichbar. |
| Semester gesamt | MSH-Untersuchung + Planung oralchir. Eingriffe/DVT-Indikation (`chir_msh, chir_dvt`) | 4 | Je 2 Leistungen à 1 P: niederschwellige 1-Punkt-Leistungen als idealer Einstieg – die Kategorie Chirurgie/Implantologie blieb im Original drei Semester komplett leer. |
| Semester gesamt | KFO-Fall 1: Diagnostik-Start (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell`) | 4 | Beginn des ersten KFO-Falls mit einfachen 1-P-Diagnostikschritten – im Original blieb KFO (größte Lücke, 48 P) bis IK III unberührt. |
| Semester gesamt | Plastische definitive Füllungen Klasse V (`zhs_fuell_5`) | 2 | Soll-Leistung (2 Stück à 1 P, Demo-Schwierigkeit 1), die im Original nie erbracht wurde – passt didaktisch ins erste Semester. |
| Semester gesamt | Prophylaxesitzungen + kariologische Befunde (Aufstockung) (`zhs_prophylaxe, zhs_befund`) | 5.5 | zhs_prophylaxe 6 statt 3 P, zhs_befund 7,5 statt 5 P: einfache ZHS-Grundleistungen (Demo-Schwierigkeit 1) stärken die später schwächste Kategorie von Beginn an. |

**IK II** (retrospektiv) – Fokus: Prothetik-Klumpen (72 P Kronen = 66 % der Semesterlast) entzerren und zugunsten leerer Kategorien umverteilen – Semesterlast bleibt bei ca. 108,5 P

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Semester gesamt | Krone auf Zahn/Implantat (inkl. Stumpfaufbau) (`proth_krone`) | 42 | Reduktion von 72 auf 42 P: die extreme Klumpung in einem Semester war didaktisch und organisatorisch unausgewogen; 30 P werden für unterversorgte Kategorien frei. |
| Semester gesamt | Implantat-prothetische Beratung + Implantatnachsorge (`chir_impl_beratung, chir_impl_nachsorge`) | 8 | Je 4 Leistungen à 1 P – damit wäre die Kategorie Chirurgie/Implantologie (16 P) bereits nach IK II vollständig erfüllt gewesen. |
| Semester gesamt | KFO-Fall 1: Diagnostik-Abschluss + 3 Kontrollsitzungen (`kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion, kfo_kontrolle`) | 6.5 | 5 × 1 P Fallabschluss plus 3 Kontrollen à 0,5 P – Fall 1 wäre damit komplett (12 P), erster Baustein gegen die 48-P-Lücke. |
| Semester gesamt | KFO-Fall 2: Diagnostik-Start (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell`) | 4 | Kontinuierlicher Fallaufbau statt Nullrunde: pro Semester ein KFO-Fall angehen, damit die Kontrollsitzungen (6 je Fall) realistisch über die Zeit verteilbar sind. |
| Semester gesamt | Füllungen Kl. I/II + Befunde + UPT (Aufstockung) (`zhs_fuell_1_2, zhs_befund, pa_upt`) | 11.5 | zhs_fuell_1_2 +6 P, zhs_befund +4 P, pa_upt +1,5 P: ZHS sackte im Original in IK II auf 4 P ab; die UPT-Aufstockung hätte die PA-Restlücke früh geschlossen. |

**IK III** (retrospektiv) – Fokus: Übererfüllte Kategorien (Endo 125 %, KZH 150 %, Prothetik) auf Soll begrenzen, freie Kapazität in KFO investieren – Semesterlast bleibt bei ca. 95,5 P

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Semester gesamt | Wurzelkanalaufbereitung + -füllung (`endo_aufbereitung, endo_fuellung`) | 15 | 9 + 6 statt 12 + 8 P: zusammen mit IK II (5 P) ist das Endo-Soll (20 P) damit exakt erfüllt; 5 P Übererfüllung werden zugunsten leerer Kategorien abgebaut. Demo-Schwierigkeit 3 bleibt sinnvoll im dritten Semester platziert. |
| Semester gesamt | KZH-Befund + Behandlung (`kzh_befund, kzh_behandlung`) | 4 | 4 statt 8 P: das KZH-Soll (8 P) wäre mit IK II (4 P) + reduziertem IK III bereits erreicht – 4 P Übererfüllung werden frei. |
| Semester gesamt | Interimsprothese (Ersatz ≥1 Stützzone) (`proth_interims`) | 0 | Streichen (−10 P): Prothetik ist zu diesem Zeitpunkt auch ohne diese Leistung übererfüllt; die 10 P sind in der KFO-Lücke deutlich wirksamer. |
| Semester gesamt | KFO-Fall 2: Abschluss + KFO-Fall 3: Diagnostik (`kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion, kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell`) | 14 | Fall 2 komplettieren (5 P) und Fall 3 vollständig diagnostizieren (9 P): nach IK III wären damit ca. 24,5 von 48 KFO-Punkten erreicht statt 0 – IK IV müsste nur noch die Hälfte tragen. |
| Semester gesamt | KFO-Kontrollsitzungen + Füllungen Kl. III/IV (Aufstockung) (`kfo_kontrolle, zhs_fuell_3_4`) | 5 | 6 Kontrollen à 0,5 P (3 P) + 2 P zusätzliche Füllungen: hält KFO-Fälle im Recall und stützt die ZHS-Kategorie weiter. |

**IK IV** (prospektiv) – Fokus: 14-Wochen-Plan, ca. 97 P (im Rahmen der bisherigen Semesterlasten 66–108,5 P): schließt KFO (48 P), Chirurgie (16 P), ZHS (29 P) und PA-Rest (4 P) vollständig – keine Demo-Schwierigkeit-3-Leistungen nötig, da Endo/Prothetik bereits übererfüllt

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| W1–2 | Systematische Untersuchung der Mundschleimhaut (4 Untersuchungen à 1 P) (`chir_msh`) | 4 | Niederschwelliger Einstieg in die leere Kategorie Chirurgie/Implantologie (0 %); 1-P-Leistungen sind gut in die ersten Behandlungstermine integrierbar. |
| W1–3 | KFO-Fall 1: kompletter Diagnostik-Durchlauf (9 × 1 P) (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion`) | 9 | Größte Lücke (48 P) sofort angehen; früher Fallstart ist Pflicht, damit die 6 Kontrollsitzungen je Fall noch im Semester liegen können. |
| W2–4 | Prophylaxesitzung MuHy + PZR (3 Sitzungen à 1,5 P) (`zhs_prophylaxe`) | 4.5 | ZHS steht bei 48 % (Ampel gering); Prophylaxe (Demo-Schwierigkeit 1) ist planbar und terminstabil – idealer kontinuierlicher Baustein. |
| W3–5 | KFO-Fall 2: kompletter Diagnostik-Durchlauf (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion`) | 9 | Gestaffelter Fallaufbau (1 neuer Fall alle ~2 Wochen) verteilt die 48-P-Lücke gleichmäßig und vermeidet Klumpung am Semesterende. |
| W3–6 | Plastische Füllungen Klasse I und II (ca. 4–6 Füllungen) (`zhs_fuell_1_2`) | 9 | Größter Einzelbaustein der ZHS-Lücke; Demo-Schwierigkeit 2 – nach den Einstiegswochen gut platziert, Patientenpool aus Befunden der Vorwochen. |
| W4–6 | Planung oralchir. Eingriffe / DVT-Indikation (4 Planungen à 1 P) (`chir_dvt`) | 4 | Zweiter Chirurgie-Baustein; Planungsleistungen lassen sich mit den laufenden Befundterminen koppeln. |
| W5–7 | KFO-Fall 3: kompletter Diagnostik-Durchlauf (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion`) | 9 | Fortsetzung der Fallstaffel zur Semestermitte. |
| W6–9 | Kariologischer Befund, Kariesrisiko, Therapieplanung (3 Befunde à 2,5 P) (`zhs_befund`) | 7.5 | Schließt die Befund-Teillücke in ZHS und generiert zugleich Patienten für die Füllungstherapie der Folgewochen. |
| W7–9 | Implantat-prothetische Beratung (4 Beratungen à 1 P) (`chir_impl_beratung`) | 4 | Dritter Chirurgie-Baustein; Beratungen sind mit dem übererfüllten Prothetik-Erfahrungsschatz des Probanden fachlich gut hinterlegt. |
| W8–10 | KFO-Fall 4: kompletter Diagnostik-Durchlauf (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion`) | 9 | Letzter der vier Fälle (4 × 12 P = 48 P Kategoriesoll); Start spätestens W8, damit die Kontrollsitzungen noch ins Semester passen. |
| W9–11 | Plastische definitive Füllungen Klasse III/IV (2–3 Füllungen) (`zhs_fuell_3_4`) | 6 | Anspruchsvollere Füllungsklasse (Demo-Schwierigkeit 2) bewusst in der zweiten Semesterhälfte – nach Routineaufbau durch Kl. I/II. |
| W10–12 | Implantatnachsorge (4 Sitzungen à 1 P) (`chir_impl_nachsorge`) | 4 | Letzter Chirurgie-Baustein – Kategorie damit bei 16/16 P (100 %). |
| W10–13 | KFO-Kontrollsitzungen (24 Sitzungen à 0,5 P, 6 je Fall) (`kfo_kontrolle`) | 12 | Kontrollen aller vier Fälle gebündelt in der Schlussphase; kurze 0,5-P-Einheiten sind parallel zum übrigen Programm terminierbar. |
| W11–13 | Plastische definitive Füllungen Klasse V (2 Füllungen à 1 P) (`zhs_fuell_5`) | 2 | Einzige nie erbrachte ZHS-Soll-Leistung (Demo-Schwierigkeit 1) – schließt die letzte inhaltliche Teillücke der Kategorie. |
| W12–14 | Unterstützende Parodontitistherapie / Recall (2 Sitzungen à 2 P) (`pa_upt`) | 4 | Schließt die PA-Restlücke (28,5 → 32,5 P); UPT-Recalls passen natürlich ans Semesterende und stärken das Soll von 4 UPT-Sitzungen. |

### Auswirkungen auf die Kompetenzentwicklung

| Kategorie | Ende IK III (Ist) | Ende IK IV (optimiert, projiziert) | Kommentar |
|---|---|---|---|
| Parodontologie | 89 % | 100 % | 28,5/32 P = 89 % (gut). Plan: +4 P pa_upt (W12–14) → 32,5/32 = 102 %, gedeckelt 100 %. |
| Zahnhartsubstanz/Prävention/Restauration | 48 % | 100 % | 26,5/55 P = 48 % (Ampel gering). Plan: +29 P (Prophylaxe 4,5 + Füllungen Kl. I/II 9 + Befunde 7,5 + Kl. III/IV 6 + Kl. V 2) → 55,5/55 = 101 %, gedeckelt 100 %. |
| Endodontologie | 100 % | 100 % | 25/20 P = 125 %, gedeckelt 100 % – bereits erfüllt, keine IK-IV-Punkte eingeplant. |
| Kinderzahnheilkunde | 100 % | 100 % | 12/8 P = 150 %, gedeckelt 100 % – bereits erfüllt, keine IK-IV-Punkte eingeplant. |
| Prothetik | 100 % | 100 % | 144/116 P = 124 %, gedeckelt 100 % – bereits deutlich übererfüllt, keine IK-IV-Punkte eingeplant. |
| Schnittmenge Restauration/Prothetik | 100 % | 100 % | 34/33 P = 103 %, gedeckelt 100 % – bereits erfüllt, keine IK-IV-Punkte eingeplant. |
| Chirurgie/Implantologie | 0 % | 100 % | 0/16 P = 0 % (komplette Lücke). Plan: +16 P (chir_msh 4, chir_dvt 4, chir_impl_beratung 4, chir_impl_nachsorge 4) → 16/16 = 100 %. |
| Kieferorthopädie (KFO) | 0 % | 100 % | 0/48 P = 0 % (größte Lücke). Plan: 4 komplette KFO-Fälle à 9 P Diagnostik (36 P) + 24 Kontrollsitzungen à 0,5 P (12 P) → 48/48 = 100 %. |

## Stud. 3

**Fazit:** Stud. 3 hat nach drei von vier Semestern mit 299,5 von 328 Punkten (91 %) ein sehr gutes Gesamtvolumen, aber eine deutlich schiefe Verteilung: Prothetik (131 %), KZH (200 %), ZHS (134 %) und Endo (125 %) sind übererfüllt, während Schnittmenge Restauration/Prothetik bei 9 % steht und Chirurgie/Implantologie sowie KFO komplett leer sind (je 0 %). Die verbleibenden 96,5 Pflichtpunkte entsprechen fast einer vollen Semesterlast dieses Probanden (bisher 88,5–115,5 P je IK) – der vorgeschlagene 14-Wochen-Plan für IK IV (ca. 6,9 P/Woche, unter der IK-III-Last von 8,25 P/Woche) schließt alle Lücken auf 100 %, lässt aber wenig Puffer; kritischster Posten sind die 4 KFO-Fälle. Retrospektiv wäre die Schieflage vermeidbar gewesen, indem pro Semester ca. 15 P Kronen-Überschuss in die leeren Kategorien umgelenkt worden wären; selbst dann bliebe KFO teilweise ein IK-IV-Thema. Limitationen: Schwierigkeitsgrade und Zeitwerte sind DEMO-Platzhalter (alle darauf gestützten Reihenfolge-Aussagen vorläufig, Lehrenden-Rating ausstehend); Punkte liegen nur semesteraggregiert vor (keine Aussagen zur Reihenfolge innerhalb eines Semesters); IK IV fehlt quellbedingt. Für Stud. 3 enthält der korrigierte Export keine unaufgeschlüsselten Blocksummen ('hinweis'-Einträge), die Summen wurden programmatisch verifiziert.

### Befunde (Prüfung Reihenfolge & Inhalt vs. Originalstand)

| Aspekt | Schweregrad | Befund |
|---|---|---|
| mindestanforderung | KRITISCH | Ampel Ende IK III: 5 von 8 Kategorien 'gut' (Zahnhartsubstanz 134 %, Endodontologie 125 %, Kinderzahnheilkunde 200 %, Prothetik 131 % – jeweils auf 100 % gedeckelt; Parodontologie 92 %), aber 3 von 8 Kategorien 'gering': Schnittmenge Restauration/Prothetik 9 % (3 von 33 P), Chirurgie/Implantologie 0 % (0 von 16 P), KFO 0 % (0 von 48 P). – *Exakt aus kategorien_summen vs. Katalog-Mindestpunkten gerechnet: Paro 29,5/32 = 92 %; ZHS 73,5/55; Endo 25/20; KZH 16/8; Prothetik 152,5/116; Schnittmenge 3/33 = 9 %; Chirurgie und KFO ohne jeden Eintrag. Ampelregel der Quelle: >=75 % gut, 50–75 % mittel, <50 % gering.* |
| luecke | KRITISCH | Zwei Kategorien komplett ohne Leistungen über alle drei erfassten Semester: Chirurgie/Implantologie (16 P Soll) und Kieferorthopädie (48 P Soll). Zusammen mit dem Schnittmengen-Rest (30 P) und dem Paro-Rest (2,5 P) müssen 96,5 P vollständig in IK IV erbracht werden. – *In den Semesterlisten von Stud. 3 taucht kein einziger chir_*- oder kfo_*-Code auf; Schnittmenge nur einmal (schnitt_stumpfaufbau, 3 P, IK II). 96,5 P entsprechen ungefähr einer vollen Semesterlast dieses Probanden (bisher 88,5 / 95,5 / 115,5 P je IK) – machbar, aber ohne jeden Puffer für Ausfälle oder Patientenabsagen.* |
| ausgewogenheit | relevant | Starke Klumpenbildung in der Prothetik: 60 P in IK I (68 % der Semesterpunkte), 47,5 P in IK II (50 %), 45 P in IK III (39 %) – insgesamt 152,5 P und damit 131 % des Prothetik-Solls, während drei andere Kategorien (fast) leer sind. Auch KZH (200 %) und ZHS (134 %) sind deutlich übererfüllt. – *Die Übererfüllung bindet Kapazität: Prothetik +36,5 P, ZHS +18,5 P, KZH +8 P und Endo +5 P über Soll ergeben zusammen ca. 68 P, die rechnerisch für Chirurgie, KFO und Schnittmenge gefehlt haben. Das Gesamtvolumen (299,5 von 328 P = 91 % nach 3 von 4 Semestern) ist gut – das Problem ist die Verteilung, nicht der Fleiß.* |
| reihenfolge | relevant | Kein 'einfach → schwer'-Verlauf erkennbar: Bereits IK I besteht zu ca. 51 % aus Leistungen der Demo-Schwierigkeit 3 (45 P proth_krone von 88,5 P gesamt); der Schwierigkeit-3-Anteil bleibt danach ähnlich hoch (IK II ca. 61 %, IK III ca. 59 %). Umgekehrt startet die Endodontologie (Schwierigkeit 3) erst in IK II statt mit einfachen Vorleistungen in IK I. – *Basierend auf den DEMO-Schwierigkeitsgraden (heuristische Platzhalter, Lehrenden-Konsens steht laut meta.bekannte_luecken aus) – diese Aussage ist daher vorläufig. Zusätzliche Limitation: Punkte sind je Semester aggregiert, die Reihenfolge INNERHALB eines Semesters ist aus den Daten nicht ableitbar; bewertbar ist nur der Verlauf zwischen den Semestern.* |
| inhalt | Hinweis | Datenqualität für diesen Probanden: Stud. 3 enthält in diesem Export keine als 'hinweis' markierten, nicht aufgeschlüsselten Blocksummen – alle Einträge sind einer Leistungsart zugeordnet. Die Summenprüfung (Einzeleinträge vs. kategorien_summen) geht für alle Kategorien exakt auf. – *Programmatisch nachgerechnet: Semesterlisten summieren sich exakt auf die hinterlegten kategorien_summen (IK I 88,5 P, IK II 95,5 P, IK III 115,5 P). Die generelle Blocksummen-Limitation des korrigierten Imports betrifft andere Probanden, nicht Stud. 3. IK IV fehlt quellbedingt (laufendes Semester).* |

### Optimierter Verlauf

**IK I** (retrospektiv) – Fokus: Prothetik-Klumpen entzerren, leichte Einstiegsleistungen aus Chirurgie und KFO-Diagnostik vorziehen (Semesterlast bleibt bei ca. 90 P statt 88,5 P; keine Wochenauflösung möglich, da Punkte nur semesteraggregiert vorliegen)

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| IK-weit (retrospektiv, keine Wochenauflösung) | Krone auf Zahn/Implantat (inkl. Stumpfaufbau) (`proth_krone`) | 30 | Statt 45 P nur ca. 30 P (2 statt 3 Kronen-Äquivalente): Schwierigkeit-3-Leistungen (Demo-Wert) gehören nicht massiert ins erste klinische Semester; 15 P werden frei. |
| IK-weit (retrospektiv, keine Wochenauflösung) | Systematische MSH-Untersuchung (4x) + Planung oralchir. Eingriffe/DVT-Indikation (4x) (`chir_msh, chir_dvt`) | 8 | Leichte 1-Punkt-Leistungen – idealer Einstieg im ersten Semester und schließt die Chirurgie-Kategorie zur Hälfte, die real bei 0 P blieb. |
| IK-weit (retrospektiv, keine Wochenauflösung) | KFO-Falldiagnostik Fall 1 (Erstgespräch bis Röntgenbefund) (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_foto, kfo_roentgen`) | 6 | KFO-Diagnostikkette besteht aus 1-Punkt-Leistungen und kann früh beginnen; real blieb KFO bis Ende IK III bei 0 P. |
| IK-weit (retrospektiv, keine Wochenauflösung) | adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 3 | Mittlere Schwierigkeit (Demo-Wert 2), koppelt sinnvoll an die ohnehin laufenden Kronenversorgungen – Schnittmengen-Kategorie startet nicht bei 0. |

**IK II** (retrospektiv) – Fokus: Zweite Kronen-Welle (45 P) halbieren, freiwerdende Kapazität in Schnittmenge und KFO-Planung lenken (Semesterlast ca. 98 P statt 95,5 P)

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| IK-weit (retrospektiv, keine Wochenauflösung) | Krone auf Zahn/Implantat (inkl. Stumpfaufbau) (`proth_krone`) | 30 | Statt 45 P ca. 30 P – zusammen mit der IK-I-Reduktion sinkt Prothetik auf 122,5 P und bleibt trotzdem über dem Soll von 116 P (106 %). |
| IK-weit (retrospektiv, keine Wochenauflösung) | Inlay oder Teilkrone (inkl. Stumpfaufbau) (`schnitt_inlay`) | 12 | Größter Einzelposten der Schnittmengen-Kategorie (12–15 P); fachlich naheliegend bei vorhandener Kronen-Routine dieses Probanden. |
| IK-weit (retrospektiv, keine Wochenauflösung) | Stiftaufbau (`schnitt_stiftaufbau`) | 3 | Koppelt an die in IK II real laufenden Endo-Leistungen (endo_aufbereitung/endo_fuellung) – Synergie Endo → Stiftaufbau. |
| IK-weit (retrospektiv, keine Wochenauflösung) | KFO Fall 1: 3D-Analyse, Behandlungsplan, Konstruktionszeichnung + 6 Kontrollsitzungen (`kfo_3d, kfo_plan, kfo_konstruktion, kfo_kontrolle`) | 6 | Führt den in IK I diagnostizierten KFO-Fall zu Ende (Fall komplett = 12 P); KFO erreicht damit retrospektiv 25 % statt 0 %. |
| IK-weit (retrospektiv, keine Wochenauflösung) | Implantat-prothetische Beratung (4x) (`chir_impl_beratung`) | 4 | Leichte 1-Punkt-Leistungen, gut zwischen Prothetik-Terminen platzierbar; Chirurgie steigt auf 12 von 16 P. |

**IK III** (retrospektiv) – Fokus: Befund-Überschüsse (ZHS, KZH) leicht reduzieren, Paro-Soll schließen, Chirurgie komplettieren, zweiten Schnittmengen-Baustein setzen (Semesterlast ca. 116 P wie real 115,5 P)

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| IK-weit (retrospektiv, keine Wochenauflösung) | Unterstützende Parodontitistherapie (1 zusätzliche Sitzung) (`pa_upt`) | 2.5 | Schließt die Paro-Lücke von 2,5 P (29,5 → 32 P = 100 %); geringer Aufwand, hohe Wirkung auf die Ampel. |
| IK-weit (retrospektiv, keine Wochenauflösung) | Kariesbedingte Reparatur Kronenrand + weiterer adhäsiver Stumpfaufbau (`schnitt_reparatur, schnitt_stumpfaufbau`) | 6 | Schnittmenge erreicht damit retrospektiv 27 von 33 P (82 %, 'gut') statt real 9 %. |
| IK-weit (retrospektiv, keine Wochenauflösung) | Implantatnachsorge (4x) (`chir_impl_nachsorge`) | 4 | Komplettiert Chirurgie/Implantologie auf 16 von 16 P (100 %) statt real 0 %. |
| IK-weit (retrospektiv, keine Wochenauflösung) | Kariologische Befunde ca. 6,5 statt 12,5 P; KZH-Befunde ca. 2 statt 5 P (`zhs_befund, kzh_befund`) | 8.5 | Reduktion der Befund-Überschüsse (ZHS 134 %, KZH 200 % Soll-Erfüllung) um ca. 9 P schafft die Kapazität für die obigen Ergänzungen, ohne dass eine Kategorie unter ihr Soll fällt. |

**IK IV** (prospektiv) – Fokus: 14-Wochen-Plan zum Schließen der realen Lücken: KFO 48 P (4 komplette Fälle a 12 P), Schnittmenge 30 P, Chirurgie 16 P, Paro-Rest 2,5 P – Gesamt 96,5 P (ca. 6,9 P/Woche, unter der bisherigen IK-III-Last von 8,25 P/Woche, also machbar mit Puffer). Anspruchsvolle Leistungen (Inlays; Demo-Schwierigkeit) bewusst nicht in die ersten Wochen gelegt.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| 1–2 | 4x Systematische MSH-Untersuchung + 4x Planung oralchir. Eingriffe/DVT-Indikation (`chir_msh, chir_dvt`) | 8 | Leichte 1-Punkt-Leistungen als Einstieg (Schwierigkeit laut Demo-Heuristik niedrig) – halbiert die Chirurgie-Lücke sofort. |
| 1–3 | KFO Fall A: komplette Diagnostik- und Planungskette (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion`) | 9 | KFO ist mit 48 P die größte Lücke – Fall A muss sofort starten, damit die 6 Kontrollsitzungen über das Semester verteilt werden können. |
| 2–4 | 1 UPT-Sitzung (`pa_upt`) | 2.5 | Schließt den Paro-Rest (29,5 → 32 P = 100 %); minimaler Aufwand, früh terminieren wegen Recall-Logik. |
| 4–6 | 1x adhäsiver Stumpfaufbau + 1x Stiftaufbau (`schnitt_stumpfaufbau, schnitt_stiftaufbau`) | 6 | Mittlere Schwierigkeit (Demo-Wert 2) als Aufbaustufe vor den Inlays; nutzt die vorhandene Endo-/Kronen-Routine des Probanden. |
| 4–14 (laufend) | KFO Fall A: 6 Kontrollsitzungen a 0,5 P (`kfo_kontrolle`) | 3 | Vervollständigt Fall A auf 12 P; Kontrollen sind kurz und parallel zu allen anderen Blöcken planbar. |
| 5–8 | Inlay oder Teilkrone Nr. 1 (inkl. Stumpfaufbau) (`schnitt_inlay`) | 12 | Anspruchsvollster Einzelposten (12–15 P) – bewusst erst nach der Warm-up-Phase; Proband hat aus 152,5 Prothetik-P nachweislich die nötige Kronen-Routine. |
| 6–9 | KFO Fall B: kompletter Durchlauf (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion, kfo_kontrolle`) | 12 | Zweiter von vier KFO-Fällen (4 x 12 P = 48 P Soll); gestaffelter Start verteilt die Kontrollsitzungen realistisch. |
| 8–10 | 4x Implantat-prothetische Beratung (`chir_impl_beratung`) | 4 | Kurze Beratungsleistungen, flexibel zwischen die laufenden Fälle legbar; Chirurgie bei 12 von 16 P. |
| 9–12 | Inlay oder Teilkrone Nr. 2 (inkl. Stumpfaufbau) (`schnitt_inlay`) | 12 | Bringt die Schnittmenge auf exakt 33 P (3 + 6 + 12 + 12); Soll-Anzahl des Katalogs ist 1 Stück – das zweite Inlay/die Teilkrone dient der Punkteerfüllung der Kategorie (alternativ 4x kleinere Schnittmengen-Leistungen, sofern Patientenangebot). |
| 10–13 | KFO Fall C: kompletter Durchlauf (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion, kfo_kontrolle`) | 12 | Dritter KFO-Fall; Diagnostikleistungen sind kurz genug, um zwei Fälle parallel zu führen. |
| 11–14 | KFO Fall D: kompletter Durchlauf (`kfo_erstgespraech, kfo_anamnese, kfo_abformung, kfo_modell, kfo_3d, kfo_foto, kfo_roentgen, kfo_plan, kfo_konstruktion, kfo_kontrolle`) | 12 | Vierter Fall komplettiert die 48 KFO-P. Risiko: Kontrollsitzungen der spät startenden Fälle drängen sich in Wochen 12–14 – bei Engpass Fälle C/D eine Woche vorziehen (Puffer von ca. 1,4 P/Woche ist vorhanden). |
| 12–14 | 4x Implantatnachsorge (`chir_impl_nachsorge`) | 4 | Komplettiert Chirurgie/Implantologie auf 16 von 16 P; Nachsorgen passen ans Semesterende. |

### Auswirkungen auf die Kompetenzentwicklung

| Kategorie | Ende IK III (Ist) | Ende IK IV (optimiert, projiziert) | Kommentar |
|---|---|---|---|
| Parodontologie | 92 % | 100 % | 29,5/32 P = 92 % (gut). Plan: +2,5 P pa_upt in Wochen 2–4 → 32/32 P. |
| Zahnhartsubstanz/Prävention/Restauration | 100 % | 100 % | 73,5/55 P = 134 %, auf 100 gedeckelt. Bereits übererfüllt – im IK-IV-Plan bewusst keine weiteren ZHS-Punkte. |
| Endodontologie | 100 % | 100 % | 25/20 P = 125 %, gedeckelt auf 100. Soll erfüllt, keine IK-IV-Maßnahme nötig. |
| Kinderzahnheilkunde | 100 % | 100 % | 16/8 P = 200 %, gedeckelt auf 100. Deutlich übererfüllt, keine IK-IV-Maßnahme. |
| Prothetik | 100 % | 100 % | 152,5/116 P = 131 %, gedeckelt auf 100. Größter Überschuss (+36,5 P) – im Plan keine weitere Prothetik, die Routine wird stattdessen für die Schnittmengen-Inlays genutzt. |
| Schnittmenge Restauration/Prothetik | 9 % | 100 % | 3/33 P = 9 % (gering). Plan: +6 P Stumpf-/Stiftaufbau + 2x Inlay/Teilkrone a 12 P → 33/33 P. |
| Chirurgie/Implantologie | 0 % | 100 % | 0/16 P (Komplettlücke). Plan: je 4x MSH, DVT-Planung, Implantatberatung, Implantatnachsorge (16 x 1 P) → 16/16 P. |
| Kieferorthopädie (KFO) | 0 % | 100 % | 0/48 P (größte Komplettlücke). Plan: 4 komplette KFO-Fälle a 12 P, gestaffelt ab Woche 1 → 48/48 P. Engster Posten des Plans (Patientenverfügbarkeit für 4 Fälle prüfen). |

## Stud. 4

**Fazit:** Stud. 4 zeigt einen didaktisch grundsätzlich plausiblen Verlauf (punktegewichtete Demo-Schwierigkeit 1,69 → 2,15 → 2,07, also einfach → schwer zwischen den Semestern; Aussage Demo-basiert und nur zwischen, nicht innerhalb der Semester möglich), aber eine deutliche inhaltliche Schieflage: Endo (125 %), KZH (213 %) und Paro (133 %) sind übererfüllt, während Chirurgie/Implantologie und KFO nach drei Semestern komplett leer sind und Prothetik (53 %) sowie die Schnittmenge (9 %) weit unter dem Minimum liegen. Gesamtstand Ende IK III: 195/328 P = 59 %, Restlücke 157,5 P bei bisherigen Semesterlasten von 59–74 P. Der vorgeschlagene IK-IV-Plan (78,5 P, 14 Wochen) schließt Chirurgie (100 %) und ZHS (100 %) vollständig, hebt Prothetik und Schnittmenge auf je 73 % und startet die KFO mit einem Diagnostikfall (19 %) – projizierter Gesamtstand Ende IK IV: 273,5/328 P = 83 %. Die verbleibende KFO-Lücke (39 P) ist individuell nicht mehr aufholbar und sollte als strukturelles Problem (fehlender KFO-Zugang in IK I–III) an die Kursleitung zurückgemeldet werden. Limitationen: Schwierigkeit/Zeit sind Demo-Platzhalter (für nie erbrachte Chirurgie-/KFO-Codes fehlen sie ganz), IK IV fehlt in der Quelle, Punkte sind je Semester aggregiert; Blocksummen-Einträge ('hinweis') existieren bei Stud. 4 nicht – diese Limitation entfällt hier.

### Befunde (Prüfung Reihenfolge & Inhalt vs. Originalstand)

| Aspekt | Schweregrad | Befund |
|---|---|---|
| luecke | KRITISCH | Zwei Kategorien komplett ohne Leistungen über IK I–III: Chirurgie/Implantologie (0/16 P) und Kieferorthopädie (0/48 P). – *In kategorien_summen und in allen Semester-Einzeleinträgen von Stud. 4 taucht kein einziger chir_*- oder kfo_*-Code auf. Zusammen fehlen 64 Punkte allein aus diesen beiden Kategorien – die KFO-Lücke (48 P) ist bei bisherigen Semesterlasten von 59–74 P in einem einzigen Semester strukturell nicht mehr vollständig schließbar.* |
| mindestanforderung | KRITISCH | Ampel Ende IK III: 4× gut/übererfüllt (Paro 133 %, Endo 125 %, KZH 213 %, jeweils auf 100 % gedeckelt; ZHS 85 %), Prothetik 53 % (mittel), Schnittmenge Restauration/Prothetik 9 % (gering), Chirurgie und KFO 0 % (gering). Gesamt 195/328 P = 59 %. – *Exakt aus kategorien_summen ÷ Katalog-Mindestpunkte gerechnet: Paro 42,5/32; ZHS 46,5/55; Endo 25/20; KZH 17/8; Prothetik 61/116; Schnittmenge 3/33; Chir 0/16; KFO 0/48. Offene Restlücke zu allen Mindestpunkten: 157,5 P – bei einer bisherigen Maximallast von 74 P/Semester ist selbst ein ambitioniertes IK IV nur eine Teilschließung.* |
| reihenfolge | Hinweis | Didaktische Reihenfolge zwischen den Semestern grob aufsteigend: punktegewichtete mittlere Demo-Schwierigkeit 1,69 (IK I) → 2,15 (IK II) → 2,07 (IK III). Abweichung: pa_ait (Schwierigkeit 3, 8 P) bereits im IK I. – *IK I ist klar von leichten Leistungen dominiert (Befunde, Prophylaxe, UPT, Recall – Stufe 1–2), die schweren Endo- und Kronen-Leistungen kommen erst ab IK II – das entspricht dem Prinzip einfach → schwer. Die AIT im IK I ist der einzige frühe Stufe-3-Block. WICHTIG: Beruht vollständig auf den DEMO-Schwierigkeitsgraden (Platzhalter laut meta.bekannte_luecken, Lehrenden-Konsens ausstehend). Da Punkte je Semester aggregiert sind, ist keine Aussage zur Reihenfolge INNERHALB eines Semesters möglich – nur der Semestervergleich.* |
| ausgewogenheit | relevant | Deutliche Schieflage: Übererfüllung in Paro (+10,5 P), Endo (+5 P) und KZH (+9 P über Minimum, 213 %), während zwei Kategorien leer bleiben und die Schnittmenge nur 3 P erhält. – *Rund 24,5 P wurden über das Kategorienminimum hinaus in bereits erfüllte Kategorien investiert (z. B. dritte AIT im IK III, 9 P KZH im IK III obwohl das Minimum von 8 P schon Ende IK II erreicht war). Diese Punkte hätten die Chirurgie-Lücke (16 P) vollständig und einen KFO-Einstieg decken können.* |
| inhalt | relevant | Prothetik-Profil schmal und repetitiv: nur 2× Klammermodellguss (je 15 P, IK I und IK III), 1× Kronenblock (21 P, IK II) und Recalls – trotz drei Semestern nur 53 %. Große Werkstücke (Total-/Teilprothese, Brücke, Teleskop) fehlen komplett; die Schnittmenge (Inlay/Teilkrone, Stift-/Stumpfaufbau, Reparatur) ist mit einem einzigen Stumpfaufbau (3 P) fast unberührt. – *Aus den Einzeleinträgen: proth_modellguss erscheint identisch in IK I und IK III statt einer Steigerung zu komplexeren prothetischen Arbeiten; schnitt_inlay, schnitt_reparatur und schnitt_stiftaufbau kommen nie vor. Die beiden größten Punktekategorien des Katalogs (Prothetik 116 P, Schnittmenge 33 P) sind damit die Hauptursache des Gesamtrückstands.* |
| inhalt | Hinweis | Datenqualität: Stud. 4 hat keine Einträge mit dem Feld 'hinweis' (nicht aufgeschlüsselte Blocksummen) – die Blocksummen-Limitation greift bei diesem Probanden nicht, alle Punkte sind einer Leistungsart zuordenbar. – *Prüfung aller Semester-Einträge: 0 Einträge mit 'hinweis'-Feld (im Gegensatz zu Stud. 1 und Stud. 5). Verbleibende Limitationen: IK IV fehlt in der Quelle (laufendes Semester), Schwierigkeit/Zeit sind Demo-Platzhalter, Punkte nur je Semester aggregiert.* |

### Optimierter Verlauf

**IK I** (retrospektiv) – Fokus: Leichter Einstieg beibehalten, aber Überhänge bei UPT/Befund/Recall (−6 P) in einen frühen Start der später leeren Kategorien Chirurgie und KFO umlenken. Semesterlast unverändert 59 P.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| 1–4 | Kariologischer Befund, Kariesrisiko, Therapieplanung (`zhs_befund`) | 7 | Leichter Einstieg (Demo-Stufe 1); 7 statt tatsächlich 9 P – Katalog-Soll (4 Befunde à 2–3 P) bleibt gedeckt, 2 P werden frei. |
| 1–6 | Prophylaxesitzung MuHy + PZR (`zhs_prophylaxe`) | 6 | Unverändert; leichte Leistung, gut für den Semesterstart. |
| 1–6 | Unterstützende Parodontitistherapie (UPT, Recall) (`pa_upt`) | 4 | 4 statt 6 P – Paro wird ohnehin übererfüllt; 2 P werden für leere Kategorien frei. |
| 3–8 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 8 | Unverändert; mittlere Schwierigkeit (Demo-Stufe 2) ab Semestermitte. |
| 3–8 | Plastische definitive Füllungen Klasse III/IV (`zhs_fuell_3_4`) | 2 | Unverändert. |
| 4–12 | Systematische Untersuchung der Mundschleimhaut (`chir_msh`) | 2 | NEU: kleine 1-P-Befundleistungen früh streuen statt Kategorie leer zu lassen (Schwierigkeit im Datensatz unbekannt, da Demo-Werte nur für erbrachte Codes vorliegen). |
| 4–12 | Planung oralchir. Eingriffe / Indikationsstellung DVT (`chir_dvt`) | 1 | NEU: Planungsleistung, gut parallel zu Befunden integrierbar. |
| 4–12 | Implantat-prothetische Beratung (`chir_impl_beratung`) | 1 | NEU: Beratungsleistung ohne großen Zeitblock. |
| 5–10 | Antiinfektiöse Parodontitistherapie (MHT, FMS, Reevaluation) (`pa_ait`) | 8 | Beibehalten, aber erst ab Semestermitte statt als früher Stufe-3-Block (didaktisch: schwer nach leicht; Demo-basiert). |
| 7–14 | Klammermodellgussprothese (Ersatz ≥1 Stützzone) (`proth_modellguss`) | 15 | Unverändert; großes Werkstück (Demo-Stufe 2) in der zweiten Semesterhälfte. |
| 9–14 | Recall (`proth_recall`) | 3 | 3 statt 5 P – Katalog-Soll (1 Sitzung, 2–3 P) bleibt erfüllt. |
| 10–14 | Erstaufnahmegespräch / KIG-Klassifizierung (`kfo_erstgespraech`) | 1 | NEU: KFO-Fallstart bereits im IK I, damit die 48-P-Kategorie nicht bis zuletzt leer bleibt. |
| 10–14 | KFO-Anamnese, Aufklärung, Epikrise (`kfo_anamnese`) | 1 | NEU: gehört zum selben KFO-Fall wie das Erstgespräch. |

**IK II** (retrospektiv) – Fokus: Kronenblock und Endo-Einstieg beibehalten; Überhänge bei UPT/KZH-Befund/Recall (−6 P) in den Einstieg der Schnittmenge (Stumpf- und Stiftaufbau) umlenken. Semesterlast unverändert 62 P.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| 1–4 | Kariologischer Befund, Kariesrisiko, Therapieplanung (`zhs_befund`) | 3 | Unverändert; leichter Einstieg. |
| 1–5 | Befund inkl. Planung (Milch-/Wechselgebiss) (`kzh_befund`) | 3.5 | 3,5 statt 4,5 P – KZH-Minimum (8 P) wird auch so bis Ende IK II fast erreicht; 1 P wird frei. |
| 1–6 | Individuelle, ausführliche Prophylaxesitzung (Milch-/Wechselgebiss) (`kzh_prophylaxe`) | 3.5 | Unverändert. |
| 2–7 | Unterstützende Parodontitistherapie (UPT, Recall) (`pa_upt`) | 5 | 5 statt 7,5 P – Paro-Minimum ist mit AIT-Serie gesichert; 2,5 P werden frei. |
| 3–8 | Antiinfektiöse Parodontitistherapie (MHT, FMS, Reevaluation) (`pa_ait`) | 8 | Unverändert; zweite von drei Soll-AITs. |
| 4–9 | Plastische definitive Füllungen Klasse III/IV (`zhs_fuell_3_4`) | 3 | Unverändert. |
| 5–10 | Wurzelkanalaufbereitung inkl. Arbeitslänge + Masterpoint (je Kanal) (`endo_aufbereitung`) | 3 | Unverändert; erster Endo-Kanal (Demo-Stufe 3) ab Semestermitte. |
| 6–11 | Wurzelkanalfüllung inkl. Röntgenkontrolle + adhäsive Deckfüllung (je Kanal) (`endo_fuellung`) | 2 | Unverändert; folgt auf die Aufbereitung. |
| 6–13 | Krone auf Zahn/Implantat (inkl. Stumpfaufbau) (`proth_krone`) | 21 | Unverändert; größter Block des Semesters (Demo-Stufe 3) in der zweiten Hälfte. |
| 8–13 | adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 3 | NEU: passt fachlich direkt zur Kronenversorgung – die Schnittmenge wäre so nicht bis IK III leer geblieben. |
| 8–13 | Stiftaufbau (`schnitt_stiftaufbau`) | 3 | NEU: gleicher Patientenkontext wie Krone/Stumpfaufbau, mittlere Schwierigkeit. |
| 10–14 | Prophylaxesitzung MuHy + PZR (`zhs_prophylaxe`) | 1.5 | Unverändert. |
| 12–14 | Recall (`proth_recall`) | 2.5 | 2,5 statt 5 P – Recall-Soll (1 Sitzung) bleibt erfüllt; 2,5 P werden frei. |

**IK III** (retrospektiv) – Fokus: Endo-Serie und Modellguss beibehalten; KZH-Übererfüllung (−7 P) sowie UPT-/Befund-Überhänge (−5 P) in die vollständige Schließung der Chirurgie-Kategorie umlenken. Semesterlast unverändert 74 P.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| 1–3 | Kariologischer Befund, Kariesrisiko, Therapieplanung (`zhs_befund`) | 2.5 | 2,5 statt 5 P – Befund-Soll ist längst übererfüllt; 2,5 P werden frei. |
| 1–4 | Prophylaxesitzung MuHy + PZR (`zhs_prophylaxe`) | 3 | Unverändert; leichter Einstieg. |
| 1–5 | Unterstützende Parodontitistherapie (UPT, Recall) (`pa_upt`) | 2.5 | 2,5 statt 5 P – UPT-Soll (4 Sitzungen) ist nach IK I+II erfüllt. |
| 2–6 | non-invasive / invasive Behandlung (`kzh_behandlung`) | 1 | Beibehalten (Soll 1 Behandlung); die übrigen 7 P KZH entfallen, da das Minimum (8 P) bereits Ende IK II praktisch erreicht war. |
| 2–6 | Individuelle, ausführliche Prophylaxesitzung (Milch-/Wechselgebiss) (`kzh_prophylaxe`) | 1 | Reduziert auf Restbedarf zum KZH-Minimum. |
| 3–10 | Wurzelkanalaufbereitung inkl. Arbeitslänge + Masterpoint (je Kanal) (`endo_aufbereitung`) | 12 | Unverändert; Endo-Hauptserie (Demo-Stufe 3) über die Semestermitte verteilt. |
| 4–8 | Antiinfektiöse Parodontitistherapie (MHT, FMS, Reevaluation) (`pa_ait`) | 8 | Unverändert; dritte AIT komplettiert das Katalog-Soll (3 Patienten). |
| 5–12 | Wurzelkanalfüllung inkl. Röntgenkontrolle + adhäsive Deckfüllung (je Kanal) (`endo_fuellung`) | 8 | Unverändert; folgt den Aufbereitungen. |
| 5–12 | Systematische Untersuchung der Mundschleimhaut (`chir_msh`) | 4 | NEU: 4 Untersuchungen à 1 P – mit den frei gewordenen KZH-/UPT-Punkten wäre die Chirurgie (16 P) bis Ende IK III vollständig schließbar gewesen. |
| 5–12 | Planung oralchir. Eingriffe / Indikationsstellung DVT (`chir_dvt`) | 4 | NEU: komplettiert das DVT-Soll (4 Planungen; 1 bereits retrospektiv in IK I)... punkte_ziel hier als 4er-Block angesetzt. |
| 6–13 | Klammermodellgussprothese (Ersatz ≥1 Stützzone) (`proth_modellguss`) | 15 | Beibehalten als realistisch erreichbares großes Werkstück; idealerweise wäre hier ein anderes Prothetik-Werkstück (z. B. Interimsprothese + Unterfütterung) gewählt worden, um das Spektrum zu verbreitern. |
| 7–12 | Implantat-prothetische Beratung (`chir_impl_beratung`) | 4 | NEU: Beratungsserie parallel zur Prothetik-Behandlung. |
| 8–13 | adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 3 | Unverändert (tatsächlich erbracht). |
| 9–13 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 1 | Unverändert. |
| 9–13 | Plastische definitive Füllungen Klasse III/IV (`zhs_fuell_3_4`) | 3 | Unverändert. |
| 10–14 | Plastische definitive Füllungen Klasse V (`zhs_fuell_5`) | 2 | Unverändert. |

**IK IV** (prospektiv) – Fokus: 14-Wochen-Plan mit 78,5 P (leicht über der bisherigen Höchstlast von 74 P, vertretbar durch viele kleine 1-P-Leistungen): Chirurgie vollständig schließen (+16), ZHS exakt schließen (+8,5), Schnittmenge (+21) und Prothetik (+24) maximal aufholen, KFO-Einstieg (+9). Priorisierung nach Lückengröße × Machbarkeit – die KFO-Restlücke (48 P) ist in einem Semester nicht vollständig schließbar und wird transparent nur angeteilt.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| 1–2 | Kariologischer Befund, Kariesrisiko, Therapieplanung (`zhs_befund`) | 3 | Leichter Einstieg (Demo-Stufe 1); Teil der ZHS-Restlücke von 8,5 P. |
| 1–2 | Prophylaxesitzung MuHy + PZR (`zhs_prophylaxe`) | 1.5 | Leichte Leistung zum Semesterstart; schließt zusammen mit Befund und Füllungen die ZHS exakt auf 55/55 P. |
| 1–3 | Systematische Untersuchung der Mundschleimhaut (`chir_msh`) | 4 | 4 Untersuchungen à 1 P (Katalog-Soll); Befundleistung, gut in die Anfangswochen streubar. Schwierigkeit unbekannt – Code wurde nie erbracht, kein Demo-Wert vorhanden. |
| 2–4 | Erstaufnahmegespräch / KIG-Klassifizierung (`kfo_erstgespraech`) | 1 | Start des einen realistisch machbaren KFO-Diagnostikfalls (9 Einzelleistungen à 1 P). |
| 2–4 | KFO-Anamnese, Aufklärung, Epikrise (`kfo_anamnese`) | 1 | Gleicher KFO-Fall, direkt nach dem Erstgespräch. |
| 2–4 | Abformung OK/UK, Scan, Registrat, Zielbiss (`kfo_abformung`) | 1 | Diagnostikunterlagen des KFO-Falls. |
| 2–4 | Modellherstellung (analog und digital) (`kfo_modell`) | 1 | Folgt unmittelbar auf die Abformung. |
| 3–5 | Planung oralchir. Eingriffe / Indikationsstellung DVT (`chir_dvt`) | 4 | 4 Planungen à 1 P (Katalog-Soll); Planungsleistungen ohne große Behandlungsblöcke. |
| 3–5 | Implantat-prothetische Beratung (`chir_impl_beratung`) | 4 | 4 Beratungen à 1 P (Katalog-Soll); parallel zur Prothetik-Planung sinnvoll. |
| 3–6 | Plastische Füllungen Klasse I und II (`zhs_fuell_1_2`) | 4 | Mittlere Schwierigkeit (Demo-Stufe 2); komplettiert die ZHS-Restlücke auf exakt 8,5 P. |
| 4–7 | adhäsiver Stumpfaufbau (`schnitt_stumpfaufbau`) | 3 | Schnittmengen-Aufbau (Demo-Stufe 2), fachlich Vorstufe zur Kronen-/Inlayversorgung ab Woche 6. |
| 4–7 | Stiftaufbau (`schnitt_stiftaufbau`) | 3 | Zweiter Aufbau (Demo-Stufe 2); nutzt denselben Patientenpool wie die prothetischen Arbeiten. |
| 5–8 | 3D-Modellanalyse (`kfo_3d`) | 1 | Auswertungsteil des KFO-Falls. |
| 5–8 | Foto/Gesichtsscan mit Auswertung (`kfo_foto`) | 1 | Auswertungsteil des KFO-Falls. |
| 5–8 | Rö, Befund OPG und FRS (`kfo_roentgen`) | 1 | Röntgenbefundung des KFO-Falls. |
| 5–8 | KFO-Behandlungsplan (`kfo_plan`) | 1 | Behandlungsplan als Abschluss der KFO-Diagnostik. |
| 5–8 | Konstruktionszeichnung Gerät / ClinCheck (`kfo_konstruktion`) | 1 | Komplettiert den KFO-Diagnostikfall (9/48 P – Restlücke von 39 P bleibt und ist als strukturelles Defizit an die Lehre zu melden). |
| 6–10 | Inlay oder Teilkrone (inkl. Stumpfaufbau) (`schnitt_inlay`) | 12 | Größte Einzelleistung der Schnittmenge (12–15 P, konservativ mit 12 angesetzt); als anspruchsvolles Werkstück bewusst in die Semestermitte gelegt, nicht in die ersten Wochen. |
| 6–10 | Kariesbedingte Reparatur Kronenrand (`schnitt_reparatur`) | 3 | Komplettiert die Schnittmengen-Zielsumme von 21 P in IK IV (24/33 = 73 %). |
| 7–12 | Krone auf Zahn/Implantat (inkl. Stumpfaufbau) (`proth_krone`) | 12 | Schweres Werkstück (Demo-Stufe 3) in der zweiten Semesterhälfte; Prothetik ist mit 55 P Rückstand die größte Lücke – Priorität nach Lückengröße. |
| 9–13 | Interimsprothese (Ersatz ≥1 Stützzone) (`proth_interims`) | 10 | Mittelschweres Werkstück (Demo-Stufe 2 bei anderen Probanden), verbreitert das bisher schmale Prothetik-Spektrum (bisher nur Modellguss/Krone/Recall). |
| 11–14 | Implantatnachsorge (`chir_impl_nachsorge`) | 4 | 4 Sitzungen à 1 P; schließt die Chirurgie exakt auf 16/16 P. |
| 12–14 | Recall (`proth_recall`) | 2 | Leichter Abschluss (Demo-Stufe 1); rundet die Prothetik-Zielsumme auf 24 P (85/116 = 73 %). |

### Auswirkungen auf die Kompetenzentwicklung

| Kategorie | Ende IK III (Ist) | Ende IK IV (optimiert, projiziert) | Kommentar |
|---|---|---|---|
| Parodontologie | 100 % | 100 % | 42,5/32 P = 133 %, auf 100 gedeckelt. Bereits übererfüllt – im IK-IV-Plan bewusst keine weiteren Punkte. |
| Zahnhartsubstanz/Prävention/Restauration | 85 % | 100 % | 46,5/55 P = 85 %. Plan: +8,5 P (Befund 3, Prophylaxe 1,5, Füllungen Kl. I/II 4) → exakt 55/55 P = 100 %. |
| Endodontologie | 100 % | 100 % | 25/20 P = 125 %, gedeckelt. Erfüllt – keine weiteren Punkte geplant. |
| Kinderzahnheilkunde | 100 % | 100 % | 17/8 P = 213 %, gedeckelt – stärkste Übererfüllung. Keine weiteren Punkte geplant. |
| Prothetik | 53 % | 73 % | 61/116 P = 53 %. Plan: +24 P (Krone 12, Interimsprothese 10, Recall 2) → 85/116 = 73 %. Größte absolute Lücke; volle Schließung (55 P) würde allein fast die gesamte realistische Semesterlast binden. |
| Schnittmenge Restauration/Prothetik | 9 % | 73 % | 3/33 P = 9 %. Plan: +21 P (Inlay/Teilkrone 12, Stumpf- 3, Stiftaufbau 3, Reparatur 3) → 24/33 = 73 %. Stärkster relativer Zugewinn. |
| Chirurgie/Implantologie | 0 % | 100 % | 0/16 P. Plan: +16 P (je 4× MSH, DVT-Planung, Implantatberatung, Implantatnachsorge à 1 P) → 16/16 = 100 %. Kleine Einheiten, hohe Machbarkeit – vollständig schließbar. |
| Kieferorthopädie (KFO) | 0 % | 19 % | 0/48 P. Plan: +9 P (ein kompletter Diagnostikfall, 9 Einzelleistungen à 1 P) → 9/48 = 19 %. Bleibt auch optimiert die kritische Restlücke (39 P) – in einem Semester strukturell nicht schließbar, curricular zu adressieren. |

## Stud. 5

**Fazit:** Stud. 5 zeigt das ausgeprägteste Ungleichgewicht der Kohorte: 286,5 Gesamtpunkte, davon 68 % Prothetik (193,5/116 = 167 % des Mindestziels), während vier von acht Kategorien nach drei Semestern bei 0 % stehen – darunter als einziger Proband auch die Endodontologie (0/20 P), was fachlich die kritischste individuelle Lücke ist. Die anrechenbare Mindesterfüllung liegt trotz hoher Gesamtleistung nur bei 61 % (200/328 P). Die Semesterlasten sind stark schief (62/73/151,5 P), wobei IK III durch eine nicht aufgeschlüsselte 99-P-Kronenblocksumme dominiert wird (Limitation: Leistungsart im Block unbekannt). Die Reihenfolge-Bewertung (Anteil schwerer Leistungen steigend 45 %→66 %→84 %) beruht auf DEMO-Schwierigkeitsgraden und ist wegen semesterweiser Aggregation nur zwischen, nicht innerhalb von Semestern belastbar. Der vorgeschlagene 14-Wochen-Plan für IK IV (128 P ≈ 9,1 P/Woche, zwischen den bisherigen Semesterlasten) schließt rechnerisch alle Lücken auf 100 %; realistisch sicher erreichbar sind ZHS, Endo, Schnittmenge und Chirurgie (81 P), während die KFO-Komponente (48 P, bei allen Probanden leer) unter Machbarkeitsvorbehalt steht und vorab kursorganisatorisch zu klären ist. Priorität bei Engpässen: Endodontologie vor Schnittmenge vor ZHS vor Chirurgie vor KFO.

### Befunde (Prüfung Reihenfolge & Inhalt vs. Originalstand)

| Aspekt | Schweregrad | Befund |
|---|---|---|
| luecke | KRITISCH | Endodontologie ist über alle drei erfassten Semester (IK I–III) komplett leer: 0 von 20 Mindestpunkten (0 %). – *In keinem Semester von Stud. 5 existiert ein Eintrag mit Kategorie 'Endodontologie' (weder endo_aufbereitung noch endo_fuellung noch endo_revision). Stud. 5 ist damit der einzige der fünf Probanden ohne jede Endo-Leistung – die Lücke ist individuell, nicht strukturell, und muss in IK IV vollständig geschlossen werden.* |
| luecke | KRITISCH | Schnittmenge Restauration/Prothetik ebenfalls komplett leer: 0 von 33 Mindestpunkten (0 %) – trotz massiver Prothetik-Aktivität. – *Kein einziger schnitt_*-Eintrag (Inlay/Teilkrone, Stumpf-/Stiftaufbau, Kronenrand-Reparatur) in IK I–III. Auffällig, weil parallel 193,5 Prothetik-Punkte erbracht wurden. Möglicher Erfassungseffekt: Die 99-P-Blocksumme in IK III (Feld 'hinweis') könnte Stumpf-/Stiftaufbauten enthalten, die Leistungsart im Block ist aber unbekannt – belegbar sind 0 P (Limitation).* |
| ausgewogenheit | KRITISCH | Extreme Prothetik-Klumpenbildung: 193,5 von 286,5 Gesamtpunkten (68 %) entfallen auf Prothetik; in IK III sind es 128,5 von 151,5 P (85 %) in einem Semester. – *Prothetik erreicht 167 % des Mindestziels (193,5/116), während vier Kategorien bei 0 % stehen. Allein der IK-III-Eintrag proth_krone umfasst 99,0 P (~74 h Arbeitszeit) und ist eine nicht aufgeschlüsselte Blocksumme ('hinweis') – die Interpretation der IK-III-Zusammensetzung ist daher nur eingeschränkt möglich.* |
| mindestanforderung | KRITISCH | Ampel Ende IK III: 4× gut (Parodontologie 100 %*, Kinderzahnheilkunde 100 %*, Prothetik 100 %*, ZHS 80 %), 0× mittel, 4× gering (Endo, Schnittmenge, Chirurgie/Implantologie, KFO je 0 %). Anrechenbare Mindesterfüllung gesamt: 200 von 328 P = 61 %. – *Exakt gerechnet: Parodontologie 38/32 = 118,75 % → 100 (gedeckelt); KZH 11/8 = 137,5 % → 100; Prothetik 193,5/116 = 166,8 % → 100; ZHS 44/55 = 80 %. Überschüsse einer Kategorie sind nicht auf andere übertragbar – trotz 286,5 Gesamtpunkten sind nur 61 % der Kategorien-Mindestziele abgedeckt.* |
| luecke | relevant | Chirurgie/Implantologie (0/16) und KFO (0/48) sind bei Stud. 5 leer – aber auch bei allen vier anderen Probanden im Export. – *Da kein einziger Proband chir_*- oder kfo_*-Einträge hat, liegt vermutlich eine strukturelle Ursache vor (separater Kursteil oder Erfassungslücke im Kursblatt) und kein individuelles Defizit von Stud. 5. Formal fehlen die Punkte trotzdem und werden im IK-IV-Plan eingeplant; die Machbarkeit von 48 KFO-P in einem Semester sollte kursorganisatorisch geklärt werden.* |
| reihenfolge | Hinweis | Zwischen den Semestern steigt der Anteil schwerer Leistungen (Demo-Schwierigkeit 3): IK I 45 % (28/62 P), IK II 66 % (48/73 P), IK III 84 % (127/151,5 P) – formal aufsteigend, aber bereits IK I enthält eine 20-P-Totalprothese (Schwierigkeit 3). – *DEMO-Kennzeichnung: Die Schwierigkeitsgrade sind heuristische Platzhalter (laut meta.bekannte_luecken), der Lehrenden-Konsens steht aus – diese Bewertung ist vorläufig. Zudem sind Punkte je Semester aggregiert: Aussagen zur Reihenfolge INNERHALB eines Semesters sind nicht möglich, nur der Semestervergleich (Limitation, keine Spekulation über Wochenabfolgen).* |
| ausgewogenheit | relevant | ZHS-Aktivität fällt kontinuierlich ab (25,0 → 15,0 → 4,0 P), obwohl das Mindestziel noch nicht erreicht ist (44/55 = 80 %); Kl.-III/IV- und Kl.-V-Füllungen (zhs_fuell_3_4, zhs_fuell_5) fehlen komplett. – *In IK III wurden nur noch 4,0 ZHS-Punkte erbracht (Befund 2,5 + Prophylaxe 1,5), keine einzige Füllung. Die fehlenden 11 P sind klein und gut in IK IV nachholbar; zwei Katalog-Leistungsarten der Kategorie sind aber in drei Semestern nie vorgekommen.* |
| inhalt | relevant | Semesterlasten stark unausgeglichen: 62,0 / 73,0 / 151,5 P – IK III trägt mehr als IK I und IK II zusammen (Faktor 2,4 zu IK I). – *Der Sprung entsteht fast vollständig durch den 99-P-Kronenblock (Blocksumme mit 'hinweis'). Bei 1 P ≈ 45 min entspricht IK III ≈ 114 h klinischer Arbeit in 14 Kurswochen (~8 h/Woche) gegenüber ≈ 47 h in IK I – didaktisch wäre eine gleichmäßigere Verteilung mit früherem Beginn der später leeren Kategorien besser gewesen.* |

### Optimierter Verlauf

**IK I** (retrospektiv) – Fokus: Breite früh anlegen: leichte Einstiegsleistungen der später leeren Kategorien (Endo, Chirurgie, KFO) neben der vorhandenen ZHS/Paro-Basis; Zielniveau ~75 P statt 62 P.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Semester gesamt (aggregiert, keine Wochenauflösung in den Daten) | Wurzelkanalaufbereitung + Wurzelkanalfüllung (1 einfacher Kanal) (`endo_aufbereitung + endo_fuellung`) | 5 | Früher Endo-Einstieg hätte den späteren Totalausfall (0/20 P nach drei Semestern) verhindert; 1 Kanal (3+2 P) ist neben der bestehenden IK-I-Last (62 P) realistisch. |
| Semester gesamt (aggregiert) | Systematische MSH-Untersuchung (2×) + Planung oralchir. Eingriffe/DVT-Indikation (2×) (`chir_msh + chir_dvt`) | 4 | Je 1-P-Leistungen mit niedriger Hürde – ideal als Einstieg im ersten klinischen Semester; hätte die Chirurgie-Lücke (0/16) halbiert angelegt. |
| Semester gesamt (aggregiert) | KFO-Diagnostikpaket Fall 1 (Erstgespräch, Anamnese, Abformung, Modell) (`kfo_erstgespraech / kfo_anamnese / kfo_abformung / kfo_modell`) | 4 | KFO besteht aus vielen 0,5–1-P-Schritten (Demo-Schwierigkeit niedrig) – als Fallstrecke über die Semester verteilbar statt komplett auf IK IV zu verschieben. |

**IK II** (retrospektiv) – Fokus: Endo fortführen, Schnittmenge eröffnen, Chirurgie/KFO weiterlaufen lassen – statt der Mono-Fokussierung auf die zweite Totalprothese (40 der 73 P).

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Semester gesamt (aggregiert) | Wurzelkanalaufbereitung + -füllung (2. Kanal) (`endo_aufbereitung + endo_fuellung`) | 5 | Kontinuität statt Lücke: nach dem IK-I-Einstieg wäre Endo hier bei 10/20 P (50 %) statt bei 0 %. |
| Semester gesamt (aggregiert) | Adhäsiver Stumpfaufbau + Stiftaufbau (`schnitt_stumpfaufbau + schnitt_stiftaufbau`) | 6 | Passt fachlich direkt zur laufenden prothetischen Versorgung (Totalprothese/Kronenvorbereitung) – die Schnittmenge wäre nicht bei 0/33 geblieben. |
| Semester gesamt (aggregiert) | Implantat-prothetische Beratung (2×) + Implantatnachsorge (2×) (`chir_impl_beratung + chir_impl_nachsorge`) | 4 | Setzt das Chirurgie-Paket fort (kumuliert 8/16 P); je 1-P-Leistungen, gut zwischen Prothetik-Terminen platzierbar. |
| Semester gesamt (aggregiert) | KFO Fall 1: 3D-Modellanalyse, Foto/Gesichtsscan, Rö-Befund, Behandlungsplan (`kfo_3d / kfo_foto / kfo_roentgen / kfo_plan`) | 4 | Fallstrecke Fall 1 wird abgeschlossen bis auf Konstruktion/Kontrollen – kumuliert 8 KFO-P statt 0. |

**IK III** (retrospektiv) – Fokus: Prothetik-Klumpen begrenzen (Kronenblock von 99 P auf ~60 P deckeln, Rest planbar nach IK IV), freiwerdende Kapazität in Endo-Abschluss, Inlay/Teilkrone und ZHS-Füllungen lenken.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| Semester gesamt (aggregiert) | Kronenblock (Blocksumme) auf ~60 P begrenzen statt 99 P (`proth_krone`) | 60 | Der 99-P-Block ('hinweis': Leistungsart unbekannt) machte 65 % der IK-III-Last aus, obwohl Prothetik das Mindestziel (116 P) bereits deutlich überschritt; ~39 P wären ohne Zielgefährdung verschiebbar gewesen (Prothetik bliebe bei 154,5/116 = 133 %). |
| Semester gesamt (aggregiert) | 2 weitere Kanäle (Aufbereitung + Füllung) + 1 Revision (`endo_aufbereitung + endo_fuellung + endo_revision`) | 13 | Hätte Endo auf 23/20 P (100 %) gebracht; Revision (Schwierigkeit 3, Demo) sinnvoll erst im dritten Semester nach zwei Übungsfällen. |
| Semester gesamt (aggregiert) | Inlay/Teilkrone inkl. Stumpfaufbau + Kronenrand-Reparatur (`schnitt_inlay + schnitt_reparatur`) | 18 | Anspruchsvolle Schnittmengen-Leistung (12–15 P) gehört in das Semester mit der höchsten prothetischen Aktivität; kumuliert 24/33 P statt 0. |
| Semester gesamt (aggregiert) | Füllungen Kl. I/II, III/IV und V (`zhs_fuell_1_2 + zhs_fuell_3_4 + zhs_fuell_5`) | 9 | ZHS fiel real auf 4 P ohne eine einzige Füllung – 9 zusätzliche Füllungspunkte hätten die Kategorie auf 53/55 P (96 %) gebracht und die nie erbrachten Leistungsarten Kl. III/IV und V abgedeckt. |
| Semester gesamt (aggregiert) | Konstruktionszeichnung/ClinCheck + 6 Kontrollsitzungen (`kfo_konstruktion + kfo_kontrolle`) | 4 | Abschluss KFO-Fall 1 (kumuliert 12/48 P) – reduziert die auf IK IV entfallende KFO-Restlast. |

**IK IV** (prospektiv) – Fokus: 14-Wochen-Plan zum Schließen ALLER realen Lücken aus dem Ist-Stand: Endo 20 P, Schnittmenge 33 P, Chirurgie 16 P, KFO 48 P, ZHS 11 P = 128 P (~9,1 P/Woche ≈ 6,9 h/Woche; liegt zwischen den bisherigen Lasten IK II 73 P und IK III 151,5 P). Schwere Leistungen (Demo-Schwierigkeit 3) ab Woche 3, nicht in den ersten Wochen.

| Wochen | Leistung | Punkte-Ziel | Begründung |
|---|---|---|---|
| W1–2 | ZHS-Rest: Füllungen Kl. I/II (4 P), kariologische Befunde (4 P), Prophylaxe MuHy+PZR (3 P) (`zhs_fuell_1_2 + zhs_befund + zhs_prophylaxe`) | 11 | Kleinste Lücke zuerst (44→55 P schließt ZHS auf 100 %); Demo-Schwierigkeit 1–2, ideal als Warm-up in den ersten beiden Wochen. |
| W1–4 | Chirurgie-Paket: je 4× MSH-Untersuchung, DVT-Planung, Implantat-Beratung, Implantat-Nachsorge (je 1 P) (`chir_msh + chir_dvt + chir_impl_beratung + chir_impl_nachsorge`) | 16 | 16 einzelne 1-P-Leistungen, niedrige Schwierigkeit, gut zwischen andere Termine streubar – schließt Chirurgie/Implantologie komplett (0→16 P, 100 %). Vorbehalt: Kategorie ist bei allen Probanden leer, Kursorganisation klären. |
| W2–5 | KFO-Fall 1 komplett (Diagnostikstrecke 9×1 P + 6 Kontrollsitzungen à 0,5 P) (`kfo_erstgespraech … kfo_kontrolle (Fall 1)`) | 12 | Ein kompletter Falldurchlauf bringt 12 P; Start früh, da viele kleinteilige Schritte (Demo-Schwierigkeit niedrig) mit Labor-/Wartezeiten. |
| W3–7 | Endo-Block 1: 3 Kanäle Aufbereitung (9 P) + 3 Kanäle Füllung (6 P) (`endo_aufbereitung + endo_fuellung`) | 15 | Größte fachlich-kritische Lücke (0/20, einziger Proband ohne Endo); Demo-Schwierigkeit 3, daher erst ab W3 und über 5 Wochen gestreckt statt komprimiert. |
| W5–8 | Schnittmenge Basis: 2× adhäsiver Stumpfaufbau (6 P), 1× Stiftaufbau (3 P), 1× Kronenrand-Reparatur (3 P) (`schnitt_stumpfaufbau + schnitt_stiftaufbau + schnitt_reparatur`) | 12 | Mittelschwere 3-P-Leistungen als Vorbereitung auf das Inlay; fachlich anschlussfähig an die hohe Prothetik-Erfahrung des Probanden (Machbarkeit hoch). |
| W6–9 | KFO-Fall 2 komplett (`kfo (Fall 2)`) | 12 | Fortsetzung der KFO-Strecke (kumuliert 24/48 P); parallelisierbar, da Einzelschritte kurz sind. |
| W8–10 | Endo-Abschluss: 1 Revision (3 P) + 1 weiterer Füllungskanal (2 P) (`endo_revision + endo_fuellung`) | 5 | Revision (Demo-Schwierigkeit 3) bewusst NACH den Übungskanälen aus W3–7; schließt Endodontologie exakt auf 20/20 P (100 %). |
| W9–12 | Inlay/Teilkrone inkl. Stumpfaufbau (15 P) + 2 weitere Stumpfaufbauten (6 P) (`schnitt_inlay + schnitt_stumpfaufbau`) | 21 | Anspruchsvollste Schnittmengen-Leistung in die zweite Semesterhälfte nach der Basis aus W5–8; schließt die Kategorie exakt auf 33/33 P (100 %). |
| W10–12 | KFO-Fall 3 komplett (`kfo (Fall 3)`) | 12 | Kumuliert 36/48 P; die Fallstrecken 3 und 4 tragen das größte Mengenrisiko – bei Engpässen zuerst hier priorisieren, da alle anderen Kategorien dann bereits bei 100 % stehen. |
| W12–14 | KFO-Fall 4 komplett + Puffer für offene Kontrollsitzungen (`kfo (Fall 4)`) | 12 | Schließt KFO rechnerisch auf 48/48 P (100 %). Vorbehalt: 4 komplette KFO-Fälle in einem Semester sind ambitioniert und die Kategorie ist bei allen 5 Probanden leer – organisatorische Machbarkeit (eigener Kursteil?) vor Semesterstart mit der Kursleitung klären. |

### Auswirkungen auf die Kompetenzentwicklung

| Kategorie | Ende IK III (Ist) | Ende IK IV (optimiert, projiziert) | Kommentar |
|---|---|---|---|
| Parodontologie | 100 % | 100 % | 38,0/32 P = 118,75 %, gedeckelt auf 100. Bereits übererfüllt – im IK-IV-Plan bewusst keine weiteren Paro-Punkte eingeplant. |
| Zahnhartsubstanz/Prävention/Restauration | 80 % | 100 % | 44,0/55 P = 80 % (Ampel gut, aber unvollständig). IK-IV-Plan W1–2: +11 P (Füllungen, Befunde, Prophylaxe) → 55/55. |
| Endodontologie | 0 % | 100 % | 0/20 P – einziger Proband ohne jede Endo-Leistung. IK-IV-Plan W3–10: 4 Kanäle Aufbereitung/Füllung + 1 Revision = +20 P → 20/20. |
| Kinderzahnheilkunde | 100 % | 100 % | 11,0/8 P = 137,5 %, gedeckelt auf 100. Übererfüllt, keine weiteren KZH-Punkte geplant. |
| Prothetik | 100 % | 100 % | 193,5/116 P = 166,8 %, gedeckelt auf 100. Massiv übererfüllt (inkl. 99-P-Blocksumme mit 'hinweis', Leistungsart unbekannt); IK IV bewusst prothetikfrei geplant. |
| Schnittmenge Restauration/Prothetik | 0 % | 100 % | 0/33 P. IK-IV-Plan W5–12: Stumpf-/Stiftaufbauten, Reparatur (12 P) + Inlay-Block (21 P) = +33 P → 33/33. |
| Chirurgie/Implantologie | 0 % | 100 % | 0/16 P. IK-IV-Plan W1–4: 16× 1-P-Leistungen = +16 P → 16/16. Vorbehalt: Kategorie bei allen 5 Probanden leer – vermutlich strukturelle Erfassungs-/Kurslücke. |
| Kieferorthopädie (KFO) | 0 % | 100 % | 0/48 P. IK-IV-Plan: 4 komplette Fallstrecken à 12 P = +48 P → 48/48. Größter Machbarkeitsvorbehalt des Plans (bei allen Probanden leer; 4 Fälle/Semester ambitioniert – kursorganisatorisch klären). |
