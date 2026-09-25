from pymongo import MongoClient

cliente = MongoClient("mongodb://localhost:27017/")

try:
    cliente.admin.command("ping")
    print("Conectado ao MongoDB!")

except Exception as erro:
    print("Erro: ", erro)

finally:
    cliente.close();
    print("Conexão encerrada!")
