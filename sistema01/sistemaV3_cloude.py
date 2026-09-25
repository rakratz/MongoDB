"""
Sistema de Matrículas - CRUD com MongoDB (PyMongo)

Requisitos:
    pip install pymongo
    MongoDB em execução em localhost:27017
"""
import re
import sys
from datetime import datetime

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

# Collation pt-BR com strength=1: compara ignorando maiúsculas/minúsculas e
# acentos ("puc goias" == "PUC Goiás") e ordena corretamente ("Álvaro" antes de "Bruno").
COLLATION_PT = Collation(locale="pt", strength=1)


# --------------------------------------------------
# CONEXÃO COM O MONGODB
# --------------------------------------------------
def conectar():
    """Conecta ao MongoDB, testa a conexão e garante o índice único de matrícula."""
    try:
        cliente = MongoClient(URI, serverSelectionTimeoutMS=3000)
        cliente.admin.command("ping")  # força a verificação da conexão
    except ConnectionFailure:
        print(f"Erro: não foi possível conectar ao MongoDB em {URI}")
        print("Verifique se o serviço do MongoDB está em execução.")
        sys.exit(1)

    colecao = cliente[NOME_BANCO][NOME_COLECAO]
    # Índice único: o próprio banco impede matrículas duplicadas
    colecao.create_index("matricula", unique=True)
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
    """Mostra os dados de um aluno (usa .get para tolerar campos ausentes)."""
    status = "Ativo" if aluno.get("ativo", False) else "Inativo"
    print("-" * 40)
    print(f"Matrícula   : {aluno.get('matricula', '-')}")
    print(f"Nome        : {aluno.get('nome', '-')}")
    print(f"Curso       : {aluno.get('curso', '-')}")
    print(f"Período     : {aluno.get('periodo', '-')}")
    print(f"Status      : {status}")
    print(f"Instituição : {aluno.get('instituicao', '-')}")


def listar(colecao, filtro=None, campo_ordem="nome"):
    """Função genérica de listagem: evita repetir o mesmo laço em várias funções."""
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


def buscar_por_matricula(colecao):
    """Pede a matrícula e devolve (matricula, documento ou None)."""
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
    except DuplicateKeyError:
        # Proteção extra caso outro usuário cadastre a mesma matrícula ao mesmo tempo
        print("Já existe um aluno com essa matrícula!")


# --------------------------------------------------
# READ - LISTAGENS
# --------------------------------------------------
def listar_todos(colecao):
    print("\n--- LISTAR TODOS OS ALUNOS (por matrícula) ---")
    listar(colecao, campo_ordem="matricula")


def listar_ordem_alfabetica(colecao):
    print("\n--- LISTAR ALUNOS EM ORDEM ALFABÉTICA ---")
    listar(colecao, campo_ordem="nome")


def listar_por_instituicao(colecao):
    print("\n--- LISTAR ALUNOS POR INSTITUIÇÃO ---")
    instituicao = ler_texto("Nome da instituição: ")
    listar(colecao, {"instituicao": instituicao})


def listar_por_curso(colecao):
    print("\n--- LISTAR ALUNOS POR CURSO ---")
    curso = ler_texto("Nome do curso: ")
    listar(colecao, {"curso": curso})


def listar_por_periodo(colecao):
    print("\n--- LISTAR ALUNOS POR PERÍODO ---")
    periodo = ler_inteiro("Período: ", PERIODO_MIN, PERIODO_MAX)
    listar(colecao, {"periodo": periodo})


# --------------------------------------------------
# READ - BUSCAS
# --------------------------------------------------
def buscar_aluno(colecao):
    print("\n--- BUSCAR ALUNO POR MATRÍCULA ---")
    _, aluno = buscar_por_matricula(colecao)
    if aluno:
        exibir_aluno(aluno)
    else:
        print("Aluno não encontrado.")


def buscar_aluno_nome(colecao):
    print("\n--- BUSCAR ALUNO POR NOME ---")
    trecho = ler_texto("Nome do aluno ou parte do nome: ")
    # re.escape evita que caracteres como "." ou "(" sejam interpretados como regex
    listar(colecao, {"nome": {"$regex": re.escape(trecho), "$options": "i"}})


# --------------------------------------------------
# UPDATE - ATUALIZAR ALUNO
# --------------------------------------------------
def atualizar_aluno(colecao):
    print("\n--- ATUALIZAR ALUNO ---")
    matricula, aluno = buscar_por_matricula(colecao)
    if not aluno:
        print("Aluno não encontrado!")
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

    # Atualiza somente os campos que realmente mudaram
    alteracoes = {k: v for k, v in novos_dados.items() if aluno.get(k) != v}
    if not alteracoes:
        print("Nenhuma alteração realizada.")
        return

    alteracoes["data_atualizacao"] = datetime.now()
    colecao.update_one({"matricula": matricula}, {"$set": alteracoes})
    print(f"Aluno atualizado com sucesso! ({len(alteracoes) - 1} campo(s) alterado(s))")


# --------------------------------------------------
# DELETE - EXCLUIR ALUNO
# --------------------------------------------------
def excluir_aluno(colecao):
    print("\n--- EXCLUIR ALUNO ---")
    matricula, aluno = buscar_por_matricula(colecao)
    if not aluno:
        print("Aluno não encontrado!")
        return

    exibir_aluno(aluno)
    if ler_sim_nao("Deseja realmente excluir? (S/N): "):
        resultado = colecao.delete_one({"matricula": matricula})
        if resultado.deleted_count:
            print("Aluno excluído com sucesso!")
        else:
            print("O aluno não pôde ser excluído (talvez já tenha sido removido).")
    else:
        print("Exclusão cancelada.")


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
}


def exibir_menu():
    print("\n" + "=" * 40)
    print("       SISTEMA DE MATRÍCULAS")
    print("=" * 40)
    for chave, (descricao, _) in OPCOES.items():
        print(f"{chave:>2} - {descricao}")
    print(" 0 - Sair")


def main():
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
                continue

            try:
                item[1](alunos)
            except PyMongoError as erro:
                print(f"Erro no banco de dados: {erro}")
    except (KeyboardInterrupt, EOFError):
        print("\nSistema encerrado.")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()
