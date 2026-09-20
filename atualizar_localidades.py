import gzip
import json
from pathlib import Path
from urllib.request import Request, urlopen


API_BASE = "https://servicodados.ibge.gov.br/api/v1/localidades"

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "static"
    / "data"
    / "brazilian_locations.json"
)


def get_json(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Zenvix-Connect/1.0",
            "Accept-Encoding": "gzip",
        },
    )

    with urlopen(request, timeout=30) as response:
        content = response.read()

        if response.headers.get("Content-Encoding") == "gzip":
            content = gzip.decompress(content)

        return json.loads(content.decode("utf-8"))

def main():
    print("Consultando estados no IBGE...")

    estados = get_json(f"{API_BASE}/estados")

    resultado = {}

    for estado in sorted(estados, key=lambda item: item["sigla"]):
        uf = estado["sigla"]

        print(
            f"Baixando municípios de {uf} - "
            f"{estado['nome']}..."
        )

        municipios = get_json(
            f"{API_BASE}/estados/{estado['id']}/municipios"
        )

        cidades = sorted(
            {
                municipio["nome"]
                for municipio in municipios
                if municipio.get("nome")
            },
            key=str.casefold,
        )

        resultado[uf] = {
            "nome": estado["nome"],
            "cidades": cidades,
        }

        print(f"  -> {len(cidades)} municípios")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as arquivo:
        json.dump(
            resultado,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

    total_estados = len(resultado)
    total_cidades = sum(
        len(estado["cidades"])
        for estado in resultado.values()
    )

    print()
    print("======================================")
    print("LOCALIDADES ATUALIZADAS COM SUCESSO")
    print("======================================")
    print(f"Estados: {total_estados}")
    print(f"Municípios/localidades: {total_cidades}")
    print(f"Arquivo: {OUTPUT_FILE}")
    print("======================================")


if __name__ == "__main__":
    main()