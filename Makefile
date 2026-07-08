# Atalhos para rodar o benchmark via Docker.
#
# Fluxo tipico (gera graficos no final):
#   make build
#   export NETEM="delay 25ms loss 1%"
#   make down && make up && make bench
#   export NETEM="delay 100ms loss 5%"
#   make down && make up && make bench
#   make plot
#
# Os graficos saem em results/*.png

NETEM   ?=
PAYLOAD ?= 1024
N       ?= 1000
RESULTS ?= results/results.jsonl

export NETEM
export PAYLOAD

RUN = docker compose run --rm client python bench.py --host server --port 8443 --insecure

.PHONY: build up down warm cold concurrent all bench plot report clean-results

build:
	docker compose build

up:
	docker compose up -d server
	@echo "servidor no ar. NETEM='$(NETEM)' PAYLOAD=$(PAYLOAD)"

down:
	docker compose down

# --- rodadas avulsas (so imprimem na tela) --------------------------------
warm:
	$(RUN) --proto h11 -n $(N) --mode warm
	$(RUN) --proto h3  -n $(N) --mode warm

cold:
	$(RUN) --proto h11 -n 200 --mode cold
	$(RUN) --proto h3  -n 200 --mode cold

concurrent:
	$(RUN) --proto h11 -n 500 --mode concurrent
	$(RUN) --proto h3  -n 500 --mode concurrent

all: warm cold concurrent

# --- rodada que SALVA os resultados para gerar graficos -------------------
# roda os 3 modos nos 2 protocolos e acrescenta tudo em results/results.jsonl
bench:
	@mkdir -p results
	$(RUN) --proto h11 -n $(N) --mode warm       --out /app/$(RESULTS)
	$(RUN) --proto h3  -n $(N) --mode warm       --out /app/$(RESULTS)
	$(RUN) --proto h11 -n 200 --mode cold        --out /app/$(RESULTS)
	$(RUN) --proto h3  -n 200 --mode cold        --out /app/$(RESULTS)
	$(RUN) --proto h11 -n 500 --mode concurrent  --out /app/$(RESULTS)
	$(RUN) --proto h3  -n 500 --mode concurrent  --out /app/$(RESULTS)
	@echo ">> resultados acrescentados em $(RESULTS)"

# gera os graficos a partir do que estiver em results/results.jsonl
plot:
	docker compose run --rm --no-deps client python plot.py

report: bench plot

clean-results:
	rm -f results/*.jsonl results/*.png
