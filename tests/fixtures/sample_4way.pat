!===================================================================
! T5833 4-WAY INTERLEAVE BURST PATTERN WITH SDEF
!===================================================================
PATT_NAME: PAT_LPDDR4_BURST ;
SDEF_USE: "sample.sdef" ;
WAY_MODE: 4 ;
PIN_ASSIGN: CLK, CS_N, DQ0, DQ1 ;

START:
             TS1  NOP                   1010 0000 DDDD 0000 ; ! Write 4-burst
             TS2  NOP                   1010 1111 HHHH LLLL ; ! Read 4-burst
END_PAT:     TS1  STOP                  0000 1111 ZZZZ ZZZZ ;
