import os

from colors import (
    BOLD,
    BRIGHT_CYAN,
    CYAN,
    GREEN,
    RED,
    YELLOW,
    c,
)

BANNER = r"""
  ╔═══════════════════════════════════════╗
  ║                                       ║
  ║   ██████╗ ██╗   ██╗███╗   ███╗        ║
  ║  ██╔════╝ ╚██╗ ██╔╝████╗ ████║        ║
  ║  ██║  ███╗ ╚████╔╝ ██╔████╔██║        ║
  ║  ██║   ██║  ╚██╔╝  ██║╚██╔╝██║        ║
  ║  ╚██████╔╝   ██║   ██║ ╚═╝ ██║        ║
  ║   ╚═════╝    ╚═╝   ╚═╝     ╚═╝        ║
  ║                                       ║
  ║      Management System                ║
  ╚═══════════════════════════════════════╝
"""


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    print(c(BANNER, BOLD + BRIGHT_CYAN))
    print(c("  Trainers · Members · Classes · Attendance", YELLOW))
    print()


def print_header(title: str) -> None:
    width = max(len(title) + 6, 44)
    top = "╔" + "═" * (width - 2) + "╗"
    mid = "║" + title.center(width - 2) + "║"
    bot = "╚" + "═" * (width - 2) + "╝"
    print()
    print(c(top, CYAN))
    print(c(mid, BOLD + BRIGHT_CYAN))
    print(c(bot, CYAN))


def print_menu(options: list[tuple[str, str]]) -> None:
    print(c("  ┌─ Options ─────────────────────", CYAN))
    for key, label in options:
        print(c(f"  │  [{key}]", YELLOW), f" {label}")
    print(c("  └───────────────────────────────", CYAN))


def print_section(title: str) -> None:
    line = "─" * 36
    print()
    print(c(f"  {title}", BOLD + YELLOW))
    print(c(f"  {line}", CYAN))


def print_empty(message: str) -> None:
    print(c(f"  {message}", CYAN))


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        return

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    header_line = "  " + " │ ".join(
        header.ljust(widths[index]) for index, header in enumerate(headers)
    )
    separator = "  " + "─┼─".join("─" * width for width in widths)

    print(c(header_line, BOLD + BRIGHT_CYAN))
    print(c(separator, CYAN))
    for row in rows:
        print(
            "  "
            + " │ ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        )


def print_success(message: str) -> None:
    print(c("  ╭─ ✓ Success ─────────────────", GREEN))
    print(c(f"  │  {message}", GREEN))
    print(c("  ╰──────────────────────────────", GREEN))


def print_error(message: str) -> None:
    print(c("  ╭─ ✗ Error ────────────────────", RED))
    print(c(f"  │  {message}", RED))
    print(c("  ╰──────────────────────────────", RED))


def pause() -> None:
    print(c("  ───────────────────────────────", CYAN))
    input(c("  ▶ Press Enter to continue… ", BRIGHT_CYAN))


def prompt_option() -> str:
    return input(c("\n  Option: ", CYAN)).strip()
