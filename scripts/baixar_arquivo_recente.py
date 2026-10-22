import sys
import re
import requests
import pandas as pd

from config_relacao import PASTA_UPLOAD

# =====================================================
# CONFIGURAÇÃO
# =====================================================

DATASET = "relacao_nominal_servidores"

API_URL = (
    f"https://dados.mg.gov.br/api/3/action/package_show?id={DATASET}"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================
# CONSULTA API
# =====================================================

def listar_csvs():

    resp = requests.get(API_URL, headers=HEADERS, timeout=120)

    if resp.status_code != 200:
        raise Exception(
            f"Erro ao acessar API. Status: {resp.status_code}"
        )

    dados = resp.json()

    if not dados["success"]:
        raise Exception("API retornou erro.")

    por_comp = {}

    for r in dados["result"]["resources"]:

        if r["format"].upper() != "CSV":
            continue

        match = re.search(r"(\d{6})", r["name"])

        if match:

            comp = int(match.group(1))

            por_comp[comp] = {
                "competencia": comp,
                "nome": r["name"],
                "url": r["url"]
            }

    if not por_comp:
        raise Exception("Nenhum CSV encontrado.")

    return por_comp

# =====================================================
# DOWNLOAD E SALVAMENTO (CSV na pasta upload)
# =====================================================

def baixar(item):

    print()
    print("-" * 60)
    print(f"Arquivo: {item['nome']}")
    print("-" * 60)

    print("Carregando CSV...")

    df = pd.read_csv(
        item["url"],
        sep=";",
        encoding="latin1",
        low_memory=False
    )

    print(f"Linhas: {len(df):,}")
    print(f"Colunas: {len(df.columns)}")

    csv_saida = PASTA_UPLOAD / f"dados_serv_{item['competencia']}.csv"

    print("Salvando CSV...")

    df.to_csv(
        csv_saida,
        sep=";",
        encoding="utf-8-sig",
        index=False
    )

    print(csv_saida)

# =====================================================
# MAIN
# =====================================================

def main(competencias):

    print("=" * 60)
    print("RELAÇÃO NOMINAL DOS SERVIDORES - DADOS MG")
    print("=" * 60)

    if not PASTA_UPLOAD.exists():
        raise Exception(f"Pasta upload não encontrada: {PASTA_UPLOAD}")

    por_comp = listar_csvs()

    comps = sorted(por_comp)

    if competencias and competencias[0] == "--a-partir":

        # Modo reprocessamento: do mês informado até o mais recente,
        # mais o mês anterior a ele (base de comparação)
        inicio = int(competencias[1])

        anteriores = [c for c in comps if c < inicio]
        seguintes = [c for c in comps if c >= inicio]

        if not seguintes:
            raise Exception(
                f"Nenhuma competência a partir de {inicio} no portal. "
                f"Mais recente: {comps[-1]}"
            )

        if not anteriores:
            raise Exception(
                f"Não há competência anterior a {inicio} no portal "
                f"para servir de base de comparação."
            )

        alvos = [por_comp[c] for c in [anteriores[-1]] + seguintes]

    elif competencias:

        # Competências específicas
        faltando = [c for c in competencias if int(c) not in por_comp]

        if faltando:
            disponiveis = ", ".join(str(c) for c in comps)
            raise Exception(
                f"Competências não encontradas no portal: {', '.join(faltando)}\n"
                f"Disponíveis: {disponiveis}"
            )

        alvos = [por_comp[int(c)] for c in sorted(set(competencias))]

    else:

        # Modo normal: mês mais recente + mês anterior
        # (o anterior é necessário para calcular o delta)
        if len(comps) < 2:
            raise Exception("O portal tem menos de 2 competências.")

        alvos = [por_comp[comps[-2]], por_comp[comps[-1]]]

    print()
    print("Competências a baixar:")
    for a in alvos:
        print(f"  {a['competencia']} - {a['nome']}")

    for item in alvos:
        baixar(item)

    print()
    print("Concluído com sucesso.")


if __name__ == "__main__":
    main(sys.argv[1:])
