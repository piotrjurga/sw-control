# Sterowanie

## Uruchomienie

Skrytpt wymaga Pythona >= 3.8, więc też Raspbiana w wersji Buster lub nowszej.
Trzeba zainstalować wymagane paczki z apt (a nie z pip!).

```bash
$ apt install python3-pandas python3-aiohttp
```

Następnie można włączyć serwer:

```bash
$ python3 -m aiohttp.web -H 0.0.0.0 -P 8080 main:make_app
# albo
$ python3 main.py
```

## API

### Aktualne pomiary

- timestamp: czas uniksowy w sekundach (float!)
- Ci: poziom zbiornika
- Yi: status zaworu (1: otwarty)
- Pi: status pompy (1: włączona)

```
GET /status -> {
    "status": "ok",
    "state": {
        "timestamp": 1582809916.5852017,
        "C1": 33, "C2": 20, "C3": 16, "C4": 21, "C5": 33,
        "Y1": 1, "Y2": 1, "Y3": 1,
        "P1": 0, "P2": 0, "P3": 0, "P4": 0
    }
}
```

### Historia pomiarów

- last: ile ostatnich pomiarów wysłać (opcjonalne)
- timestamp[j]: czas uniksowy w sekundach (float!)
- Ci[j]: poziom zbiornika
- Yi[j]: status zaworu (1: otwarty)
- Pi[j]: status pompy (1: włączona)

```
GET /history?last=int -> {
    "status": "ok",
    "state": {
        "timestamp": [1582809916.5852017, ...],
        "C1": [33, 33, ...],
        "C2": [20, 20, ...],
        ...
        "P4": [0, 0, 1, ...]
    }
}
```

### Aktualna konfiguracja

- C_min: minimalna pojemność zbiornika przy której może być włączona pompa
- C_max: maksymalna pojemność zbiornika przy której może być otwarty zawór
- C_cap: pojemność danego zbiornika
- T_ust: ustawienia czasowe

```
GET /config -> {
    "status": "ok",
    "C_min": [8, 4, 8.9, 4, 5],
    "C_max": [14, 8, 9.0, 8, 20],
    "C_cap": [33, 20, 16, 21, 33],
    "T_ust": [8, 8, 8, 8, 2]
}
```

### Informacja o błędnym zapytaniu

- status: ok/error
- message: wiadomość dla programisty

```
ERROR -> {"status": "error", "message": "..."}
```

