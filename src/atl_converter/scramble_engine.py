"""T5833 Prescramble 파서 및 수식 계산/변환 엔진"""

import re
from typing import Dict, List, Tuple


class PrescrambleEngine:
    """T5833 Prescramble 수식을 파싱하고 논리-물리 어드레스 변환을 수행하는 엔진"""

    def __init__(self) -> None:
        # target_bit -> list of (axis, bit_index)
        self.x_equations: Dict[int, List[Tuple[str, int]]] = {}
        self.y_equations: Dict[int, List[Tuple[str, int]]] = {}
        self.dq_invert_conditions: Dict[int, List[Tuple[str, int]]] = {}

    def parse_equations(self, content: str) -> None:
        """Prescramble 수식 텍스트를 파싱하여 내부 규칙 사전에 등록합니다."""
        eq_regex = re.compile(r"PHYS_(X|Y|DQ_INV)\[(\d+)\]\s*=\s*(.*?)(?:;|$)", re.IGNORECASE)
        term_regex = re.compile(r"LOG_(X|Y)\[(\d+)\]", re.IGNORECASE)

        for line in content.splitlines():
            stripped = line.strip()
            # 전체 주석 라인 무시 (!, ;, * 로 시작)
            if not stripped or stripped.startswith("!") or stripped.startswith(";") or stripped.startswith("*"):
                continue

            # 인라인 주석 처리: 수식 뒤에 오는 ;, !, // 주석 분리
            clean_line = stripped.split(";")[0].split("!")[0].split("//")[0].strip()

            if not clean_line:
                continue


            match = eq_regex.match(clean_line)
            if not match:
                continue

            target_type, target_idx_str, rhs = match.groups()
            target_idx = int(target_idx_str)

            terms = term_regex.findall(rhs)
            parsed_terms = [(axis.upper(), int(bit_idx)) for axis, bit_idx in terms]

            target_type = target_type.upper()
            if target_type == "X":
                self.x_equations[target_idx] = parsed_terms
            elif target_type == "Y":
                self.y_equations[target_idx] = parsed_terms
            elif target_type == "DQ_INV":
                self.dq_invert_conditions[target_idx] = parsed_terms

    def translate_address(self, log_x: int, log_y: int) -> Tuple[int, int]:
        """논리적 X, Y 주소를 스크램블 수식에 따라 물리적 X, Y 주소로 변환합니다."""
        phys_x = 0
        for target_bit, terms in self.x_equations.items():
            bit_val = 0
            for axis, sbit in terms:
                source_val = ((log_x >> sbit) & 1) if axis == "X" else ((log_y >> sbit) & 1)
                bit_val ^= source_val
            phys_x |= bit_val << target_bit

        phys_y = 0
        for target_bit, terms in self.y_equations.items():
            bit_val = 0
            for axis, sbit in terms:
                source_val = ((log_x >> sbit) & 1) if axis == "X" else ((log_y >> sbit) & 1)
                bit_val ^= source_val
            phys_y |= bit_val << target_bit

        return phys_x, phys_y

    def is_dq_inverted(self, dq_pin_idx: int, log_x: int, log_y: int) -> bool:
        """특정 DQ 핀의 데이터가 주어진 논리 주소에서 반전(Invert)되는지 여부를 계산합니다."""
        if dq_pin_idx not in self.dq_invert_conditions:
            return False

        invert_val = 0
        for axis, sbit in self.dq_invert_conditions[dq_pin_idx]:
            source_val = ((log_x >> sbit) & 1) if axis == "X" else ((log_y >> sbit) & 1)
            invert_val ^= source_val

        return invert_val == 1
