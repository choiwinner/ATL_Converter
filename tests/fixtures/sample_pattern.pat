!===================================================================
! T5833 GOLDEN SAMPLE PATTERN
!===================================================================
PATT_NAME: PAT_BURST_TEST ;
PIN_ASSIGN: CLK, CS_N, WE_N, DQ0, DQ1 ;

START:
             TS1  NOP                   1 1 1 Z Z ; ! Init Vector
             TS1  INCX                  1 0 0 D 0 ; ! Write 0
             TS2  NOP                   1 1 1 Z Z ; ! Wait 1 cycle
             TS1  INCX                  1 0 0 D 1 ; ! Write 1
END_PAT:     TS1  STOP                  0 1 1 Z Z ; ! Finish
