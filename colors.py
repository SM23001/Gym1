# Códigos ANSI para colores en terminal (Linux/Ubuntu, macOS, Windows 10+)

RESET = "\033[0m"
BOLD = "\033[1m"

# Colores normales 1
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

# Colores brillantes (opcional)
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_RED = "\033[91m"
BRIGHT_CYAN = "\033[96m"


def c(text: str, color: str) -> str:
    """Envuelve el texto con el color indicado y resetea al final."""
    return f"{color}{text}{RESET}"
