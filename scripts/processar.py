import pandas as pd
import os
import re
import sys
import warnings
import openpyxl
from glob import glob

warnings.filterwarnings("ignore")

# =====================================================
# CONFIGURAÇÃO
# =====================================================

from config_relacao import PASTA_UPLOAD, ARQUIVO_DM, LIMITE_CSV_MB

# Os CSVs completos são baixados na própria pasta upload,
# e o delta .xlsx é salvo nela também
PASTA_ORIGEM = PASTA_UPLOAD

# =====================================================
# MAPA ÓRGÃOS
# =====================================================

MAPA_ORGAOS = {
    "AGENCIA REGULADORA DE SERVICOS DE ABASTECIMENTO DE AGUA E DE ESGOTAMENTO": "ARSAE MG",
    "DEFENSORIA PUBLICA DO ESTADO DE MINAS GERAIS": "DEFENSORIA PUBLICA",
    "DEPARTAMENTO DE EDIFICACOES E ESTRADAS DE RODAGEM DO ESTADO DE MINAS": "DEPARTAMENTO DE EDIFICACOES E ESTRADAS DE RODAGEM",
    "ESCOLA DE SAUDE PUBLICA DO ESTADO DE MINAS GERAIS": "ESCOLA DE SAUDE",
    "FUNDACAO CENTRO DE HEMATOLOGIA E HEMOTERAPIA DO ESTADO DE MINAS GERAIS": "FUNDACAO HEMOMINAS",
    "FUNDACAO DE ARTE DE OURO PRETO": "FAOP FUNDACAO ARTE OURO PRETO",
    "FUNDACAO DE EDUCACAO PARA O TRABALHO DE MINAS GERAIS": "UTRAMIG FUND EDUC PARA O TRAB",
    "FUNDACAO EDUCACIONAL CAIO MARTINS": "FUCAM FUND EDUC CAIO MARTINS",
    "FUNDACAO ESTADUAL DO MEIO AMBIENTE": "FEAM FUNDACAO DO MEIO AMBIENTE",
    "FUNDACAO EZEQUIEL DIAS": "FUNED FUNDACAO EZEQUIEL DIAS",
    "FUNDACAO HOSPITALAR DO ESTADO DE MINAS GERAIS": "FHEMIG FUND HOSPITALAR EST MG",
    "FUNDACAO TV MINAS CULTURAL E EDUCATIVA": "FUNDACAO TV MINAS",
    "GABINETE MILITAR DO GOVERNADOR DO ESTADO": "GABINETE MILITAR",
    "INSTITUTO DE DESENVOLVIMENTO DO NORTE E NORDESTE DE MINAS GERAIS": "IDENE INST DES NORTE NORD MG",
    "INSTITUTO DE METROLOGIA E QUALIDADE DO ESTADO DE MINAS GERAIS": "INSTITUTO DE METROLOGIA E QUALIDADE",
    "INSTITUTO DE PREVIDENCIA DOS SERVIDORES DO ESTADO DE MINAS GERAIS": "IPSEMG INSTITUTO PREVIDENCIA",
    "INSTITUTO DE PREVIDENCIA DOS SERVIDORES MILITARES DO ESTADO DE MG": "IPSM",
    "INSTITUTO ESTADUAL DE FLORESTAS": "IEF INST EST DE FLORESTAS",
    "INSTITUTO ESTADUAL DO PATRIMONIO HISTORICO E ARTISTICO DE MINAS GERAIS": "IEPHA INST PATRIM HISTORICO",
    "INSTITUTO MINEIRO DE AGROPECUARIA": "IMA INST MINEIRO AGROPECUARIA",
    "INSTITUTO MINEIRO DE GESTAO DAS AGUAS": "IGAM INST DE GESTAO DAS AGUAS",
    "LOTERIA DO ESTADO DE MINAS GERAIS": "LOTERIA DO ESTADO DE MG",
    "OUVIDORIA GERAL DO ESTADO": "OUVIDORIA GERAL",
    "POLICIA CIVIL DO ESTADO DE MINAS GERAIS": "POLICIA CIVIL",
    "SECRETARIA DE ESTADO DA AGRICULTURA PECUARIA E ABASTECIMENTO": "SECRETARIA DA AGRICULTURA",
    "SECRETARIA DE ESTADO DA FAZENDA": "SECRETARIA DA FAZENDA",
    "SECRETARIA DE ESTADO DE CULTURA E TURISMO": "SECRETARIA CULTURA E TURISMO",
    "SECRETARIA DE ESTADO DE DESENVOLVIMENTO ECONOMICO": "SECRETARIA DE DESENVOLVIMENTO ECONOMICO",
    "SECRETARIA DE ESTADO DE EDUCACAO": "SECRETARIA DE EDUCACAO",
    "SECRETARIA DE ESTADO DE GOVERNO": "SECRETARIA DE GOVERNO",
    "SECRETARIA DE ESTADO DE INFRAESTRUTURA MOBILIDADE E PARCERIAS": "SECRETARIA DE INFRAESTRUTURA E MOBILIDADE",
    "SECRETARIA DE ESTADO DE JUSTICA E SEGURANCA PUBLICA": "SECRETARIA DE JUSTICA E SEGURANCA PUBLICA",
    "SECRETARIA DE ESTADO DE PLANEJAMENTO E GESTAO": "SEC DE PLANEJAMENTO E GESTAO",
    "SECRETARIA DE ESTADO DE SAUDE": "SECRETARIA DE SAUDE",
    "SECRETARIA DE ESTADO DO MEIO AMBIENTE E DESENVOLVIMENTO SUSTENTAVEL": "SECRETARIA DO MEIO AMBIENTE",
    "UNIVERSIDADE DO ESTADO DE MINAS GERAIS": "UEMG UNIV EST DE MINAS GERAIS",
    "UNIVERSIDADE ESTADUAL DE MONTES CLAROS": "UNIMONTES UNIV MONTES CLAROS"
}

# =====================================================
# LEITURA ROBUSTA
# =====================================================

def ler_csv_robusto(arquivo):

    delimitadores = [';', ',', '\t', '|']
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']

    for enc in encodings:
        for delim in delimitadores:

            try:

                df = pd.read_csv(
                    arquivo,
                    sep=delim,
                    encoding=enc,
                    dtype=str,
                    engine='python',
                    on_bad_lines='skip'
                )

                if len(df.columns) > 1:
                    df.columns = df.columns.str.strip()
                    return df, delim

            except:
                pass

    return None, None

# =====================================================
# LISTAR ARQUIVOS MENSAIS
# =====================================================

def listar_arquivos():

    arquivos = []

    for f in os.listdir(PASTA_ORIGEM):

        if re.match(r'^dados_serv_\d{6}\.csv$', f):
            arquivos.append(f)

    return sorted(
        arquivos,
        key=lambda x: re.search(r'(\d{6})', x).group(1)
    )

# =====================================================
# CARREGAR DM_DIARIO
# =====================================================

def carregar_dm():

    if not os.path.exists(ARQUIVO_DM):
        print(f"dm_diario.csv não encontrado em {ARQUIVO_DM}")
        return {}

    dm = pd.read_csv(
        ARQUIVO_DM,
        sep=None,
        engine="python",
        dtype=str
    )

    dm.columns = dm.columns.str.strip()

    col_id = [c for c in dm.columns if "tempo" in c.lower()][0]
    col_data = [c for c in dm.columns if "format" in c.lower()][0]

    dm[col_id] = dm[col_id].astype(str).str.strip()

    return dict(zip(dm[col_id], dm[col_data]))

# =====================================================
# LIMPAR ID DATA
# =====================================================

def limpar_id(valor):

    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if "," in valor:
        valor = valor.split(",")[0]

    if "." in valor:
        valor = valor.split(".")[0]

    return valor

# =====================================================
# CONVERSÃO DE DATAS
# =====================================================

def converter_datas(df):

    mapa_datas = carregar_dm()

    if not mapa_datas:
        return df

    colunas_data = [
        c for c in df.columns
        if c.startswith("id_data")
    ]

    if not colunas_data:
        return df

    precisa_converter = False

    for col in colunas_data:

        amostra = df[col].dropna().head(100)

        if len(amostra) == 0:
            continue

        encontrou = (
            amostra.astype(str)
            .str.strip()
            .apply(limpar_id)
            .isin(mapa_datas.keys())
            .any()
        )

        if encontrou:
            precisa_converter = True
            break

    if not precisa_converter:

        print("Conversão de datas: ignorada")
        return df

    print("Conversão de datas: executada")

    for col in colunas_data:

        original = df[col].copy()

        df[col] = (
            df[col]
            .apply(limpar_id)
            .map(mapa_datas)
            .fillna(original)
        )

    return df

# =====================================================
# PADRONIZAÇÕES
# =====================================================

def padronizar_orgao(valor):

    if pd.isna(valor):
        return ''

    valor = str(valor).strip().upper()

    return MAPA_ORGAOS.get(valor, valor)

def corrigir_contrato(valor):

    if pd.isna(valor):
        return ''

    txt = str(valor).upper()

    if "CONTRATO" in txt and "TEMP" in txt:
        return "CONTRATO TEMPORARIO"

    return valor

def aplicar_padronizacao(df):

    for col in [
        'desc_instituicao_dotacao',
        'desc_instituicao_lotacao'
    ]:

        if col in df.columns:
            df[col] = df[col].apply(padronizar_orgao)

    if 'descsitserv' in df.columns:
        df['descsitserv'] = df['descsitserv'].apply(corrigir_contrato)

    return df

# =====================================================
# NORMALIZAÇÃO COMPARAÇÃO
# =====================================================

import re
from datetime import datetime

def normalizar(v):

    if pd.isna(v):
        return ""

    v = str(v).strip()

    if v.lower() in (
        "",
        "nan",
        "none",
        "null"
    ):
        return ""

    # remove espaços duplicados
    v = re.sub(r"\s+", " ", v)

    # datas
    formatos = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(
                v,
                fmt
            ).strftime("%d/%m/%Y")
        except:
            pass

    # números
    try:

        txt = (
            v.replace(".", "")
             .replace(",", ".")
        )

        n = float(txt)

        if n.is_integer():
            return str(int(n))

        return str(round(n, 6))

    except:
        pass

    return v.upper()

# =====================================================
# GERAR DELTA
# =====================================================

def gerar_delta(df_ant, df_atu, ano_mes):

    for df in [df_ant, df_atu]:

        df['masp'] = df['masp'].astype(str).str.strip()
        df['adm'] = df['adm'].astype(str).str.strip()

        df['_chave'] = (
            df['masp'] + "|" + df['adm']
        )

        df.drop_duplicates(
            subset=['_chave'],
            keep='last',
            inplace=True
        )

    chaves_ant = set(df_ant['_chave'])
    chaves_atu = set(df_atu['_chave'])

    dict_ant = df_ant.set_index('_chave').to_dict('index')
    dict_atu = df_atu.set_index('_chave').to_dict('index')

    colunas = [
        c for c in df_atu.columns
        if c in df_ant.columns
        and c not in (
            '_chave',
            'masp',
            'adm',
            'ano_mes'
        )
    ]

    registros = []

    novos = alterados = removidos = 0

    # NOVOS
    for chave in chaves_atu - chaves_ant:

        reg = dict_atu[chave].copy()

        reg.pop('_chave', None)

        reg['situacao_delta'] = 'NOVO'

        registros.append(reg)

        novos += 1

    # ALTERADOS
    for chave in chaves_ant & chaves_atu:

        a = dict_ant[chave]
        b = dict_atu[chave]

        mudou = any(
            a.get(c) != b.get(c)
            for c in colunas
        )

        if mudou:

            reg = b.copy()

            reg.pop('_chave', None)

            reg['situacao_delta'] = 'ALTERADO'

            registros.append(reg)

            alterados += 1

    # REMOVIDOS
    for chave in chaves_ant - chaves_atu:

        reg = dict_ant[chave].copy()

        reg.pop('_chave', None)

        reg['ano_mes'] = ano_mes

        reg['situacao_delta'] = 'REMOVIDO'

        registros.append(reg)

        removidos += 1

    df_delta = pd.DataFrame(registros)

    return (
        df_delta,
        novos,
        alterados,
        removidos
    )

# =====================================================
# MAIN
# =====================================================

def main(competencia=None):

    arquivos = listar_arquivos()

    if len(arquivos) < 2:

        print("Necessários pelo menos 2 arquivos.")
        return False

    if competencia:

        # Modo reprocessamento: compara a competência pedida
        # com o arquivo imediatamente anterior a ela
        arquivo_atual = f"dados_serv_{competencia}.csv"

        if arquivo_atual not in arquivos:
            print(f"Arquivo {arquivo_atual} não encontrado em {PASTA_ORIGEM}")
            return False

        idx = arquivos.index(arquivo_atual)

        if idx == 0:
            print(f"Não há arquivo anterior a {arquivo_atual} para comparar.")
            return False

        arquivo_anterior = arquivos[idx - 1]

    else:

        arquivo_anterior = arquivos[-2]
        arquivo_atual = arquivos[-1]

    print("=" * 60)
    print("RELACAO NOMINAL")
    print("=" * 60)

    print(f"Mês anterior : {arquivo_anterior}")
    print(f"Mês atual    : {arquivo_atual}")

    caminho_ant = os.path.join(
        PASTA_ORIGEM,
        arquivo_anterior
    )

    caminho_atu = os.path.join(
        PASTA_ORIGEM,
        arquivo_atual
    )

    df_ant, _ = ler_csv_robusto(caminho_ant)
    df_atu, delim = ler_csv_robusto(caminho_atu)

    if df_ant is None or df_atu is None:

        print("Erro ao ler arquivos.")
        return False

    # =====================================================
    # PADRONIZA OS DOIS ARQUIVOS
    # =====================================================

    df_ant = df_ant.copy()
    df_atu = df_atu.copy()

    df_ant = converter_datas(df_ant)
    df_ant = aplicar_padronizacao(df_ant)

    df_atu = converter_datas(df_atu)
    df_atu = aplicar_padronizacao(df_atu)

    # =====================================================
    # NORMALIZA TODOS OS CAMPOS
    # =====================================================

    for col in df_ant.columns:
        df_ant[col] = df_ant[col].apply(normalizar)

    for col in df_atu.columns:
        df_atu[col] = df_atu[col].apply(normalizar)

    ano_mes = re.search(
        r'(\d{6})',
        arquivo_atual
    ).group(1)

    (
        df_delta,
        novos,
        alterados,
        removidos
    ) = gerar_delta(
        df_ant,
        df_atu,
        ano_mes
    )
    # =====================================================
    # SALVAR XLSX
    # =====================================================

    if "_chave" in df_delta.columns:
        df_delta = df_delta.drop(columns=["_chave"])

    # =====================================================
    # VERIFICA TAMANHO (limite de 100 MB do GitHub)
    # =====================================================

    tamanho_mb = (
        len(df_delta.to_csv(index=False).encode("utf-8"))
        / (1024 * 1024)
    )

    print()
    print(f"Linhas no delta        : {len(df_delta):,}")
    print(f"Tamanho estimado do CSV: {tamanho_mb:.1f} MB")

    if tamanho_mb > LIMITE_CSV_MB:
        print()
        print("ERRO: o CSV deste delta passaria do limite do GitHub (100 MB).")
        print("O delta NÃO foi salvo e nada será publicado.")
        print(f"NOVOS: {novos} | ALTERADOS: {alterados} | REMOVIDOS: {removidos}")
        return False

    arquivo_saida = os.path.join(
        PASTA_UPLOAD,
        arquivo_atual.replace(".csv", ".xlsx")
    )

    df_delta.to_excel(
        arquivo_saida,
        index=False,
        engine="openpyxl"
    )

    print()
    print("RESULTADO")
    print("-" * 60)
    print(f"NOVOS      : {novos}")
    print(f"ALTERADOS  : {alterados}")
    print(f"REMOVIDOS  : {removidos}")
    print(f"TOTAL      : {len(df_delta)}")
    print()
    print("Arquivo XLSX salvo:")
    print(arquivo_saida)

    return True

if __name__ == "__main__":

    competencia = sys.argv[1] if len(sys.argv) > 1 else None

    sys.exit(0 if main(competencia) else 1)