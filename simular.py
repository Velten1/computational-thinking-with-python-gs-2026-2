import argparse
import json
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


def requisitar(url, dados=None):
    corpo = json.dumps(dados).encode("utf-8") if dados is not None else None
    pedido = Request(url, data=corpo, headers={"Content-Type": "application/json"})
    try:
        resposta = urlopen(pedido, timeout=5)
    except HTTPError as erro:
        resposta = erro
    with resposta:
        return resposta.code, json.load(resposta)


def demonstrar(base):
    dispositivo = f"vigia-demo-{uuid4().hex[:8]}"
    inicio = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=8)
    consulta = urlencode({"dispositivo_id": dispositivo})
    cenarios = [(25, "normal", None), (32, "atencao", 1.75), (46, "critico", 3.5)]

    for indice, (valor, classe, subida) in enumerate(cenarios):
        dados = {
            "leitura_id": f"{dispositivo}-{indice + 1}",
            "dispositivo_id": dispositivo,
            "metrica": "nivel_agua_cm",
            "valor": valor,
            "medido_em": (inicio + timedelta(minutes=4 * indice)).isoformat(),
            "origem": "simulacao",
        }
        codigo, registro = requisitar(f"{base}/leituras", dados)
        print(f"POST /leituras {json.dumps(dados)}")
        print(f"HTTP {codigo} {json.dumps(registro)}")
        assert codigo == 201 and registro["classificacao"] == classe

        codigo, resumo = requisitar(f"{base}/resumo?{consulta}")
        print(f"GET /resumo → HTTP {codigo} {json.dumps(resumo)}\n")
        assert codigo == 200 and resumo["subida_cm_min"] == subida

    assert requisitar(f"{base}/leituras", dados)[0] == 200
    assert requisitar(f"{base}/leituras", {**dados, "valor": 50})[0] == 409
    invalida = {**dados, "leitura_id": f"{dispositivo}-invalida", "valor": -1}
    assert requisitar(f"{base}/leituras", invalida)[0] == 422
    codigo, historico = requisitar(f"{base}/leituras?{consulta}")
    assert codigo == 200 and [item["valor"] for item in historico] == [25, 32, 46]
    print(f"GET /leituras → {len(historico)} registros para {dispositivo}")
    print("Reenvio, conflito de ID e leitura inválida conferidos.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa a demonstração HTTP do VIGIA")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    demonstrar(parser.parse_args().url.rstrip("/"))
