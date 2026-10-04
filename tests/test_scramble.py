"""T5833 Prescramble 수식 엔진 단위 테스트"""

from pathlib import Path

from atl_converter.scramble_engine import PrescrambleEngine

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_and_translate_address() -> None:
    sample_path = FIXTURES_DIR / "sample_scramble.scram"
    content = sample_path.read_text(encoding="utf-8")

    engine = PrescrambleEngine()
    engine.parse_equations(content)

    # PHYS_X[0] = LOG_X[0]
    # PHYS_X[1] = LOG_X[1] ^ LOG_X[0]
    # PHYS_X[2] = LOG_X[2] ^ LOG_Y[0]
    # PHYS_Y[0] = LOG_Y[0]
    # PHYS_Y[1] = LOG_Y[1] ^ LOG_X[1]

    # 테스트 1: LOG_X=0, LOG_Y=0 -> PHYS_X=0, PHYS_Y=0
    px, py = engine.translate_address(0, 0)
    assert px == 0
    assert py == 0

    # 테스트 2: LOG_X=3 (0b011: X0=1, X1=1, X2=0), LOG_Y=1 (0b001: Y0=1, Y1=0)
    # PHYS_X[0] = 1
    # PHYS_X[1] = 1 ^ 1 = 0
    # PHYS_X[2] = 0 ^ 1 = 1  -> PHYS_X = 1*4 + 0*2 + 1*1 = 5 (0b101)
    # PHYS_Y[0] = 1
    # PHYS_Y[1] = 0 ^ 1 = 1  -> PHYS_Y = 1*2 + 1*1 = 3 (0b011)
    px, py = engine.translate_address(log_x=3, log_y=1)
    assert px == 5
    assert py == 3


def test_dq_inversion() -> None:
    sample_path = FIXTURES_DIR / "sample_scramble.scram"
    content = sample_path.read_text(encoding="utf-8")

    engine = PrescrambleEngine()
    engine.parse_equations(content)

    # PHYS_DQ_INV[0] = LOG_X[0] ^ LOG_Y[0]
    # X0=1, Y0=0 -> Invert=True
    assert engine.is_dq_inverted(dq_pin_idx=0, log_x=1, log_y=0) is True
    # X0=1, Y0=1 -> Invert=False (1^1=0)
    assert engine.is_dq_inverted(dq_pin_idx=0, log_x=1, log_y=1) is False


def test_semicolon_and_star_comments_in_scramble() -> None:
    content = """
    ; This is a header comment with semicolon
    * This is a comment with asterisk at column 0
    PHYS_X[0] = LOG_X[0] ; inline semicolon comment
    PHYS_X[1] = LOG_X[1] ^ LOG_X[0] ; another comment
    """
    engine = PrescrambleEngine()
    engine.parse_equations(content)

    assert 0 in engine.x_equations
    assert 1 in engine.x_equations
    px, _ = engine.translate_address(log_x=1, log_y=0)
    assert px == 3  # X0=1, X1=1^0=1 (0b11=3)
