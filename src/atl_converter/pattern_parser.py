"""T5833 ALPG Pattern 및 SDEF 파서/수정 모듈"""

import re
from typing import List, Optional

from atl_converter.models import PatternProgram, SDEFDefinition, VectorLine


class SDEFParser:
    """T5833 SDEF (Signal Definition) 파서"""

    def __init__(self) -> None:
        self.sdef_name_regex = re.compile(r'SDEF\s+"([^"]+)"', re.IGNORECASE)
        self.group_regex = re.compile(r"([A-Za-z0-9_]+)\s*=\s*([^;]+);", re.IGNORECASE)

    def parse(self, content: str) -> SDEFDefinition:
        """SDEF 파일 내용을 파싱하여 SDEFDefinition 객체로 반환합니다."""
        sdef = SDEFDefinition()

        # 이름 추출
        name_match = self.sdef_name_regex.search(content)
        if name_match:
            sdef.sdef_name = name_match.group(1).strip()

        # GROUP 블록 파싱
        in_group_block = False
        for line in content.splitlines():
            clean_line = line.split("!")[0].split("//")[0].strip()
            if not clean_line:
                continue

            if "GROUP" in clean_line.upper() and "{" in clean_line:
                in_group_block = True
                continue
            if in_group_block and "}" in clean_line:
                in_group_block = False
                continue

            if in_group_block:
                grp_match = self.group_regex.search(clean_line)
                if grp_match:
                    grp_name = grp_match.group(1).strip()
                    pins_str = grp_match.group(2).strip()
                    pins = [p.strip() for p in pins_str.split(",") if p.strip()]
                    sdef.groups[grp_name] = pins

        return sdef


class PatternParser:
    """T5833 패턴 파일을 파싱하고 수정 및 코드 생성을 담당하는 클래스 (1-way, 2-way, 4-way 지원)"""

    def __init__(self) -> None:
        self.patt_name_regex = re.compile(r"PATT_NAME\s*:\s*([^;]+);", re.IGNORECASE)
        self.pin_assign_regex = re.compile(r"PIN_ASSIGN\s*:\s*([^;]+);", re.IGNORECASE)
        self.sdef_use_regex = re.compile(r'SDEF_USE\s*:\s*"?([^";]+)"?\s*;', re.IGNORECASE)
        self.way_mode_regex = re.compile(r"WAY(?:_MODE)?\s*:\s*(\d+)\s*;", re.IGNORECASE)

    def parse(self, content: str) -> PatternProgram:
        """패턴 소스 문자열을 파싱하여 PatternProgram 객체로 변환합니다."""
        lines = content.splitlines()
        prog = PatternProgram()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # 빈 줄 또는 전체 주석 라인 처리 (!, ;, * 로 시작하는 라인)
            if not stripped or stripped.startswith("!") or stripped.startswith(";") or stripped.startswith("*"):
                prog.vectors.append(
                    VectorLine(
                        raw_line=line,
                        line_number=idx,
                        is_blank_or_comment_only=True,
                    )
                )
                continue

            # 헤더 파싱: SDEF_USE
            sdef_match = self.sdef_use_regex.search(stripped)
            if sdef_match:
                prog.sdef_file = sdef_match.group(1).strip()
                prog.vectors.append(
                    VectorLine(
                        raw_line=line,
                        line_number=idx,
                        is_blank_or_comment_only=True,
                    )
                )
                continue

            # 헤더 파싱: WAY_MODE
            way_match = self.way_mode_regex.search(stripped)
            if way_match:
                prog.way_mode = int(way_match.group(1).strip())
                prog.vectors.append(
                    VectorLine(
                        raw_line=line,
                        line_number=idx,
                        is_blank_or_comment_only=True,
                    )
                )
                continue

            # 헤더 파싱: PATT_NAME
            patt_match = self.patt_name_regex.search(stripped)
            if patt_match:
                prog.pattern_name = patt_match.group(1).strip()
                prog.vectors.append(
                    VectorLine(
                        raw_line=line,
                        line_number=idx,
                        is_blank_or_comment_only=True,
                    )
                )
                continue

            # 헤더 파싱: PIN_ASSIGN
            pin_match = self.pin_assign_regex.search(stripped)
            if pin_match:
                pins = [p.strip() for p in pin_match.group(1).split(",") if p.strip()]
                prog.pin_list = pins
                prog.vectors.append(
                    VectorLine(
                        raw_line=line,
                        line_number=idx,
                        is_blank_or_comment_only=True,
                    )
                )
                continue

            # 벡터 라인 파싱
            parsed_vec = self._parse_vector_line(line, idx)
            prog.vectors.append(parsed_vec)

        # Way 모드가 명시되지 않은 경우 벡터 데이터를 통해 자동 감지
        if prog.way_mode == 1 and prog.pin_list:
            detected_way = self._detect_way_mode(prog)
            if detected_way > 1:
                prog.way_mode = detected_way

        return prog

    def _detect_way_mode(self, prog: PatternProgram) -> int:
        """벡터 라인의 토큰 길이를 기반으로 1-way, 2-way, 4-way를 추론합니다."""
        for vec in prog.vectors:
            if vec.is_blank_or_comment_only or not vec.pin_vectors:
                continue
            tokens = vec.pin_vectors.strip().split()
            if tokens:
                token_len = len(tokens[0])
                if token_len in (2, 4):
                    return token_len
        return 1

    def _parse_vector_line(self, line: str, line_number: int) -> VectorLine:
        """단일 벡터 라인을 파싱합니다."""
        # 주석 분리 (; ! 또는 ! 기준)
        comment = ""
        main_part = line
        if ";" in line:
            parts = line.split(";", 1)
            main_part = parts[0]
            comment_str = parts[1].strip()
            if comment_str.startswith("!"):
                comment = comment_str.lstrip("!").strip()
            else:
                comment = comment_str
        elif "!" in line:
            parts = line.split("!", 1)
            main_part = parts[0]
            comment = parts[1].strip()

        # 라벨 추출 (예: START:)
        tokens = main_part.strip().split()
        if not tokens:
            return VectorLine(
                raw_line=line,
                line_number=line_number,
                is_blank_or_comment_only=True,
            )

        label = None
        if tokens[0].endswith(":"):
            label = tokens[0][:-1]
            tokens = tokens[1:]

        # 라벨만 단독으로 있는 줄인 경우 원본 유지
        if not tokens:
            return VectorLine(
                raw_line=line,
                line_number=line_number,
                label=label,
                is_blank_or_comment_only=True,
            )

        # 나머지 토큰 분석 (최소 TS와 PIN 벡터 데이터가 존재해야 함)
        ts = None
        instruction = "NOP"
        pin_vectors = ""

        if tokens:
            ts = tokens[0]
            tokens = tokens[1:]

        if tokens:
            # 마지막 토큰(들)이 핀 벡터, 중간 토큰이 명령어인 경우 처리
            if len(tokens) >= 2:
                instruction = tokens[0]
                pin_vectors = " ".join(tokens[1:])
            else:
                pin_vectors = tokens[0]

        return VectorLine(
            raw_line=line,
            line_number=line_number,
            label=label,
            ts=ts,
            instruction=instruction,
            pin_vectors=pin_vectors,
            comment=comment if comment else None,
            is_blank_or_comment_only=False,
        )

    def modify_ts(
        self,
        program: PatternProgram,
        target_ts: str,
        new_ts: str,
        instruction_filter: Optional[str] = None,
    ) -> int:
        """조건에 일치하는 벡터의 TS를 일괄 치환하고 변경된 라인 수를 반환합니다."""
        count = 0
        for vec in program.vectors:
            if vec.is_blank_or_comment_only:
                continue
            if vec.ts == target_ts:
                if instruction_filter and vec.instruction != instruction_filter:
                    continue
                vec.ts = new_ts
                count += 1
        return count

    def remap_pins(
        self,
        program: PatternProgram,
        old_pins: List[str],
        new_pins: List[str],
    ) -> None:
        """신규 핀 배치 순서에 맞게 모든 벡터 라인의 핀 상태 열을 재정렬합니다 (1-way, 2-way, 4-way 완벽 지원)."""
        if len(old_pins) != len(new_pins):
            raise ValueError("기존 핀 목록과 신규 핀 목록의 개수가 일치하지 않습니다.")

        old_idx_map = {pin: idx for idx, pin in enumerate(old_pins)}

        for vec in program.vectors:
            if vec.is_blank_or_comment_only or not vec.pin_vectors:
                continue

            raw_vec = vec.pin_vectors.strip()
            tokens = raw_vec.split()

            # 공백 분리형 vs 컴팩트(연속)형 구분
            if len(tokens) == len(old_pins):
                # 공백으로 각 핀이 분리된 경우 (1-way, 2-way, 4-way 공통)
                new_tokens = [tokens[old_idx_map[p]] for p in new_pins]
                vec.pin_vectors = " ".join(new_tokens)
            elif len(tokens) == 1 and program.way_mode == 1 and len(raw_vec) == len(old_pins):
                # 1-way 컴팩트형 (예: "101D0")
                char_tokens = list(raw_vec)
                new_tokens = [char_tokens[old_idx_map[p]] for p in new_pins]
                vec.pin_vectors = "".join(new_tokens)
            elif len(tokens) == 1 and program.way_mode > 1 and len(raw_vec) == len(old_pins) * program.way_mode:
                # N-way 컴팩트형 (예: 2-way "1000DD")
                w = program.way_mode
                chunked = [raw_vec[i * w : (i + 1) * w] for i in range(len(old_pins))]
                new_tokens = [chunked[old_idx_map[p]] for p in new_pins]
                vec.pin_vectors = "".join(new_tokens)

    def sync_with_sdef(self, program: PatternProgram, sdef: SDEFDefinition, group_name: str) -> None:
        """SDEF에 선언된 특정 핀 그룹 순서에 맞추어 패턴의 PIN_ASSIGN 및 벡터 컬럼을 자동 동기화합니다."""
        if group_name not in sdef.groups:
            raise KeyError(f"SDEF 내에 '{group_name}' 그룹이 존재하지 않습니다.")

        target_pins = sdef.groups[group_name]
        if program.pin_list:
            self.remap_pins(program, old_pins=program.pin_list, new_pins=target_pins)
            program.pin_list = target_pins

    def emit(self, program: PatternProgram) -> str:
        """PatternProgram 객체를 T5833 패턴 소스 코드로 직렬화합니다."""
        output_lines: List[str] = []
        for vec in program.vectors:
            output_lines.append(vec.emit())
        return "\n".join(output_lines)
