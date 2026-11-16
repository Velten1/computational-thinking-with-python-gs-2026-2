# VIGIA · Computational Thinking with Python

Protótipo acadêmico da Global Solution 2026.2. O VIGIA ajuda moradores que passam a pé por uma travessia sujeita a alagamento a entender o nível observado e sua tendência. O projeto se relaciona ao ODS 11 pela proposta de informação local em áreas expostas a alagamentos. Os limites abaixo são didáticos.

**Identificação da entrega**

Turma 1TIAPZ

- Caio Ryan Velten Alves — RM 572913
- João Vitor Fernandes Gomes — RM 573882
- Igor Cypriano Moreno da Silva — RM 570353

## Rodar no Windows

```powershell
cd VIGIA-Python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app
```

Em outro terminal, dentro da pasta do projeto:

```powershell
.\.venv\Scripts\python.exe simular.py
```

A demonstração usa HTTP de verdade e leituras simuladas identificadas. Abra [a documentação da API](http://127.0.0.1:8000/docs) ou consulte o dispositivo impresso pelo script. O CSV aparece em `dados/leituras.csv`. Para uma demonstração isolada, defina `VIGIA_CSV` no terminal do servidor antes de iniciá-lo.

## Integração e contrato

**ESP32 ou simulador → POST /leituras → validação e classificação → CSV → GET /leituras e GET /resumo → painel.**

```json
{
  "leitura_id": "vigia-001-0001",
  "dispositivo_id": "vigia-001",
  "metrica": "nivel_agua_cm",
  "valor": 32,
  "medido_em": "2026-11-16T14:04:00-03:00",
  "origem": "simulacao"
}
```

Os seis campos são obrigatórios. Use um ID estável e único por leitura, valor numérico finito e horário ISO 8601 com fuso. A API normaliza o horário para UTC, registra também o horário de recebimento e permite consultar o histórico por dispositivo, métrica e origem. A origem pode ser `simulacao` ou `sensor`.

O nível aceita 0 a 100 cm na montagem didática. A API também aceita `chuva_mm_h`, `temperatura_c` e `umidade_pct` como medições de contexto enviadas em eventos próprios. O risco por nível é `normal` abaixo de 30 cm, `atencao` a partir de 30 cm e `critico` a partir de 45 cm. Os campos adicionais do firmware podem acompanhar o JSON. A API persiste os seis campos do contrato, o horário de recebimento e a classificação.

`POST /leituras` devolve 201 para uma leitura nova, 200 para reenvio idêntico, 409 se o mesmo ID tiver outro conteúdo e 422 para entrada inválida.

`GET /resumo?dispositivo_id=vigia-001&origem=simulacao` calcula a diferença em centímetros dividida pelo intervalo em minutos. Usa os dois horários distintos mais recentes do mesmo dispositivo e da mesma origem. O indicador é `null` quando só há um horário, e a API retorna 404 se ainda não houver nível registrado.

## Evidências da entrega

| Cenário | Nível | Classe | Velocidade |
|---|---:|---|---:|
| Primeira leitura | 25 cm | normal | indisponível |
| Quatro minutos depois | 32 cm | atencao | 1,75 cm/min |
| Mais quatro minutos | 46 cm | critico | 3,5 cm/min |

O simulador imprime as três requisições, respostas e resumos. Para a entrega, capture também o GET do histórico e as três linhas correspondentes do CSV. Use o ID impresso para reunir as evidências.

## Limites do protótipo

O CSV funciona com uma instância do servidor em um único processo, como no comando acima. O serviço local ainda precisa de proteção de escrita antes de ser exposto à internet. O contrato está documentado para conectar o ESP32 e combinar o encaminhamento à Lambda com a equipe de Cloud. Os estados representam a regra didática de nível da API, e o firmware pode aplicar regras locais adicionais.
