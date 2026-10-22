import re
import sys
import subprocess
from pathlib import Path

# =====================================================
# USO
# =====================================================
#
#     python atualizar.py
#
# O script pergunta se deseja reprocessar meses:
#   - NÃO: baixa e publica o mês mais recente (rotina mensal)
#   - SIM: pede o mês inicial e reprocessa dele até o mais recente
#
# Atalho sem perguntas (reprocessar a partir de um mês):
#     python atualizar.py 202604
#
# =====================================================

PASTA_REPO = Path(__file__).resolve().parent
PASTA_SCRIPTS = PASTA_REPO / "scripts"
PASTA_UPLOAD = PASTA_REPO / "upload"

PADRAO_CSV = r"^dados_serv_(\d{6})\.csv$"


def rodar(script, *args):

    print()
    print("#" * 60)
    print(f"# {script} {' '.join(args)}")
    print("#" * 60)

    r = subprocess.run(
        [sys.executable, str(PASTA_SCRIPTS / script), *args],
        cwd=PASTA_SCRIPTS
    )

    if r.returncode != 0:
        sys.exit(f"\nFalha em {script}. Processo interrompido.")


def competencia_valida(c):

    return (
        re.fullmatch(r"\d{6}", c) is not None
        and 1 <= int(c[4:]) <= 12
    )


def limpar_csvs_temporarios():

    # Remove CSVs que tenham sobrado de uma execução interrompida
    for f in PASTA_UPLOAD.iterdir():
        if f.is_file() and re.match(PADRAO_CSV, f.name):
            f.unlink()
            print(f"CSV temporário antigo removido: {f.name}")


def perguntar():

    print("=" * 60)
    print("RELAÇÃO NOMINAL DOS SERVIDORES")
    print("=" * 60)

    while True:

        r = input("Deseja reprocessar meses? (s/n): ").strip().lower()

        if r in ("n", "nao", "não"):
            return None

        if r in ("s", "sim"):
            break

        print("Responda s ou n.")

    while True:

        inicio = input(
            "A partir de qual mês? (AAAAMM, ex.: 202604): "
        ).strip()

        if not competencia_valida(inicio):
            print("Mês inválido. Use o formato AAAAMM.")
            continue

        r = input(
            f"Confirma reprocessar de {inicio} até o mês mais recente? (s/n): "
        ).strip().lower()

        if r in ("s", "sim"):
            return inicio


def atualizacao_normal():

    print()
    print(">> Atualização normal (mês mais recente)")

    rodar("baixar_arquivo_recente.py")
    rodar("processar.py")
    rodar("publicar.py")


def reprocessamento(inicio):

    print()
    print(f">> Reprocessamento a partir de {inicio}")

    # Baixa do mês inicial até o mais recente + o mês base anterior
    rodar("baixar_arquivo_recente.py", "--a-partir", inicio)

    comps = sorted(
        m.group(1)
        for m in (re.match(PADRAO_CSV, f.name) for f in PASTA_UPLOAD.iterdir())
        if m and m.group(1) >= inicio
    )

    print()
    print("Meses que serão reprocessados: " + ", ".join(comps))

    for c in comps:
        rodar("processar.py", c)

    rodar("publicar.py", *comps)


def main():

    if not PASTA_UPLOAD.exists():
        sys.exit(f"Pasta upload não encontrada: {PASTA_UPLOAD}")

    limpar_csvs_temporarios()

    if len(sys.argv) > 1:

        inicio = sys.argv[1]

        if not competencia_valida(inicio):
            sys.exit(f"Mês inválido: {inicio} (use AAAAMM)")

    else:

        inicio = perguntar()

    if inicio:
        reprocessamento(inicio)
    else:
        atualizacao_normal()

    print()
    print("=" * 60)
    print("TUDO CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    main()
