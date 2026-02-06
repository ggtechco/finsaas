# FinSaaS

**Backtest & Parameter Optimization Engine with Pine Script Support**

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Tests](https://img.shields.io/badge/Tests-189%20passing-brightgreen)
![TA Functions](https://img.shields.io/badge/TA%20Functions-47-orange)

---

## Hikaye

Diyelim ki bir arkadas sana "Bitcoin fiyati dusunce al, yukselince sat" diye bir taktik verdi. Ama bu taktik gercekten ise yariyor mu? Bunu ogrenmek icin gercek parayla denemen gerekmez -- iste FinSaaS tam olarak bunu yapar. Gecmis fiyat verilerini alir, senin "su durumda al, bu durumda sat" kurallarini uygular ve sanki o gunlerde gercekten alim-satim yapmissin gibi simule eder. Sonucta sana "10.000 lira ile baslasakdin, bugun 12.400 liran olurdu" gibi somut bir rapor verir. Ustelik sadece bir taktik denemekle kalmaz: "acaba 10 gunluk ortalama mi, 20 gunluk mu daha iyi?" gibi yuzlerce kombinasyonu otomatik deneyip en iyi ayarlari bulur. Kisacasi, FinSaaS bir "zaman makinesi" gibi dusunulebilir -- alim-satim fikirlerini gercek risk almadan gecmiste test etmeni saglar.

---

## Ozellikler

- **Pine Script Destegi** - Pine Script kodunu parse, analiz ve Python'a transpile ederek dogrudan backtest calistirma
- **Deterministik Aritmetik** - Tum hesaplamalar `decimal.Decimal` ile yapilir, floating-point hatasi yok
- **Event-Driven Simulasyon** - Bar-by-bar calistirma, look-ahead bias riski yok
- **47 TA Fonksiyonu** - Pine Script `ta.*` namespace'i ile uyumlu teknik analiz kutuphanesi
- **Grid Search & Genetic Optimizasyon** - DEAP tabanli genetik algoritma ve grid search ile parametre optimizasyonu
- **Web Dashboard** - FastAPI tabanli REST API ile backtest ve optimizasyon
- **CLI + Python API** - Hem komut satirindan hem programatik erisim

---

## Hizli Baslangic

### Kurulum

```bash
pip install -e .

# Gelistirme ortami (test + lint araclari)
pip install -e ".[dev]"
```

### Ilk Backtest (Python API)

```python
from decimal import Decimal
from finsaas.api.facade import backtest
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam
from finsaas.core.types import Side

class SMACrossover(Strategy):
    fast = IntParam(default=10, min_val=5, max_val=50)
    slow = IntParam(default=30, min_val=20, max_val=100)

    def on_init(self):
        self.fast_ma = self.create_series()
        self.slow_ma = self.create_series()

    def on_bar(self, ctx):
        self.fast_ma.current = self.ta.sma(self.close, self.fast)
        self.slow_ma.current = self.ta.sma(self.close, self.slow)

        if self.ta.crossover(self.fast_ma, self.slow_ma):
            self.entry("long", Side.LONG)
        elif self.ta.crossunder(self.fast_ma, self.slow_ma):
            self.close_position("long")

result = backtest(
    strategy=SMACrossover(),
    csv_path="data.csv",
    symbol="BTCUSDT",
    initial_capital=Decimal("10000"),
)
print(f"Return: {result.metrics['total_return_pct']:.2f}%")
```

---

## Mimari

```
Pine Script (.pine)
       |
       v
 +-----------+     +-----------+     +-------------+
 |  Parser   | --> | Semantic  | --> | Transpiler  |
 |  (Lark)   |     | Analyzer  |     | (AST->Py)   |
 +-----------+     +-----------+     +-------------+
                                           |
                                           v
                                   Python Strategy
                                           |
       +-----------------------------------+
       v
 +------------+     +----------+     +-----------+
 | Event Loop | --> |  Broker  | --> | Portfolio  |
 | (bar-by-bar)|    | (orders) |     | (positions)|
 +------------+     +----------+     +-----------+
       |                                   |
       v                                   v
 +------------+                    +-----------+
 | TA Library |                    | Analytics |
 | (47 func)  |                    | (metrics) |
 +------------+                    +-----------+
```

| Modul | Aciklama |
|-------|----------|
| `core/` | Temel tipler, Series, BarContext, event sistemi, config |
| `data/` | SQLAlchemy modelleri, CSV/InMemory feed, migrations |
| `engine/` | Broker, Portfolio, EventLoop, Runner, komisyon/slippage |
| `strategy/` | Strategy ABC, parametreler, registry, TA kutuphanesi |
| `pine/` | Parser, AST, semantic analiz, transpiler, runtime |
| `optimization/` | Grid search, genetik algoritma, objective fonksiyonlar |
| `analytics/` | Metrikler, trade analizi, equity curve, raporlar |
| `web/` | FastAPI dashboard, REST API |
| `cli/` | Typer CLI (backtest, data, optimize, pine, serve) |
| `api/` | Programatik Python API (facade pattern) |

---

## Strateji Yazma

### Python DSL

```python
from finsaas.strategy.base import Strategy
from finsaas.strategy.parameters import IntParam, FloatParam
from finsaas.core.types import Side

class RSIStrategy(Strategy):
    length = IntParam(default=14, min_val=5, max_val=30)
    overbought = FloatParam(default=70, min_val=60, max_val=85)
    oversold = FloatParam(default=30, min_val=15, max_val=40)

    def on_init(self):
        self.rsi_val = self.create_series()

    def on_bar(self, ctx):
        self.rsi_val.current = self.ta.rsi(self.close, self.length)

        if self.rsi_val.current < self.oversold:
            self.entry("long", Side.LONG)
        elif self.rsi_val.current > self.overbought:
            self.close_position("long")
```

**Parametre Tipleri:** `IntParam`, `FloatParam`, `BoolParam`, `EnumParam`

**Order Metodlari:** `entry()`, `exit()`, `close_position()`, `close_all()`

**OHLCV Serileri:** `self.open`, `self.high`, `self.low`, `self.close`, `self.volume`

### Pine Script

```pine
//@version=5
strategy("SMA Cross", overlay=true)

fast = input.int(10, "Fast Length")
slow = input.int(30, "Slow Length")

fastMA = ta.sma(close, fast)
slowMA = ta.sma(close, slow)

if ta.crossover(fastMA, slowMA)
    strategy.entry("Long", strategy.long)

if ta.crossunder(fastMA, slowMA)
    strategy.close("Long")
```

### Pine Script -> Python Transpile

```bash
# Python koduna cevir
finsaas pine parse strategy.pine

# Dosyaya kaydet
finsaas pine parse strategy.pine -o strategy.py

# Sadece dogrulama
finsaas pine validate strategy.pine
```

---

## CLI Kullanimi

### Backtest

```bash
finsaas backtest run \
  --strategy SMACrossover \
  --symbol BTCUSDT \
  --csv data.csv \
  --capital 10000 \
  --param fast=10 \
  --param slow=30 \
  --output text
```

### Optimizasyon

```bash
# Grid Search
finsaas optimize run \
  --strategy SMACrossover \
  --symbol BTCUSDT \
  --csv data.csv \
  --method grid \
  --objective sharpe

# Genetik Algoritma
finsaas optimize run \
  --strategy SMACrossover \
  --symbol BTCUSDT \
  --csv data.csv \
  --method genetic \
  --objective sharpe \
  --generations 50 \
  --population 50 \
  --workers 4
```

### Web Dashboard

```bash
# Dashboard'u baslat
finsaas serve --port 8000 --reload
```

---

## Web Dashboard & API

Dashboard `finsaas serve` ile baslatildiktan sonra `http://localhost:8000` adresinden erisilebilir.

### API Endpointleri

| Method | Endpoint | Aciklama |
|--------|----------|----------|
| `GET` | `/api/health` | Sistem durumu |
| `GET` | `/api/strategies` | Kayitli stratejileri listele |
| `GET` | `/api/strategies/{name}/params` | Strateji parametre tanimlari |
| `POST` | `/api/data/upload` | CSV dosyasi yukle |
| `GET` | `/api/data/files` | Yuklenen dosyalari listele |
| `POST` | `/api/backtest` | Backtest calistir |
| `POST` | `/api/optimize` | Parametre optimizasyonu calistir |

---

## TA Kutuphanesi (47 Fonksiyon)

Tum fonksiyonlar Pine Script `ta.*` namespace'i ile uyumludur ve `Decimal` aritmetik kullanir.

### Moving Averages
`sma` `ema` `rma` `smma` `wma` `hma` `vwma` `linreg`

### Momentum & Oscillators
`rsi` `macd` `mom` `roc` `stoch` `cci` `mfi` `wpr`

### Volatility & Range
`atr` `tr` `bb` `bbw` `stdev` `variance` `kc` `kcw`

### Trend
`supertrend` `sar` `dmi`

### Volume
`obv` `vwap` `cum`

### Pattern & Pivot
`pivothigh` `pivotlow` `crossover` `crossunder` `cross`

### Istatistik & Yardimci
`highest` `lowest` `highestbars` `lowestbars` `change` `rising` `falling` `median` `correlation` `barsince` `valuewhen`

---

## Optimizasyon

### Python API ile Optimizasyon

```python
from finsaas.api.facade import optimize

result = optimize(
    strategy_cls=SMACrossover,
    csv_path="data.csv",
    symbol="BTCUSDT",
    method="genetic",     # "grid" veya "genetic"
    objective="sharpe",   # "sharpe", "sortino", "return", "max_dd"
    generations=50,
    population_size=50,
    max_workers=4,
)

print(f"En iyi Sharpe: {result.best_value:.4f}")
print(f"En iyi parametreler: {result.best_params}")
```

**Grid Search** - Tum parametre kombinasyonlarini dener, kucuk arama uzaylari icin ideal.

**Genetic (DEAP)** - Buyuk parametre uzaylarinda etkili, nesiller boyunca en iyi bireyleri secer.

---

## Proje Yapisi

```
src/finsaas/
├── api/           # Python API facade
├── analytics/     # Metrikler, trade analizi, raporlar
├── cli/           # Typer CLI komutlari
│   └── commands/  # backtest, data, optimize, pine
├── core/          # Temel tipler, Series, Context, Config
├── data/          # SQLAlchemy modelleri, feed'ler, migrations
├── engine/        # Broker, Portfolio, EventLoop, Runner
│   └── ...        # Komisyon, slippage, risk modelleri
├── optimization/  # Grid search, genetik algoritma
├── pine/          # Parser, AST, semantic analiz, transpiler
├── strategy/      # Strategy ABC, parametreler, registry
│   └── builtins/  # TA kutuphanesi, math, strategy ops
└── web/           # FastAPI dashboard, routes
```

---

## Gelistirme

```bash
make dev          # Gelistirme bagimliklarini kur
make test         # Testleri calistir (189 test)
make test-cov     # Coverage raporu ile testler
make lint         # Ruff ile lint kontrolu
make format       # Ruff ile kod formatlama
make typecheck    # Mypy ile tip kontrolu
make migrate      # Alembic migration'lari uygula
make clean        # Cache dosyalarini temizle
```

---

## Deploy

### Docker / Railway

```bash
docker build -t finsaas .
docker run -p 8000:8000 finsaas
```

Proje Railway deploy icin hazir bir `Dockerfile` icerir. `PORT` environment variable'i otomatik olarak kullanilir.

---

## Tech Stack

| Kategori | Teknoloji |
|----------|-----------|
| Dil | Python 3.9+ |
| Web | FastAPI, Uvicorn |
| CLI | Typer, Rich |
| Veritabani | SQLAlchemy 2, Alembic, PostgreSQL |
| Pine Script Parser | Lark |
| Genetik Algoritma | DEAP |
| Validasyon | Pydantic |
| Test | pytest, pytest-cov |
| Lint & Format | Ruff |
| Tip Kontrolu | Mypy (strict mode) |
