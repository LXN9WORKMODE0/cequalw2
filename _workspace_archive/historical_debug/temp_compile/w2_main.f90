!***********************************************************************************************************************************
!**                                        CE-QUAL-W2 Console Entry Point v4.5.5                                            **
!**                                                              **
!**  Console-only entry point for running CE-QUAL-W2 without Windows GUI                                    **
!***********************************************************************************************************************************

PROGRAM W2_MAIN

  ! Use required modules
  USE IFPORT
  USE MAIN
  USE GLOBAL;     USE NAMESC; USE GEOMC;  USE LOGICC; USE PREC;  USE SURFHE;  USE KINETIC; USE SHADEC; USE EDDY
  USE STRUCTURES; USE TRANS;  USE TVDC;   USE SELWC;  USE GDAYC; USE SCREENC; USE TDGAS;   USE RSTART
  USE INITIALVELOCITY; USE BUILDVERSION; USE MetFileRegion

  IMPLICIT NONE

  ! Local copies of variables normally in MSCLIB (Windows GUI module)
  ! We define them locally to bypass GUI dependency
  LOGICAL :: STOP_PUSHED_LOCAL = .FALSE.
  LOGICAL :: RESTART_PUSHED_LOCAL = .FALSE.
  LOGICAL :: RESTARTED_LOCAL = .FALSE.

  INTEGER(4) :: LENGTH, ISTATUS
  CHARACTER(255) :: DIRC
  CHARACTER(8)  :: CHAR8
  CHARACTER(30) :: CHAR30
  CHARACTER(1000) :: TEXT1
  CHARACTER(72) :: TEXTMSG
  INTEGER       :: RESULT, IOPENFISH
  LOGICAL       :: CSVFORMAT, RSO_EXISTS
  REAL          :: DEPTH
  INTEGER       :: IIDX

  ! Console banner
  WRITE(*,'(A)') '========================================'
  WRITE(*,'(A)') 'CE-QUAL-W2 v4.5.5 - Console Edition'
  WRITE(*,'(A)') 'Hydrodynamic + Temperature Simulation'
  WRITE(*,'(A)') '========================================'
  WRITE(*,*)

  ! Initialize control flags (use local copies to avoid MSCLIB dependency)
  END_RUN    = .FALSE.
  ERROR_OPEN  = .FALSE.
  WARNING_OPEN = .FALSE.
  STOP_PUSHED_LOCAL = .FALSE.
  RESTART_PUSHED_LOCAL = .FALSE.

!***********************************************************************************************************************************
!**                                                       Task 1: Inputs                                                          **
!***********************************************************************************************************************************

  ! Get command line argument for working directory
  CALL GET_COMMAND_ARGUMENT(1,DIRC,LENGTH,ISTATUS)
  DIRC = TRIM(DIRC)

  IF(LENGTH /= 0) THEN
    ISTATUS = CHDIR(DIRC)
    SELECT CASE(ISTATUS)
      CASE(2)  ! ENOENT
        WRITE(*,*) 'ERROR: The directory does not exist: ', TRIM(DIRC)
        STOP
      CASE(20)   ! ENOTDIR
        WRITE(*,*) 'ERROR: This is not a directory: ', TRIM(DIRC)
        STOP
      CASE(0)    ! NO ERROR
        WRITE(*,'(A,A)') 'Working directory: ', TRIM(DIRC)
    END SELECT
  END IF

  ! Get current directory
  MODDIR = FILE$CURDRIVE
  LENGTH = GETDRIVEDIRQQ(MODDIR)

  ! Write compiler version file
  OPEN(CON, FILE='W2CodeCompilerVersion.opt', STATUS='UNKNOWN')
  WRITE(CON,'(A,F5.2)') ' CE-QUAL-W2 Version #:', W2VER
  WRITE(CON,*) 'Compiler Version and Code Compile Date'
  WRITE(CON,*) 'INTEL_COMPILER_VERSION:', INTEL_COMPILER_VERSION
  WRITE(CON,*) 'INTEL_COMPILER_BUILD_DATE:', INTEL_COMPILER_BUILD_DATE
  WRITE(CON,*) 'CE-QUAL-W2 Version compile date:', BUILDTIME
  CLOSE(CON)

  ! Read control file
  INQUIRE(FILE='w2_con.npt', EXIST=CSVFORMAT)
  IF(CSVFORMAT) THEN
    CONFN = 'w2_con.npt'
  ELSE
    CONFN = 'w2_con.csv'
  END IF

  OPEN (CON, FILE=CONFN, STATUS='OLD', IOSTAT=RESULT)
  IF (RESULT /= 0) THEN
    WRITE(*,'(A)') 'ERROR: Could not open w2_con.npt or w2_con.csv'
    STOP
  END IF

  WRITE(*,'(A,A)') 'Control file: ', TRIM(CONFN)
  WRITE(*,'(A)') 'Reading input files...'

  ! Call INPUT subroutine (CON remains open)
  CALL INPUT

  IF(MET_REGIONS) CALL METREGIONSWB

  WRITE(*,'(A)') 'Input files read successfully.'

  ! Open Error File
  OPEN (W2ERR, FILE='w2.err', STATUS='UNKNOWN')

  ! Check for dynamic pipe adjustment file
  INQUIRE(FILE='w2_dynpipe_adjust.npt', EXIST=DYNPIPEADJUST)
  DYNPAD = 'OF'
  DYNPAD_PIPE = 1
  IF(DYNPIPEADJUST) THEN
    OPEN(CON, FILE='w2_dynpipe_adjust.npt', STATUS='OLD')
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    READ(CON,*)
    OPEN(DYNPIPELOG, FILE='dynpipe_adjustment_log.csv', STATUS='UNKNOWN')
    WRITE(DYNPIPELOG, '(A)') 'JDAY,BP(DYNPAD_PIPE),Z(DYNPAD_SEG),SZ(DYNPAD_SEG),DLT,(Z(DYNPAD_SEG)-SZ(DYNPAD_SEG))/DLT'
    CLOSE(CON)
  END IF

  ! Check for multiple waterbody file
  MWB_EXIST = .FALSE.
  INQUIRE(FILE='w2_multiple_WB.npt', EXIST=MWB_EXIST)
  IF(MWB_EXIST) THEN
    WRITE(*,'(A)') 'Multiple waterbody configuration detected.'
  END IF

!***********************************************************************************************************************************
!**                                                    Initialization                                                            **
!***********************************************************************************************************************************

  WRITE(*,'(A)') 'Initializing model...'

  CALL INIT

  ! Initial water level and velocity if needed
  IF(.NOT. RESTART_IN) THEN
    IF(INIT_VEL) THEN
      WRITE(*,'(A)') 'Computing initial velocities...'
      ALLOCATE (QSSI(IMX), LOOP_BRANCH(NBR), ELWSS(IMX), UAVG(IMX))
      ELWSS = ELWS
      B = BSAVE
      CALL INITGEOM
      CALL INITIAL_U_VELOCITY
      DEALLOCATE (QSSI, LOOP_BRANCH, ELWSS)
    END IF
  END IF

  ! Open warning file
  IF(.NOT. WARNING_OPEN) THEN
    OPEN (WRN, FILE='w2.wrn', STATUS='UNKNOWN')
  ELSE
    OPEN (WRN, FILE='w2.wrn', POSITION='APPEND')
    WRITE(WRN,*) '***RESTART*** APPENDING ON JDAY', JDAY
  END IF

  WRITE(*,'(A)') 'Model initialized successfully.'

  ! Initialize output
  CALL OUTPUTINIT

  IF(SELECTC == '      ON') CALL SELECTIVEINIT
  IF(SELECTC == '    USGS') CALL SELECTIVEINITUSGS
  IF(TDGTA) CALL InitTDGtarget
  IF(AERATEC == '      ON' .AND. OXYGEN_DEMAND) CALL AERATE

  WRITE(*,'(A,F0.2,A,F0.2)') 'Simulation period: ', TMSTRT, ' to ', TMEND
  WRITE(*,'(A)') 'Starting simulation...'
  WRITE(*,*)

!***********************************************************************************************************************************
!**                                                   Task 2: Main Loop                                                          **
!***********************************************************************************************************************************

  DO WHILE (.NOT. END_RUN .AND. .NOT. STOP_PUSHED_LOCAL)

    ! Read time-varying data
    IF (JDAY >= NXTVD) CALL READ_INPUT_DATA (NXTVD)
    CALL INTERPOLATE_INPUTS

    ! Time step setup
    DLTTVD = (NXTVD-JDAY)*DAY
    DLT    = MIN(DLT, DLTTVD+1.0)
    DLTS1  = DLT
    IF (DLT <= DLTTVD+0.999) THEN
      DLTS = DLT
    ELSE
      KLOC = 1
      ILOC = 1
    END IF

    ! Update wind for evaporation
    IF(MET_REGIONS) THEN
      DO JW=1,NMETFILEREGIONS
        DO IIDX=METREGSTART(JW), METREGEND(JW)
          WIND2(IIDX) = WIND(JW)*WSC(IIDX)*LOG(2.0D0/Z0(METREGWB(JW)))/LOG(WINDH(METREGWB(JW))/Z0(METREGWB(JW)))
        END DO
      END DO
    ELSE
      DO JW=1,NWB
        DO IIDX=CUS(BS(JW)), DS(BE(JW))
          WIND2(IIDX) = WIND(JW)*WSC(IIDX)*LOG(2.0D0/Z0(JW))/LOG(WINDH(JW)/Z0(JW))
        END DO
      END DO
    END IF

    ! Hydrodynamics
    CALL HYDROINOUT

    ! Temperature
    CALL TEMPERATURE

    ! NOTE: Water quality (wqconstituents) is intentionally NOT called
    ! Set CONSTITUENTS = .FALSE. in control file to disable

    ! Update state
    CALL UPDATE

    ! Output at specified intervals
    IF (JDAY >= NXTMTS .OR. JDAY >= TSRD(TSRDP+1) .OR. NIT == 1) THEN
      CALL OUTPUTA
    END IF

    ! Balances
    CALL BALANCES

    ! Layer add/subtract
    CALL LAYERADDSUB

    IF(ERROR_OPEN) THEN
      WRITE(*,'(A)') 'ERROR detected - stopping simulation'
      EXIT
    END IF

    ! Progress output every ~10% of simulation
    IF (JDAY >= TMSTRT + (TMEND-TMSTRT)*0.1) THEN
      IF (TMEND > TMSTRT) THEN
        WRITE(*,'(A,F0.1,A,F0.2,A,I0)') ' Progress: ', &
          (JDAY-TMSTRT)/(TMEND-TMSTRT)*100.0, '% | Day: ', JDAY, ' | Iter: ', NIT
      END IF
      TMSTRT = TMSTRT + (TMEND-TMSTRT)*0.1  ! Prevent repeated output
    END IF

  END DO

  WRITE(*,*)
  WRITE(*,'(A)') 'Simulation complete.'

!***********************************************************************************************************************************
!**                                                 Task 3: Finalization                                                        **
!***********************************************************************************************************************************

  IF(STOP_PUSHED_LOCAL) THEN
    WRITE(*,'(A)') 'Simulation stopped by user.'
    IF(RESTART_OUT) CALL RESTART_OUTPUT ('rso.opt')
  END IF

  IF(END_RUN .AND. RESTART_OUT) CALL RESTART_OUTPUT ('rso.opt')

  CALL ENDSIMULATION

  WRITE(*,'(A)') 'Cleanup complete.'
  WRITE(*,'(A)') '========================================'
  WRITE(*,'(A)') 'CE-QUAL-W2 finished successfully.'
  WRITE(*,'(A)') '========================================'

END PROGRAM W2_MAIN