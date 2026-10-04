"""T5833 Pattern 및 Prescramble 공통 데이터 모델 (IR: Intermediate Representation)"""

from typing import List, Optional

from pydantic import BaseModel, Field


class VectorLine(BaseModel):
    """T5833 패턴의 개별 사이클 벡터 라인 표현 모델"""

    raw_line: str = Field(description="원본 소스 라인 텍스트")
    line_number: int = Field(description="소스 파일 내 라인 번호 (1-based)")
    label: Optional[str] = Field(default=None, description="분기용 라벨명 (예: START:)")
    ts: Optional[str] = Field(default=None, description="타이밍 세트 / Rate (예: TS1, RATE2)")
    instruction: Optional[str] = Field(default=None, description="ALPG 명령어 (예: NOP, INCX, LOOP(256))")
    pin_vectors: Optional[str] = Field(default=None, description="핀 상태 비트열 (예: 1 0 1 D 0 또는 101D0)")
    comment: Optional[str] = Field(default=None, description="주석 문자열 (! 뒤의 텍스트)")
    is_blank_or_comment_only: bool = Field(default=False, description="주석만 있거나 빈 줄 여부")

    def emit(self) -> str:
        """포맷팅된 T5833 패턴 라인으로 복원합니다."""
        if self.is_blank_or_comment_only or (self.ts is None and not self.pin_vectors):
            return self.raw_line

        label_part = f"{self.label}:".ljust(12) if self.label else " " * 12
        ts_part = (self.ts or "").ljust(6)
        inst_part = (self.instruction or "").ljust(20)
        vec_part = self.pin_vectors or ""
        comment_part = f" ; ! {self.comment}" if self.comment else " ;"
        return f"{label_part}{ts_part}{inst_part}{vec_part}{comment_part}"


class SDEFDefinition(BaseModel):
    """T5833 SDEF (Signal Definition) 모델"""

    sdef_name: str = Field(default="UNKNOWN_SDEF")
    signals: List[str] = Field(default_factory=list, description="정의된 시그널 목록")
    groups: dict[str, List[str]] = Field(default_factory=dict, description="핀 그룹 정의 (예: CMD_GRP, DATA_GRP)")
    way_assign: dict[str, int] = Field(default_factory=dict, description="시그널/그룹별 Way 할당 (1, 2, 4)")


class PatternProgram(BaseModel):
    """T5833 전체 패턴 프로그램 모델"""

    pattern_name: str = Field(default="UNKNOWN_PATTERN")
    sdef_file: Optional[str] = Field(default=None, description="참조하는 SDEF 파일 경로/이름")
    way_mode: int = Field(default=1, description="패턴 Way 모드 (1-way, 2-way, 4-way)")
    pin_list: List[str] = Field(default_factory=list, description="헤더에 정의된 핀 목록")
    vectors: List[VectorLine] = Field(default_factory=list, description="벡터 라인 목록")
