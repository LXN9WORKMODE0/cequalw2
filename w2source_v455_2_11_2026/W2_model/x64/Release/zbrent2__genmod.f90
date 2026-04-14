        !COMPILER-GENERATED INTERFACE MODULE: Mon Mar 23 11:47:26 2026
        ! This source file is for reference only and may not completely
        ! represent the generated interface used by the compiler.
        MODULE ZBRENT2__genmod
          INTERFACE 
            RECURSIVE FUNCTION ZBRENT2(FUNC,BARG)
              REAL(KIND=8) :: FUNC
              EXTERNAL FUNC
              REAL(KIND=8) :: BARG
              REAL(KIND=8) :: ZBRENT2
            END FUNCTION ZBRENT2
          END INTERFACE 
        END MODULE ZBRENT2__genmod
