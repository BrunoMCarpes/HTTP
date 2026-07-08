#!/bin/sh
set -e

# Aplica emulação de rede na interface do contêiner ANTES de rodar o comando.
# NETEM é aplicado no EGRESS de cada contêiner separadamente. Se você definir
# o mesmo NETEM no servidor e no cliente, o atraso soma nas duas direções:
#   NETEM="delay 25ms"  ->  ~50ms de RTT total.
if [ -n "$NETEM" ]; then
    echo ">> aplicando netem em eth0: $NETEM"
    if tc qdisc add dev eth0 root netem $NETEM; then
        echo ">> netem ativo:"
        tc qdisc show dev eth0 | sed 's/^/>>   /'
    else
        echo ">> ERRO: nao consegui aplicar netem."
        echo ">>       carregue o modulo no HOST:  sudo modprobe sch_netem"
        echo ">>       e confirme o cap_add: NET_ADMIN no docker-compose.yml"
        exit 1
    fi
fi

exec "$@"
