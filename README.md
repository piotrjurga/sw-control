# Sterowanie

## Uruchomienie
Skrytpt wymaga Pythona >= 3.8, więc też Raspbiana w wersji Buster lub nowszej.
Trzeba zainstalować wymagane paczki z apt (a nie z pip!).

```bash
$ apt install python3-pandas python3-aiohttp
```

Następnie można włączyć serwer:

```bash
$ make serve
# albo
$ python3 app.py
# albo
$ python3 -m aiohttp.web -H 0.0.0.0 -P 8080 app:make_app
```

Serwer wysyła stan na adres `DB_URL`, do ustawienia w `config.py`.

## API

Wiadomości do serwera można łatwo wysyłać za pomocą narzędzia `curl` w wierszu polecenia.

**Przykłady**
```
$ curl -XGET localhost:8080/history?last=20
$ curl -XPUT localhost:8080/state -d '{"Y1": 0, "P1": 1}'
```

### GET `/info`
Zwróć informacje o stacji (dostępne identyfikatory zbiorników, pomp, zaworów).

```
GET /info
{
    "containers": ["C1", "C2", "C3", "C4", "C5"],
    "pumps": ["P1", "P2", "P3", "P4"],
    "valves": ["Y1", "Y2", "Y3"]
}
```

### GET `/history`
Zwróć ostatnie stany stacji. Następniki w liście są nowsze od poprzedników.

**Parametry**
- `last`: ile ostatnich stanów zwrócić (opcjonalny int, domyślnie 10)

**Body**
- `time`: czas danego stanu
- `Ci`: historia poziomów wody zbiornika
- `Yi`: historia stanów zaworu (1: otwarty)
- `Pi`: historia stanów pompy (1: włączona)

```
GET /history?last=5
{
    "time": ["", ...],
    "C1": [18, 19, 20, 20, 21], ...
    "Y1": [0, 0, 0, 0, 0], ...
    "P1": [1, 1, 1, 0, 0], ...
}
```

### GET `/state`
Zwróć aktualny stan stacji.

**Body**
- `time`: czas stanu
- `mode`: tryb działania stacji (`idle`: spoczynek, `auto`: automatyczny, `manual`
- `Ci`: poziom wody zbiornika
- `Yi`: stan zaworu (1: otwarty)
- `Pi`: stan pompy (1: włączona)

```
GET /state
{  
    "time": "",
    "mode": "auto",
    "C1": 18, ...
    "P1": 1, ...
    "Y1": 1, ...
}
```

### PUT `/state`
Ustaw tryb działania stacji, jeśli podano, a następnie stany zaworów i pomp.

**Body**
Tak samo jak w `GET /state`, można pominąć dowolne klucze.
- `mode`: `idle | auto | manual`
- `Yi`: ...
- `Pi`: ...

```
PUT /state
{"mode": "manual", "Y1": 1, "Y2": 1, "Y3": 1}
```

### GET `/config`
Zwróć aktualną konfigurację stacji.

**Body**
Dla każdego klucza `Ci`:
- `min`, `max`: minimalny i maksymalny poziom wody w zbiorniku
- `rd`, `rg`: dolny i górny roboczy poziom wody w zbiorniku
- `cap`: faktyczna pojemność danego zbiornika
- `t_ust`: czas (w sekundach) utrzymywania poziomu wody pomiędzy `rd` i `rg`
- ograniczenia: `0 <= min < rd < rg < max < cap`

**Przykład**
```
GET /config
{
    "C1": {"min": 2, "max": 8, "cap": 10, "rd": 4, "rg": 7, "t_ust": 60},
    ...
}
```

### PUT `/config`
Zmień aktualną konfigurację stacji.
Klucze w body takie same jak w `GET /config`.
Dowolne klucze mogą być pominięte.

**Przykład**
```
PUT /config
{
    "C2": {"rd": 3, "t_ust": 180},
    "C3": {"rd": 3}
}
```


## Stare API

### Zmiana konfiguracji

- C_min: minimalna pojemność zbiornika przy której może być włączona pompa
- C_max: maksymalna pojemność zbiornika przy której może być otwarty zawór
- Ograniczenia: 0 < C_min < C_max < C_cap

```
PUT /config
{
    "C_min": [C1_min, C2_min, C3_min, C4_min, C5_min],
    "C_max": [C1_max, C2_max, C3_max, C4_max, C5_max]
}
200 - OK
```

### Tryb manualny

- data.steering_state: RM/ID

```
PUT /manual
```

### Zmiana stanu

- type: pump/valve
- data.state = true/false

```
PUT /manual/<type>/<id>
```

