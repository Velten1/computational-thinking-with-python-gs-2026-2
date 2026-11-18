# VIGIA · Computational Thinking with Python

Protótipo acadêmico da Global Solution 2026.2. O VIGIA ajuda moradores que passam a pé por uma travessia sujeita a alagamento a entender o nível observado e sua tendência. O projeto se relaciona ao ODS 11 pela proposta de informação local em áreas expostas a alagamentos. Os limites abaixo são didáticos.

**Identificação da entrega**

Turma 1TIAPZ

- Caio Ryan Velten Alves — RM 572913
- João Vitor Fernandes Gomes — RM 573882
- Igor Cypriano Moreno da Silva — RM 570353

## Relatório e reprodução

O [relatório de entrega](VIGIA%20-%20Entrega%20Computational%20Thinking%20with%20Python.pdf) apresenta o contrato da API e os registros da demonstração. Para reproduzir os testes no Windows, abra um terminal na pasta clonada do repositório.

```powershell
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

Executamos as três leituras via HTTP e consultamos o histórico gerado. O relatório registra o JSON, a resposta, a linha correspondente no CSV e o indicador de cada cenário. Também verificamos que um reenvio idêntico manteve apenas a linha original, que um ID reutilizado com outro valor retornou 409 e que uma leitura inválida retornou 422.

## Limites do protótipo

Demonstramos a API localmente com requisições HTTP simuladas. O CSV foi projetado para uma instância em um único processo. Os estados resultam de limiares didáticos de nível, e a velocidade descreve a variação entre duas medições. A integração física com o ESP32 e o encaminhamento à Lambda ficam fora da demonstração apresentada.

O [CSV da demonstração HTTP](evidencias/leituras-demonstracao.csv) contém as três leituras de uma execução adicional do simulador, com horários próprios dessa execução. Ele permite inspecionar o histórico persistido. Os cenários reproduzem os níveis de 25, 32 e 46 cm, com as mesmas classes e indicadores apresentados no relatório.
