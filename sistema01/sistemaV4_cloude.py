"""
Sistema de Matrículas - Versão 3
CRUD com MongoDB (PyMongo) + registro de log do sistema

Requisitos:
    pip install pymongo
    MongoDB em execução em localhost:27017

O log é gravado em "sistema_matricula.log", na mesma pasta do programa.
"""
import getpass
import logging
import re
import sys
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collation import Collation
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

# --------------------------------------------------
# CONFIGURAÇÕES
# --------------------------------------------------
URI = "mongodb://localhost:27017/"
NOME_BANCO = "sistema_matricula"
NOME_COLECAO = "alunos"
PERIODO_MIN, PERIODO_MAX = 1, 12

# Arquivo de log na mesma pasta do script
ARQUIVO_LOG = Path(__file__).with_name("sistema_matricula.log")
TAMANHO_MAX_LOG = 1_000_000   # 1 MB por arquivo
QTD_BACKUPS_LOG = 3           # mantém .log.1, .log.2 e .log.3

# Collation pt-BR com strength=1: ignora maiúsculas/minúsculas e acentos
COLLATION_PT = Collation(locale="pt", strength=1)


# --------------------------------------------------
# CONFIGURAÇÃO DO LOG
# --------------------------------------------------
def configurar_log():
    """
    Cria o logger do sistema.
    - RotatingFileHandler: quando o arquivo atinge 1 MB, ele é renomeado
      (.log.1, .log.2...) e um novo arquivo é iniciado, evitando crescer sem limite.
    - Formato: data/hora | nível | mensagem
    """
    logger = logging.getLogger("sistema_matricula")
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # evita duplicar handlers se a função for chamada 2x
        handler = RotatingFileHandler(
            ARQUIVO_LOG,
            maxBytes=TAMANHO_MAX_LOG,
            backupCount=QTD_BACKUPS_LOG,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        ))
        logger.addHandler(handler)
    return logger


log = configurar_log()


# --------------------------------------------------
# CONEXÃO COM O MONGODB
# --------------------------------------------------
def conectar():
    """Conecta ao MongoDB, testa a conexão e garante o índice único de matrícula."""
    try:
        cliente = MongoClient(URI, serverSelectionTimeoutMS=3000)
        cliente.admin.command("ping")
    except ConnectionFailure as erro:
        log.critical(f"CONEXAO | Falha ao conectar em {URI} | {erro}")
        print(f"Erro: não foi possível conectar ao MongoDB em {URI}")
        print("Verifique se o serviço do MongoDB está em execução.")
        sys.exit(1)

    colecao = cliente[NOME_BANCO][NOME_COLECAO]
    colecao.create_index("matricula", unique=True)
    log.info(f"CONEXAO | Conectado a {URI} | banco={NOME_BANCO} | coleção={NOME_COLECAO}")
    return cliente, colecao


# --------------------------------------------------
# FUNÇÕES AUXILIARES DE ENTRADA
# --------------------------------------------------
def ler_texto(msg, padrao=None):
    """Lê um texto não vazio. Se houver 'padrao', Enter mantém o valor atual."""
    while True:
        valor = input(msg).strip()
        if valor:
            return valor
        if padrao is not None:
            return padrao
        print("  Campo obrigatório. Tente novamente.")


def ler_inteiro(msg, minimo=None, maximo=None, padrao=None):
    """Lê um inteiro validando faixa. Se houver 'padrao', Enter mantém o valor atual."""
    while True:
        valor = input(msg).strip()
        if not valor and padrao is not None:
            return padrao
        try:
            numero = int(valor)
        except ValueError:
            print("  Digite um número inteiro válido.")
            continue
        if minimo is not None and numero < minimo:
            print(f"  O valor deve ser maior ou igual a {minimo}.")
        elif maximo is not None and numero > maximo:
            print(f"  O valor deve ser menor ou igual a {maximo}.")
        else:
            return numero


def ler_sim_nao(msg, padrao=None):
    """Lê uma resposta S/N e devolve True/False."""
    while True:
        valor = input(msg).strip().upper()
        if not valor and padrao is not None:
            return padrao
        if valor in ("S", "SIM"):
            return True
        if valor in ("N", "NAO", "NÃO"):
            return False
        print("  Responda com S ou N.")


# --------------------------------------------------
# FUNÇÕES AUXILIARES DE EXIBIÇÃO
# --------------------------------------------------
def exibir_aluno(aluno):
    status = "Ativo" if aluno.get("ativo", False) else "Inativo"
    print("-" * 40)
    print(f"Matrícula   : {aluno.get('matricula', '-')}")
    print(f"Nome        : {aluno.get('nome', '-')}")
    print(f"Curso       : {aluno.get('curso', '-')}")
    print(f"Período     : {aluno.get('periodo', '-')}")
    print(f"Status      : {status}")
    print(f"Instituição : {aluno.get('instituicao', '-')}")


def listar(colecao, filtro=None, campo_ordem="nome"):
    """Listagem genérica. Devolve a quantidade de alunos exibidos (usada no log)."""
    cursor = (colecao.find(filtro or {})
              .collation(COLLATION_PT)
              .sort(campo_ordem, ASCENDING))
    total = 0
    for aluno in cursor:
        exibir_aluno(aluno)
        total += 1

    if total == 0:
        print("Nenhum aluno encontrado.")
    else:
        print("-" * 40)
        print(f"Total: {total} aluno(s).")
    return total


def buscar_por_matricula(colecao):
    matricula = ler_inteiro("Matrícula do aluno: ", minimo=1)
    return matricula, colecao.find_one({"matricula": matricula})


# --------------------------------------------------
# CREATE - CADASTRAR ALUNO
# --------------------------------------------------
def cadastrar_aluno(colecao):
    print("\n--- CADASTRAR ALUNO ---")

    matricula = ler_inteiro("Matrícula do aluno: ", minimo=1)
    if colecao.find_one({"matricula": matricula}):
        print("Já existe um aluno com essa matrícula!")
        log.warning(f"CADASTRO | Recusado: matrícula {matricula} já existe")
        return

    aluno = {
        "matricula": matricula,
        "nome": ler_texto("Nome do aluno: "),
        "curso": ler_texto("Curso do aluno: "),
        "periodo": ler_inteiro(f"Período ({PERIODO_MIN}-{PERIODO_MAX}): ",
                               PERIODO_MIN, PERIODO_MAX),
        "instituicao": ler_texto("Instituição do aluno: "),
        "ativo": True,
        "data_cadastro": datetime.now(),
    }

    try:
        colecao.insert_one(aluno)
        print("Aluno cadastrado com sucesso!")
        log.info(f"CADASTRO | matrícula={matricula} | nome={aluno['nome']} | "
                 f"curso={aluno['curso']} | período={aluno['periodo']} | "
                 f"instituição={aluno['instituicao']}")
    except DuplicateKeyError:
        print("Já existe um aluno com essa matrícula!")
        log.warning(f"CADASTRO | Recusado pelo índice único: matrícula {matricula}")


# --------------------------------------------------
# READ - LISTAGENS
# --------------------------------------------------
def listar_todos(colecao):
    print("\n--- LISTAR TODOS OS ALUNOS (por matrícula) ---")
    total = listar(colecao, campo_ordem="matricula")
    log.info(f"CONSULTA | Listar todos | {total} resultado(s)")


def listar_ordem_alfabetica(colecao):
    print("\n--- LISTAR ALUNOS EM ORDEM ALFABÉTICA ---")
    total = listar(colecao, campo_ordem="nome")
    log.info(f"CONSULTA | Listar em ordem alfabética | {total} resultado(s)")


def listar_por_instituicao(colecao):
    print("\n--- LISTAR ALUNOS POR INSTITUIÇÃO ---")
    instituicao = ler_texto("Nome da instituição: ")
    total = listar(colecao, {"instituicao": instituicao})
    log.info(f"CONSULTA | Por instituição='{instituicao}' | {total} resultado(s)")


def listar_por_curso(colecao):
    print("\n--- LISTAR ALUNOS POR CURSO ---")
    curso = ler_texto("Nome do curso: ")
    total = listar(colecao, {"curso": curso})
    log.info(f"CONSULTA | Por curso='{curso}' | {total} resultado(s)")


def listar_por_periodo(colecao):
    print("\n--- LISTAR ALUNOS POR PERÍODO ---")
    periodo = ler_inteiro("Período: ", PERIODO_MIN, PERIODO_MAX)
    total = listar(colecao, {"periodo": periodo})
    log.info(f"CONSULTA | Por período={periodo} | {total} resultado(s)")


# --------------------------------------------------
# READ - BUSCAS
# --------------------------------------------------
def buscar_aluno(colecao):
    print("\n--- BUSCAR ALUNO POR MATRÍCULA ---")
    matricula, aluno = buscar_por_matricula(colecao)
    if aluno:
        exibir_aluno(aluno)
        log.info(f"CONSULTA | Busca matrícula={matricula} | encontrado")
    else:
        print("Aluno não encontrado.")
        log.info(f"CONSULTA | Busca matrícula={matricula} | não encontrado")


def buscar_aluno_nome(colecao):
    print("\n--- BUSCAR ALUNO POR NOME ---")
    trecho = ler_texto("Nome do aluno ou parte do nome: ")
    total = listar(colecao, {"nome": {"$regex": re.escape(trecho), "$options": "i"}})
    log.info(f"CONSULTA | Busca por nome='{trecho}' | {total} resultado(s)")


# --------------------------------------------------
# UPDATE - ATUALIZAR ALUNO
# --------------------------------------------------
def atualizar_aluno(colecao):
    print("\n--- ATUALIZAR ALUNO ---")
    matricula, aluno = buscar_por_matricula(colecao)
    if not aluno:
        print("Aluno não encontrado!")
        log.info(f"ATUALIZACAO | matrícula={matricula} | não encontrado")
        return

    exibir_aluno(aluno)
    print("\n(Pressione Enter para manter o valor atual)")

    status_atual = "S" if aluno.get("ativo") else "N"
    novos_dados = {
        "nome": ler_texto(f"Nome [{aluno['nome']}]: ", padrao=aluno["nome"]),
        "curso": ler_texto(f"Curso [{aluno['curso']}]: ", padrao=aluno["curso"]),
        "periodo": ler_inteiro(f"Período [{aluno['periodo']}]: ",
                               PERIODO_MIN, PERIODO_MAX, padrao=aluno["periodo"]),
        "instituicao": ler_texto(f"Instituição [{aluno['instituicao']}]: ",
                                 padrao=aluno["instituicao"]),
        "ativo": ler_sim_nao(f"Aluno ativo? (S/N) [{status_atual}]: ",
                             padrao=aluno.get("ativo", True)),
    }

    alteracoes = {k: v for k, v in novos_dados.items() if aluno.get(k) != v}
    if not alteracoes:
        print("Nenhuma alteração realizada.")
        log.info(f"ATUALIZACAO | matrícula={matricula} | sem alterações")
        return

    # Monta o histórico "campo: antes -> depois" para o log (auditoria)
    detalhes = "; ".join(f"{campo}: '{aluno.get(campo)}' -> '{valor}'"
                         for campo, valor in alteracoes.items())

    alteracoes["data_atualizacao"] = datetime.now()
    colecao.update_one({"matricula": matricula}, {"$set": alteracoes})
    print(f"Aluno atualizado com sucesso! ({len(alteracoes) - 1} campo(s) alterado(s))")
    log.info(f"ATUALIZACAO | matrícula={matricula} | {detalhes}")


# --------------------------------------------------
# DELETE - EXCLUIR ALUNO
# --------------------------------------------------
def excluir_aluno(colecao):
    print("\n--- EXCLUIR ALUNO ---")
    matricula, aluno = buscar_por_matricula(colecao)
    if not aluno:
        print("Aluno não encontrado!")
        log.info(f"EXCLUSAO | matrícula={matricula} | não encontrado")
        return

    exibir_aluno(aluno)
    if not ler_sim_nao("Deseja realmente excluir? (S/N): "):
        print("Exclusão cancelada.")
        log.info(f"EXCLUSAO | matrícula={matricula} | cancelada pelo usuário")
        return

    resultado = colecao.delete_one({"matricula": matricula})
    if resultado.deleted_count:
        print("Aluno excluído com sucesso!")
        # Grava os dados do aluno excluído: permite reconstruir o registro se preciso
        log.warning(f"EXCLUSAO | matrícula={matricula} | nome={aluno.get('nome')} | "
                    f"curso={aluno.get('curso')} | período={aluno.get('periodo')} | "
                    f"instituição={aluno.get('instituicao')} | ativo={aluno.get('ativo')}")
    else:
        print("O aluno não pôde ser excluído (talvez já tenha sido removido).")
        log.warning(f"EXCLUSAO | matrícula={matricula} | delete_one não removeu nenhum documento")


# --------------------------------------------------
# ESTATÍSTICAS - AGGREGATION PIPELINE
# --------------------------------------------------
def estatisticas(colecao):
    print("\n--- ESTATÍSTICAS ---")
    total = colecao.count_documents({})
    ativos = colecao.count_documents({"ativo": True})
    print(f"Total de alunos : {total}")
    print(f"Ativos          : {ativos}")
    print(f"Inativos        : {total - ativos}")
    log.info(f"CONSULTA | Estatísticas | total={total} | ativos={ativos}")

    if total == 0:
        return

    pipeline = [
        {"$group": {
            "_id": "$curso",
            "total": {"$sum": 1},
            "ativos": {"$sum": {"$cond": ["$ativo", 1, 0]}},
        }},
        {"$sort": {"total": DESCENDING, "_id": ASCENDING}},
    ]
    print("\nAlunos por curso:")
    print(f"{'Curso':<30}{'Total':>7}{'Ativos':>8}")
    for grupo in colecao.aggregate(pipeline):
        print(f"{str(grupo['_id']):<30}{grupo['total']:>7}{grupo['ativos']:>8}")


# --------------------------------------------------
# LOG - VISUALIZAR ÚLTIMOS REGISTROS
# --------------------------------------------------
def ver_log(colecao=None):
    """Mostra as últimas N linhas do arquivo de log (não usa o banco)."""
    print("\n--- ÚLTIMOS REGISTROS DO LOG ---")
    if not ARQUIVO_LOG.exists():
        print("O arquivo de log ainda não existe.")
        return

    quantidade = ler_inteiro("Quantas linhas exibir? [20]: ", minimo=1, padrao=20)
    with open(ARQUIVO_LOG, encoding="utf-8") as arquivo:
        # deque com maxlen guarda apenas as últimas N linhas, sem carregar tudo na memória
        ultimas = deque(arquivo, maxlen=quantidade)

    for linha in ultimas:
        print(linha, end="")
    print(f"\nArquivo: {ARQUIVO_LOG}")


# --------------------------------------------------
# PROGRAMA PRINCIPAL
# --------------------------------------------------
OPCOES = {
    "1": ("Cadastrar aluno", cadastrar_aluno),
    "2": ("Listar alunos", listar_todos),
    "3": ("Listar alunos em ordem alfabética", listar_ordem_alfabetica),
    "4": ("Listar alunos por instituição", listar_por_instituicao),
    "5": ("Listar alunos por curso", listar_por_curso),
    "6": ("Listar alunos por período", listar_por_periodo),
    "7": ("Buscar aluno por matrícula", buscar_aluno),
    "8": ("Buscar aluno por nome", buscar_aluno_nome),
    "9": ("Atualizar aluno", atualizar_aluno),
    "10": ("Excluir aluno", excluir_aluno),
    "11": ("Estatísticas", estatisticas),
    "12": ("Ver log do sistema", ver_log),
}


def exibir_menu():
    print("\n" + "=" * 40)
    print("     SISTEMA DE MATRÍCULAS - v3")
    print("=" * 40)
    for chave, (descricao, _) in OPCOES.items():
        print(f"{chave:>2} - {descricao}")
    print(" 0 - Sair")


def main():
    usuario = getpass.getuser()
    log.info(f"SISTEMA | Iniciado pelo usuário '{usuario}'")

    cliente, alunos = conectar()
    try:
        while True:
            exibir_menu()
            opcao = input("Escolha uma opção: ").strip()

            if opcao == "0":
                print("Sistema encerrado.")
                break

            item = OPCOES.get(opcao)
            if item is None:
                print("Opção inválida!")
                log.warning(f"MENU | Opção inválida digitada: '{opcao}'")
                continue

            try:
                item[1](alunos)
            except PyMongoError as erro:
                print(f"Erro no banco de dados: {erro}")
                # log.exception grava a mensagem e o traceback completo
                log.exception(f"BANCO | Erro na opção {opcao} ({item[0]})")
            except Exception as erro:
                print(f"Erro inesperado: {erro}")
                log.exception(f"SISTEMA | Erro inesperado na opção {opcao} ({item[0]})")
    except (KeyboardInterrupt, EOFError):
        print("\nSistema encerrado.")
        log.info("SISTEMA | Interrompido pelo usuário (Ctrl+C)")
    finally:
        cliente.close()
        log.info("SISTEMA | Encerrado")


if __name__ == "__main__":
    main()
