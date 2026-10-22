from pathlib import Path

# =====================================================
# CAMINHOS (relativos à localização deste arquivo)
# =====================================================

# .../portal_relacao_nominal_servidores/scripts
PASTA_SCRIPTS = Path(__file__).resolve().parent

# .../portal_relacao_nominal_servidores
PASTA_REPO = PASTA_SCRIPTS.parent

# .../portal_relacao_nominal_servidores/upload
PASTA_UPLOAD = PASTA_REPO / "upload"

# Tabela de datas usada na conversão (fica junto dos scripts)
ARQUIVO_DM = PASTA_SCRIPTS / "dm_diario.csv"

# =====================================================
# PUBLICAÇÃO
# =====================================================

# Somente alterações dentro destas pastas sobem para o GitHub
PASTAS_PUBLICAR = [
    "upload",
    "dataset",
    "scripts",
]

# Arquivos que NUNCA sobem, mesmo estando nas pastas acima.
# - scripts/config.py: arquivo do template usado pela Action do
#   GitHub; se for alterado por engano, a conversão para CSV quebra.
#   (para alterá-lo de propósito, faça um commit manual)
# - __pycache__ / .pyc: arquivos gerados automaticamente pelo Python
EXCLUIR_PUBLICACAO = [
    "scripts/config.py",
    "**/__pycache__/**",
    "**/*.pyc",
]

# =====================================================
# PADRÕES DE NOME
# =====================================================

# Delta publicado (único tipo de arquivo mantido na upload)
PADRAO_DELTA = r"^dados_serv_\d{6}\.xlsx$"

# CSV completo baixado do portal (temporário)
PADRAO_CSV = r"^dados_serv_\d{6}\.csv$"

# =====================================================
# LIMITE DE TAMANHO
# =====================================================

# O GitHub rejeita arquivos acima de 100 MB. A Action converte
# o delta .xlsx em CSV na pasta dataset/data; se o CSV estimado
# passar deste limite, o processamento para antes de publicar.
LIMITE_CSV_MB = 95
