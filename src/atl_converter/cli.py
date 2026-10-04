"""ATL_Converter CLI 인터페이스"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from atl_converter.pattern_parser import PatternParser
from atl_converter.scramble_engine import PrescrambleEngine

app = typer.Typer(help="Advantest T5833 Pattern & Prescramble 변환 도구")
console = Console()


@app.command()
def modify_ts(
    pattern_file: Path = typer.Argument(..., help="수정할 T5833 패턴 파일 경로"),
    output_file: Path = typer.Argument(..., help="출력할 결과 파일 경로"),
    target_ts: str = typer.Option(..., "--from-ts", "-f", help="기존 타이밍 세트 명 (예: TS1)"),
    new_ts: str = typer.Option(..., "--to-ts", "-t", help="변경할 타이밍 세트 명 (예: TS3)"),
    instruction: Optional[str] = typer.Option(None, "--inst", "-i", help="특정 ALPG 명령어 필터 (예: INCX)"),
) -> None:
    """패턴 파일 내의 Timing Set(TS)을 조건에 맞게 일괄 치환합니다."""
    if not pattern_file.exists():
        console.print(f"[bold red]오류:[/bold red] 파일이 존재하지 않습니다: {pattern_file}")
        raise typer.Exit(code=1)

    content = pattern_file.read_text(encoding="utf-8")
    parser = PatternParser()
    program = parser.parse(content)

    count = parser.modify_ts(program, target_ts=target_ts, new_ts=new_ts, instruction_filter=instruction)
    result_text = parser.emit(program)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(result_text, encoding="utf-8")

    console.print(
        f"[bold green]완료![/bold green] {count}개 벡터 라인의 TS가 '{target_ts}'에서 '{new_ts}'(으)로 변경되었습니다."
    )
    console.print(f"출력 파일: [cyan]{output_file}[/cyan]")


@app.command()
def test_scramble(
    scramble_file: Path = typer.Argument(..., help="T5833 Prescramble 수식 파일 경로"),
    log_x: int = typer.Option(0, "--x", help="논리 X 어드레스 (정수)"),
    log_y: int = typer.Option(0, "--y", help="논리 Y 어드레스 (정수)"),
) -> None:
    """Prescramble 수식을 로드하여 특정 논리 주소가 어떻게 물리 주소로 변환되는지 시뮬레이션합니다."""
    if not scramble_file.exists():
        console.print(f"[bold red]오류:[/bold red] 파일이 존재하지 않습니다: {scramble_file}")
        raise typer.Exit(code=1)

    engine = PrescrambleEngine()
    engine.parse_equations(scramble_file.read_text(encoding="utf-8"))

    phys_x, phys_y = engine.translate_address(log_x, log_y)
    console.print("[bold yellow]=== Prescramble 변환 시뮬레이션 결과 ===[/bold yellow]")
    console.print(f"논리 주소: Logical X = {log_x} (0x{log_x:X}), Logical Y = {log_y} (0x{log_y:X})")
    console.print(f"물리 주소: Physical X = {phys_x} (0x{phys_x:X}), Physical Y = {phys_y} (0x{phys_y:X})")


if __name__ == "__main__":
    app()
