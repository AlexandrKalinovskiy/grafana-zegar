# Zegar – natywne okno Linux w Dockerze

Prosty zegar cyfrowy działający jako **natywne okno na pulpicie Linux**, uruchamiany w kontenerze Docker z przekazaniem X11.

---

## Struktura projektu

```
zegar/
├── clock.py            # Główna aplikacja (Python + Tkinter)
├── .env                # Konfiguracja (ignorowana przez git)
├── .env.example        # Szablon konfiguracji
├── requirements.txt    # Zależności Python
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## Konfiguracja – plik `.env`

```env
# Strefa czasowa kontenera
TZ=Europe/Warsaw

# O której godzinie zegar zaczyna pulsować/mrugać (format 24h)
PULSE_START_TIME=08:00:00

# Jak długo trwa efekt (w sekundach)
PULSE_DURATION_SECS=60
```

W skonfigurowanym oknie czasowym zegar **miga na czerwono** z ciemnym tłem.  
Po zmianie `.env` wystarczy zrestartować kontener – **nie trzeba przebudowywać obrazu**.

---

## Uruchomienie

### 1. Zezwól kontenerowi na rysowanie okna na Twoim pulpicie

```bash
xhost +local:docker
```

> Uruchom to raz po każdym logowaniu. Możesz dodać do `~/.profile` lub `~/.xprofile`.

### 2. Skopiuj konfigurację i dostosuj ją

```bash
cp .env.example .env
# edytuj .env według potrzeb
```

### 3. Uruchom kontener

```bash
docker-compose up --build -d
```

Okno zegara pojawi się na pulpicie.

### 4. Zatrzymanie

```bash
docker-compose down
```

---

## Zależności

| Pakiet | Opis |
|--------|------|
| `python-dotenv` | Wczytywanie pliku `.env` |
| `python3-tk` | Tkinter (instalowany przez apt w obrazie Docker) |

Tkinter jest wbudowany w Pythona – nie wymaga żadnych zewnętrznych bibliotek poza `python-dotenv`.

---

## Responsywność okna

Okno można dowolnie **rozciągać myszką**. Rozmiar czcionki automatycznie dopasowuje się do wymiarów okna (obliczany proporcjonalnie do szerokości i wysokości).
