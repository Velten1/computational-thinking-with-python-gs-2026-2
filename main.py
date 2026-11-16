import csv
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, FiniteFloat, model_validator


app = FastAPI(title="VIGIA | Monitoramento de travessia", version="1.0.0")
CSV_PATH = Path(os.environ.get("VIGIA_CSV", Path(__file__).parent / "dados" / "leituras.csv"))
CSV_LOCK = Lock()
NIVEL = "nivel_agua_cm"
LIMITES = {NIVEL: (0, 100), "chuva_mm_h": (0, None),
           "temperatura_c": (None, None), "umidade_pct": (0, 100)}


class Leitura(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    leitura_id: str = Field(min_length=1, max_length=100)
    dispositivo_id: str = Field(min_length=1, max_length=100)
    metrica: Literal["nivel_agua_cm", "chuva_mm_h", "temperatura_c", "umidade_pct"]
    valor: FiniteFloat = Field(strict=True)
    medido_em: AwareDatetime
    origem: Literal["simulacao", "sensor"]

    @model_validator(mode="after")
    def validar_faixa(self):
        minimo, maximo = LIMITES[self.metrica]
        if (minimo is not None and self.valor < minimo) or (
            maximo is not None and self.valor > maximo
        ):
            raise ValueError("Valor fora da faixa da métrica")
        self.medido_em = self.medido_em.astimezone(UTC)
        return self


class Registro(Leitura):
    recebido_em: AwareDatetime
    classificacao: Literal["normal", "atencao", "critico", "contexto"]


class Resumo(BaseModel):
    dispositivo_id: str
    origem: Literal["simulacao", "sensor"]
    nivel_cm: float
    medido_em: AwareDatetime
    classificacao: Literal["normal", "atencao", "critico", "contexto"]
    subida_cm_min: float | None


def classificar(leitura: Leitura) -> str:
    if leitura.metrica != NIVEL:
        return "contexto"
    if leitura.valor >= 45:
        return "critico"
    if leitura.valor >= 30:
        return "atencao"
    return "normal"


def ler_csv() -> list[Registro]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8", newline="") as arquivo:
        return [
            Registro.model_validate({**linha, "valor": float(linha["valor"])})
            for linha in csv.DictReader(arquivo)
        ]


@app.post("/leituras", status_code=201, response_model=Registro)
def registrar(leitura: Leitura, resposta: Response):
    with CSV_LOCK:
        for anterior in ler_csv():
            if anterior.leitura_id == leitura.leitura_id:
                if anterior.model_dump(include=set(Leitura.model_fields)) != leitura.model_dump():
                    raise HTTPException(409, "ID já utilizado com outro conteúdo")
                resposta.status_code = 200
                return anterior

        registro = Registro(**leitura.model_dump(), recebido_em=datetime.now(UTC),
                            classificacao=classificar(leitura))
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        escrever_cabecalho = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0
        with CSV_PATH.open("a", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(Registro.model_fields))
            if escrever_cabecalho:
                escritor.writeheader()
            escritor.writerow(registro.model_dump(mode="json"))
        return registro


@app.get("/leituras", response_model=list[Registro])
def historico(dispositivo_id: str | None = None, metrica: str | None = None,
              origem: Literal["simulacao", "sensor"] | None = None):
    with CSV_LOCK:
        registros = ler_csv()
    filtrados = [
        item for item in registros
        if (dispositivo_id is None or item.dispositivo_id == dispositivo_id)
        and (metrica is None or item.metrica == metrica)
        and (origem is None or item.origem == origem)
    ]
    return sorted(filtrados, key=lambda item: (item.medido_em, item.recebido_em))


@app.get("/resumo", response_model=Resumo)
def resumo(dispositivo_id: str = Query(min_length=1),
           origem: Literal["simulacao", "sensor"] = "simulacao"):
    niveis = historico(dispositivo_id, NIVEL, origem)
    if not niveis:
        raise HTTPException(404, "Nenhuma leitura de nível para o dispositivo e a origem")

    ultima = niveis[-1]
    subida = None
    for anterior in reversed(niveis[:-1]):
        minutos = (ultima.medido_em - anterior.medido_em).total_seconds() / 60
        if minutos > 0:
            subida = round((ultima.valor - anterior.valor) / minutos, 4)
            break

    return Resumo(dispositivo_id=dispositivo_id, origem=origem, nivel_cm=ultima.valor,
                  medido_em=ultima.medido_em, classificacao=ultima.classificacao,
                  subida_cm_min=subida)
