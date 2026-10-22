import os
import re
import sys
import subprocess

from config_relacao import (
    PASTA_REPO,
    PASTA_UPLOAD,
    PASTAS_PUBLICAR,
    EXCLUIR_PUBLICACAO,
    PADRAO_DELTA,
)

# =====================================================
# ENCONTRAR ÚLTIMO DELTA
# =====================================================

def encontrar_ultimo_delta():

    arquivos = [
        f for f in os.listdir(PASTA_UPLOAD)
        if re.match(PADRAO_DELTA, f)
    ]

    if not arquivos:
        return None

    arquivos.sort(
        key=lambda x: re.search(r"(\d{6})", x).group(1)
    )

    return arquivos[-1]

# =====================================================
# LIMPAR PASTA UPLOAD (mantém só os deltas .xlsx)
# =====================================================

def limpar_upload():

    print()
    print("Limpando pasta upload (mantendo só dados_serv_AAAAMM.xlsx):")

    removidos = 0

    for f in sorted(os.listdir(PASTA_UPLOAD)):

        caminho = PASTA_UPLOAD / f

        if not caminho.is_file():
            continue

        if re.match(PADRAO_DELTA, f):
            continue

        try:
            caminho.unlink()
            print(f"  removido: {f}")
            removidos += 1
        except OSError as e:
            print(f"  AVISO: não foi possível remover {f} ({e})")

    if removidos == 0:
        print("  nada a remover.")

# =====================================================
# EXECUTAR COMANDO
# =====================================================

def executar(cmd, pasta):

    print()
    print("> " + " ".join(cmd))

    resultado = subprocess.run(
        cmd,
        cwd=pasta,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if resultado.stdout:
        print(resultado.stdout)

    if resultado.stderr:
        print(resultado.stderr)

    return resultado.returncode == 0

# =====================================================
# MAIN
# =====================================================

def main(competencias=None):

    print("=" * 60)
    print("PUBLICAÇÃO GITHUB")
    print("=" * 60)

    print(f"Repositório : {PASTA_REPO}")
    print(f"Upload      : {PASTA_UPLOAD}")

    if not (PASTA_REPO / ".git").exists():
        print("Repositório git não encontrado.")
        return False

    if not PASTA_UPLOAD.exists():
        print("Pasta upload não encontrada.")
        return False

    if competencias:

        # Modo reprocessamento: publica as competências pedidas
        competencias = sorted(competencias)

        arquivos = [f"dados_serv_{c}.xlsx" for c in competencias]

        faltando = [
            a for a in arquivos
            if not (PASTA_UPLOAD / a).exists()
        ]

        if faltando:
            print("Deltas não encontrados na pasta upload:")
            for a in faltando:
                print(f"  {a}")
            return False

        mensagem_commit = (
            "Reprocessamento relacao nominal servidores "
            + ", ".join(competencias)
        )

    else:

        arquivo = encontrar_ultimo_delta()

        if not arquivo:
            print("Nenhum delta encontrado.")
            return False

        arquivos = [arquivo]

        ano_mes = re.search(r"(\d{6})", arquivo).group(1)

        mensagem_commit = (
            f"Atualizacao relacao nominal servidores {ano_mes}"
        )

    print()
    print("Deltas desta execução:")
    for a in arquivos:
        print(f"  {a}")

    # Remove tudo da upload que não for delta .xlsx
    limpar_upload()

    # Somente as pastas permitidas que existem no repositório
    pastas_git = [
        p for p in PASTAS_PUBLICAR
        if (PASTA_REPO / p).exists()
    ]

    for p in PASTAS_PUBLICAR:
        if p not in pastas_git:
            print(f"Aviso: pasta '{p}' não existe no repositório; ignorada.")

    print()
    print("Executando Git")
    print("Pastas publicadas : " + ", ".join(pastas_git))
    print("Nunca publicados  : " + ", ".join(EXCLUIR_PUBLICACAO))

    # Esvazia a área de preparação, para que só entre no commit
    # o que for adicionado abaixo (nada da raiz ou de outras pastas)
    sucesso = executar(["git", "reset", "-q"], PASTA_REPO)

    if not sucesso:
        print("Erro ao preparar o git (git reset)")
        return False

    pathspecs = pastas_git + [
        f":(exclude,glob){p}" for p in EXCLUIR_PUBLICACAO
    ]

    # Adiciona SOMENTE as alterações das pastas permitidas
    # (novos, modificados e excluídos), menos os excluídos
    sucesso = executar(
        ["git", "add", "-A", "--", *pathspecs],
        PASTA_REPO
    )

    if not sucesso:
        print("Erro no git add")
        return False

    status = subprocess.run(
        ["git", "diff", "--cached", "--name-status"],
        cwd=PASTA_REPO,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if not status.stdout.strip():
        print()
        print("Nenhuma alteração nas pastas permitidas. Nada a publicar.")
        return True

    print()
    print("Alterações que serão publicadas (A=novo, M=modificado, D=excluído):")
    print(status.stdout)

    sucesso = executar(
        ["git", "commit", "-m", mensagem_commit],
        PASTA_REPO
    )

    if not sucesso:
        print("Commit não realizado.")
        return False

    sucesso = executar(
        ["git", "push"],
        PASTA_REPO
    )

    if not sucesso:
        print("Erro no git push")
        return False

    print()
    print("=" * 60)
    print("PUBLICAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"Commit: {mensagem_commit}")

    return True

# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":

    sys.exit(0 if main(sys.argv[1:]) else 1)
