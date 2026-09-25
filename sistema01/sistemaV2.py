from pymongo import MongoClient

# --------------------------------------------------
# CONEXÃO COM O MONGODB
# --------------------------------------------------

# Conectar ao servidor MongoDB Local
cliente = MongoClient("mongodb://localhost:27017/")

# Selecionar o Banco de Dados (Ou Criar se não existir)
banco = cliente["sistema_matricula"]

# Selecionar a coleção
alunos = banco["alunos"]

# --------------------------------------------------
# CREATE - CADASTRO DE ALUNO
# --------------------------------------------------
def cadastar_aluno():
    print("\n --- CADASTRAR ALUNO ---")

    matricula = int(input("Matrícula do Aluno: "))
    nome = input("Nome do Aluno: ")
    curso = input("Curso do Aluno: ")
    periodo = int(input("Período: "))
    instituicao = input("Instituição do Aluno: ")

    # Verificar se o aluno já existe
    aluno_existente = alunos.find_one({"matricula": matricula})

    if aluno_existente:
        print("Já existe um aluno com essa matrícula!")
        return

    # Criar o aluno (documento) no MongoDB
    aluno = {
        "matricula": matricula,
        "nome": nome,
        "curso": curso,
        "periodo": periodo,
        "ativo": True,
        "instituicao": instituicao
    }

    # Inserir (CREATE)
    alunos.insert_one(aluno)
    print("Aluno cadastrado com sucesso!")

# --------------------------------------------------
# READ - LISTAR TODOS OS ALUNOS
# --------------------------------------------------
def lista_alunos():
    print("\n --- LISTAR TODOS OS ALUNOS ---")

    # READ
    resultado = alunos.find()

    encontrou = False

    for aluno in resultado:
        encontrou = True

        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if  aluno["ativo"]:
            print("Status: Ativo",)
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])

    if not encontrou:
        print("Nenhum aluno cadastrado!")

# --------------------------------------------------
# READ - LISTAR TODOS OS ALUNOS EM ORDEM ALFABÉTICA
# --------------------------------------------------
def listar_alunos_ordem_alfaberica():
    print("\n --- LISTAR OS ALUNOS EM ORDEM ALFABÉTICA ---")

    # READ
    resultado = alunos.find().sort("nome", 1)

    encontrou = False

    for aluno in resultado:
        encontrou = True

        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if aluno["ativo"]:
            print("Status: Ativo", )
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])

    if not encontrou:
        print("Nenhum aluno cadastrado!")

# --------------------------------------------------
# READ - LISTAR TODOS OS ALUNOS POR INSTITUIÇÃO
# --------------------------------------------------
def listar_alunos_instituicao():
    print("\n --- LISTAR OS ALUNOS POR INSTITUICÃO ---")

    instituicao = input("Informe o nome da Instituição: ")

    # READ
    resultado = alunos.find({"instituicao":instituicao}).sort("nome", 1)

    encontrou = False

    for aluno in resultado:
        encontrou = True

        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if aluno["ativo"]:
            print("Status: Ativo", )
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])

    if not encontrou:
        print("Nenhum aluno cadastrado!")

# --------------------------------------------------
# READ - LISTAR TODOS OS ALUNOS POR CURSO
# --------------------------------------------------
def listar_alunos_curso():
    print("\n --- LISTAR OS ALUNOS POR CURSO ---")

    curso = input("Informe o nome da Curso: ")

    # READ
    resultado = alunos.find({"curso":curso}).sort("nome", 1)

    encontrou = False

    for aluno in resultado:
        encontrou = True

        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if aluno["ativo"]:
            print("Status: Ativo", )
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])

    if not encontrou:
        print("Nenhum aluno cadastrado!")

# --------------------------------------------------
# READ - LISTAR TODOS OS ALUNOS POR PERÍODO
# --------------------------------------------------
def listar_alunos_perido():
    print("\n --- LISTAR OS ALUNOS POR PERÍODO ---")

    periodo = int(input("Informe o período: "))

    # READ
    resultado = alunos.find({"periodo":periodo}).sort("nome", 1)

    encontrou = False

    for aluno in resultado:
        encontrou = True

        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if aluno["ativo"]:
            print("Status: Ativo", )
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])

    if not encontrou:
        print("Nenhum aluno cadastrado!")


# --------------------------------------------------
# READ - BUSCA ALUNO
# --------------------------------------------------
def buscar_aluno():
    print("\n --- BUSCAR ALUNO ---")

    matricula = int(input("Matrícula do Aluno: "))
    # READ
    aluno = alunos.find_one({"matricula": matricula})

    if aluno:
        print("\nAluno Encontrado!")
        print("")
        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if aluno["ativo"]:
            print("Status: Ativo", )
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])
    else:
        print("Aluno não encontrado")

# --------------------------------------------------
# READ - BUSCA ALUNO POR NOME
# --------------------------------------------------
def buscar_aluno_nome():
    print("\n --- BUSCAR ALUNO POR NOME---")

    nome = input("Nome do Aluno ou parte do nome: ")
    # READ
    # aluno = alunos.find_one({"nome": nome})
    resultado = alunos.find({
        "nome": {"$regex": nome, "$options": "i"}
    })
    encontrou = False

    for aluno in resultado:
        encontrou = True

        print("\nAluno Encontrado!")
        print("")
        print("-----------------------------")
        print("Matrícula: ", aluno["matricula"])
        print("Nome: ", aluno["nome"])
        print("Curso: ", aluno["curso"])
        print("Período", aluno["periodo"])
        if aluno["ativo"]:
            print("Status: Ativo", )
        else:
            print("Status: Inativo", )
        print("Instituição", aluno["instituicao"])

    if not encontrou:
        print("Aluno não encontrado")

# --------------------------------------------------
# UPDATE - ATUALIZAR ALUNO
# --------------------------------------------------
def atualizar_aluno():
    print("\n --- ATUALIZAR ALUNO ---")

    matricula = int(input("Matrícula do Aluno: "))
    # READ
    aluno = alunos.find_one({"matricula": matricula})

    if not aluno:
        print("Aluno não encontrado!")
        return

    print("Aluno: ", aluno["nome"])

    novo_nome = input("Nome do Aluno: ")
    novo_curso = input("Curso do Aluno: ")
    novo_periodo = int(input("Período: "))
    nova_instituicao = input("Instituição do Aluno: ")
    novo_status = input("O Aluno está Ativo? (S/N): ")
    if novo_status.upper() == "S":
        novo_ativo = True
    else:
        novo_ativo = False

    # UPDATE
    alunos.update_one(
        {"matricula": matricula},
        {"$set": {
            "nome": novo_nome,
            "curso": novo_curso,
            "periodo": novo_periodo,
            "ativo": novo_ativo,
            "instituicao": nova_instituicao
        }})
    print("Aluno Atualizado com sucesso!")


# --------------------------------------------------
# DELETE - EXLCUIR ALUNO
# --------------------------------------------------
def excluir_aluno():
    print("\n --- EXLUIR ALUNO ---")

    matricula = int(input("Matrícula do Aluno: "))
    # READ
    aluno = alunos.find_one({"matricula": matricula})

    if not aluno:
        print("Aluno não encontrado!")
        return

    print("Aluno: ", aluno["nome"])

    confirmacao = input("Deseja realmente exlcuir? (S/N): ")

    if confirmacao.upper() == "S":
        # DELETE
        alunos.delete_one({"matricula": matricula})
        print("Aluno excluído com sucesso!")
    else:
        print("Exclusão cancelada!")

# Programa Principal

while True:
    print("\n============================")
    print("    SISTEMA DE MATRÍCULAS")
    print("============================")

    print("1 - Cadastrar aluno")
    print("2 - Listar alunos")
    print("3 - Listar alunos em ordem alfabética")
    print("4 - Listar alunos por instituição")
    print("5 - Listar alunos por curso")
    print("6 - Listar alunos por período")
    print("7 - Buscar aluno")
    print("8 - Buscar aluno por nome")
    print("9 - Atualziar aluno")
    print("10 - Excluir aluno")
    print("0 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        cadastar_aluno()
    elif opcao == "2":
        lista_alunos()
    elif opcao == "3":
        listar_alunos_ordem_alfaberica()
    elif opcao == "4":
        listar_alunos_instituicao()
    elif opcao == "5":
        listar_alunos_curso()
    elif opcao == "6":
        listar_alunos_perido()
    elif opcao == "7":
        buscar_aluno()
    elif opcao == "8":
        buscar_aluno_nome()
    elif opcao == "9":
        atualizar_aluno()
    elif opcao == "10":
        excluir_aluno()
    elif opcao == "0":
        print("Sistema Encerrado")
        break
    else:
        print("Opção inválida")
