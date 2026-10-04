"""T5833 패턴 파서 및 변환 기능 단위 테스트"""

from pathlib import Path

from atl_converter.pattern_parser import PatternParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_golden_pattern() -> None:
    sample_path = FIXTURES_DIR / "sample_pattern.pat"
    content = sample_path.read_text(encoding="utf-8")

    parser = PatternParser()
    prog = parser.parse(content)

    assert prog.pattern_name == "PAT_BURST_TEST"
    assert prog.pin_list == ["CLK", "CS_N", "WE_N", "DQ0", "DQ1"]
    assert len(prog.vectors) > 0


def test_modify_ts_with_filter() -> None:
    sample_path = FIXTURES_DIR / "sample_pattern.pat"
    content = sample_path.read_text(encoding="utf-8")

    parser = PatternParser()
    prog = parser.parse(content)

    # TS1 중 INCX 명령어인 라인만 TS3으로 치환
    count = parser.modify_ts(prog, target_ts="TS1", new_ts="TS3", instruction_filter="INCX")
    assert count == 2

    # 재직렬화 후 TS3이 반영되었는지 확인
    emitted = parser.emit(prog)
    assert "TS3   INCX" in emitted


def test_remap_pins() -> None:
    sample_path = FIXTURES_DIR / "sample_pattern.pat"
    content = sample_path.read_text(encoding="utf-8")

    parser = PatternParser()
    prog = parser.parse(content)

    old_pins = ["CLK", "CS_N", "WE_N", "DQ0", "DQ1"]
    new_pins = ["CS_N", "CLK", "WE_N", "DQ1", "DQ0"]

    parser.remap_pins(prog, old_pins, new_pins)

    # V002 라인(원래 1 0 0 D 0 -> CLK=1, CS_N=0, WE_N=0, DQ0=D, DQ1=0)
    # 신규 순서 CS_N, CLK, WE_N, DQ1, DQ0 -> 0 1 0 0 D
    emitted = parser.emit(prog)
    assert "0 1 0 0 D" in emitted


def test_4way_pattern_parsing_and_remapping() -> None:
    sample_path = FIXTURES_DIR / "sample_4way.pat"
    content = sample_path.read_text(encoding="utf-8")

    parser = PatternParser()
    prog = parser.parse(content)

    assert prog.pattern_name == "PAT_LPDDR4_BURST"
    assert prog.way_mode == 4
    assert prog.sdef_file == "sample.sdef"

    # 4-way 핀 순서 재배열: CLK, CS_N, DQ0, DQ1 -> CS_N, CLK, DQ1, DQ0
    old_pins = ["CLK", "CS_N", "DQ0", "DQ1"]
    new_pins = ["CS_N", "CLK", "DQ1", "DQ0"]
    parser.remap_pins(prog, old_pins, new_pins)

    emitted = parser.emit(prog)
    # V001: 1010 0000 DDDD 0000 -> 0000 1010 0000 DDDD
    assert "0000 1010 0000 DDDD" in emitted


def test_sdef_parsing_and_sync() -> None:
    sdef_path = FIXTURES_DIR / "sample.sdef"
    sdef_content = sdef_path.read_text(encoding="utf-8")

    from atl_converter.pattern_parser import SDEFParser

    sdef_parser = SDEFParser()
    sdef = sdef_parser.parse(sdef_content)

    assert sdef.sdef_name == "SAMPLE_LPDDR4_PKG"
    assert "REORDERED_PINS" in sdef.groups
    assert sdef.groups["REORDERED_PINS"] == ["CS_N", "CLK", "DQ1", "DQ0"]

    # 패턴 파일과 SDEF 동기화
    pat_path = FIXTURES_DIR / "sample_4way.pat"
    pat_parser = PatternParser()
    prog = pat_parser.parse(pat_path.read_text(encoding="utf-8"))

    pat_parser.sync_with_sdef(prog, sdef, group_name="REORDERED_PINS")
    assert prog.pin_list == ["CS_N", "CLK", "DQ1", "DQ0"]

    emitted = pat_parser.emit(prog)
    assert "0000 1010 0000 DDDD" in emitted


def test_semicolon_and_star_comments_in_pattern() -> None:
    content = """
    ; Header comment with semicolon
    * Header comment with asterisk
    PATT_NAME: PAT_COMMENT_TEST ;
    PIN_ASSIGN: CLK, CS, DQ ;
    ; First vector line
    V01:        TS1  INCX  1 0 D ; inline comment after vector
    * Another comment line
    V02:        TS1  NOP   0 0 0 ; semicolon comment
    """
    parser = PatternParser()
    prog = parser.parse(content)

    assert prog.pattern_name == "PAT_COMMENT_TEST"
    assert prog.pin_list == ["CLK", "CS", "DQ"]

    # 실제 유효 벡터 2개 파싱 확인
    valid_vectors = [v for v in prog.vectors if not v.is_blank_or_comment_only]
    assert len(valid_vectors) == 2
    assert valid_vectors[0].instruction == "INCX"
    assert valid_vectors[0].pin_vectors == "1 0 D"
    assert valid_vectors[0].comment == "inline comment after vector"
    assert valid_vectors[1].instruction == "NOP"
    assert valid_vectors[1].comment == "semicolon comment"
