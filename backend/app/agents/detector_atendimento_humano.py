import re
import unicodedata


def normalizar_pedido_humano(mensagem: str) -> str:
    texto = unicodedata.normalize("NFKD", mensagem.casefold())
    texto = "".join(
        caractere for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"\s+", " ", texto).strip()


def detectar_pedido_atendimento_humano(mensagem: str) -> bool:
    texto = normalizar_pedido_humano(mensagem)

    if not texto:
        return False

    pedidos_diretos = {
        "humano",
        "atendente",
        "atendimento humano",
        "pessoa real",
        "quero um humano",
        "quero um atendente",
        "preciso de um atendente",
        "preciso de um humano",
        "falar com humano",
        "falar com um humano",
        "falar com atendente",
        "falar com um atendente",
        "falar com luciano",
        "quero falar com luciano",
    }

    if texto.strip(" .!?,") in pedidos_diretos:
        return True

    padroes = [
        r"\b(?:quero|preciso|prefiro|gostaria de)\s+"
        r"(?:ser atendid[oa] por|falar com|conversar com)\s+"
        r"(?:um[a]?\s+)?"
        r"(?:humano|pessoa|atendente|especialista|consultor|luciano)\b",

        r"\b(?:quero|preciso)\s+(?:de\s+)?"
        r"(?:um[a]?\s+)?(?:humano|atendente|pessoa real)\b",

        r"\b(?:pode|poderia|consegue)?\s*"
        r"(?:me\s+)?(?:transferir|encaminhar|passar)\s+"
        r"(?:para|pra|com)\s+"
        r"(?:um[a]?\s+|o\s+|a\s+)?"
        r"(?:humano|atendente|pessoa|especialista|luciano)\b",

        r"\bme\s+(?:transfere|encaminha|encaminhe|passa|coloca)\s+"
        r"(?:para|pra|com)\s+"
        r"(?:um[a]?\s+|o\s+|a\s+)?"
        r"(?:humano|atendente|pessoa|especialista|luciano)\b",

        r"\b(?:so|somente|apenas)\s+"
        r"(?:(?:vou|quero|irei)\s+)?"
        r"(?:continuar|continuo|conversar|converso|falar|falo)\b"
        r".{0,100}\b(?:humano|pessoa|atendente)\b",

        r"\bquero\s+atendimento\s+com\s+"
        r"(?:um[a]?\s+)?pessoa\b",

        r"\bnao\s+quero\s+mais\s+falar\s+com\s+"
        r"(?:robo|bot|ia)\b.{0,100}"
        r"\b(?:humano|pessoa|atendente)\b",
    ]

    if any(re.search(padrao, texto) for padrao in padroes):
        return True

    # Perguntas informativas nao representam pedido de transferencia.
    if re.search(
        r"\b(?:voces oferecem|oferecem|como funciona|"
        r"como e|o que e|qual e|quanto custa)\b",
        texto,
    ):
        return False

    # Interesse em contratar ou criar automacao nao e transferencia.
    if re.search(
        r"\b(?:automatizar|automacao|automatizado|automatizada|"
        r"implementar)\b.{0,70}\batendimento humano\b",
        texto,
    ):
        return False

    return False
