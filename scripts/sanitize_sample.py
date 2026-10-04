"""사내 실제 T5833 Pattern 및 Scramble 파일 비식별화(Sanitizer) 도구

문법 구조, 토큰 구분자, Way 비트 폭, 키워드는 보존하면서
제품명, 주석 상세 내용, 신호 명칭 등의 민감 정보를 마스킹합니다.
"""

import re
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="T5833 파일 비식별화(Sanitizer) 도구")
console = Console()


@app.command()
def sanitize_pattern(
    input_file: Path = typer.Argument(..., help="원본 사내 패턴 파일"),
    output_file: Path = typer.Argument(..., help="비식별화된 출력 파일"),
) -> None:
    """패턴 파일의 주석 및 제품명을 마스킹하고 문법 구조를 보존합니다."""
    if not input_file.exists():
        console.print(f"[bold red]오류:[/bold red] 파일이 존재하지 않습니다: {input_file}")
        raise typer.Exit(code=1)

    lines = input_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    sanitized_lines = []

    for line in lines:
        stripped = line.strip()

        # 전체 주석 라인은 더미로 교체
        if stripped.startswith("!"):
            sanitized_lines.append("! --- SANITIZED COMMENT ---")
            continue

        # 라인 중간 주석 마스킹
        if "!" in line:
            code_part, _ = line.split("!", 1)
            line = f"{code_part.rstrip()} ! SANITIZED_COMMENT"

        # PATT_NAME 마스킹
        line = re.sub(
            r"PATT_NAME\s*:\s*([^;]+);",
            "PATT_NAME: PAT_SANITIZED_001 ;",
            line,
            flags=re.IGNORECASE,
        )

        sanitized_lines.append(line)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(sanitized_lines), encoding="utf-8")
    console.print(f"[bold green]비식별화 완료![/bold green] 파일 생성: {output_file}")


if __name__ == "__main__":
    app()
