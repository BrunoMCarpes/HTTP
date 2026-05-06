# Análise Comparativa de Desempenho e Eficiência: HTTP/1.1 vs HTTP/3

Trabalho prático para a disciplina de Redes de Computadores.

## Dados do Grupo e Projeto
* **Líder:** Bruno Morales Carpes
* **Integrantes:** Vinicius Diehl Rodrigues, Wuesley Nogueira Paz
* **Professor:** Rodrigo Mansilha
* **Google Doc:** https://docs.google.com/document/d/1Q0bqjlOJ76txzb0peVOHycTA8zGw012hwdvXUPB3mH0/edit?usp=sharing
* **GitHub:** https://github.com/BrunoMCarpes/HTTP

## Introdução e Problema
O projeto analisa a evolução do protocolo HTTP, focando na transição do modelo baseado em TCP (HTTP/1.1) para a arquitetura QUIC baseada em UDP (HTTP/3). O problema central reside na carência de avaliações práticas que comparem a performance e a segurança dessas implementações, especialmente considerando que o HTTP/3 opera no espaço do usuário (user-space), dificultando a visibilidade por ferramentas de rede convencionais.

## Proposta e Tecnologias
A solução consiste em um ambiente experimental para medir latência, vazão e resiliência dos protocolos sob condições de rede adversas. 

As tecnologias adotadas são:
* **Linguagem:** Python
* **Implementação HTTP/3:** Biblioteca aioquic
* **Implementação HTTP/1.1:** Biblioteca httpx
* **Ambiente:** Docker (isolamento de processos)
* **Simulação de Rede:** Traffic Control (tc) do Linux
* **Análise de Dados:** Pandas
