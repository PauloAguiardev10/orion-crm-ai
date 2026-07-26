from app.database.database import engine
from app.models.models import Base


def recriar_tabelas():
    confirmacao = input(
        "Esta operação apagará todas as tabelas e dados atuais. "
        "Digite RECRIAR para continuar: "
    )

    if confirmacao != "RECRIAR":
        print("Operação cancelada.")
        return

    print("Removendo tabelas existentes...")
    Base.metadata.drop_all(bind=engine)

    print("Criando a nova estrutura...")
    Base.metadata.create_all(bind=engine)

    print("Tabelas recriadas com sucesso!")


if __name__ == "__main__":
    recriar_tabelas()