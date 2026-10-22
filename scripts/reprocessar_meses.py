import re
import sys
import subprocess
from pathlib import Path
 
from processar import PASTA_ORIGEM, listar_arquivos
 
# =====================================================
# CONFIGURAÇÃO
# =====================================================
 
# Competências com erro que serão baixadas de novo e reprocessadas
COMPETENCIAS = [
    "202603",
    "202604",
    "202605",
    "202606",
    "202607",
    "202608",
    "202609",
]
 
# Se já existir algum mês posterior (ex.: 202609) na pasta,
# o delta dele foi calculado contra o 202608 errado.
# Com True, ele também é recalculado (sem baixar de novo).
INCLUIR_MESES_POSTERIORES = True
 
PASTA_SCRIPTS = Path(__file__).resolve().parent
 
# =====================================================
# FUNÇÕES
# =====================================================
 
def mes_anterior(comp):
 
    ano, mes = int(comp[:4]), int(comp[4:])
 
    if mes == 1:
        return f"{ano - 1}12"
 
    return f"{ano}{mes - 1:02d}"
 
 
def rodar(script, *args):
 
    print()
    print("#" * 60)
    print(f"# {script} {' '.join(args)}")
    print("#" * 60)
 
    r = subprocess.run(
        [sys.executable, script, *args],
        cwd=PASTA_SCRIPTS
    )
 
    if r.returncode != 0:
        sys.exit(f"\nFalha em {script}. Reprocessamento interrompido.")
 
# =====================================================
# MAIN
# =====================================================
 
def main():
 
    comps = sorted(COMPETENCIAS)
 
    # 1) DOWNLOAD
    # O delta de 202604 precisa do 202603; baixa só se não existir
    para_baixar = list(comps)
 
    base = mes_anterior(comps[0])
 
    if not (PASTA_ORIGEM / f"dados_serv_{base}.csv").exists():
        print(f"dados_serv_{base}.csv não existe localmente; será baixado.")
        para_baixar.insert(0, base)
 
    rodar("baixar_arquivo_recente.py", *para_baixar)
 
    # 2) PROCESSAMENTO (em ordem, cada mês contra o anterior)
    para_processar = list(comps)
 
    if INCLUIR_MESES_POSTERIORES:
 
        locais = [
            re.search(r"(\d{6})", f).group(1)
            for f in listar_arquivos()
        ]
 
        posteriores = [c for c in locais if c > comps[-1]]
 
        if posteriores:
            print()
            print("Meses posteriores encontrados (delta será recalculado):")
            print("  " + ", ".join(posteriores))
            para_processar += posteriores
 
    for comp in para_processar:
        rodar("processar.py", comp)
 
    # 3) PUBLICAÇÃO (um único commit com todos os meses)
    rodar("publicar.py", *para_processar)
 
    print()
    print("=" * 60)
    print("REPROCESSAMENTO CONCLUÍDO")
    print("=" * 60)
    print("Competências: " + ", ".join(para_processar))
 
 
if __name__ == "__main__":
    main()