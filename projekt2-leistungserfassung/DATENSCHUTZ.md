# Datenschutz- & Sicherheitskonzept

Die App verarbeitet **sensible Daten** (klinische Leistungen von Studierenden).
Sie ist so gebaut, dass Studierende **anonym** behandelt werden und Daten
**nicht** durch simples Verändern einer ID zugänglich sind.

## 1. Anonymisierung der Studierenden

- In der Datenbank steht **kein Klarname**, sondern ein **zufälliges Pseudonym**
  (z. B. `S-a9Kx`), erzeugt mit `secrets.token_urlsafe`.
- Doktoranden und die Auswertung sehen **ausschließlich Pseudonyme**.
- Der **Klarname** wird zwar gespeichert, ist aber **nur für Doktoranden/Admins**
  sichtbar (autorisierte Prüfer) – Studierende sehen nie fremde Namen.
- Studierende melden sich mit ihrem **Pseudonym als Benutzername** an (nicht
  `student1/2/…`), damit niemand durch Hochzählen fremde Konten erraten kann.

## 2. Kein Zugriff durch „Zahl am Ende ändern" (IDOR-Schutz)

- Interne Datenbank-IDs werden **nie** in URLs verwendet.
- Jeder Datensatz hat einen **zufälligen `public_token`** (nicht hochzählbar).
- Zusätzlich prüft **jede** Route serverseitig die **Eigentümerschaft**:
  Ein Student kann nur Datensätze öffnen/ändern/löschen, deren `student_id`
  seiner **Session** entspricht – sonst `403`. Die eigene Identität kommt immer
  aus der Session, nie aus der URL.
- Belegt durch den Selbsttest: `python -m tests.selftest_security`.

## 3. Rollentrennung (serverseitig erzwungen)

- Rollen: `student`, `doktorand`, `admin`.
- **Studierende sind read-only**: Sie können sich anmelden und **nur ihren
  eigenen Stand ansehen**. Es gibt für sie **keine** Schreib-Route.
- **Nur `doktorand`/`admin` tragen Leistungen ein** (`/student/<x>/eintragen`,
  `/eintrag/<t>/loeschen`) – alle mit `@role_required('doktorand','admin')`.
  Ein Student erhält dort `403`.
- Studierende erreichen weder die Doktoranden-Übersicht noch die Auswertung
  (Klarnamen) – beides `403`.

## 2a. Patientenfälle: anonym per Konzept

- Doktoranden/Profs können **Patientenfälle** erfassen (`/faelle`) – aber
  **ausschließlich anonym**: eine Fall-Nr. (wie auf dem Laufzettel), der
  Behandlungsbedarf (Leistungen aus der Blauen Liste), Schwierigkeit und
  geschätzte Dauer. Das Formular weist explizit darauf hin: **keine Namen,
  Geburtsdaten oder Diagnosen mit Personenbezug** eingeben.
- Es gibt bewusst **keine Patienten-Stammdaten-Tabelle** – die App kann
  Patientendaten strukturell gar nicht speichern.
- Fall-URLs nutzen zufällige Tokens (IDOR-Schutz wie überall).
- Studierende sehen Fälle nur als **Empfehlung für sich selbst** („Empfohlene
  Patientenfälle") – nicht, wem sonst ein Fall zugewiesen ist. Anlegen/Ändern
  ist für Studierende gesperrt (`403`, im Selbsttest belegt).

## 3a. KI-Studien-Assistent (nur eigene Daten)

- Der Bot beantwortet Freitext-Fragen jetzt per **KI** (Anthropic-API; ohne
  konfigurierten API-Schlüssel antwortet er regelbasiert). An das Modell gehen
  **ausschließlich die aggregierten Daten der/des eingeloggten Studierenden**
  (eigener Fortschritt, eigene Lücken, eigene Fall-Empfehlungen) – keine
  Klarnamen, keine fremden Daten, keine Patientendaten.
- Serverseitig erzwungen: Route nur für Rolle `student` (Doktoranden: 403),
  CSRF-Pflicht, Rate-Limit, Fragen-Längenlimit. Der System-Prompt verbietet
  zusätzlich Aussagen über andere und medizinische Ratschläge.
- Ohne verfügbare KI antwortet der Bot regelbasiert (klar gekennzeichnet).

## 3b. Alte Demo-Antworten (Schnellfragen)

- Unten rechts auf der Studenten-Seite: ein **Demo**-Assistent (noch kein echter
  Bot, keine KI, kein Netzwerkabruf).
- Er bekommt seine Daten aus `student_stats.bot_context(db, session['student_id'])`
  – also **ausschließlich die Daten der/des eingeloggten Studierenden**. Es gibt
  keinen Endpoint, über den der Bot Daten anderer Studierender laden könnte.
  Damit lässt sich über den Bot **niemals** herausfinden, was andere haben.

## 4. Weitere Schutzmaßnahmen

- **Passwörter** werden nur als Hash gespeichert (`werkzeug`, scrypt/pbkdf2).
- **CSRF-Schutz**: jedes Formular trägt ein Session-Token; POST ohne gültiges
  Token → `400`.
- **Session-Cookies**: `HttpOnly` + `SameSite=Lax`. In Produktion zusätzlich
  `SESSION_COOKIE_SECURE=True` hinter HTTPS.
- **Lokal only**: keine externen Dienste, keine Telemetrie.

## 5. Datensparsamkeit

- Patientenbezug nur als **anonymer Fallbezug** (Fall-Nr.), keine Klardaten.
- Auswertung nur **aggregiert**.

## 6. Kein Datenverlust / keine Daten im Repo

- `data/` (Datenbank), `backups/`, `instance/` (Secret-Key) sind **git-ignoriert**
  → sensible Daten landen **nie** auf GitHub.
- `python -m scripts.backup` sichert die DB + CSV-Export (nur Pseudonyme).

## 7. Empfehlungen für den Produktivbetrieb

- Login-Benutzernamen ebenfalls **nicht-identifizierend** vergeben (zentrale Ausgabe).
- HTTPS erzwingen, `SESSION_COOKIE_SECURE=True`.
- Rollen/Zugänge zentral verwalten; regelmäßige Backups an sicherem Ort.
- Zugriff auf die Pseudonym-Zuordnung strikt auf Projektleitung beschränken.
