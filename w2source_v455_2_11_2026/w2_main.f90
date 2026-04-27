! CE-QUAL-W2 computations v4.5.5
PROGRAM W2_MAIN
  USE IFPORT                 ! to get current working directory
  USE MAIN
  USE GLOBAL;     USE NAMESC; USE GEOMC;  USE LOGICC; USE PREC;  USE SURFHE;  USE KINETIC; USE SHADEC; USE EDDY
  USE STRUCTURES; USE TRANS;  USE TVDC;   USE SELWC;  USE GDAYC; USE SCREENC; USE TDGAS;   USE RSTART
  USE INITIALVELOCITY; USE BUILDVERSION; USE MetFileRegion
  ! MACROPHYTEC, POROSITYC, ZOOPLANKTONC removed - water quality related
  ! modSYSTDG removed - TDG related (fish protection)
  ! CEMAVars, CEMASedimentDiagenesis removed - sediment diagenesis
  ! ENVIRPMOD removed - environmental performance (fish related)
  ! BIOENERGETICS removed - fish bioenergetics
  ! HYPOAERATION removed - hypolimnetic aeration
  IMPLICIT NONE
 ! include "omp_lib.h"      ! OPENMP directive to adjust the # of processors TOGGLE FOR DEBUG

  EXTERNAL RESTART_OUTPUT
  INTEGER       :: RESULT         !, RESULT1, IRESULT   ! SW 2/2019
  INTEGER       :: HYDRO_ITER
  REAL          :: DEPTH
  REAL(R8)      :: HYDRO_MAX_DZ, HYDRO_MAX_DQ, TAIL_Z_UP, QINJB_ACTIVE, QDT_SUM_DIAG, QSS_SUM_DIAG, TAIL_Q_DIAG
  LOGICAL       :: CSVFORMAT
  ! logical :: PLUNGEPT=.true.
  CHARACTER(30) :: CHAR30
  CHARACTER(8)  :: CHAR8
  CHARACTER(256) :: STATUS_TEXT
  LOGICAL :: STOP_PUSHED_LOCAL, RESTART_PUSHED_LOCAL
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: QIN_INNER_PREV
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_WSE_UP_SAVE, TAIL_WSE_DN_SAVE, TAIL_Q_LINK_SAVE, TAIL_DEPTH_UP_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_STORAGE_VOL_SAVE, TAIL_Q_INFLOW_SAVE, TAIL_Q_OUTFLOW_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_Q_STATE_SAVE, TAIL_Q_TARGET_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_TRAVEL_TIME_SAVE, TAIL_WAVE_CELERITY_SAVE, TAIL_REACH_LENGTH_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_TRANSITION_STATE_SAVE, TAIL_SUBMERGENCE_SAVE, TAIL_LOCAL_SLOPE_SAVE, TAIL_FROUDE_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_WSE_UP_PRED, TAIL_Q_LINK_PRED, TAIL_DEPTH_UP_PRED
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_STAGE_SEG_SAVE, TAIL_DEPTH_SEG_SAVE, TAIL_AREA_SEG_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_HRAD_SEG_SAVE, TAIL_VOL_SEG_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_Q_SEG_SAVE, TAIL_Q_TARGET_SEG_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_TRAVEL_TIME_SEG_SAVE, TAIL_CELERITY_SEG_SAVE
  INTEGER,  ALLOCATABLE, DIMENSION(:) :: TAIL_STAGE_MODE_SAVE, TAIL_CONTROL_MODE_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_TRANSITION_SEG_SAVE, TAIL_SUBMERGENCE_SEG_SAVE, TAIL_LOCAL_SLOPE_SEG_SAVE, TAIL_FROUDE_SEG_SAVE
  INTEGER,  ALLOCATABLE, DIMENSION(:,:) :: TAIL_MODE_SEG_SAVE
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_STAGE_SEG_PRED, TAIL_DEPTH_SEG_PRED, TAIL_AREA_SEG_PRED
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_HRAD_SEG_PRED, TAIL_VOL_SEG_PRED
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_Q_SEG_PRED, TAIL_Q_TARGET_SEG_PRED
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_TRAVEL_TIME_SEG_PRED, TAIL_CELERITY_SEG_PRED
  REAL(R8), ALLOCATABLE, DIMENSION(:,:) :: TAIL_TRANSITION_SEG_PRED, TAIL_SUBMERGENCE_SEG_PRED, TAIL_LOCAL_SLOPE_SEG_PRED, TAIL_FROUDE_SEG_PRED
  INTEGER,  ALLOCATABLE, DIMENSION(:,:) :: TAIL_MODE_SEG_PRED
  LOGICAL,  ALLOCATABLE, DIMENSION(:) :: TAIL_STAGE_VALID_SAVE, TAIL_REACH_INITIALIZED_SAVE, TAIL_Q_STATE_INITIALIZED_SAVE
  LOGICAL,  ALLOCATABLE, DIMENSION(:) :: TAIL_STAGE_VALID_PRED
  LOGICAL,  ALLOCATABLE, DIMENSION(:,:) :: TAIL_SEG_VALID_SAVE
  LOGICAL,  ALLOCATABLE, DIMENSION(:,:) :: TAIL_SEG_VALID_PRED
  REAL(R8), ALLOCATABLE, DIMENSION(:) :: TAIL_PREDICT_WSE_DN_CACHE, TAIL_PREDICT_QLINK_CACHE
  INTEGER,  ALLOCATABLE, DIMENSION(:) :: TAIL_PREDICT_SKIP_COUNT
  LOGICAL,  ALLOCATABLE, DIMENSION(:) :: TAIL_PREDICT_CACHE_VALID
  LOGICAL,  ALLOCATABLE, DIMENSION(:) :: TAIL_PREDICT_REUSED_STEP
  REAL(R8), PARAMETER :: TAIL_PREDICT_WSE_TOL = 0.02D0, TAIL_PREDICT_Q_TOL = 25.0D0
  INTEGER,  PARAMETER :: TAIL_PREDICT_MAX_SKIP = 20

!***********************************************************************************************************************************
!**                                                       Task 1: Inputs                                                          **
!***********************************************************************************************************************************

INTEGER(4) length,istatus
character*255 dirc
!  call omp_set_num_threads(4)   ! set # of processors to NPROC  Moved to INPUT subroutine

STATUS_TEXT = ''
STOP_PUSHED_LOCAL = .FALSE.
RESTART_PUSHED_LOCAL = .FALSE.

IF(END_RUN.or.ERROR_OPEN)STOP    ! SW 6/26/15 3/18/16 Added code to prevent a thread from reinitializing output files as dialog box is closing...intermittant error Updated 8/23/2017

CALL GET_COMMAND_ARGUMENT(1,DIRC,LENGTH,ISTATUS)  
DIRC=TRIM(DIRC)

! IF(ISTATUS.NE.0)WRITE(*,*)'GET_COMMAND_ARGUMENT FAILED: STATUS=',ISTATUS

IF(LENGTH /= 0)THEN
    ISTATUS=CHDIR(DIRC)
    SELECT CASE(ISTATUS)
      CASE(2)  ! ENOENT
        WRITE(W2ERR,*)'The directory does not exist:',DIRC
        WRITE(W2ERR,*)'Run stopped'
        ERROR_OPEN=.TRUE. 
      CASE(20)   ! ENOTDIR
        WRITE(W2ERR,*)'This is not a directory:', DIRC
        WRITE(W2ERR,*)'Run stopped'
        ERROR_OPEN=.TRUE. 
      CASE(0)    ! NO ERROR
    END SELECT  
ENDIF

MODDIR = FILE$CURDRIVE              !  GET CURRENT DIRECTORY
LENGTH = GETDRIVEDIRQQ(MODDIR)

OPEN(CON,FILE='W2CodeCompilerVersion.opt',status='unknown')
write(CON,'(A,F5.2)')' CE-QUAL-W2 Version #:',W2VER
write(CON,*)'Compiler Version and Code Compile Date'
write(CON,*)'INTEL_COMPILER_VERSION:',INTEL_COMPILER_VERSION
write(CON,*)'INTEL_COMPILER_BUILD_DATE:',INTEL_COMPILER_BUILD_DATE
write(CON,*)'CE-QUAL-W2 Version compile date:',BUILDTIME
close(CON)

! FISH/BIOENERGETICS module removed - 2026-03-31

  Call ReadMetRegions    ! See if Met data is organized by regions rather than waterbodies  SW 12/13/2023  
  
! Open control file
  OPEN (CON,FILE=CONFN,STATUS='OLD',IOSTAT=I)
  IF (I /= 0) THEN
    CLOSE(CON)
    STATUS_TEXT = 'Could not open w2_con.npt'
    CONFN='w2_con.csv'
    OPEN (CON,FILE=CONFN,STATUS='OLD',IOSTAT=I)
       IF (I /= 0) THEN
       STATUS_TEXT = 'Could not open w2_con.npt and w2_con.csv'
       GO TO 240
       ENDIF
       WRITE(*,'(A)') 'Found w2_con.csv'
  END IF

CALL INPUT
IF (ERROR_OPEN) THEN
  STATUS_TEXT = TRIM(TEXT)
  GO TO 240
END IF
IF(Met_Regions)CALL MetRegionsWB   !SW 12/13/2023

! Open Error File
  OPEN (W2ERR,FILE='w2.err',STATUS='UNKNOWN')

  ! DYN PIPE ADJUSTMENT CODE
   INQUIRE(FILE='w2_dynpipe_adjust.npt',EXIST=DYNPIPEADJUST)     ! SW 5/26/15
   DYNPAD='OF'  ! IT IS ONLY CHECKED IF IT IS ='ON' 2 CHARACTER VARIABLE
   DYNPAD_PIPE=1
  IF(DYNPIPEADJUST)THEN
  OPEN(CON,FILE='w2_dynpipe_adjust.npt',status='old')
    READ(CON,*) ! SKIP LINE
    READ(CON,*) ! SKIP LINE
    READ(CON,*)DYNPAD
    READ(CON,*)! SKIP LINE
    READ(CON,*)DYNPAD_PIPE
    READ(CON,*) ! SKIP LINE
    READ(CON,*)DYNPAD_SEG
    READ(CON,*) ! SKIP LINE
    READ(CON,*)DYNPAD_WL
    READ(CON,*) ! SKIP LINE
    READ(CON,*)DYNPAD_MAXRATE
    READ(CON,*) ! SKIP LINE
    READ(CON,*)DYNPAD_PERCENTCHANGE
    OPEN(DYNPIPELOG,FILE='dynpipe_adjustment_log.csv',status='unknown')
    WRITE(DYNPIPELOG,'(A)')'JDAY,BP(DYNPAD_PIPE),Z(DYNPAD_SEG),SZ(DYNPAD_SEG),DLT,(Z(DYNPAD_SEG)-SZ(DYNPAD_SEG))/DLT'
    CLOSE(CON)  
  ENDIF
  
  ! END DYN PIPE ADJUSTMENT CODE SW 2/18/2020
  
  
! Read multiple seperate waterbody file  2/9/2019 SW
WAIT_FOR_INFLOW_RESULTS=.FALSE.
MWB_EXIST= .FALSE.   ! USING OLD FILE NAME
INQUIRE(FILE='w2_multiple_WB.npt',EXIST=MWB_EXIST)     ! SW 5/26/15
IF(MWB_EXIST)THEN
OPEN(CON,FILE='w2_multiple_WB.npt',STATUS='OLD')
READ(CON,*)
READ(CON,*)DEG   ! USING OLD CHARACTER NAME
IF(DEG=='ON')THEN
!--------------
!new variables:
!--------------
!  N_WAITS    -- integer specifying the number of input file sets to await
!  NWAIT      -- integer counter index for do loops
!  WAIT_TYPE  -- character array holding the type of input file we're awaiting ('BR' or 'TR')
!  WAIT_INDEX -- integer array holding the branch or tributary index for a set of files we're awaiting
!  FILEDIR    -- character array to hold the directory names of the awaited files
    
    WAIT_FOR_INFLOW_RESULTS=.TRUE.
    READ (CON,*)                                                                                                        !SR 11/26/19
    READ (CON,*) N_WAITS                                                                                                !SR 11/26/19
    IF (N_WAITS.GT.0) THEN                                                                                              !SR 11/26/19
      ALLOCATE (WAIT_TYPE(MAX(1,N_WAITS)), WAIT_INDEX(MAX(1,N_WAITS)), FILEDIR(MAX(1,N_WAITS)))                         !SR 11/26/19
    ELSE                                                                                                                !SR 11/26/19
      WRITE (W2ERR,'(A)') 'ERROR-- Number of inputs to wait for must be greater than zero in multiple_WB.npt file.'             !SR 11/26/19
      STOP                                                                                                              !SR 11/26/19
    END IF                                                                                                              !SR 11/26/19
    READ (CON,*)                                                                                                        !SR 11/26/19
    DO NWAIT=1,N_WAITS                                                                                                  !SR 11/26/19
      READ (CON,*) WAIT_TYPE(NWAIT), WAIT_INDEX(NWAIT), FILEDIR(NWAIT)                                                  !SR 11/26/19
    END DO                                                                                                              !SR 11/26/19
    READ (CON,*)
    READ (CON,*) TIME_BUFFER
    IF (TIME_BUFFER < 0) THEN                                                                                           !SR 11/26/19
      WRITE (W2ERR,'(A)') 'ERROR-- Buffer time (days of data to await) in multiple_WB.npt cannot be less than zero.'            !SR 11/26/19
      STOP                                                                                                              !SR 11/26/19
    END IF                                                                                                              !SR 11/26/19
    READ (CON,*)
    READ (CON,*) WAIT_TIME
    IF (WAIT_TIME <= 0) THEN                                                                                            !SR 11/26/19
      WRITE (W2ERR,'(A)') 'ERROR-- Delay time in multiple_WB.npt must be greater than zero.'                                    !SR 11/26/19
      STOP                                                                                                              !SR 11/26/19
    END IF                                                                                                              !SR 11/26/19
    OPEN (9911,FILE='WaitForRunLog.opt',STATUS='unknown')         !moved: no need to create file if not used            !SR 11/26/19
  END IF
  CLOSE (CON)
END IF
!-----------------------------------------------------------------------------------------------------
!Setting up some variables so that the program knows which inputs to wait for... just before CALL INIT
!-----------------------------------------------------------------------------------------------------
  ! Set up some variables so that the program knows which inputs to wait for and where to find them                     !SR 11/26/19
  WAIT_FOR_TRIB_INPUT   = .FALSE.                                                                                       !SR 11/26/19
  WAIT_FOR_BRANCH_INPUT = .FALSE.                                                                                       !SR 11/26/19
  IF (WAIT_FOR_INFLOW_RESULTS) THEN
    DO NWAIT=1,N_WAITS                                                                                                  !SR 11/26/19
      IF (WAIT_TYPE(NWAIT) == 'BR') THEN                                   ! BR for branch input                        !SR 11/26/19
        WAIT_FOR_BRANCH_INPUT(WAIT_INDEX(NWAIT)) = .TRUE.                                                               !SR 11/26/19
        BR_FILEDIR(WAIT_INDEX(NWAIT))            = FILEDIR(NWAIT)                                                       !SR 11/26/19
      ELSEIF (WAIT_TYPE(NWAIT) == 'TR') THEN                               ! TR for tributary input                     !SR 11/26/19
        WAIT_FOR_TRIB_INPUT(WAIT_INDEX(NWAIT))   = .TRUE.                                                               !SR 11/26/19
        TR_FILEDIR(WAIT_INDEX(NWAIT))            = FILEDIR(NWAIT)                                                       !SR 11/26/19
      END IF                                                                                                            !SR 11/26/19
    END DO                                                                                                              !SR 11/26/19
  END IF


  RESTART_IN   =  RSIC == '      ON'.OR. RESTART_PUSHED_LOCAL
! Restart data
  IF (RESTART_PUSHED_LOCAL) RSIFN = 'rso.opt'
  JDAY = TMSTRT

  IF (RESTART_IN) THEN
    RSI=10   ! SW 5/26/15
    VERT_PROFILE = .FALSE.
    LONG_PROFILE = .FALSE.
    OPEN  (RSI,FILE=RSIFN,FORM='UNFORMATTED',STATUS='OLD')
    READ  (RSI) NIT,    NV,     KMIN,   IMIN,   NSPRF,  CMBRT,  ZMIN,   IZMIN,  START,  CURRENT
    READ  (RSI) DLTDP,  SNPDP,  TSRDP,  VPLDP,  PRFDP,  CPLDP,  SPRDP,  RSODP,  SCRDP,  FLXDP,  WDODP
    READ  (RSI) JDAY,   ELTM,   ELTMF,  DLT,    DLTAV,  DLTS,   MINDLT, JDMIN,  CURMAX
    READ  (RSI) NXTMSN, NXTMTS, NXTMPR, NXTMCP, NXTMVP, NXTMRS, NXTMSC, NXTMSP, NXTMFL, NXTMWD, NXWL, NXFLOWBAL, NXNPBAL,NXTMWD_SEC,NXTMUK
    READ  (RSI) VOLIN,  VOLOUT, VOLUH,  VOLDH,  VOLPR,  VOLTRB, VOLDT,  VOLWD,  VOLEV,  VOLSBR, VOLTR, VOLSR,VOLICE,ICEBANK
    READ  (RSI) TSSEV,  TSSPR,  TSSTR,  TSSDT,  TSSWD,  TSSIN,  TSSOUT, TSSS,   TSSB,   TSSICE
    READ  (RSI) TSSUH,  TSSDH,  TSSUH2, TSSDH2, CSSUH2, CSSDH2, VOLUH2, VOLDH2, QUH1
    READ  (RSI) ESBR,   ETBR,   EBRI
    READ  (RSI) Z,      SZ,     ELWS,   SAVH2,  SAVHR,  H2
    READ  (RSI) KTWB,   KTI,    SKTI,   SBKT
    READ  (RSI) ICE,    ICETH,  CUF,    QSUM
    READ  (RSI) U,      W,      SU,     SW,     AZ,     SAZ,    DLTLIM, SELWS
    READ  (RSI) T1,     T2,     C1,     C2,     C1S,    SED,    KFS,    CSSK
    READ  (RSI) EPD,    EPM
    ! MACROPHYTEC variables removed: MACMBRT,MACRC,MAC,MACRM,MACSS
#ifdef ZOOPLANKTONC
    READ  (RSI) SEDC, SEDN, SEDP, ZOO, CD  ! mlm 10/06
#else
    READ  (RSI) SEDC, SEDN, SEDP, CD  ! ZOO removed
#endif
    READ  (RSI) SDKV                       ! cb 11/30/06
    READ  (RSI) TKE                        ! sw 10/4/07
    READ  (RSI) BR_INACTIVE,WARNING_OPEN                ! SW 8/1/2018
#ifdef ENVIRPMOD
    if(envirpc == '      ON')THEN

      allocate(cc_e(NCT),c_int(NCT),c_top(NCT),cd_e(NDC),cd_int(NDC),cd_top(NDC),c_avg(NCT),cd_avg(NDC),cn_e(NCT),cdn_e(NDC))
      cc_e='   '
      c_int=0.0
      c_top=0.0
      cd_e='   '
      cd_int=0.0
      cd_top=0.0
      c_avg=0.0
      cd_avg=0.0
      cn_e=0.0
      cdn_e=0.0
      NAC_E=0
      NACD_E=0
      OPEN(1500,file='w2_envirprf.npt',status='old')

     CSVFORMAT=.FALSE.
     READ(1500,'(//A)')CHAR30
     DO J=1,30
         IF(CHAR30(J:J)==',')THEN
             CSVFORMAT=.TRUE.
             EXIT
         ENDIF
     ENDDO
     REWIND(1500)

      IF(CSVFORMAT)THEN
        READ(1500,*)
        READ(1500,*)
        READ (1500,*) I_SEGINT,numclass,selectivec,sjday1,sjday2,istart(1),iend(1),(istart(I),iend(I),I=2,I_SEGINT)
        SELECTIVEC=ADJUSTR(SELECTIVEC)
        IF(I_SEGINT==0)I_SEGINT=1
        READ(1500,*)
        READ(1500,*)
        Read (1500,*) VEL_VPR, VEL_INT, VEL_TOP,TEMP_VPR,TEMP_INT,TEMP_TOP, depth_vpr,d_int,d_top
        VEL_VPR=ADJUSTR(VEL_VPR);TEMP_VPR=ADJUSTR(TEMP_VPR);DEPTH_VPR=ADJUSTR(DEPTH_VPR)
        READ(1500,*)
        READ(1500,*)
        DO JC=1,NCT
        READ (1500,*) CHAR8, CC_E(JC), C_INT(JC), C_TOP(JC)
        CC_E(JC)=ADJUSTR(CC_E(JC))
        ENDDO
        READ(1500,*)
        READ(1500,*)
        DO JD=1,NDC
        READ (1500,*) CHAR8, CD_E(JD),CD_INT(JD), CD_TOP(JD)
        CD_E(JD)=ADJUSTR(CD_E(JD))
        ENDDO
      ELSE
      READ (1500,'(//I1,7X,I8,5x,a3,f8.0,f8.0,9(i8,i8))') I_SEGINT,numclass,selectivec,sjday1,sjday2,istart(1),iend(1),(istart(I),iend(I),I=2,I_SEGINT)
      IF(I_SEGINT==0)I_SEGINT=1
      Read (1500,'(//8x,3(5x,a3,f8.3,f8.3))') VEL_VPR, VEL_INT, VEL_TOP,TEMP_VPR,TEMP_INT,TEMP_TOP, depth_vpr,d_int,d_top
      READ (1500,'(//(8X,(5X,A3,F8.0,F8.0)))') (CC_E(JC), C_INT(JC), C_TOP(JC), JC=1,NCT)
      READ (1500,'(//(8X,(5X,A3,F8.0,F8.0)))') (CD_E(JD),CD_INT(JD), CD_TOP(JD), JD=1,NDC)
      ENDIF
      CLOSE(1500)

          DO JC=1,NCT
          IF (CC_E(JC).EQ.' ON') THEN
            NAC_E     = NAC_E+1
            CN_E(NAC_E) = JC
          END IF
          End DO
          DO JD=1,NDC
          IF (CD_E(JD).EQ.' ON') THEN
            NACD_E     = NACD_E+1
            CDN_E(NACD_E) = JD
          END IF
          End DO

    allocate (c_cnt(I_SEGINT,NCT),cd_cnt(I_SEGINT,NDC),c_class(I_SEGINT,NCT,numclass),cd_class(I_SEGINT,NDC,numclass),c_tot(I_SEGINT,NCT),cd_tot(I_SEGINT,NDC),t_class(I_SEGINT,numclass),v_class(I_SEGINT,numclass),c_sum(NCT),cd_sum(NDC))
    allocate (conc_c(NCT,numclass),conc_cd(NDC,numclass))
    allocate(d_class(I_SEGINT,numclass))
    ALLOCATE (D_TOT(I_SEGINT),D_CNT(I_SEGINT),T_TOT(I_SEGINT),T_CNT(I_SEGINT))
    ALLOCATE(V_TOT(I_SEGINT),V_CNT(I_SEGINT),VOLGL(I_SEGINT),SUMVOLT(I_SEGINT))

    READ(RSI)T_CLASS,V_CLASS,C_CLASS,CD_CLASS,T_TOT,T_CNT,SUMVOLT,V_CNT,V_TOT,C_TOT,C_CNT,CD_TOT,CD_CNT

    ENDIF
#endif
    IF(NPI > 0)READ(RSI)YS,VS,VST,YST,DTP,QOLD
    READ(RSI)TPOUT,TPTRIB,TPDTRIB,TPWD,TPPR,TPIN,TP_SEDSOD_PO4,PFLUXIN,TNOUT,TNTRIB,TNDTRIB,TNWD,TNPR,TNIN,TN_SEDSOD_NH4,NFLUXIN,ATMDEP_P,ATMDEP_N,NH3GASLOSS     ! TP_SEDBURIAL,TN_SEDBURIAL,

    CLOSE (RSI)
  END IF

  ! Open warning file

  IF(.NOT.WARNING_OPEN)THEN
      OPEN (WRN,FILE='w2.wrn',STATUS='UNKNOWN')
  ELSE
      OPEN (WRN,FILE='w2.wrn',POSITION='APPEND')
      WRITE(WRN,*)'***RESTART*** APPENDING ON JDAY',JDAY
  ENDIF
  IF (PKSD_INPUT_WARNING) THEN                               ! warning carried from INPUT routine                       !SR 11/09/19
    WRITE (WRN,'(A)') 'WARNING -- PKSD inputs in the ph_buffering.npt file must be greater than zero.'                  !SR 11/09/19
    WRITE (WRN,'(A/)') 'Please fix your inputs. For now, PKSD values of zero will be set to 1.'                         !SR 11/09/19
    PKSD_INPUT_WARNING = .FALSE.                                                                                        !SR 11/09/19
  END IF                                                                                                                !SR 11/09/19

  CALL INITIALIZE_TAIL_SEGMENT_STORAGE()
  
CALL INIT


! determining initial horizontal velocities and water levels
    once_through=.true.
    IF(inituwl == '      ON')init_vel=.true.    
    if(.not. restart_in)then       
      if(init_vel)then
        allocate (qssi(imx),loop_branch(nbr),elwss(imx),uavg(imx))
        elwss=elws
        call initial_water_level
        b=bsave
        call initgeom
        call initial_u_velocity       
        open(NUNIT,file='init_wl_u_check.dat',status='unknown')
        write(NUNIT,'("       i elws_calc    qssi       u   depth elws_init")')
        DO JW=1,NWB        
          DO JB=BS(JW),BE(JW)
            IU = CUS(JB)
            ID = DS(JB)
            do i=iu,id
              depth=(elws(i)-el(kbi(i)+1,i))/COSA(JB)    ! SR 1/2024
              write(NUNIT,'(i8,f8.3,f8.2,f8.3,2f8.2)')i,elws(i),qssi(i),u(kt,i),depth,elwss(i)
            end do
          end do
        end do
        close(NUNIT)
        deallocate (qssi,loop_branch,elwss)
      end if    
    end if

  IF (.NOT. RESTART_IN) THEN
    LINE    = CCTIME(1:2)//':'//CCTIME(3:4)//':'//CCTIME(5:6)
    WRITE(*,'(A,A)') 'Starting time: ', TRIM(LINE)
    WRITE(*,'(A)') 'Status: Executing'
    CURRENT = 0.0
  ELSE
    CALL CPU_TIME (CURRENT)
  END IF

  CALL OUTPUTINIT
    IF (RESTART_IN) THEN
    DO JW=1,NWB
      IF (SCREEN_OUTPUT(JW)) CONTINUE
    ENDDO
    ENDIF
  ALLOCATE(QIN_INNER_PREV(NBR))
  QIN_INNER_PREV = 0.0D0
  ALLOCATE(TAIL_WSE_UP_SAVE(NBR), TAIL_WSE_DN_SAVE(NBR), TAIL_Q_LINK_SAVE(NBR), TAIL_DEPTH_UP_SAVE(NBR))
  ALLOCATE(TAIL_STORAGE_VOL_SAVE(NBR), TAIL_Q_INFLOW_SAVE(NBR), TAIL_Q_OUTFLOW_SAVE(NBR))
  ALLOCATE(TAIL_Q_STATE_SAVE(NBR), TAIL_Q_TARGET_SAVE(NBR))
  ALLOCATE(TAIL_TRAVEL_TIME_SAVE(NBR), TAIL_WAVE_CELERITY_SAVE(NBR), TAIL_REACH_LENGTH_SAVE(NBR))
  ALLOCATE(TAIL_TRANSITION_STATE_SAVE(NBR), TAIL_SUBMERGENCE_SAVE(NBR), TAIL_LOCAL_SLOPE_SAVE(NBR), TAIL_FROUDE_SAVE(NBR))
  ALLOCATE(TAIL_WSE_UP_PRED(NBR), TAIL_Q_LINK_PRED(NBR), TAIL_DEPTH_UP_PRED(NBR))
  ALLOCATE(TAIL_STAGE_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_DEPTH_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_AREA_SEG_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_HRAD_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_VOL_SEG_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_Q_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_Q_TARGET_SEG_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_TRAVEL_TIME_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_CELERITY_SEG_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_STAGE_MODE_SAVE(NBR), TAIL_CONTROL_MODE_SAVE(NBR))
  ALLOCATE(TAIL_TRANSITION_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_SUBMERGENCE_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_LOCAL_SLOPE_SEG_SAVE(MAX_TAIL_SEG,NBR), TAIL_FROUDE_SEG_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_MODE_SEG_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_STAGE_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_DEPTH_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_AREA_SEG_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_HRAD_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_VOL_SEG_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_Q_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_Q_TARGET_SEG_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_TRAVEL_TIME_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_CELERITY_SEG_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_TRANSITION_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_SUBMERGENCE_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_LOCAL_SLOPE_SEG_PRED(MAX_TAIL_SEG,NBR), TAIL_FROUDE_SEG_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_MODE_SEG_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_STAGE_VALID_SAVE(NBR), TAIL_REACH_INITIALIZED_SAVE(NBR), TAIL_Q_STATE_INITIALIZED_SAVE(NBR))
  ALLOCATE(TAIL_STAGE_VALID_PRED(NBR))
  ALLOCATE(TAIL_SEG_VALID_SAVE(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_SEG_VALID_PRED(MAX_TAIL_SEG,NBR))
  ALLOCATE(TAIL_PREDICT_WSE_DN_CACHE(NBR), TAIL_PREDICT_QLINK_CACHE(NBR), TAIL_PREDICT_SKIP_COUNT(NBR), TAIL_PREDICT_CACHE_VALID(NBR), TAIL_PREDICT_REUSED_STEP(NBR))
  TAIL_WSE_UP_SAVE = 0.0D0; TAIL_WSE_DN_SAVE = 0.0D0; TAIL_Q_LINK_SAVE = 0.0D0; TAIL_DEPTH_UP_SAVE = 0.0D0
  TAIL_STORAGE_VOL_SAVE = 0.0D0; TAIL_Q_INFLOW_SAVE = 0.0D0; TAIL_Q_OUTFLOW_SAVE = 0.0D0
  TAIL_Q_STATE_SAVE = 0.0D0; TAIL_Q_TARGET_SAVE = 0.0D0
  TAIL_TRAVEL_TIME_SAVE = 0.0D0; TAIL_WAVE_CELERITY_SAVE = 0.0D0; TAIL_REACH_LENGTH_SAVE = 0.0D0
  TAIL_TRANSITION_STATE_SAVE = 0.0D0; TAIL_SUBMERGENCE_SAVE = 0.0D0; TAIL_LOCAL_SLOPE_SAVE = 0.0D0; TAIL_FROUDE_SAVE = 0.0D0
  TAIL_WSE_UP_PRED = 0.0D0; TAIL_Q_LINK_PRED = 0.0D0; TAIL_DEPTH_UP_PRED = 0.0D0
  TAIL_STAGE_SEG_SAVE = 0.0D0; TAIL_DEPTH_SEG_SAVE = 0.0D0; TAIL_AREA_SEG_SAVE = 0.0D0
  TAIL_HRAD_SEG_SAVE = 0.0D0; TAIL_VOL_SEG_SAVE = 0.0D0
  TAIL_Q_SEG_SAVE = 0.0D0; TAIL_Q_TARGET_SEG_SAVE = 0.0D0
  TAIL_TRAVEL_TIME_SEG_SAVE = 0.0D0; TAIL_CELERITY_SEG_SAVE = 0.0D0
  TAIL_TRANSITION_SEG_SAVE = 0.0D0; TAIL_SUBMERGENCE_SEG_SAVE = 0.0D0; TAIL_LOCAL_SLOPE_SEG_SAVE = 0.0D0; TAIL_FROUDE_SEG_SAVE = 0.0D0
  TAIL_MODE_SEG_SAVE = 0
  TAIL_STAGE_SEG_PRED = 0.0D0; TAIL_DEPTH_SEG_PRED = 0.0D0; TAIL_AREA_SEG_PRED = 0.0D0
  TAIL_HRAD_SEG_PRED = 0.0D0; TAIL_VOL_SEG_PRED = 0.0D0
  TAIL_Q_SEG_PRED = 0.0D0; TAIL_Q_TARGET_SEG_PRED = 0.0D0
  TAIL_TRAVEL_TIME_SEG_PRED = 0.0D0; TAIL_CELERITY_SEG_PRED = 0.0D0
  TAIL_TRANSITION_SEG_PRED = 0.0D0; TAIL_SUBMERGENCE_SEG_PRED = 0.0D0; TAIL_LOCAL_SLOPE_SEG_PRED = 0.0D0; TAIL_FROUDE_SEG_PRED = 0.0D0
  TAIL_MODE_SEG_PRED = 0
  TAIL_STAGE_MODE_SAVE = 0; TAIL_CONTROL_MODE_SAVE = 0
  TAIL_STAGE_VALID_SAVE = .FALSE.; TAIL_REACH_INITIALIZED_SAVE = .FALSE.; TAIL_Q_STATE_INITIALIZED_SAVE = .FALSE.
  TAIL_STAGE_VALID_PRED = .FALSE.
  TAIL_SEG_VALID_SAVE = .FALSE.
  TAIL_SEG_VALID_PRED = .FALSE.
  TAIL_PREDICT_WSE_DN_CACHE = 0.0D0
  TAIL_PREDICT_QLINK_CACHE = 0.0D0
  TAIL_PREDICT_SKIP_COUNT = 0
  TAIL_PREDICT_CACHE_VALID = .FALSE.
  TAIL_PREDICT_REUSED_STEP = .FALSE.

  IF (.NOT. RESTART_IN) CALL CPU_TIME (START)

! macrophyte_on removed - MACROPHYTEC module deleted
! if (macrophyte_on.and.constituents) call porosity
  IF(SELECTC == '      ON')CALL SELECTIVEINIT   ! new subroutine for selecting water temperature target
  IF(SELECTC == '    USGS')CALL SELECTIVEINITUSGS   ! new subroutine for selecting water temperature target
  ! Reduced build accepts AERATEC in input but does not execute aeration logic.

!***********************************************************************************************************************************
!**                                                   Task 2: Calculations                                                        **
!***********************************************************************************************************************************
  DO WHILE (.NOT. END_RUN.AND. .NOT. STOP_PUSHED_LOCAL)    
    IF (JDAY >= NXTVD) CALL READ_INPUT_DATA (NXTVD)
    CALL INTERPOLATE_INPUTS
    DLTTVD = (NXTVD-JDAY)*DAY
    DLT    =  MIN(DLT,DLTTVD+1.0)
    DLTS1  =  DLT
    IF (DLT <= DLTTVD+0.999) THEN
      DLTS = DLT
    ELSE
      KLOC = 1
      ILOC = 1
    END IF

    ! update wind at 2m for evaopration and evaoprative heat flux computations  ! SW 5/21/15

       If(Met_Regions)then   ! SW 12/13/2023
           DO JW=1,NMetFileRegions
                DO I=MetRegStart(JW),MetRegEnd(JW)
                    WIND2(I) = WIND(JW)*WSC(I)*DLOG(2.0D0/Z0(MetRegWB(JW)))/DLOG(WINDH(MetRegWB(JW))/Z0(MetRegWB(JW)))    
                END DO
           ENDDO
           
       else
              DO JW=1,NWB
                 DO I=CUS(BS(JW)),DS(BE(JW))
                  WIND2(I) = WIND(JW)*WSC(I)*DLOG(2.0D0/Z0(JW))/DLOG(WINDH(JW)/Z0(JW))    
                 END DO
              ENDDO
              
       endif
 
210 continue   ! timestep violation entry point
 IF(SELECTC == '      ON')CALL SELECTIVE   ! subroutine for selecting water temperature target
 IF(SELECTC == '    USGS')CALL SELECTIVEUSGS   ! subroutine for selecting water temperature target
CALL HYDROINOUT
CALL SAVE_TAIL_DYNAMIC_STATE()
CALL RUN_TAIL_PREDICTOR()

!***********************************************************************************************************************************
!**                                           Task 2.2: Hydrodynamic calculations                                                 **
!***********************************************************************************************************************************
!!$OMP PARALLEL DO default(Private)   !(KT,IU,ID,IUT,IDT,K,I,JB,ZB,WWT,DFC,JJB,BETABR,GC2,HRAD,UDR,UDL,AB)
    DO JW=1,NWB
      KT = KTWB(JW)
      DO JB=BS(JW),BE(JW)
        IF(BR_INACTIVE(JB))CYCLE    ! SW 6/12/17
            IU = MAX(CUS(JB), TAIL_COUPLE_SEG(JB))
            ID = DS(JB)

!***********************************************************************************************************************************
!**                                Task 2.2.1: Boundary concentrations, temperatures, and densities                               **
!***********************************************************************************************************************************

        IUT = IU
        IDT = ID
        IF (UP_FLOW(JB)) THEN
          IF (.NOT. INTERNAL_FLOW(JB)) THEN
            DO K=KT,KB(IU)
                IF (QIND(JB)+QINSUM(JB).GT.0.0) THEN
                  TIN(JB)               = (TINSUM(JB)               *QINSUM(JB)+TIND(JB)          *QIND(JB))/(QIND(JB)+QINSUM(JB))
                  CIN(CN(1:NAC),JB)     =  MAX((CINSUM(CN(1:NAC),JB)*QINSUM(JB)+CIND(CN(1:NAC),JB)*QIND(JB))/(QIND(JB)+QINSUM(JB)),&
                                                0.0)
                  T1(K,IU-1)            =  TIN(JB)
                  T2(K,IU-1)            =  TIN(JB)
                  C1S(K,IU-1,CN(1:NAC)) =  CIN(CN(1:NAC),JB)
                  QIN(JB)               =  QIND(JB)+QINSUM(JB)
                ELSE
                  QIN(JB)               =  0.0
                  TIN(JB)               =  TIND(JB)
                  T1(K,IU-1)            =  TIND(JB)
                  T2(K,IU-1)            =  TIND(JB)
                  C1S(K,IU-1,CN(1:NAC)) =  CIND(CN(1:NAC),JB)
                END IF
            END DO
          ELSE IF (.NOT. DAM_INFLOW(JB)) THEN                                                                          !TC 08/03/04
            IF (JBUH(JB) >= BS(JW) .AND. JBUH(JB) <= BE(JW)) THEN
              TIN(JB)           = T1(KT,UHS(JB))
              CIN(CN(1:NAC),JB) = MAX(C1S(KT,UHS(JB),CN(1:NAC)),0.0)
              DO K=KT,KB(IU)    !CONCURRENT(K=KT:KB(IU))             !DO K=KT,KB(IU)
                T1(K,IU-1)            = T1(K,UHS(JB))
                T2(K,IU-1)            = T1(K,UHS(JB))
                C1S(K,IU-1,CN(1:NAC)) = C1S(K,UHS(JB),CN(1:NAC))
                C1(K,IU-1,CN(1:NAC))  = C1S(K,UHS(JB),CN(1:NAC))
                C2(K,IU-1,CN(1:NAC))  = C1S(K,UHS(JB),CN(1:NAC))
              END DO                      
            ELSE
              CALL UPSTREAM_WATERBODY
              TIN(JB)           = T1(KT,IU-1)
              CIN(CN(1:NAC),JB) = MAX(C1(KT,IU-1,CN(1:NAC)),0.0)
            END IF
          ELSE
            TIN(JB)           = TINSUM(JB)
            QIN(JB)           = QINSUM(JB)
            CIN(CN(1:NAC),JB) = MAX(CINSUM(CN(1:NAC),JB),0.0)
            DO K=KT,KB(ID)
              T1(K,IU-1)            = TIN(JB)
              T2(K,IU-1)            = TIN(JB)
              C1S(K,IU-1,CN(1:NAC)) = CIN(CN(1:NAC),JB)
            END DO
           END IF
        END IF
        IF (DN_FLOW(JB)) THEN
          DO K=KT,KB(ID)
              T1(K,ID+1)            = T2(K,ID)
              T2(K,ID+1)            = T2(K,ID)
              C1S(K,ID+1,CN(1:NAC)) = C1S(K,ID,CN(1:NAC))
          END DO
        END IF
        IF (UP_HEAD(JB)) THEN
          IUT = IU-1
          IF (UH_INTERNAL(JB)) THEN
            IF (JBUH(JB) >= BS(JW) .AND. JBUH(JB) <= BE(JW)) THEN
              DO K=KT,KB(IUT)
                RHO(K,IUT)           = RHO(K,UHS(JB))
                T1(K,IUT)            = T2(K,UHS(JB))
                T2(K,IUT)            = T2(K,UHS(JB))
                C1S(K,IUT,CN(1:NAC)) = C1S(K,UHS(JB),CN(1:NAC))
                C1(K,IUT,CN(1:NAC))  = C1S(K,UHS(JB),CN(1:NAC))
                C2(K,IUT,CN(1:NAC))  = C1S(K,UHS(JB),CN(1:NAC))
              END DO
            ELSE
              CALL UPSTREAM_WATERBODY
            END IF
            DO K=KT,KB(IUT)
              RHO(K,IUT) = DENSITY(T2(K,IUT),DMAX1(TDS(K,IUT),0.0D0),DMAX1(TISS(K,IUT),0.0D0))
            END DO
          ELSE IF (UH_EXTERNAL(JB)) THEN
            DO K=KT,KB(IUT)
              RHO(K,IUT)           = DENSITY(TUH(K,JB),DMAX1(TDS(K,IUT),0.0D0),DMAX1(TISS(K,IUT),0.0D0))
              T1(K,IUT)            = TUH(K,JB)
              T2(K,IUT)            = TUH(K,JB)
              C1S(K,IUT,CN(1:NAC)) = CUH(K,CN(1:NAC),JB)
              C1(K,IUT,CN(1:NAC))  = CUH(K,CN(1:NAC),JB)
              C2(K,IUT,CN(1:NAC))  = CUH(K,CN(1:NAC),JB)
            END DO
          END IF
        END IF
        IF (DN_HEAD(JB)) THEN
          IDT = ID+1
          IF (DH_INTERNAL(JB)) THEN
            IF (JBDH(JB) >= BS(JW) .AND. JBDH(JB) <= BE(JW)) THEN
             DO K=KT,KB(IDT)
                RHO(K,IDT)           = RHO(K,DHS(JB))
                T1(K,IDT)            = T2(K,DHS(JB))
                T2(K,IDT)            = T2(K,DHS(JB))
                C1S(K,IDT,CN(1:NAC)) = C1S(K,DHS(JB),CN(1:NAC))
                C1(K,IDT,CN(1:NAC))  = C1S(K,DHS(JB),CN(1:NAC))
                C2(K,IDT,CN(1:NAC))  = C1S(K,DHS(JB),CN(1:NAC))
              END DO
            ELSE
              CALL DOWNSTREAM_WATERBODY
            END IF
            DO K=KT,KB(ID)
              RHO(K,IDT) = DENSITY(T2(K,IDT),DMAX1(TDS(K,IDT),0.0D0),DMAX1(TISS(K,IDT),0.0D0))
            END DO
          ELSE IF (DH_EXTERNAL(JB)) THEN
            DO K=KT,KB(IDT)
              RHO(K,IDT)           = DENSITY(TDH(K,JB),DMAX1(TDS(K,IDT),0.0D0),DMAX1(TISS(K,IDT),0.0D0))
              T1(K,IDT)            = TDH(K,JB)
              T2(K,IDT)            = TDH(K,JB)
              C1S(K,IDT,CN(1:NAC)) = CDH(K,CN(1:NAC),JB)
              C1(K,IDT,CN(1:NAC))  = CDH(K,CN(1:NAC),JB)
              C2(K,IDT,CN(1:NAC))  = CDH(K,CN(1:NAC),JB)
            END DO
          END IF
        END IF

!***********************************************************************************************************************************
!**                                                 Task 2.2.2: Momentum terms                                                    **
!***********************************************************************************************************************************

!****** Density pressures

        DO I=IUT,IDT
          DO K=KT,KB(I)
            P(K,I) = P(K-1,I)+RHO(K,I)*G*H(K,JW)*COSA(JB)
          END DO
        END DO

!****** Horizontal density gradients

        DO I=IUT,IDT-1
          HDG(KT,I) = DLXRHO(I)*(BKT(I)+BKT(I+1))*0.5D0*H(KT,JW)*(P(KT,I+1)-P(KT,I))
          DO K=KT+1,KBMIN(I)
            HDG(K,I) = DLXRHO(I)*BHR2(K,I)*((P(K-1,I+1)-P(K-1,I))+(P(K,I+1)-P(K,I)))
          END DO
        END DO

!****** Adjusted wind speed and surface wind shear drag coefficient      
        
        DO I=IU-1,ID+1
            
          If(Met_Regions)then   ! SW 12/13/2023
          WIND10(I) = WIND(I_MetRegions(I))*WSC(I)*DLOG(10.0D0/Z0(JW))/DLOG(WINDH(JW)/Z0(JW))     ! older  version z0=0.01                      ! SW 11/28/07
          else
          WIND10(I) = WIND(JW)*WSC(I)*DLOG(10.0D0/Z0(JW))/DLOG(WINDH(JW)/Z0(JW))     ! older  version z0=0.01   
          endif
          FETCH(I)  = FETCHD(I,JB)
          IF (COS(PHI(JW)-PHI0(I)) < 0.0) FETCH(I) = FETCHU(I,JB)
          IF (FETCH(I) <= 0.0) FETCH(I) = DLX(I)
          IF (FETCH_CALC(JW)) THEN
            ZB        = 0.8D0*DLOG(FETCH(I)*0.5D0)-1.0718D0
            WIND10(I) = WIND10(I)*(5.0D0*ZB+4.6052D0)/(3.0D0*ZB+9.2103D0)
          END IF
          
          IF(WIND10(I) >= 15.0)THEN                     ! SW 1/19/2008
          CZ(I) = 0.0026D0
          ELSEIF(WIND10(I) >= 4.0)THEN
          CZ(I) = 0.0005D0*DSQRT(WIND10(I)) 
          ELSEIF(WIND10(I) >= 0.5)THEN
          CZ(I)= 0.0044D0*WIND10(I)**(-1.15D0)
          ELSE
          CZ(I)= 0.01D0
          ENDIF
          
  !        CZ(I) = 0.0
  !        IF (WIND10(I) >= 1.0)  CZ(I) = 0.0005*SQRT(WIND10(I))
  !        IF (WIND10(I) >= 4.0) CZ(I) = 0.0005*SQRT(WIND10(I))          
  !        IF (WIND10(I) >= 15.0) CZ(I) = 0.0026
        END DO

!****** Longitudinal and lateral surface wind shear and exponential decay

        DO I=IUT,IDT-1
          If(Met_Regions)then   ! SW 12/13/2023
          WSHX(I) = CZ(I)*WIND10(I)*WIND10(I)*RHOA/RHOW*DCOS(PHI(I_MetRegions(I))-PHI0(I))* ICESW(I)    ! SW 4/20/16 SPEED
          WSHY(I) = CZ(I)*WIND10(I)*WIND10(I)*RHOA/RHOW*DABS(DSIN(PHI(I_MetRegions(I))-PHI0(I)))*ICESW(I)
          else
          WSHX(I) = CZ(I)*WIND10(I)*WIND10(I)*RHOA/RHOW*DCOS(PHI(JW)-PHI0(I))* ICESW(I)    ! SW 4/20/16 SPEED
          WSHY(I) = CZ(I)*WIND10(I)*WIND10(I)*RHOA/RHOW*DABS(DSIN(PHI(JW)-PHI0(I)))*ICESW(I)
          endif
          WWT     = 0.0
          IF (WIND10(I) /= 0.0) WWT = 6.95D-2*(FETCH(I)**0.233D0)*WIND10(I)**0.534D0
          DFC = -8.0D0*PI*PI/(G*WWT*WWT+NONZERO)
          DO K=KT,KBMIN(I)
            DECAY(K,I) = DEXP(DMAX1(DFC*DEPTHB(K,I),-30.0D0))
          END DO

!******** Branch inflow lateral shear and friction

          DO JJB=1,NBR
            IF(BR_INACTIVE(JJB))CYCLE  ! SW 6/12/2017
            IF (I == UHS(JJB) .AND. .NOT. INTERNAL_FLOW(JJB)) THEN
              BETABR = (PHI0(I)-PHI0(US(JJB)))
              IF (JJB >= BS(JW) .AND. JJB <= BE(JW)) THEN
                DO K=KT,KBMIN(I)
                  IF (U(K,US(JJB)) < 0.0) THEN
                    UXBR(K,I) = UXBR(K,I)+ABS(U(K,US(JJB)))*DCOS(BETABR)     *VOLUH2(K,JJB)/(DLT*DLX(I))
                    UYBR(K,I) = UYBR(K,I)              +ABS(DSIN(BETABR))*ABS(VOLUH2(K,JJB))/DLT
                  END IF
                END DO
              ELSE
                CALL UPSTREAM_BRANCH
              END IF
            END IF
            IF (I == DHS(JJB)) THEN
              BETABR = (PHI0(I)-PHI0(DS(JJB)))
              IF (I == US(JB) .AND. UHS(JB) /= DS(JJB)) THEN
                IF (JJB >= BS(JW) .AND. JJB <= BE(JW)) THEN
                  DO K=KT,KBMIN(I)
                    IF (U(K,DS(JJB)) >= 0.0) THEN
                      UXBR(K,I) = UXBR(K,I)+U(K,DS(JJB))*   DCOS(BETABR) *VOLDH2(K,JJB)/(DLT*DLX(I))
                      UYBR(K,I) = UYBR(K,I)            +ABS(DSIN(BETABR))*VOLDH2(K,JJB)/DLT
                    END IF
                  END DO
                ELSE
                  CALL DOWNSTREAM_BRANCH
                END IF
              ELSE IF (I /= US(JB)) THEN
                IF (JJB >= BS(JW) .AND. JJB <= BE(JW)) THEN
                  DO K=KT,KBMIN(I)
                    IF (U(K,DS(JJB)) >= 0.0) THEN
                      UXBR(K,I) = UXBR(K,I)+U(K,DS(JJB))*   DCOS(BETABR) *VOLDH2(K,JJB)/(DLT*DLX(I))
                      UYBR(K,I) = UYBR(K,I)            +ABS(DSIN(BETABR))*VOLDH2(K,JJB)/DLT
                    END IF
                  END DO
                ELSE
                  CALL DOWNSTREAM_BRANCH
                END IF
              END IF
            END IF
          END DO
          DO K=KT,KBMIN(I)
            FRICBR(K,I) = (FI(JW)/8.0D0)*RHO(K,I)*(UYBR(K,I)/(DLX(I)*H2(K,I)))**2
          END DO
        END DO

!!****** Vertical eddy viscosities/diffusivities
!        FIRSTI(JW) = IUT
!		LASTI(JW) = IDT
        DO I=IUT,IDT-1
          CALL CALCULATE_AZ
          IF (KBMIN(I) <= KT+1 .AND. KB(I) > KBMIN(I)) THEN
            AZ(KBMIN(I),I) = AZMIN
            DZ(KBMIN(I),I) = DZMIN
          END IF
        END DO
        IF (AZC(JW) == '     TKE'.OR.AZC(JW) == '    TKE1') THEN
          AZT(:,IDT-1)  = AZ(:,IDT-1)
          DO I=IUT,IDT-2
            DO K=KT,KBMIN(I)
              AZT(K,I)  = 0.5*(AZ(K,I)+AZ(K,I+1))
            END DO
          AZ(KBMIN(I),I) = AZMIN              !SG 10/4/07 SW 10/4/07
          END DO
          AZ(KT:KMX-1,IUT:IDT-1)=AZT(KT:KMX-1,IUT:IDT-1)
        END IF
        DO JWR=1,NIW
        IF (WEIR_CALC) AZ(KTWR(JWR)-1:KBWR(JWR),IWR(1:NIW)) = 0.0
        END DO

!****** Average eddy diffusivities

        IF(AZC(JW) /= '     TKE'.AND.AZC(JW) /= '    TKE1')THEN
        DZ(KT:KB(IDT)-1,IDT) = DZT(KT:KB(IDT)-1,IDT-1)    ! DZT is only used for non-TKE algorithms
        ELSE
        DZ(KT:KB(IDT)-1,IDT) = DZ(KT:KB(IDT)-1,IDT-1)
        ENDIF
        DO I=IUT,IDT-1
          DO K=KT,KB(I)-1
            IF (K >= KBMIN(I)) THEN
              IF (KB(I-1) >= KB(I) .AND. I /= IUT) THEN
                DZ(K,I) = DZ(K,I-1)
              ELSE
                DZ(K,I) = DZMIN
              END IF
            ELSE
              IF(AZC(JW) /= '     TKE'.AND.AZC(JW) /= '    TKE1')THEN
                 IF(I == IUT)THEN                             ! SW 10/20/07
                    DZ(K,I)=DZT(K,I)
                 ELSE
                    DZ(K,I) = (DZT(K,I)+DZT(K,I-1))*0.5D0        ! SW 10/20/07  (DZT(K,I)+DZT(K+1,I))*0.5 ! FOR NON-TKE ALGORITHMS, AVERAGE DZ FROM EDGES TO CELL CENTERS
                 ENDIF
              ENDIF
            END IF
          END DO
        END DO

! Hypolimnetic aeration removed - HYPOAERATION module deleted

!****** Density inversions

        DO I=IUT,IDT
          DO K=KT,KB(I)-1
            DZQ(K,I) = MIN(1.0D-2,DZ(K,I))                                    !MIN(1.0E-4,DZ(K,I)) No reason to limit DZ in rivers/estuaries-used in ULTIMATE scheme
             IF (RHO(K,I) > RHO(K+1,I)) THEN
                 IF(DZMAX > 0.0)THEN
                     DZ(K,I) = DZMAX
                 ELSE
                     DZ(K,I) = DZ(K,I)*ABS(DZMAX)    !    CHANGE dzmax TO A MULTIPLIER IF ENETERED AS A NEGATIVE #
                 ENDIF
             ENDIF
          END DO
        END DO
        
    

!****** Wind, velocity, and bottom shear stresses @ top and bottom of cell

        SB(:,IUT:IDT-1) = 0.0
        DO I=IUT,IDT-1
          ST(KT,I) = WSHX(I)*BR(KTI(I),I)
          DO K=KT+1,KBMIN(I)
            ST(K,I) = WSHX(I)*DECAY(K-1,I)*BR(K,I)
            IF (.NOT. IMPLICIT_VISC(JW)) ST(K,I) = ST(K,I)+AZ(K-1,I)*(BR(K-1,I)+BR(K,I))*0.5D0*(U(K-1,I)-U(K,I))/((AVH2(K-1,I)       &
                                                   +AVH2(K-1,I+1))*0.5D0)
          END DO
          GC2 = 0.0
          IF (FRIC(I) /= 0.0) GC2 = G/(FRIC(I)*FRIC(I))

          HRAD=BHR2(KT,I)/(BR(KTI(I),I)-BR(KT+1,I)+2.0D0*AVHR(KT,I))
          ! MACROPHYTE block removed
          IF(MANNINGS_N(JW))THEN
            GC2=G*FRIC(I)*FRIC(I)/HRAD**0.33333333D0
          END IF
          IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. I == IU) THEN
            GC2 = GC2*FRONT_DRAG_FACTOR(JB)
          END IF
          IF (ONE_LAYER(I)) THEN
            SB(KT,I) = ST(KT+1,I)+GC2*(BR(KTI(I),I)+2.0D0*AVHR(KT,I))*U(KT,I)*DABS(U(KT,I))
          ELSE
            SB(KT,I) = GC2*(BR(KTI(I),I)-BR(KT+1,I)+2.0D0*AVHR(KT,I))*U(KT,I)*DABS(U(KT,I))
            DO K=KT+1,KBMIN(I)-1
              HRAD=(BHR2(K,I)/(BR(K,I)-BR(K+1,I)+2.0D0*H(K,JW)))
              ! MACROPHYTE block removed
              IF(MANNINGS_N(JW))THEN
                GC2=G*FRIC(I)*FRIC(I)/HRAD**0.33333333D0
              END IF
              SB(K,I) = GC2*(BR(K,I)-BR(K+1,I)+2.0D0*H(K,JW))*U(K,I)*DABS(U(K,I))
            END DO
            IF (KT /= KBMIN(I)) THEN
              HRAD=(BHR2(KBMIN(I),I)/(BR(KBMIN(I),I)+2.0D0*H(KBMIN(I),JW)))
              ! MACROPHYTE block removed
              IF(MANNINGS_N(JW))THEN
                GC2=G*FRIC(I)*FRIC(I)/HRAD**0.33333333D0
              END IF

              IF (KBMIN(I) /= KB(I)) THEN
                SB(KBMIN(I),I) = GC2*(BR(KBMIN(I),I)-BR(KBMIN(I)+1,I)+2.0D0*H2(K,I))*U(KBMIN(I),I)*DABS(U(KBMIN(I),I))
              ELSE
                SB(KBMIN(I),I) = GC2*(BR(KBMIN(I),I)+2.0D0*H2(K,I))*U(KBMIN(I),I)*DABS(U(KBMIN(I),I))
              END IF
            END IF
          END IF
          DO K=KT,KBMIN(I)-1
            SB(K,I) = SB(K,I)+ST(K+1,I)
          END DO
          SB(KBMIN(I),I) = SB(KBMIN(I),I)+WSHX(I)*DECAY(KBMIN(I),I)*(BR(KBMIN(I)-1,I)+BR(KBMIN(I),I))*0.5D0
        END DO

!****** Horizontal advection of momentum

        DO I=IU,ID-1
          DO K=KT,KBMIN(I)
            UDR       = (1.0D0+DSIGN(1.0D0,(U(K,I)+U(K,I+1))*0.5D0))*0.5D0
            UDL       = (1.0D0+DSIGN(1.0D0,(U(K,I)+U(K,I-1))*0.5D0))*0.5D0
            ADMX(K,I) = (BH2(K,I+1)*(U(K,I+1)+U(K,I))*0.5D0*(UDR*U(K,I)+(1.0-UDR)*U(K,I+1))-BH2(K,I)*(U(K,I)+U(K,I-1))               &
                        *0.5D0*(UDL*U(K,I-1)+(1.0D0-UDL)*U(K,I)))/DLXR(I)
          END DO
        END DO

!****** Horizontal dispersion of momentum

        DO I=IU,ID-1
          DO K=KT,KBMIN(I)
            IF(AX(JW) >= 0.0)THEN
            DM(K,I) = AX(JW)*(BH2(K,I+1)*(U(K,I+1)-U(K,I))/DLX(I+1)-BH2(K,I)*(U(K,I)-U(K,I-1))/DLX(I))/DLXR(I)
            ELSE
            DM(K,I) = ABS(U(K,I))*ABS(AX(JW))*H(K,JW)*(BH2(K,I+1)*(U(K,I+1)-U(K,I))/DLX(I+1)-BH2(K,I)*(U(K,I)-U(K,I-1))/DLX(I))/DLXR(I)     ! SW 8/2/2017 SCALE AX WITH U, FOR EXAMPLE AX=0.1U
            ENDIF
          END DO
        END DO

!****** Vertical advection of momentum

        DO I=IU,ID-1
          DO K=KT,KB(I)-1
            AB        = (1.0D0+DSIGN(1.0D0,(W(K,I+1)+W(K,I))*0.5D0))*0.5D0
            ADMZ(K,I) = (BR(K,I)+BR(K+1,I))*0.5D0*(W(K,I+1)+W(K,I))*0.5D0*(AB*U(K,I)+(1.0-AB)*U(K+1,I))
          END DO
        END DO

!****** Gravity force due to channel slope

        DO I=IU-1,ID
          GRAV(KT,I) = AVHR(KT,I)*(BKT(I)+BKT(I+1))*0.5D0*G*SINAC(JB)                                                
          DO K=KT+1,KB(I)                                                                                              
            GRAV(K,I) = BHR2(K,I)*G*SINAC(JB)
          END DO
        END DO

        IF(ICEC(JW)  == '    ONWB')THEN
        DO I = IU,ID            ! water loss due to ice formation or water gain due to ice melting
          VolIce(jb)=VolIce(jb)+iceqss(i)*dlt
          QSS(KT,I) = QSS(KT,I) + IceQSS(I)
          IceQSS(I) = 0.0d00
        END DO
        END IF


!***********************************************************************************************************************************
!**                                            Task 2.2.3: Water surface elevation                                                **
!***********************************************************************************************************************************

!****** Tridiagonal coefficients

        BHRHO(IU-1:ID+1) = 0.0D0; D(IU-1:ID+1) = 0.0D0; F(IU-1:ID+1) = 0.0D0
        DO I=IU,ID-1
          DO K=KT,KBMIN(I)
            BHRHO(I) = BHRHO(I)+(BH2(K,I+1)/RHO(K,I+1)+BH2(K,I)/RHO(K,I))
          END DO
          DO K=KT,KB(I)
            D(I) = D(I)+(U(K,I)*BHR2(K,I)-U(K,I-1)*BHR2(K,I-1)-QSS(K,I)+(UXBR(K,I)-UXBR(K,I-1))*DLT)
            F(I) = F(I)+(-SB(K,I)+ST(K,I)-ADMX(K,I)+DM(K,I)-HDG(K,I)+GRAV(K,I))
          END DO
        END DO

!****** Boundary tridiagonal coefficients

        D(IU) = 0.0D0
        DO K=KT,KB(IU)
          D(IU) = D(IU)+(U(K,IU)*BHR2(K,IU)-QSS(K,IU))+UXBR(K,IU)*DLT
        END DO
        IF (DN_FLOW(JB)) THEN
          DO K=KT,KB(ID)
            D(ID) = D(ID)-U(K,ID-1)*BHR2(K,ID-1)-QSS(K,ID)+(UXBR(K,ID)-UXBR(K,ID-1))*DLT+QOUT(K,JB)
          END DO
        END IF
        IF (UP_HEAD(JB)) THEN
          DO K=KT,KBMIN(IU-1)
            BHRHO(IU-1) = BHRHO(IU-1)+(BH2(K,IU)/RHO(K,IU)+BH2(K,IU-1)/RHO(K,IU-1))
          END DO
          DO K=KT,KB(IU)
            D(IU)   = D(IU)-U(K,IU-1)*BHR2(K,IU-1)
            F(IU-1) = F(IU-1)-(SB(K,IU-1)-ST(K,IU-1)+HDG(K,IU-1)-GRAV(K,IU-1))
          END DO
        END IF
        IF (DN_HEAD(JB)) THEN
          DO K=KT,KBMIN(ID)
            BHRHO(ID) = BHRHO(ID)+(BH2(K,ID+1)/RHO(K,ID+1)+BH2(K,ID)/RHO(K,ID))
          END DO
          DO K=KT,KB(ID)
            D(ID) = D(ID)+(U(K,ID)*BHR2(K,ID)-U(K,ID-1)*BHR2(K,ID-1)-QSS(K,ID))+(UXBR(K,ID)-UXBR(K,ID-1))*DLT
            F(ID) = F(ID)+(-SB(K,ID)+ST(K,ID)-HDG(K,ID)+GRAV(K,ID))
          END DO
        END IF
      END DO
    END DO
 !!$OMP END PARALLEL DO
    DO JW=1,NWB
      KT = KTWB(JW)
      DO JB=BS(JW),BE(JW)
      IF(BR_INACTIVE(JB))CYCLE
        IU = MAX(CUS(JB), TAIL_COUPLE_SEG(JB))
        ID = DS(JB)
        IF (INTERNAL_FLOW(JB) .AND. .NOT. DAM_INFLOW(JB)) THEN                                                         !TC 08/03/04
          QIN(JB) = 0.0D0
          DO K=KTWB(JWUH(JB)),KB(UHS(JB))
            QIN(JB) = QIN(JB)+U(K,UHS(JB))*BHR2(K,UHS(JB))
          END DO
        END IF
        QINJB_ACTIVE = EFFECTIVE_UPSTREAM_INFLOW(JB)
        IF (JB == 1 .AND. (NIT <= 10 .OR. MOD(NIT,500) == 0)) THEN
          QDT_SUM_DIAG = 0.0D0
          QSS_SUM_DIAG = 0.0D0
          DO I=CUS(JB),DS(JB)
            QDT_SUM_DIAG = QDT_SUM_DIAG+QDT(I)
            DO K=KT,KB(I)
              QSS_SUM_DIAG = QSS_SUM_DIAG+QSS(K,I)
            END DO
          END DO
          TAIL_Q_DIAG = 0.0D0
          IF (TAIL_STAGE_VALID(JB)) TAIL_Q_DIAG = TAIL_Q_LINK(JB)
          WARNING_OPEN = .TRUE.
          WRITE (WRN,'(A,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') '[V22_BOUNDARY_FLUX]', &
            'JB=',JB, 'QIN=',QIN(JB), 'QEFF=',QINJB_ACTIVE, 'QDT_SUM=',QDT_SUM_DIAG, 'QSS_SUM=',QSS_SUM_DIAG, &
            'TAIL_Q=',TAIL_Q_DIAG
        END IF
        IF (UP_FLOW(JB)) D(IU) = D(IU)-QINJB_ACTIVE

!****** Boundary surface elevations

        IF (UH_INTERNAL(JB)) THEN
          Z(IU-1)    = ((-EL(KTWB(JWUH(JB)),UHS(JB))+Z(UHS(JB))*COSA(JBUH(JB)))+EL(KT,IU-1)+SINA(JB)*DLXR(IU-1))/COSA(JB)
          ELWS(IU-1) = EL(KT,IU-1)-Z(IU-1)*COSA(JB)
          KTI(IU-1)  = 2 
          DO WHILE (EL(KTI(IU-1),IU-1) >= ELWS(IU-1))          ! SR 1/2024
            KTI(IU-1) = KTI(IU-1)+1
          END DO
          KTI(IU-1) = MAX(KTI(IU-1)-1,2)
        END IF
        IF (UH_EXTERNAL(JB)) Z(IU-1) = (EL(KT,IU-1)-(ELUH(JB)+SINA(JB)*DLX(IU)*0.5D0))/COSA(JB)
        IF (DH_INTERNAL(JB)) THEN
          Z(ID+1)    = ((-EL(KTWB(JWDH(JB)),DHS(JB))+Z(DHS(JB))*COSA(JBDH(JB)))+EL(KT,ID+1))/COSA(JB)
          ELWS(ID+1) = EL(KT,ID+1)-Z(ID+1)*COSA(JB)
          KTI(ID+1)  = 2
          DO WHILE (EL(KTI(ID+1),ID+1) >= ELWS(ID+1))          ! SR 1/2024
            KTI(ID+1) = KTI(ID+1)+1
          END DO
          KTI(ID+1) = MAX(KTI(ID+1)-1,2)
          IF (KTI(ID+1) >= KB(ID)) THEN
            Z(ID+1)    = Z(ID)-SLOPE(JB)*DLX(ID)/2.0D0
            ELWS(ID+1) = EL(KT,ID+1)-Z(ID+1)*COSA(JB)
            KTI(ID+1)  = 2
            DO WHILE (EL(KTI(ID+1),ID+1) >= ELWS(ID+1))       ! SR 1/2024
              KTI(ID+1) = KTI(ID+1)+1
            END DO
            KTI(ID+1) = MAX(KTI(ID+1)-1,2)
          END IF
        END IF
        IF (DH_EXTERNAL(JB)) Z(ID+1) = (EL(KT,ID+1)-(ELDH(JB)-SINA(JB)*DLX(ID)*0.5D0))/COSA(JB)

!****** Implicit water surface elevation solution

        DO I=IU,ID   !CONCURRENT(I=IU:ID)                         !DO I=IU,ID
          A(I) = -RHO(KT,I-1)*G*COSA(JB)*DLT*DLT* BHRHO(I-1)*0.5D0/DLXR(I-1)
          C(I) = -RHO(KT,I+1)*G*COSA(JB)*DLT*DLT* BHRHO(I)  *0.5D0/DLXR(I)
          V(I) =  RHO(KT,I)  *G*COSA(JB)*DLT*DLT*(BHRHO(I)  *0.5D0/DLXR(I)+BHRHO(I-1)*0.5D0/DLXR(I-1))+DLX(I)*BI(KT,I)
          D(I) =  DLT*(D(I)+DLT*(F(I)-F(I-1)))+DLX(I)*BI(KT,I)*Z(I)
        END DO                   
        IF (UP_HEAD(JB)) D(IU) = D(IU)-A(IU)*Z(IU-1)
        IF (DN_HEAD(JB)) D(ID) = D(ID)-C(ID)*Z(ID+1)
        IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. TAIL_STAGE_VALID(JB) .AND. UP_FLOW(JB) .AND. .NOT. HEAD_FLOW(JB)) THEN
          TAIL_Z_UP = Z(IU)
          IF (ABS(COSA(JB)) > 1.0D-12) THEN
            TAIL_Z_UP = (EL(KT,IU-1)-(TAIL_WSE_UP(JB)+SINA(JB)*DLX(IU)*0.5D0))/COSA(JB)
          END IF
          D(IU) = D(IU)-TAIL_HEAD_FEEDBACK_RELAX*A(IU)*TAIL_Z_UP
          WARNING_OPEN = .TRUE.
          WRITE (WRN,'(A,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') '[V9_TAIL_FEEDBACK]', 'JB=',JB, &
            'TAIL_WSE=',TAIL_WSE_UP(JB), 'TAIL_Z=',TAIL_Z_UP, 'RELAX=',TAIL_HEAD_FEEDBACK_RELAX
        END IF
        BTA(IU) = V(IU)
        GMA(IU) = D(IU)
        DO I=IU+1,ID
          BTA(I) = V(I)-A(I)/BTA(I-1)*C(I-1)
          GMA(I) = D(I)-A(I)/BTA(I-1)*GMA(I-1)
        END DO      
        Z(ID) = GMA(ID)/BTA(ID)
          !if(z(id) /= z(id))then       ! Check for NAN
          !    write(7678,'(a,f12.3,i5,e13.4,e13.4,e13.4,e13.4,2e13.4)')'Z(id)=NAN',jday,id,gma(id),c(id),bta(id),sz(id),f(id),f(id-1)
          !endif
        DO I=ID-1,IU,-1
          Z(I) = (GMA(I)-C(I)*Z(I+1))/BTA(I)
          !if(z(i) /= z(i))then    ! Check for NAN
          !    write(7678,'(a,f12.3,i5,e13.4,e13.4,e13.4,e13.4,e13.4)')'Z(i)=NAN',jday,i,z(i+1),gma(i),c(i),bta(i),sz(i)
          !endif
        END DO

!****** Boundary water surface elevations

        IF (UP_FLOW(JB) .AND. .NOT. HEAD_FLOW(JB)) THEN
          Z(IU-1) = Z(IU)
          IF (UPSTREAM_DOMAIN_LOCK(JB) .AND. TAIL_STAGE_VALID(JB)) THEN
            TAIL_Z_UP = Z(IU)
            IF (ABS(COSA(JB)) > 1.0D-12) THEN
              TAIL_Z_UP = (EL(KT,IU-1)-(TAIL_WSE_UP(JB)+SINA(JB)*DLX(IU)*0.5D0))/COSA(JB)
            END IF
            Z(IU-1) = (1.0D0-TAIL_HEAD_FEEDBACK_RELAX)*Z(IU) + TAIL_HEAD_FEEDBACK_RELAX*TAIL_Z_UP
          END IF
        END IF
        IF (UP_FLOW(JB) .AND.       HEAD_FLOW(JB)) Z(IU-1) = (-EL(KTWB(JWUH(JB)),UHS(JB))+Z(UHS(JB))*COSA(JBUH(JB))+EL(KT,IU-1)  &
                                                             +SINA(JBUH(JB))*DLXR(IU-1))/COSA(JBUH(JB))
        IF (DN_FLOW(JB))                           Z(ID+1) = Z(ID)

!****** Updated surface layer and geometry

        IF (.NOT. TRAPEZOIDAL(JW)) THEN                                                                                !SW 07/16/04
          DO I=IU-1,ID+1
            IF (EL(KT,I)-Z(I)*COSA(JB) > EL(KTI(I),I)) THEN
              DO WHILE ( EL(KT,I)-Z(I)*COSA(JB) > EL(KTI(I),I) .AND. KTI(I) /= 2)
                Z(I)   = (EL(KT,I)-EL(KTI(I),I)-(EL(KT,I)-EL(KTI(I),I)-Z(I)*COSA(JB))*(B(KTI(I),I)/B(KTI(I)-1,I)))/COSA(JB)
!                IF(MACROPHYTE_ON)THEN
!                  KTIP=KTI(I)
!!C  KEEPING TRACK IF COLUMN KTI HAS MACROPHYTES
!                  IF(KTIP.GT.2)KTICOL(I)=.FALSE.
!                END IF
                KTI(I) =  MAX(KTI(I)-1,2)
              END DO
            ELSE IF (EL(KT,I)-Z(I)*COSA(JB) <= EL(KTI(I)+1,I)) THEN                         ! SR 1/2024
              DO WHILE (EL(KT,I)-Z(I)*COSA(JB) <= EL(KTI(I)+1,I) .AND. KTI(I) < KB(I))                   ! sw 7/18/11      ! SR 1/2024
                Z(I)   = (EL(KT,I)-EL(KTI(I)+1,I)-(EL(KT,I)-EL(KTI(I)+1,I)-Z(I)*COSA(JB))*(B(KTI(I),I)/B(KTI(I)+1,I)))/COSA(JB)
                KTI(I) =  KTI(I)+1
                !IF(MACROPHYTE_ON)KTICOL(I)=.TRUE.  
                IF (KTI(I) >= KB(I)) EXIT
              END DO
            END IF
            BI(KT:KB(I),I) =  B(KT:KB(I),I)
            BI(KT,I)       =  B(KTI(I),I)
            H1(KT,I)       =  H(KT,JW)-Z(I)
            AVH1(KT,I)     = (H1(KT,I)+H1(KT+1,I))*0.5D0
            IF (KT == KTI(I) .OR. KTI(I) >= KB(I)) THEN
              BH1(KT,I) = B(KT,I)*H1(KT,I)
            ELSE
              BH1(KT,I) = BI(KT,I)*(EL(KT,I)-Z(I)*COSA(JB)-EL(KTI(I)+1,I))/COSA(JB)
            END IF
            DO K=KTI(I)+1,KT
              BH1(KT,I) = BH1(KT,I)+BNEW(K,I)*H(K,JW) !BNEW(K,I)*H(K,JW)   ! SW 1/23/06
            END DO
            BKT(I)    = BH1(KT,I)/H1(KT,I)
            IF(KBI(I) < KB(I))BKT(I)=BH1(KT,I)/(H1(KT,I)-(EL(KBI(I)+1,I)-EL(KB(I)+1,I))/COSA(JB))    ! SW 1/23/06
            VOL(KT,I) = BH1(KT,I)*DLX(I)
          END DO
          DO I=IU-1,ID
            !AVHR(KT,I) = H1(KT,I)  +(H1(KT,I+1) -H1(KT,I))*DLX(I)/(DLX(I)+DLX(I+1))                          !SW 07/29/04  (H1(KT,I+1) +H1(KT,I))*0.5   
            !IF(KBI(I) < KB(I))AVHR(KT,I)=(H1(KT,I)-(EL(KBI(I)+1,I)-EL(KB(I)+1,I))/COSA(JB))  &
            !   +(H1(KT,I+1)-(EL(KBI(I)+1,I+1)-EL(KB(I)+1,I+1))/COSA(JB) -H1(KT,I)+(EL(KBI(I)+1,I)&
            !   -EL(KB(I)+1,I))/COSA(JB))*DLX(I)/(DLX(I)+DLX(I+1))        ! SW 1/23/06
          IF (KBI(I) < KB(I) .OR. KBI(I+1) < KB(I+1)) THEN                           ! SR 7/2024
            HTMP1 = H1(KT,I)
            HTMP2 = H1(KT,I+1)
            IF (KBI(I)   < KB(I))   HTMP1 = H1(KT,I)  -(EL(KBI(I)+1,I)    -EL(KB(I)+1,I))    /COSA(JB)
            IF (KBI(I+1) < KB(I+1)) HTMP2 = H1(KT,I+1)-(EL(KBI(I+1)+1,I+1)-EL(KB(I+1)+1,I+1))/COSA(JB)
            AVHR(KT,I) = HTMP1 +(HTMP2-HTMP1)*DLX(I)/(DLX(I)+DLX(I+1))
          ELSE
            AVHR(KT,I) = H1(KT,I) +(H1(KT,I+1)-H1(KT,I))*DLX(I)/(DLX(I)+DLX(I+1))
          END IF
              
            BHR1(KT,I) =  BH1(KT,I)+(BH1(KT,I+1)-BH1(KT,I))*DLX(I)/(DLX(I)+DLX(I+1))                          !SW 07/29/04 (BH1(KT,I+1)+BH1(KT,I))*0.5 
            IF(CONSTRICTION(KT,I))THEN    ! SW 6/26/2018
              IF(BHR1(KT,I) > BCONSTRICTION(I)*H1(KT,I))BHR1(KT,I)= BCONSTRICTION(I)*H1(KT,I)
            ENDIF
          END DO
          
        IF (KBI(ID+1) < KB(ID+1)) THEN         ! SR 7/2024
          AVHR(KT,ID+1) = H1(KT,ID+1)-(EL(KBI(ID+1)+1,ID+1)-EL(KB(ID+1)+1,ID+1))/COSA(JB)
        ELSE
          AVHR(KT,ID+1) = H1(KT,ID+1)
        END IF

        !  AVHR(KT,ID+1) = H1(KT,ID+1)
          BHR1(KT,ID+1) = BH1(KT,ID+1)
          DLVOL(JB)        = 0.0
        ELSE                                                                                                           !SW 07/16/04
          DO I=IU-1,ID+1
            BI(KT:KB(I),I) =  B(KT:KB(I),I)
            CALL GRID_AREA2
            H1(KT,I)   =  H(KT,JW)-Z(I)
            AVH1(KT,I) = (H1(KT,I)+H1(KT+1,I))*0.5
            CALL GRID_AREA1 (EL(KT,I)-Z(I),EL(KT+1,I),BH1(KT,I),BI(KT,I))
            BKT(I)    = BH1(KT,I)/H1(KT,I)
            if(kbi(i) < kb(i))bkt(i)=bh1(kt,i)/(h1(kt,i)-(el(kbi(i)+1,i)-el(kb(i)+1,i))/COSA(JB))    ! SW 1/23/06
            VOL(KT,I) = BH1(KT,I)*DLX(I)
          END DO
          DO I=IU-1,ID
            !AVHR(KT,I) = H1(KT,I)  +(H1(KT,I+1) -H1(KT,I))*DLX(I)/(DLX(I)+DLX(I+1))                          !SW 07/29/04
            !if(kbi(i) < kb(i))avhr(kt,i)=(h1(kt,i)-(el(kbi(i)+1,i)-el(kb(i)+1,i))/COSA(JB)) &
            !   +(H1(KT,I+1)-(el(kbi(i)+1,i+1)-el(kb(i)+1,i+1))/COSA(JB) -H1(KT,I)+(el(kbi(i)+1,i)&
            !   -el(kb(i)+1,i))/COSA(JB))*DLX(I)/(DLX(I)+DLX(I+1))                                                     ! SW 1/23/06
           IF (KBI(I) < KB(I) .OR. KBI(I+1) < KB(I+1)) THEN                           ! SR 7/2024
            HTMP1 = H1(KT,I)
            HTMP2 = H1(KT,I+1)
            IF (KBI(I)   < KB(I))   HTMP1 = H1(KT,I)  -(EL(KBI(I)+1,I)    -EL(KB(I)+1,I))    /COSA(JB)
            IF (KBI(I+1) < KB(I+1)) HTMP2 = H1(KT,I+1)-(EL(KBI(I+1)+1,I+1)-EL(KB(I+1)+1,I+1))/COSA(JB)
            AVHR(KT,I) = HTMP1 +(HTMP2-HTMP1)*DLX(I)/(DLX(I)+DLX(I+1))
          ELSE
            AVHR(KT,I) = H1(KT,I) +(H1(KT,I+1)-H1(KT,I))*DLX(I)/(DLX(I)+DLX(I+1))
          END IF

            BHR1(KT,I) = BH1(KT,I)+(BH1(KT,I+1)-BH1(KT,I))*DLX(I)/(DLX(I)+DLX(I+1))                        !SW 07/29/04
          END DO
         ! AVHR(KT,ID+1) = H1(KT,ID+1)
          
        IF (KBI(ID+1) < KB(ID+1)) THEN         ! SR 7/2024
          AVHR(KT,ID+1) = H1(KT,ID+1)-(EL(KBI(ID+1)+1,ID+1)-EL(KB(ID+1)+1,ID+1))/COSA(JB)
        ELSE
          AVHR(KT,ID+1) = H1(KT,ID+1)
        END IF

          BHR1(KT,ID+1) = BH1(KT,ID+1)
          DLVOL(JB)     = 0.0
        END IF
        ELWS(CUS(JB):DS(JB)+1) = EL(KT,CUS(JB):DS(JB)+1)-Z(CUS(JB):DS(JB)+1)*COSA(JB)
        DO I=IU,ID
          DLVOL(JB) = DLVOL(JB)+(BH1(KT,I)-BH2(KT,I))*DLX(I)
          IF (KT == 2 .AND. H1(KT,I) > H(2,JW) .AND. .NOT. SURFACE_WARNING) THEN
            WRITE (WRN,'(A,I0,A,F0.3)') 'Water surface is above the top of layer 2 in segment ',I,' at day ',JDAY
            WARNING_OPEN    = .TRUE.
            SURFACE_WARNING = .TRUE.
          END IF
        END DO

!        IF(MACROPHYTE_ON)THEN
!!C  IF DEPTH IN KTI LAYER BECOMES GREATER THAN THRESHOLD, SETTING
!!C      MACROPHYTE CONC. IN KTI COLUMN TO INITIAL CONC.
!          DO I=IU,ID
!            DEPKTI=ELWS(I)-EL(KTI(I)+1,I)
!
!!******* MACROPHYTES, SETTING CONC. OF MACROPHYTES IN NEW COLUMNS TO
!!********* INITIAL CONCENTRATION IF COLUMN DEPTH IS GREATER THAN 'THRKTI'
!            IF(.NOT.KTICOL(I).AND.DEPKTI.GE.THRKTI)THEN
!              KTICOL(I)=.TRUE.
!              JT=KTI(I)
!              MACT(JT,KT,I)=0.0
!              DO M=1,NMC
!                !MACRC(JT,KT,I,M)=MACWBCI(JW,M)
!                IF (ISO_macrophyte(JW,m))  macrc(jt,kt,I,m) = macwbci(JW,m)     ! cb 3/7/16
!                IF (VERT_macrophyte(JW,m)) macrc(jt,kt,I,m) = 0.1
!                IF (long_macrophyte(JW,m)) macrc(jt,kt,I,m) = 0.1
!                COLB=EL(KTI(I)+1,I)
!                COLDEP=ELWS(I)-COLB
!                !MACRM(JT,KT,I,M)=MACWBCI(JW,M)*COLDEP*CW(JT,I)*DLX(I)
!                MACRM(JT,KT,I,M)=macrc(jt,kt,I,m)*COLDEP*CW(JT,I)*DLX(I)         ! cb 3/17/16                 
!                MACT(JT,KT,I)=MACT(JT,KT,I)+MACWBCI(JW,M)
!                MACMBRT(JB,M) = MACMBRT(JB,M)+MACRM(JT,KT,I,M)
!              END DO
!            END IF
!
!!****** MACROPHYTES, WHEN COLUMN DEPTH IS LESS THAN 'THRKTI', ZEROING OUT CONC.
!            IF(KTICOL(I).AND.DEPKTI.LT.THRKTI)THEN
!              KTICOL(I)=.FALSE.
!              JT=KTI(I)
!              MACT(JT,KT,I)=0.0
!              DO M=1,NMC
!                MACMBRT(JB,M) = MACMBRT(JB,M)-MACRM(JT,KT,I,M)
!                MACRC(JT,KT,I,M)=0.0
!                MACRM(JT,KT,I,M)=0.0
!              END DO
!            END IF
!          END DO
!        END IF

!***********************************************************************************************************************************
!**                                             Task 2.2.4: Longitudinal velocities                                               **
!***********************************************************************************************************************************

        IUT = IU
        IDT = ID
        IF (UP_HEAD(JB)) IUT = IU-1
        IF (DN_HEAD(JB)) IDT = ID+1

!****** Pressures

        DO I=IUT,IDT
          DO K=KT,KB(I)
            P(K,I) = P(K-1,I)+RHO(K,I)*G*H1(K,I)*COSA(JB)
          END DO
        END DO

!****** Horizontal pressure gradients

        DO I=IUT,IDT-1
          HPG(KT,I) = DLXRHO(I)*(BKT(I)+BKT(I+1))*0.5D0*(H1(KT,I+1)*P(KT,I+1)-H1(KT,I)*P(KT,I))
          DO K=KT+1,KBMIN(I)
            HPG(K,I) = DLXRHO(I)*BHR2(K,I)*((P(K-1,I+1)-P(K-1,I))+(P(K,I+1)-P(K,I)))
          END DO
        END DO

!****** Boundary horizontal velocities

        IF (UP_FLOW(JB)) THEN
          IF (.NOT. HEAD_FLOW(JB)) THEN
            QINF(:,JB) = 0.0
            IF (PLACE_QIN(JW)) THEN

!************ Inflow layer

              K     = KT
              SSTOT = 0.0
              DO JC=NSSS,NSSE
                SSTOT = SSTOT+CIN(JC,JB)
              END DO
              RHOIN = DENSITY(TIN(JB),DMAX1(CIN(1,JB),0.0D0),DMAX1(SSTOT,0.0D0))
              DO WHILE (RHOIN > RHO(K,IU) .AND. K < KB(IU))
                K = K+1
              END DO
              KTQIN(JB) = K
              KBQIN(JB) = K

!************ Layer inflows

              VQIN  =  QINJB_ACTIVE*DLT
              VQINI =  VQIN
              QINFR =  1.0
              INCR  = -1
              DO WHILE (QINFR > 0.0D0)
                V1 = VOL(K,IU)
                IF (K <= KB(IU)) THEN
                  IF (VQIN > 0.5D0*V1) THEN
                    QINF(K,JB) = 0.5D0*V1/VQINI
                    QINFR      = QINFR-QINF(K,JB)
                    VQIN       = VQIN-QINF(K,JB)*VQINI
                    IF (K == KT) THEN
                      K    = KBQIN(JB)
                      INCR = 1
                    END IF
                  ELSE
                    QINF(K,JB) = QINFR
                    QINFR      = 0.0D0
                  END IF
                  IF (INCR < 0) KTQIN(JB) = K
                  IF (INCR > 0) KBQIN(JB) = MIN(KB(IU),K)
                  K = K+INCR
                ELSE
                  QINF(KT,JB) = QINF(KT,JB)+QINFR
                  QINFR       = 0.0D0
                END IF
              END DO
            ELSE
              KTQIN(JB) = KT
              KBQIN(JB) = KB(IU)
              BHSUM     = 0.0D0
              DO K=KT,KB(IU)
                BHSUM = BHSUM+BH1(K,IU)
              END DO
              DO K=KT,KB(IU)
                QINF(K,JB) = BH1(K,IU)/BHSUM
              END DO
            END IF
            DO K=KT,KB(IU)
              U(K,IU-1) = QINF(K,JB)*QINJB_ACTIVE/BHR1(K,IU-1)
            END DO
          ELSE
            KTQIN(JB) = KT
            KBQIN(JB) = KB(IU)
            IF (JBUH(JB) <= BE(JW) .AND. JBUH(JB) >= BS(JW)) THEN
              DO K=KT,KB(IU)
                U(K,IU-1) = U(K,UHS(JB))*BHR1(K,UHS(JB))/BHR1(K,IU-1)
              END DO
            ELSE
              CALL UPSTREAM_VELOCITY
            END IF
          END IF
        END IF
        IF (DN_FLOW(JB)) THEN
          DO K=KT,KB(ID)
            U(K,ID) = QOUT(K,JB)/BHR1(K,ID)
          END DO
        END IF
        IF (UP_HEAD(JB)) THEN
          DO K=KT,KB(IU-1)
            U(K,IU-1) = (BHR2(K,IU-1)*U(K,IU-1)+DLT*(-SB(K,IU-1)+ST(K,IU-1)-HPG(K,IU-1)+GRAV(K,IU-1)))/BHR1(K,IU-1)
          END DO
        END IF
        IF (DN_HEAD(JB)) THEN
          DO K=KT,KB(ID+1)
            U(K,ID) = (BHR2(K,ID)*U(K,ID)+DLT*(-SB(K,ID)+ST(K,ID)-HPG(K,ID)+GRAV(K,ID)))/BHR1(K,ID)
          END DO
        END IF

!****** Horizontal velocities

        DO I=IU,ID-1
          DO K=KT,KBMIN(I)
            U(K,I) = (BHR2(K,I)*U(K,I))/BHR1(K,I)+(DLT*(-SB(K,I)+ST(K,I)-ADMZ(K,I)+ADMZ(K-1,I)-ADMX(K,I)+DM(K,I)-HPG(K,I)+GRAV(K,I)&
                     +UXBR(K,I)/H2(K,I)))/BHR1(K,I)
            IF (INTERNAL_WEIR(K,I)) U(K,I) = 0.0D0
          END DO
        END DO

!****** Implicit vertical eddy viscosity

        IF (IMPLICIT_VISC(JW)) THEN
        !  AT = 0.0D0; CT = 0.0D0; VT = 0.0D0; DT = 0.0D0
        DO I=IUT,IDT-1                ! SW CODE SPEEDUP
            DO K=KT,KBMIN(I) 
            AT(K,I) = 0.0D0; CT(K,I) = 0.0D0; VT(K,I) = 0.0D0; DT(K,I) = 0.0D0
            ENDDO
        ENDDO
          DO I=IUT,IDT-1
            DO K=KT,KBMIN(I)            !KB(I)  SW 10/7/07
              AT(K,I) = -DLT/BHR1(K,I)*AZ(K-1,I)*(BHR1(K-1,I)/AVHR(K-1,I)+BR(K,I))  /(AVH1(K-1,I)+AVH1(K-1,I+1))
              CT(K,I) = -DLT/BHR1(K,I)*AZ(K,I)  *(BHR1(K,I)  /AVHR(K,I)  +BR(K+1,I))/(AVH1(K,I)  +AVH1(K,I+1))
              VT(K,I) =  1.0D0-AT(K,I)-CT(K,I)
              DT(K,I) =  U(K,I)
            END DO
            CALL TRIDIAG(AT(:,I),VT(:,I),CT(:,I),DT(:,I),KT,KBMIN(I),KMX,U(:,I))
          END DO
        END IF

!****** Corrected horizontal velocities

        IF (UP_HEAD(JB)) THEN
          IS    =  ID
          IE    =  IU-1
          INCR  = -1
          Q(IS) =  0.0D0
          DO K=KT,KB(ID)
            Q(IS) = Q(IS)+U(K,IS)*BHR1(K,IS)
          END DO
          QSSUM(IS) = 0.0D0
          DO K=KT,KB(IS)
            QSSUM(IS) = QSSUM(IS)+QSS(K,IS)
          END DO
        ELSE
          IS   = IU-1
          IE   = ID
          INCR = 1
          IF (DN_FLOW(JB)) IE = ID-1
          Q(IS) = 0.0D0
          DO K=KT,KB(IU)
            Q(IS) = Q(IS)+U(K,IS)*BHR1(K,IS)
          END DO
        END IF
        QC(IS) = Q(IS)
        DO I=IS+INCR,IE,INCR
          QSSUM(I) = 0.0D0
          DO K=KT,KB(I)
            QSSUM(I) = QSSUM(I)+QSS(K,I)
          END DO
          BHRSUM = 0.0D0
          Q(I)   = 0.0D0
          DO K=KT,KBMIN(I)
            IF (.NOT. INTERNAL_WEIR(K,I)) THEN
              BHRSUM = BHRSUM+BHR1(K,I)
              Q(I)   = Q(I)+U(K,I)*BHR1(K,I)
            END IF
          END DO
          IF (UP_HEAD(JB)) THEN
            QC(I) = QC(I+1)+(BH1(KT,I+1)-BH2(KT,I+1))*DLX(I+1)/DLT-QSSUM(I+1)
          ELSE
            QC(I) = QC(I-1)-(BH1(KT,I)  -BH2(KT,I))  *DLX(I)  /DLT+QSSUM(I)
          END IF
          DO K=KT,KBMIN(I)
            IF (INTERNAL_WEIR(K,I)) THEN
              U(K,I) = 0.0D0
            ELSE
              U(K,I) =  U(K,I)+(QC(I)-Q(I))/BHRSUM
              IF (Q(I) /= 0.0) QERR(I) = (Q(I)-QC(I))/Q(I)*100.0
            END IF
          END DO
        END DO

!****** Head boundary flows

        IF (UP_HEAD(JB)) QUH1(KT:KB(IU-1),JB) = U(KT:KB(IU-1),IU-1)*BHR1(KT:KB(IU-1),IU-1)
        IF (DN_HEAD(JB)) QDH1(KT:KB(ID+1),JB) = U(KT:KB(ID+1),ID)  *BHR1(KT:KB(ID+1),ID)

!***********************************************************************************************************************************
!**                                              Task 2.2.5: Vertical velocities                                                  **
!***********************************************************************************************************************************

        DO I=IU,ID
          DO K=KB(I)-1,KT,-1
            WT1    =  W(K+1,I)*BB(K+1,I)
            WT2    = (BHR(K+1,I)*U(K+1,I)-BHR(K+1,I-1)*U(K+1,I-1)-QSS(K+1,I))/DLX(I)
            W(K,I) = (WT1+WT2)/BB(K,I)
          END DO
        END DO
      END DO
    END DO
    HYDRO_ITER = 1
    QIN_INNER_PREV = QIN
    IF (NIT <= 10) THEN
      WARNING_OPEN = .TRUE.
      WRITE (WRN,'(A,1X,A,I0)') '[V3_INNER_ITER]', 'PASS=', HYDRO_ITER
    END IF
    QSS = 0.0D0
    IF(SELECTC == '      ON')CALL SELECTIVE
    IF(SELECTC == '    USGS')CALL SELECTIVEUSGS
    CALL HYDROINOUT
    HYDRO_MAX_DZ = 0.0D0
    HYDRO_MAX_DQ = 0.0D0
    DO JB=1,NBR
      HYDRO_MAX_DQ = MAX(HYDRO_MAX_DQ, ABS(QIN(JB)-QIN_INNER_PREV(JB)))
    END DO
    HYDRO_ITER = 2
    IF (NIT <= 10 .OR. HYDRO_MAX_DQ > 0.0D0) THEN
      WARNING_OPEN = .TRUE.
      WRITE (WRN,'(A,1X,A,I0,1X,A,F0.4)') '[V3_INNER_ITER]', 'PASS=', HYDRO_ITER, 'MAX_DQIN=', HYDRO_MAX_DQ
    END IF
    DO JW=1,NWB
      DO JB=BS(JW),BE(JW)
        IF (.NOT. TAIL_COUPLED(JB)) CYCLE
        IF (TAIL_UPSEG(JB) <= 0 .OR. TAIL_DNSEG(JB) <= 0) CYCLE
        CALL RUN_TAIL_INTERFACE_ITERATION(JB, JW)
        TAIL_PREDICT_CACHE_VALID(JB) = .TRUE.
        TAIL_PREDICT_WSE_DN_CACHE(JB) = TAIL_WSE_DN(JB)
        TAIL_PREDICT_QLINK_CACHE(JB) = TAIL_Q_LINK(JB)
        WARNING_OPEN = .TRUE.
        IF (.NOT. TAIL_PREDICT_REUSED_STEP(JB)) THEN
          WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,L1,1X,A,F0.3,1X,A,F0.3)') '[V14_COUPLED_HYBRID]', &
            'JB=',JB, 'PASS=',2, 'COMMIT=',.TRUE., 'QLINK=',TAIL_Q_LINK(JB), 'WSE_UP=',TAIL_WSE_UP(JB)
        END IF
        IF (NIT <= 10 .OR. MOD(NIT,500) == 0) THEN
          WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,L1,1X,A,F0.3,1X,A,F0.3)') '[V18_MULTI_HYBRID]', &
            'JB=',JB, 'PASS=',2, 'COMMIT=',.TRUE., 'QLINK=',TAIL_Q_LINK(JB), 'WSE_DN=',TAIL_WSE_DN(JB)
        END IF
        IF (ABS(TAIL_IFACE_DETA(JB)) > 0.0D0 .OR. ABS(TAIL_IFACE_DQ(JB)) > 0.0D0 .OR. NIT <= 10 .OR. MOD(NIT,500) == 0) THEN
          WRITE (WRN,'(A,1X,A,I0,1X,A,ES12.4,1X,A,ES12.4,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') &
            '[V19_INTERFACE_RESIDUAL]', 'JB=',JB, 'DETA=',TAIL_IFACE_DETA(JB), 'DQ=',TAIL_IFACE_DQ(JB), &
            'ETA_P=',TAIL_IFACE_ETA_PRED(JB), 'ETA_C=',TAIL_IFACE_ETA_CORR(JB), 'Q_P=',TAIL_IFACE_Q_PRED(JB), &
            'Q_C=',TAIL_IFACE_Q_CORR(JB)
        END IF
        IF (TAIL_STAGE_VALID(JB) .AND. FRONT_STATE(JB) >= FRONT_STATE_WETTING) THEN
          WARNING_OPEN = .TRUE.
          WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') '[V6_COUPLING]', &
            'JB=',JB, 'UPSEG=',TAIL_UPSEG(JB), 'DNSEG=',TAIL_DNSEG(JB), 'WSE_UP=',TAIL_WSE_UP(JB), &
            'WSE_DN=',TAIL_WSE_DN(JB), 'QLINK=',TAIL_Q_LINK(JB)
        END IF
      END DO
    END DO

!***********************************************************************************************************************************
!**                                                  Task 2.2.6: Autostepping                                                     **
!***********************************************************************************************************************************

    DO JW=1,NWB
      KT = KTWB(JW)
      DO JB=BS(JW),BE(JW)
        DO I=CUS(JB),DS(JB)
          IF (H1(KT,I) < 0.0) THEN
            WRITE (WRN,'(A,F0.3,A,I0/4(A,F0.3))') 'Computational warning at Julian day = ',JDAY,' at segment ',I,'timestep = ',DLT,&
                                                  ' water surface deviation [Z] = ',Z(I),' m  layer thickness = ',H1(KT,I),' m'
            WARNING_OPEN = .TRUE.
            IF (DLT > DLTMIN) THEN
              WRITE (WRN,'(A,I0/2(A,F0.3),A,I0)') 'Negative surface layer thickness in segment ',I,'  time step reduced to ',  &
                                                   DLTMIN,' s on day ',JDAY,' at iteration ',NIT
              WARNING_OPEN = .TRUE.
              CURMAX       =  DLTMIN
              GO TO 220
            ELSE
              WRITE (W2ERR,'(A,F0.3/A,I0)') 'Unstable water surface elevation on day ',JDAY,'negative surface layer thickness '//  &
                                            'using minimum timestep at iteration ',NIT
              WRITE(W2ERR,*)'Branch #:',jb,' in Waterbody:',jw,' Surface layer KT:',ktwb(jw)
              WRITE (W2ERR,'(A)') 'Segment, Surface layer thickness, m, Flow m3/s, U(KT,I) m/s, ELWS, m, Prior ELWS, m'
              DO II=MAX(CUS(JB),I-3),MIN(DS(JB),I+3)
                WRITE (W2ERR,'(T4,I3,T19,F10.2,t37,e10.3,1x,e10.3,2x,f10.2,2x,f10.2)') II,H1(KT,II),QC(II),U(KT,II),ELWS(II),SELWS(II)                           ! SW 7/13/10
              END DO
              STATUS_TEXT = 'Runtime error - see w2.err'
              ERROR_OPEN = .TRUE.
              GO TO 230
            END IF
          ENDIF
          
            IF(DLTADD(JW)=='      ON'.and.ABS(H1(KT,I)-H2(KT,I))/H2(KT,I) > 0.35)THEN
            WRITE (WRN,'(A,F0.3,A,I0,A,F0.3/3(A,F0.3),a,i10,a)') 'Computational warning |h1-h2|/h2>0.35 on Julian day = ',JDAY,' at segment ',I,' timestep DLT= ',DLT,&
                                                  '   Water surface deviation [Z,m] = ',Z(I),' H1 layer thickness(m) = ',H1(KT,I),' H2 layer thickenss(m)=',h2(kt,i),' Iteration[NIT]=',nit,' DLT reduced'
            WARNING_OPEN = .TRUE.
            KLOC = KT
            ILOC = I
            IF (DLTFF*CURMAX < MINDLT) THEN
              KMIN = KT
              IMIN = I
            END IF
            CURMAX=DLT*0.5
          END IF
    END DO   ! i LOOP
        DO I=CUS(JB),DS(JB)
            TAU1=0.0D0;TAU2=0.0D0
           IF (VISCOSITY_LIMIT(JW))THEN
              IF(AX(JW) >= 0.0)TAU1   = 2.0*AX(JW)/(DLX(I)*DLX(I))
           ENDIF   
          IF (CELERITY_LIMIT(JW))  CELRTY = SQRT((ABS(RHO(KB(I),I)-RHO(KT,I)))/1000.0*G*DEPTHB(KBI(I),I)*0.5)               ! SW 1/23/06
          DO K=KT,KB(I)
            IF (VISCOSITY_LIMIT(JW) .AND. .NOT. IMPLICIT_VISC(JW)) TAU2 = 2.0*AZ(K,I)/(H1(K,JW)*H1(K,JW))
            QTOT(K,I) = (ABS(U(K,I))*BHR1(K,I)+ABS(U(K,I-1))*BHR1(K,I-1)+(ABS(W(K,I))*BB(K,I)+ABS(W(K-1,I))*BB(K-1,I))*DLX(I)      &
                        +DLX(I)*ABS(BH2(K,I)-BH1(K,I))/DLT+ABS(QSS(K,I)))*0.5
              IF (VISCOSITY_LIMIT(JW).AND.AX(JW)<0.0)THEN
              TAU1   = 2.0*ABS(U(K,I))*ABS(AX(JW))*H(K,JW) /(DLX(I)*DLX(I))
              ENDIF  
            DLTCAL    = 1.0/((QTOT(K,I)/BH1(K,I)+CELRTY)/DLX(I)+TAU1+TAU2+NONZERO)
            IF (DLTCAL < CURMAX) THEN
              KLOC   = K
              ILOC   = I
              CURMAX = DLTCAL
              IF (DLTFF*CURMAX < MINDLT) THEN
                KMIN = K
                IMIN = I
              END IF
            END IF
          END DO
        END DO
      END DO
    END DO

!** Restore timestep dependent variables and restart calculations

220 CONTINUE
    IF (CURMAX < DLT .AND. DLT > DLTMIN) THEN
      DLT = DLTFF*CURMAX
      IF (DLT <= DLTMIN) THEN
        WRITE (WRN,'(A,F0.3/A,F0.3,A)') 'Computational warning at Julian day = ',JDAY,' timestep = ',DLT,' sec: DLT<DLTMIN set DLT=DLTMIN'
        WARNING_OPEN = .TRUE.
        DLT          =  DLTMIN
      END IF
      NV        = NV+1
      Z         = SZ
      ELWS      = SELWS
      U         = SU
      W         = SW
      AZ        = SAZ
      AVH2      = SAVH2
      AVHR      = SAVHR
      KTI       = SKTI
      BKT       = SBKT
      QSS       = 0.0
      SB        = 0.0
      DLTS      = DLT

        do jw=1,nwb                                                                            ! SW 8/25/05
        do jb=bs(jw),be(jw)
        do i=us(jb)-1,ds(jb)+1
            VOL(KTWB(JW),I) = BH2(KTWB(JW),I)*DLX(I)
            BI(KTWB(JW),I) = B(KTI(I),I)
        end do
        end do
        end do


      CURMAX    = DLTMAXX/DLTFF
      IF (PIPES) THEN         
        YS   = YSS
        VS   = VSS
        VST  = VSTS
        YST  = YSTS
        DTP  = DTPS
        QOLD = QOLDS
      END IF
      CALL RESTORE_TAIL_DYNAMIC_STATE()
      TAIL_PREDICT_CACHE_VALID = .FALSE.
      TAIL_PREDICT_SKIP_COUNT = 0

      GO TO 210
    END IF
    DLTLIM(KMIN,IMIN) = DLTLIM(KMIN,IMIN)+1.0

!** Layer bottom and middle depths

    DO JW=1,NWB
      DO JB=BS(JW),BE(JW)
        DO I=CUS(JB)-1,DS(JB)
          DEPTHB(KTWB(JW),I) = H1(KTWB(JW),I)
          DEPTHM(KTWB(JW),I) = H1(KTWB(JW),I)*0.5D0
             if(kbi(i) < kb(i)  .and. (el(kbi(i)+1,i)-el(kb(i)+1,i))/COSA(JB) <  h1(ktwb(jw),i))then   ! SW 7/22/10 if h1 < elev diff this means depth is below the bottom - if we ignore that the run will continue but if dpethb is negative it will bomb in computing DECAY
             depthb(ktwb(jw),i)= h1(ktwb(jw),i)-(el(kbi(i)+1,i)-el(kb(i)+1,i))/COSA(JB)    ! SW 1/23/06
             depthm(ktwb(jw),i)=(h1(ktwb(jw),i)-(el(kbi(i)+1,i)-el(kb(i)+1,i))/COSA(JB))*0.5D0   
             endif
          DO K=KTWB(JW)+1,KMX
            DEPTHB(K,I) = DEPTHB(K-1,I)+ H1(K,I)
            DEPTHM(K,I) = DEPTHM(K-1,I)+(H1(K-1,I)+H1(K,I))*0.5D0
          END DO
        END DO
      END DO
    END DO

! CHECK FOR DYNAMIC PIPE ADJUSTMENT SW 2/18/2020
      IF(NPI>0)THEN     ! SW 12/20/2020
        IF(DYNPAD=='ON'.AND.dynpipe(DYNPAD_PIPE) == '      ON')THEN    ! CHECK FOR WL VIOLATIONS
        IF(ELWS(DYNPAD_SEG)<DYNPAD_WL)THEN
            IF(DYNPAD_MAXRATE < (Z(DYNPAD_SEG)-SZ(DYNPAD_SEG))/DLT)THEN
                BP(DYNPAD_PIPE)=BP(DYNPAD_PIPE)*(1.+DYNPAD_PERCENTCHANGE/100.)
                 IF(BP(DYNPAD_PIPE)<=0.0)BP(DYNPAD_PIPE)=DYNPAD_PERCENTCHANGE/100.
                 IF(BP(DYNPAD_PIPE)>=1.0)BP(DYNPAD_PIPE)=1.0
                 WRITE(DYNPIPELOG,'(F9.3,",",4(F10.4,","),e12.4,",")')JDAY,BP(DYNPAD_PIPE),Z(DYNPAD_SEG),SZ(DYNPAD_SEG),DLT,(Z(DYNPAD_SEG)-SZ(DYNPAD_SEG))/DLT
            ENDIF
        ENDIF
        ENDIF
      ENDIF
! END DYN PIPE ADJUSTMENT
        
CALL temperature

! Stage 3 removes the water-quality runtime entry point from the reduced build.

! update vertical momemntum and diffusivity for next time step
!    DO JW=1,NWB
!      KT = KTWB(JW)
!      DO JB=BS(JW),BE(JW)
!        IF(BR_INACTIVE(JB))CYCLE    ! SW 6/12/17
!        IUT = CUS(JB)
!        IDT = DS(JB)
!
!      !****** Vertical eddy viscosities/diffusivities   -moved from earlier in the code since TKE relies on BH1/BH2 time dependent
!
!        IF (AZC(JW) == '     TKE'.OR.AZC(JW) == '    TKE1') THEN
!          AZT(:,IDT-1)  = AZ(:,IDT-1)
!          DO I=IUT,IDT-2
!            DO K=KT,KBMIN(I)
!              AZT(K,I)  = 0.5*(AZ(K,I)+AZ(K,I+1))
!            END DO
!          AZ(KBMIN(I),I) = AZMIN              !SG 10/4/07 SW 10/4/07
!          END DO
!          AZ(KT:KMX-1,IUT:IDT-1)=AZT(KT:KMX-1,IUT:IDT-1)
!        END IF
!        DO JWR=1,NIW
!        IF (WEIR_CALC) AZ(KTWR(JWR)-1:KBWR(JWR),IWR(1:NIW)) = 0.0
!        END DO
!
!!****** Average eddy diffusivities
!
!        IF(AZC(JW) /= '     TKE'.AND.AZC(JW) /= '    TKE1')THEN
!        DZ(KT:KB(IDT)-1,IDT) = DZT(KT:KB(IDT)-1,IDT-1)    ! DZT is only used for non-TKE algorithms
!        ELSE
!        DZ(KT:KB(IDT)-1,IDT) = DZ(KT:KB(IDT)-1,IDT-1)
!        ENDIF
!        DO I=IUT,IDT-1
!          DO K=KT,KB(I)-1
!            IF (K >= KBMIN(I)) THEN
!              IF (KB(I-1) >= KB(I) .AND. I /= IUT) THEN
!                DZ(K,I) = DZ(K,I-1)
!              ELSE
!                DZ(K,I) = DZMIN
!              END IF
!            ELSE
!              IF(AZC(JW) /= '     TKE'.AND.AZC(JW) /= '    TKE1')THEN
!                 IF(I == IUT)THEN                             ! SW 10/20/07
!                    DZ(K,I)=DZT(K,I)
!                 ELSE
!                    DZ(K,I) = (DZT(K,I)+DZT(K,I-1))*0.5D0        ! SW 10/20/07  (DZT(K,I)+DZT(K+1,I))*0.5 ! FOR NON-TKE ALGORITHMS, AVERAGE DZ FROM EDGES TO CELL CENTERS
!                 ENDIF
!              ENDIF
!            END IF
!          END DO
!        END DO
!
!! Hypolimnetic aeration
!
!        IF(AERATEC == '      ON' .and. oxygen_demand)THEN
!            DO I=IUT,IDT
!             DO II=1,NAER
!                 IF(I==IASEG(II))THEN
!                     DZ(KTOPA(II):KBOTA(II),IASEG(II))=DZ(KTOPA(II):KBOTA(II),IASEG(II))*DZMULT(KTOPA(II):KBOTA(II),IASEG(II))
!                 ENDIF
!             ENDDO
!            ENDDO
!        ENDIF     
!
!
!!****** Density inversions
!
!        DO I=IUT,IDT
!          DO K=KT,KB(I)-1
!            DZQ(K,I) = MIN(1.0D-2,DZ(K,I))                                    !MIN(1.0E-4,DZ(K,I)) No reason to limit DZ in rivers/estuaries-used in ULTIMATE scheme
!             IF (RHO(K,I) > RHO(K+1,I)) THEN
!                 IF(DZMAX > 0.0)THEN
!                     DZ(K,I) = DZMAX
!                 ELSE
!                     DZ(K,I) = DZ(K,I)*ABS(DZMAX)    !    CHANGE dzmax TO A MULTIPLIER IF ENETERED AS A NEGATIVE #
!                 ENDIF
!             ENDIF
!          END DO
!        END DO
!      ENDDO
!    ENDDO

!IF(PLUNGEPT)Call Plunge_Point

CALL LAYERADDSUB
if(error_open)go to 230

CALL BALANCES

CALL UPDATE

IF (JDAY.GE.NXTMTS.OR.JDAY.GE.TSRD(TSRDP+1).or.nit==1) THEN       ! OUTPUT AT FREQUENCY OF TSR FILES
! Reduced build does not emit aeration output.
ENDIF                                                             ! OUTPUT AT FREQUENCY OF TSR FILES


CALL OUTPUTA
!**** Screen output
DO JW=1,NWB
      IF (SCREEN_OUTPUT(JW)) THEN
        IF (JDAY >= NXTMSC(JW) .OR. JDAY >= SCRD(SCRDP(JW)+1,JW)) THEN
          IF (JDAY >= SCRD(SCRDP(JW)+1,JW)) THEN
            SCRDP(JW)  = SCRDP(JW)+1
            NXTMSC(JW) = SCRD(SCRDP(JW),JW)
          END IF
          KT         = KTWB(JW)
          NXTMSC(JW) = NXTMSC(JW)+SCRF(SCRDP(JW),JW)
          WRITE(*,'(A,I0,A,F0.2)') 'Screen checkpoint | WB=', JW, ' | JDAY=', JDAY
          CALL DATE_AND_TIME (CDATE,CCTIME)
 !         DO JH=1,NHY
 !           IF (HYDRO_PLOT(JH))       CALL GRAPH_UPDATE (JH,HYD(:,:,JH),     HNAME(JH), HYMIN(JH),1.0,       LNAME(JH))
 !         END DO
 !         DO JC=1,NCT
 !           IF (CONSTITUENT_PLOT(JC)) CALL GRAPH_UPDATE (JH+JC,C2(:,:,JC),   CNAME(JC), CMIN(JC), CMULT(JC), LNAME(JH+JC))
 !         END DO
 !         DO JD=1,NDC
 !           IF (DERIVED_PLOT(JD))     CALL GRAPH_UPDATE (JH+JC+JD,CD(:,:,JD),CDNAME(JD),CDMIN(JD),CDMULT(JD),LNAME(JH+JC+JD))
 !         END DO
        END IF
      END IF
 END DO
RESTART_IN=.FALSE.   ! SW 6/29/2025
END DO    ! END OF MAIN DO WHILE LOOP

230 CONTINUE
  IF (STOP_PUSHED_LOCAL) THEN
    STATUS_TEXT  = 'Execution stopped at '//CCTIME(1:2)//':'//CCTIME(3:4)//':'//CCTIME(5:6)//' on '//CDATE(5:6)//'/'//CDATE(7:8)//'/'        &
                                          //CDATE(3:4)
    CALL RESTART_OUTPUT ('rso.opt')
  END IF

IF(END_RUN .and. RESTART_OUT)CALL RESTART_OUTPUT ('rso.opt')  ! cb 4/9/15 writing restart output at end of simulation if RSOC='ON'

if(.not.restart_in)then
endif

CALL ENDSIMULATION

240 CONTINUE
!  CALL DEALLOCATE_GRAPH

  if(error_open .and. len_trim(STATUS_TEXT) == 0)STATUS_TEXT  = 'W2 error - see w2.err. Execution stopped at '//CCTIME(1:2)//':'//CCTIME(3:4)//':'//CCTIME(5:6)//' on '//CDATE(5:6)//'/'//CDATE(7:8)//'/'        &
                                          //CDATE(3:4)            ! SW 6/30/2025

  IF (LEN_TRIM(STATUS_TEXT) > 0) THEN
    WRITE(*,'(A)') TRIM(STATUS_TEXT)
  ELSEIF (END_RUN) THEN
    WRITE(*,'(A)') 'Execution finished.'
  END IF

CONTAINS

  SUBROUTINE INITIALIZE_TAIL_SEGMENT_STORAGE()
    IF (.NOT. ALLOCATED(TAIL_STAGE_SEG)) ALLOCATE( &
      TAIL_STAGE_SEG(MAX_TAIL_SEG,NBR), TAIL_DEPTH_SEG(MAX_TAIL_SEG,NBR), TAIL_AREA_SEG(MAX_TAIL_SEG,NBR))
    IF (.NOT. ALLOCATED(TAIL_HRAD_SEG)) ALLOCATE( &
      TAIL_HRAD_SEG(MAX_TAIL_SEG,NBR), TAIL_VOL_SEG(MAX_TAIL_SEG,NBR))
    IF (.NOT. ALLOCATED(TAIL_Q_SEG)) ALLOCATE( &
      TAIL_Q_SEG(MAX_TAIL_SEG,NBR), TAIL_Q_TARGET_SEG(MAX_TAIL_SEG,NBR))
    IF (.NOT. ALLOCATED(TAIL_TRAVEL_TIME_SEG)) ALLOCATE( &
      TAIL_TRAVEL_TIME_SEG(MAX_TAIL_SEG,NBR), TAIL_CELERITY_SEG(MAX_TAIL_SEG,NBR))
    IF (.NOT. ALLOCATED(TAIL_SEG_VALID)) ALLOCATE(TAIL_SEG_VALID(MAX_TAIL_SEG,NBR))
    IF (.NOT. ALLOCATED(TAIL_TRANSITION_SEG)) ALLOCATE(TAIL_TRANSITION_SEG(MAX_TAIL_SEG,NBR), TAIL_SUBMERGENCE_SEG(MAX_TAIL_SEG,NBR), TAIL_LOCAL_SLOPE_SEG(MAX_TAIL_SEG,NBR), TAIL_FROUDE_SEG(MAX_TAIL_SEG,NBR))
    IF (.NOT. ALLOCATED(TAIL_MODE_SEG)) ALLOCATE(TAIL_MODE_SEG(MAX_TAIL_SEG,NBR))
    TAIL_STAGE_SEG = 0.0D0
    TAIL_DEPTH_SEG = 0.0D0
    TAIL_AREA_SEG = 0.0D0
    TAIL_HRAD_SEG = 0.0D0
    TAIL_VOL_SEG = 0.0D0
    TAIL_Q_SEG = 0.0D0
    TAIL_Q_TARGET_SEG = 0.0D0
    TAIL_TRAVEL_TIME_SEG = 0.0D0
    TAIL_CELERITY_SEG = 0.0D0
    TAIL_SEG_VALID = .FALSE.
    TAIL_TRANSITION_SEG = 0.0D0
    TAIL_SUBMERGENCE_SEG = 0.0D0
    TAIL_LOCAL_SLOPE_SEG = 0.0D0
    TAIL_FROUDE_SEG = 0.0D0
    TAIL_MODE_SEG = 0
  END SUBROUTINE INITIALIZE_TAIL_SEGMENT_STORAGE

  SUBROUTINE SAVE_TAIL_DYNAMIC_STATE()
    TAIL_WSE_UP_SAVE = TAIL_WSE_UP
    TAIL_WSE_DN_SAVE = TAIL_WSE_DN
    TAIL_Q_LINK_SAVE = TAIL_Q_LINK
    TAIL_DEPTH_UP_SAVE = TAIL_DEPTH_UP
    TAIL_STORAGE_VOL_SAVE = TAIL_STORAGE_VOL
    TAIL_Q_INFLOW_SAVE = TAIL_Q_INFLOW
    TAIL_Q_OUTFLOW_SAVE = TAIL_Q_OUTFLOW
    TAIL_Q_STATE_SAVE = TAIL_Q_STATE
    TAIL_Q_TARGET_SAVE = TAIL_Q_TARGET
    TAIL_TRAVEL_TIME_SAVE = TAIL_TRAVEL_TIME
    TAIL_WAVE_CELERITY_SAVE = TAIL_WAVE_CELERITY
    TAIL_REACH_LENGTH_SAVE = TAIL_REACH_LENGTH
    TAIL_TRANSITION_STATE_SAVE = TAIL_TRANSITION_STATE
    TAIL_SUBMERGENCE_SAVE = TAIL_SUBMERGENCE
    TAIL_LOCAL_SLOPE_SAVE = TAIL_LOCAL_SLOPE
    TAIL_FROUDE_SAVE = TAIL_FROUDE
    TAIL_STAGE_MODE_SAVE = TAIL_STAGE_MODE
    TAIL_CONTROL_MODE_SAVE = TAIL_CONTROL_MODE
    TAIL_STAGE_VALID_SAVE = TAIL_STAGE_VALID
    TAIL_REACH_INITIALIZED_SAVE = TAIL_REACH_INITIALIZED
    TAIL_Q_STATE_INITIALIZED_SAVE = TAIL_Q_STATE_INITIALIZED
    TAIL_STAGE_SEG_SAVE = TAIL_STAGE_SEG
    TAIL_DEPTH_SEG_SAVE = TAIL_DEPTH_SEG
    TAIL_AREA_SEG_SAVE = TAIL_AREA_SEG
    TAIL_HRAD_SEG_SAVE = TAIL_HRAD_SEG
    TAIL_VOL_SEG_SAVE = TAIL_VOL_SEG
    TAIL_Q_SEG_SAVE = TAIL_Q_SEG
    TAIL_Q_TARGET_SEG_SAVE = TAIL_Q_TARGET_SEG
    TAIL_TRAVEL_TIME_SEG_SAVE = TAIL_TRAVEL_TIME_SEG
    TAIL_CELERITY_SEG_SAVE = TAIL_CELERITY_SEG
    TAIL_TRANSITION_SEG_SAVE = TAIL_TRANSITION_SEG
    TAIL_SUBMERGENCE_SEG_SAVE = TAIL_SUBMERGENCE_SEG
    TAIL_LOCAL_SLOPE_SEG_SAVE = TAIL_LOCAL_SLOPE_SEG
    TAIL_FROUDE_SEG_SAVE = TAIL_FROUDE_SEG
    TAIL_MODE_SEG_SAVE = TAIL_MODE_SEG
    TAIL_SEG_VALID_SAVE = TAIL_SEG_VALID
  END SUBROUTINE SAVE_TAIL_DYNAMIC_STATE

  SUBROUTINE RESTORE_TAIL_DYNAMIC_STATE()
    TAIL_WSE_UP = TAIL_WSE_UP_SAVE
    TAIL_WSE_DN = TAIL_WSE_DN_SAVE
    TAIL_Q_LINK = TAIL_Q_LINK_SAVE
    TAIL_DEPTH_UP = TAIL_DEPTH_UP_SAVE
    TAIL_STORAGE_VOL = TAIL_STORAGE_VOL_SAVE
    TAIL_Q_INFLOW = TAIL_Q_INFLOW_SAVE
    TAIL_Q_OUTFLOW = TAIL_Q_OUTFLOW_SAVE
    TAIL_Q_STATE = TAIL_Q_STATE_SAVE
    TAIL_Q_TARGET = TAIL_Q_TARGET_SAVE
    TAIL_TRAVEL_TIME = TAIL_TRAVEL_TIME_SAVE
    TAIL_WAVE_CELERITY = TAIL_WAVE_CELERITY_SAVE
    TAIL_REACH_LENGTH = TAIL_REACH_LENGTH_SAVE
    TAIL_TRANSITION_STATE = TAIL_TRANSITION_STATE_SAVE
    TAIL_SUBMERGENCE = TAIL_SUBMERGENCE_SAVE
    TAIL_LOCAL_SLOPE = TAIL_LOCAL_SLOPE_SAVE
    TAIL_FROUDE = TAIL_FROUDE_SAVE
    TAIL_STAGE_MODE = TAIL_STAGE_MODE_SAVE
    TAIL_CONTROL_MODE = TAIL_CONTROL_MODE_SAVE
    TAIL_STAGE_VALID = TAIL_STAGE_VALID_SAVE
    TAIL_REACH_INITIALIZED = TAIL_REACH_INITIALIZED_SAVE
    TAIL_Q_STATE_INITIALIZED = TAIL_Q_STATE_INITIALIZED_SAVE
    TAIL_STAGE_SEG = TAIL_STAGE_SEG_SAVE
    TAIL_DEPTH_SEG = TAIL_DEPTH_SEG_SAVE
    TAIL_AREA_SEG = TAIL_AREA_SEG_SAVE
    TAIL_HRAD_SEG = TAIL_HRAD_SEG_SAVE
    TAIL_VOL_SEG = TAIL_VOL_SEG_SAVE
    TAIL_Q_SEG = TAIL_Q_SEG_SAVE
    TAIL_Q_TARGET_SEG = TAIL_Q_TARGET_SEG_SAVE
    TAIL_TRAVEL_TIME_SEG = TAIL_TRAVEL_TIME_SEG_SAVE
    TAIL_CELERITY_SEG = TAIL_CELERITY_SEG_SAVE
    TAIL_TRANSITION_SEG = TAIL_TRANSITION_SEG_SAVE
    TAIL_SUBMERGENCE_SEG = TAIL_SUBMERGENCE_SEG_SAVE
    TAIL_LOCAL_SLOPE_SEG = TAIL_LOCAL_SLOPE_SEG_SAVE
    TAIL_FROUDE_SEG = TAIL_FROUDE_SEG_SAVE
    TAIL_MODE_SEG = TAIL_MODE_SEG_SAVE
    TAIL_SEG_VALID = TAIL_SEG_VALID_SAVE
  END SUBROUTINE RESTORE_TAIL_DYNAMIC_STATE

  SUBROUTINE RUN_TAIL_INTERFACE_ITERATION(JB_IN, JW_IN)
    INTEGER, INTENT(IN) :: JB_IN, JW_IN
    INTEGER :: ITER, NSEG
    REAL(R8) :: ETA_TARGET, ETA_GUESS, Q_GUESS, PREV_RESID, CURR_RESID, RELAX_LOCAL
    REAL(R8) :: ETA_PREV_GUESS, Q_PREV_GUESS, DETA_PREV, DQ_PREV
    REAL(R8) :: ETA_STEP, Q_STEP, ETA_STEP_RELAX, Q_STEP_RELAX, ETA_STEP_SECANT, Q_STEP_SECANT
    REAL(R8) :: DENOM_ETA, DENOM_Q, ETA_CAP, Q_CAP
    REAL(R8) :: WSE_UP_BASE, WSE_DN_BASE, Q_LINK_BASE, DEPTH_UP_BASE
    REAL(R8) :: STORAGE_VOL_BASE, Q_INFLOW_BASE, Q_OUTFLOW_BASE, Q_STATE_BASE, Q_TARGET_BASE
    REAL(R8) :: TRAVEL_TIME_BASE, WAVE_CELERITY_BASE, REACH_LENGTH_BASE
    REAL(R8) :: TRANSITION_STATE_BASE, SUBMERGENCE_BASE, LOCAL_SLOPE_BASE, FROUDE_BASE
    REAL(R8) :: STAGE_SEG_BASE(MAX_TAIL_SEG), DEPTH_SEG_BASE(MAX_TAIL_SEG), AREA_SEG_BASE(MAX_TAIL_SEG)
    REAL(R8) :: HRAD_SEG_BASE(MAX_TAIL_SEG), VOL_SEG_BASE(MAX_TAIL_SEG)
    REAL(R8) :: Q_SEG_BASE(MAX_TAIL_SEG), Q_TARGET_SEG_BASE(MAX_TAIL_SEG)
    REAL(R8) :: TRAVEL_TIME_SEG_BASE(MAX_TAIL_SEG), CELERITY_SEG_BASE(MAX_TAIL_SEG)
    REAL(R8) :: TRANSITION_SEG_BASE(MAX_TAIL_SEG), SUBMERGENCE_SEG_BASE(MAX_TAIL_SEG)
    REAL(R8) :: LOCAL_SLOPE_SEG_BASE(MAX_TAIL_SEG), FROUDE_SEG_BASE(MAX_TAIL_SEG)
    INTEGER :: STAGE_MODE_BASE, CONTROL_MODE_BASE, MODE_SEG_BASE(MAX_TAIL_SEG)
    LOGICAL :: STAGE_VALID_BASE, REACH_INITIALIZED_BASE, Q_STATE_INITIALIZED_BASE
    LOGICAL :: SEG_VALID_BASE(MAX_TAIL_SEG)

    IF (.NOT. TAIL_COUPLED(JB_IN)) RETURN
    IF (TAIL_UPSEG(JB_IN) <= 0 .OR. TAIL_DNSEG(JB_IN) <= 0) RETURN

    NSEG = MAX(1, MIN(MAX_TAIL_SEG, TAIL_DOMAIN_NSEG(JB_IN)))
    ETA_TARGET = ELWS(TAIL_DNSEG(JB_IN))
    ETA_GUESS = TAIL_IFACE_ETA_PRED(JB_IN)
    Q_GUESS = MAX(TAIL_IFACE_Q_PRED(JB_IN), 0.0D0)
    ETA_PREV_GUESS = ETA_GUESS
    Q_PREV_GUESS = Q_GUESS
    DETA_PREV = 0.0D0
    DQ_PREV = 0.0D0
    RELAX_LOCAL = MIN(MAX(TAIL_IFACE_RELAX(JB_IN), TAIL_IFACE_RELAX_MIN), TAIL_IFACE_RELAX_MAX)
    IF (RELAX_LOCAL <= 0.0D0) RELAX_LOCAL = 0.50D0

    WSE_UP_BASE = TAIL_WSE_UP(JB_IN)
    WSE_DN_BASE = TAIL_WSE_DN(JB_IN)
    Q_LINK_BASE = TAIL_Q_LINK(JB_IN)
    DEPTH_UP_BASE = TAIL_DEPTH_UP(JB_IN)
    STORAGE_VOL_BASE = TAIL_STORAGE_VOL(JB_IN)
    Q_INFLOW_BASE = TAIL_Q_INFLOW(JB_IN)
    Q_OUTFLOW_BASE = TAIL_Q_OUTFLOW(JB_IN)
    Q_STATE_BASE = TAIL_Q_STATE(JB_IN)
    Q_TARGET_BASE = TAIL_Q_TARGET(JB_IN)
    TRAVEL_TIME_BASE = TAIL_TRAVEL_TIME(JB_IN)
    WAVE_CELERITY_BASE = TAIL_WAVE_CELERITY(JB_IN)
    REACH_LENGTH_BASE = TAIL_REACH_LENGTH(JB_IN)
    TRANSITION_STATE_BASE = TAIL_TRANSITION_STATE(JB_IN)
    SUBMERGENCE_BASE = TAIL_SUBMERGENCE(JB_IN)
    LOCAL_SLOPE_BASE = TAIL_LOCAL_SLOPE(JB_IN)
    FROUDE_BASE = TAIL_FROUDE(JB_IN)
    STAGE_MODE_BASE = TAIL_STAGE_MODE(JB_IN)
    CONTROL_MODE_BASE = TAIL_CONTROL_MODE(JB_IN)
    STAGE_VALID_BASE = TAIL_STAGE_VALID(JB_IN)
    REACH_INITIALIZED_BASE = TAIL_REACH_INITIALIZED(JB_IN)
    Q_STATE_INITIALIZED_BASE = TAIL_Q_STATE_INITIALIZED(JB_IN)
    STAGE_SEG_BASE(1:NSEG) = TAIL_STAGE_SEG(1:NSEG,JB_IN)
    DEPTH_SEG_BASE(1:NSEG) = TAIL_DEPTH_SEG(1:NSEG,JB_IN)
    AREA_SEG_BASE(1:NSEG) = TAIL_AREA_SEG(1:NSEG,JB_IN)
    HRAD_SEG_BASE(1:NSEG) = TAIL_HRAD_SEG(1:NSEG,JB_IN)
    VOL_SEG_BASE(1:NSEG) = TAIL_VOL_SEG(1:NSEG,JB_IN)
    Q_SEG_BASE(1:NSEG) = TAIL_Q_SEG(1:NSEG,JB_IN)
    Q_TARGET_SEG_BASE(1:NSEG) = TAIL_Q_TARGET_SEG(1:NSEG,JB_IN)
    TRAVEL_TIME_SEG_BASE(1:NSEG) = TAIL_TRAVEL_TIME_SEG(1:NSEG,JB_IN)
    CELERITY_SEG_BASE(1:NSEG) = TAIL_CELERITY_SEG(1:NSEG,JB_IN)
    TRANSITION_SEG_BASE(1:NSEG) = TAIL_TRANSITION_SEG(1:NSEG,JB_IN)
    SUBMERGENCE_SEG_BASE(1:NSEG) = TAIL_SUBMERGENCE_SEG(1:NSEG,JB_IN)
    LOCAL_SLOPE_SEG_BASE(1:NSEG) = TAIL_LOCAL_SLOPE_SEG(1:NSEG,JB_IN)
    FROUDE_SEG_BASE(1:NSEG) = TAIL_FROUDE_SEG(1:NSEG,JB_IN)
    MODE_SEG_BASE(1:NSEG) = TAIL_MODE_SEG(1:NSEG,JB_IN)
    SEG_VALID_BASE(1:NSEG) = TAIL_SEG_VALID(1:NSEG,JB_IN)

    TAIL_IFACE_ITER_COUNT(JB_IN) = 0
    TAIL_IFACE_CONVERGED(JB_IN) = .FALSE.
    TAIL_IFACE_ETA_GUESS(JB_IN) = ETA_GUESS
    TAIL_IFACE_Q_GUESS(JB_IN) = Q_GUESS
    TAIL_IFACE_ETA_PREV(JB_IN) = ETA_PREV_GUESS
    TAIL_IFACE_Q_PREV(JB_IN) = Q_PREV_GUESS
    TAIL_IFACE_DETA_STEP(JB_IN) = 0.0D0
    TAIL_IFACE_DQ_STEP(JB_IN) = 0.0D0
    PREV_RESID = HUGE(1.0D0)

    DO ITER=1,TAIL_IFACE_MAX_ITERS
      TAIL_WSE_UP(JB_IN) = WSE_UP_BASE
      TAIL_WSE_DN(JB_IN) = WSE_DN_BASE
      TAIL_Q_LINK(JB_IN) = Q_LINK_BASE
      TAIL_DEPTH_UP(JB_IN) = DEPTH_UP_BASE
      TAIL_STORAGE_VOL(JB_IN) = STORAGE_VOL_BASE
      TAIL_Q_INFLOW(JB_IN) = Q_INFLOW_BASE
      TAIL_Q_OUTFLOW(JB_IN) = Q_OUTFLOW_BASE
      TAIL_Q_STATE(JB_IN) = MAX(Q_GUESS, 0.0D0)
      TAIL_Q_TARGET(JB_IN) = MAX(Q_GUESS, 0.0D0)
      TAIL_TRAVEL_TIME(JB_IN) = TRAVEL_TIME_BASE
      TAIL_WAVE_CELERITY(JB_IN) = WAVE_CELERITY_BASE
      TAIL_REACH_LENGTH(JB_IN) = REACH_LENGTH_BASE
      TAIL_TRANSITION_STATE(JB_IN) = TRANSITION_STATE_BASE
      TAIL_SUBMERGENCE(JB_IN) = SUBMERGENCE_BASE
      TAIL_LOCAL_SLOPE(JB_IN) = LOCAL_SLOPE_BASE
      TAIL_FROUDE(JB_IN) = FROUDE_BASE
      TAIL_STAGE_MODE(JB_IN) = STAGE_MODE_BASE
      TAIL_CONTROL_MODE(JB_IN) = CONTROL_MODE_BASE
      TAIL_STAGE_VALID(JB_IN) = STAGE_VALID_BASE
      TAIL_REACH_INITIALIZED(JB_IN) = REACH_INITIALIZED_BASE
      TAIL_Q_STATE_INITIALIZED(JB_IN) = .TRUE.
      TAIL_STAGE_SEG(1:NSEG,JB_IN) = STAGE_SEG_BASE(1:NSEG)
      TAIL_DEPTH_SEG(1:NSEG,JB_IN) = DEPTH_SEG_BASE(1:NSEG)
      TAIL_AREA_SEG(1:NSEG,JB_IN) = AREA_SEG_BASE(1:NSEG)
      TAIL_HRAD_SEG(1:NSEG,JB_IN) = HRAD_SEG_BASE(1:NSEG)
      TAIL_VOL_SEG(1:NSEG,JB_IN) = VOL_SEG_BASE(1:NSEG)
      TAIL_Q_SEG(1:NSEG,JB_IN) = Q_SEG_BASE(1:NSEG)
      TAIL_Q_TARGET_SEG(1:NSEG,JB_IN) = Q_TARGET_SEG_BASE(1:NSEG)
      TAIL_TRAVEL_TIME_SEG(1:NSEG,JB_IN) = TRAVEL_TIME_SEG_BASE(1:NSEG)
      TAIL_CELERITY_SEG(1:NSEG,JB_IN) = CELERITY_SEG_BASE(1:NSEG)
      TAIL_TRANSITION_SEG(1:NSEG,JB_IN) = TRANSITION_SEG_BASE(1:NSEG)
      TAIL_SUBMERGENCE_SEG(1:NSEG,JB_IN) = SUBMERGENCE_SEG_BASE(1:NSEG)
      TAIL_LOCAL_SLOPE_SEG(1:NSEG,JB_IN) = LOCAL_SLOPE_SEG_BASE(1:NSEG)
      TAIL_FROUDE_SEG(1:NSEG,JB_IN) = FROUDE_SEG_BASE(1:NSEG)
      TAIL_MODE_SEG(1:NSEG,JB_IN) = MODE_SEG_BASE(1:NSEG)
      TAIL_SEG_VALID(1:NSEG,JB_IN) = SEG_VALID_BASE(1:NSEG)

      CALL UPDATE_TAIL_STAGE(JB_IN, JW_IN, ETA_GUESS)
      TAIL_WSE_DN(JB_IN) = ETA_TARGET
      TAIL_IFACE_ETA_CORR(JB_IN) = ETA_TARGET
      TAIL_IFACE_Q_CORR(JB_IN) = TAIL_Q_LINK(JB_IN)
      TAIL_IFACE_DETA(JB_IN) = ETA_TARGET - ETA_GUESS
      TAIL_IFACE_DQ(JB_IN) = TAIL_IFACE_Q_CORR(JB_IN) - Q_GUESS
      TAIL_IFACE_MAX_DETA(JB_IN) = MAX(TAIL_IFACE_MAX_DETA(JB_IN), ABS(TAIL_IFACE_DETA(JB_IN)))
      TAIL_IFACE_MAX_DQ(JB_IN) = MAX(TAIL_IFACE_MAX_DQ(JB_IN), ABS(TAIL_IFACE_DQ(JB_IN)))
      TAIL_IFACE_ITER_COUNT(JB_IN) = ITER
      TAIL_IFACE_CONVERGED(JB_IN) = ABS(TAIL_IFACE_DETA(JB_IN)) < TAIL_IFACE_ETA_TOL .AND. &
                                    ABS(TAIL_IFACE_DQ(JB_IN)) < TAIL_IFACE_Q_TOL
      TAIL_IFACE_RELAX(JB_IN) = RELAX_LOCAL

      IF (NIT <= 10 .OR. ITER == 1 .OR. TAIL_IFACE_CONVERGED(JB_IN) .OR. MOD(NIT,500) == 0) THEN
        WARNING_OPEN = .TRUE.
        WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,ES12.4,1X,A,ES12.4,1X,A,F0.3,1X,A,L1)') '[V20_INTERFACE_ITER]', &
          'JB=',JB_IN, 'ITER=',ITER, 'DETA=',TAIL_IFACE_DETA(JB_IN), 'DQ=',TAIL_IFACE_DQ(JB_IN), &
          'RELAX=',RELAX_LOCAL, 'CONV=',TAIL_IFACE_CONVERGED(JB_IN)
      END IF

      IF (TAIL_IFACE_CONVERGED(JB_IN)) EXIT

      CURR_RESID = MAX(ABS(TAIL_IFACE_DETA(JB_IN))/MAX(TAIL_IFACE_ETA_TOL, 1.0D-12), &
                       ABS(TAIL_IFACE_DQ(JB_IN))/MAX(TAIL_IFACE_Q_TOL, 1.0D-12))
      IF (ITER > 1) THEN
        IF (CURR_RESID > 0.95D0*PREV_RESID) RELAX_LOCAL = MAX(TAIL_IFACE_RELAX_MIN, 0.50D0*RELAX_LOCAL)
        IF (CURR_RESID < 0.50D0*PREV_RESID) RELAX_LOCAL = MIN(TAIL_IFACE_RELAX_MAX, 1.10D0*RELAX_LOCAL)
      END IF

      ETA_STEP_RELAX = RELAX_LOCAL*TAIL_IFACE_DETA(JB_IN)
      Q_STEP_RELAX = RELAX_LOCAL*TAIL_IFACE_DQ(JB_IN)
      ETA_STEP = ETA_STEP_RELAX
      Q_STEP = Q_STEP_RELAX
      ETA_CAP = MAX(ABS(ETA_STEP_RELAX), 0.05D0)
      Q_CAP = MAX(ABS(Q_STEP_RELAX), 25.0D0)

      IF (ITER > 1) THEN
        DENOM_ETA = TAIL_IFACE_DETA(JB_IN) - DETA_PREV
        IF (ABS(DENOM_ETA) > 1.0D-10) THEN
          ETA_STEP_SECANT = -TAIL_IFACE_DETA(JB_IN) * (ETA_GUESS - ETA_PREV_GUESS) / DENOM_ETA
          ETA_STEP = MAX(-2.0D0*ETA_CAP, MIN(2.0D0*ETA_CAP, ETA_STEP_SECANT))
        END IF
        DENOM_Q = TAIL_IFACE_DQ(JB_IN) - DQ_PREV
        IF (ABS(DENOM_Q) > 1.0D-8) THEN
          Q_STEP_SECANT = -TAIL_IFACE_DQ(JB_IN) * (Q_GUESS - Q_PREV_GUESS) / DENOM_Q
          Q_STEP = MAX(-2.0D0*Q_CAP, MIN(2.0D0*Q_CAP, Q_STEP_SECANT))
        END IF
      END IF

      TAIL_IFACE_ETA_PREV(JB_IN) = ETA_GUESS
      TAIL_IFACE_Q_PREV(JB_IN) = Q_GUESS
      TAIL_IFACE_DETA_STEP(JB_IN) = ETA_STEP
      TAIL_IFACE_DQ_STEP(JB_IN) = Q_STEP
      TAIL_IFACE_ETA_GUESS(JB_IN) = ETA_GUESS + ETA_STEP
      TAIL_IFACE_Q_GUESS(JB_IN) = MAX(0.0D0, Q_GUESS + Q_STEP)

      IF (NIT <= 10 .OR. ITER == 1 .OR. TAIL_IFACE_CONVERGED(JB_IN) .OR. MOD(NIT,500) == 0) THEN
        WARNING_OPEN = .TRUE.
        WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,ES12.4,1X,A,ES12.4,1X,A,F0.3,1X,A,F0.3)') '[V21_INTERFACE_SOLVE]', &
          'JB=',JB_IN, 'ITER=',ITER, 'DETA_STEP=',TAIL_IFACE_DETA_STEP(JB_IN), 'DQ_STEP=',TAIL_IFACE_DQ_STEP(JB_IN), &
          'ETA=',TAIL_IFACE_ETA_GUESS(JB_IN), 'Q=',TAIL_IFACE_Q_GUESS(JB_IN)
      END IF

      PREV_RESID = CURR_RESID
      ETA_PREV_GUESS = ETA_GUESS
      Q_PREV_GUESS = Q_GUESS
      DETA_PREV = TAIL_IFACE_DETA(JB_IN)
      DQ_PREV = TAIL_IFACE_DQ(JB_IN)
      ETA_GUESS = TAIL_IFACE_ETA_GUESS(JB_IN)
      Q_GUESS = TAIL_IFACE_Q_GUESS(JB_IN)
    END DO

    TAIL_IFACE_ETA_PRED(JB_IN) = ETA_GUESS
    TAIL_IFACE_Q_PRED(JB_IN) = Q_GUESS
    TAIL_IFACE_RELAX(JB_IN) = RELAX_LOCAL
  END SUBROUTINE RUN_TAIL_INTERFACE_ITERATION

  SUBROUTINE RUN_TAIL_PREDICTOR()
    INTEGER :: JWP, JBP
    LOGICAL :: ANY_PREDICT_COMPUTED, REUSE_PREDICTOR
    REAL(R8) :: DWSE, DQLINK

    TAIL_WSE_UP_PRED = TAIL_WSE_UP
    TAIL_Q_LINK_PRED = TAIL_Q_LINK
    TAIL_DEPTH_UP_PRED = TAIL_DEPTH_UP
    TAIL_STAGE_VALID_PRED = TAIL_STAGE_VALID
    TAIL_PREDICT_REUSED_STEP = .FALSE.
    ANY_PREDICT_COMPUTED = .FALSE.

    DO JWP=1,NWB
      DO JBP=BS(JWP),BE(JWP)
        IF (.NOT. TAIL_COUPLED(JBP)) CYCLE
        IF (TAIL_UPSEG(JBP) <= 0 .OR. TAIL_DNSEG(JBP) <= 0) CYCLE
        REUSE_PREDICTOR = .FALSE.
        IF (TAIL_PREDICT_CACHE_VALID(JBP) .AND. TAIL_STAGE_VALID(JBP)) THEN
          DWSE = ABS(TAIL_WSE_DN(JBP)-TAIL_PREDICT_WSE_DN_CACHE(JBP))
          DQLINK = ABS(TAIL_Q_LINK(JBP)-TAIL_PREDICT_QLINK_CACHE(JBP))
          IF (DWSE <= TAIL_PREDICT_WSE_TOL .AND. DQLINK <= TAIL_PREDICT_Q_TOL .AND. &
              TAIL_PREDICT_SKIP_COUNT(JBP) < TAIL_PREDICT_MAX_SKIP) THEN
            REUSE_PREDICTOR = .TRUE.
          END IF
        END IF

        IF (REUSE_PREDICTOR) THEN
          TAIL_PREDICT_REUSED_STEP(JBP) = .TRUE.
          TAIL_PREDICT_SKIP_COUNT(JBP) = TAIL_PREDICT_SKIP_COUNT(JBP)+1
          TAIL_STAGE_SEG_PRED(:,JBP) = TAIL_STAGE_SEG(:,JBP)
          TAIL_DEPTH_SEG_PRED(:,JBP) = TAIL_DEPTH_SEG(:,JBP)
          TAIL_AREA_SEG_PRED(:,JBP) = TAIL_AREA_SEG(:,JBP)
          TAIL_HRAD_SEG_PRED(:,JBP) = TAIL_HRAD_SEG(:,JBP)
          TAIL_VOL_SEG_PRED(:,JBP) = TAIL_VOL_SEG(:,JBP)
          TAIL_Q_SEG_PRED(:,JBP) = TAIL_Q_SEG(:,JBP)
          TAIL_Q_TARGET_SEG_PRED(:,JBP) = TAIL_Q_TARGET_SEG(:,JBP)
          TAIL_TRAVEL_TIME_SEG_PRED(:,JBP) = TAIL_TRAVEL_TIME_SEG(:,JBP)
          TAIL_CELERITY_SEG_PRED(:,JBP) = TAIL_CELERITY_SEG(:,JBP)
          TAIL_TRANSITION_SEG_PRED(:,JBP) = TAIL_TRANSITION_SEG(:,JBP)
          TAIL_SUBMERGENCE_SEG_PRED(:,JBP) = TAIL_SUBMERGENCE_SEG(:,JBP)
          TAIL_LOCAL_SLOPE_SEG_PRED(:,JBP) = TAIL_LOCAL_SLOPE_SEG(:,JBP)
          TAIL_FROUDE_SEG_PRED(:,JBP) = TAIL_FROUDE_SEG(:,JBP)
          TAIL_MODE_SEG_PRED(:,JBP) = TAIL_MODE_SEG(:,JBP)
          TAIL_SEG_VALID_PRED(:,JBP) = TAIL_SEG_VALID(:,JBP)
          TAIL_WSE_UP_PRED(JBP) = TAIL_WSE_UP(JBP)
          TAIL_Q_LINK_PRED(JBP) = TAIL_Q_LINK(JBP)
          TAIL_DEPTH_UP_PRED(JBP) = TAIL_DEPTH_UP(JBP)
          TAIL_STAGE_VALID_PRED(JBP) = TAIL_STAGE_VALID(JBP)
          TAIL_IFACE_ETA_PRED(JBP) = TAIL_WSE_DN(JBP)
          TAIL_IFACE_Q_PRED(JBP) = TAIL_Q_LINK(JBP)
          IF (NIT <= 10 .OR. TAIL_PREDICT_SKIP_COUNT(JBP) == 1 .OR. MOD(NIT,500) == 0) THEN
            WARNING_OPEN = .TRUE.
            WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,F0.3,1X,A,F0.3)') '[V18_PREDICT_REUSE]', &
              'JB=',JBP, 'SKIP=',TAIL_PREDICT_SKIP_COUNT(JBP), 'QLINK=',TAIL_Q_LINK(JBP), 'WSE_DN=',TAIL_WSE_DN(JBP)
          END IF
        ELSE
          TAIL_PREDICT_REUSED_STEP(JBP) = .FALSE.
          CALL UPDATE_TAIL_STAGE(JBP, JWP)
          ANY_PREDICT_COMPUTED = .TRUE.
          TAIL_PREDICT_CACHE_VALID(JBP) = .TRUE.
          TAIL_PREDICT_SKIP_COUNT(JBP) = 0
          TAIL_PREDICT_WSE_DN_CACHE(JBP) = TAIL_WSE_DN(JBP)
          TAIL_PREDICT_QLINK_CACHE(JBP) = TAIL_Q_LINK(JBP)
          TAIL_STAGE_SEG_PRED(:,JBP) = TAIL_STAGE_SEG(:,JBP)
          TAIL_DEPTH_SEG_PRED(:,JBP) = TAIL_DEPTH_SEG(:,JBP)
          TAIL_AREA_SEG_PRED(:,JBP) = TAIL_AREA_SEG(:,JBP)
          TAIL_HRAD_SEG_PRED(:,JBP) = TAIL_HRAD_SEG(:,JBP)
          TAIL_VOL_SEG_PRED(:,JBP) = TAIL_VOL_SEG(:,JBP)
          TAIL_Q_SEG_PRED(:,JBP) = TAIL_Q_SEG(:,JBP)
          TAIL_Q_TARGET_SEG_PRED(:,JBP) = TAIL_Q_TARGET_SEG(:,JBP)
          TAIL_TRAVEL_TIME_SEG_PRED(:,JBP) = TAIL_TRAVEL_TIME_SEG(:,JBP)
          TAIL_CELERITY_SEG_PRED(:,JBP) = TAIL_CELERITY_SEG(:,JBP)
          TAIL_TRANSITION_SEG_PRED(:,JBP) = TAIL_TRANSITION_SEG(:,JBP)
          TAIL_SUBMERGENCE_SEG_PRED(:,JBP) = TAIL_SUBMERGENCE_SEG(:,JBP)
          TAIL_LOCAL_SLOPE_SEG_PRED(:,JBP) = TAIL_LOCAL_SLOPE_SEG(:,JBP)
          TAIL_FROUDE_SEG_PRED(:,JBP) = TAIL_FROUDE_SEG(:,JBP)
          TAIL_MODE_SEG_PRED(:,JBP) = TAIL_MODE_SEG(:,JBP)
          TAIL_SEG_VALID_PRED(:,JBP) = TAIL_SEG_VALID(:,JBP)
          TAIL_WSE_UP_PRED(JBP) = TAIL_WSE_UP(JBP)
          TAIL_Q_LINK_PRED(JBP) = TAIL_Q_LINK(JBP)
          TAIL_DEPTH_UP_PRED(JBP) = TAIL_DEPTH_UP(JBP)
          TAIL_STAGE_VALID_PRED(JBP) = TAIL_STAGE_VALID(JBP)
          TAIL_IFACE_ETA_PRED(JBP) = TAIL_WSE_DN(JBP)
          TAIL_IFACE_Q_PRED(JBP) = TAIL_Q_LINK(JBP)
          WARNING_OPEN = .TRUE.
          WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,L1,1X,A,F0.3,1X,A,F0.3)') '[V14_COUPLED_HYBRID]', &
            'JB=',JBP, 'PASS=',1, 'COMMIT=',.FALSE., 'QLINK=',TAIL_Q_LINK(JBP), 'WSE_UP=',TAIL_WSE_UP(JBP)
          IF (NIT <= 10 .OR. MOD(NIT,500) == 0) THEN
            WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,L1,1X,A,F0.3,1X,A,F0.3)') '[V18_MULTI_HYBRID]', &
              'JB=',JBP, 'PASS=',1, 'COMMIT=',.FALSE., 'QLINK=',TAIL_Q_LINK(JBP), 'WSE_DN=',TAIL_WSE_DN(JBP)
          END IF
        END IF
      END DO
    END DO

    IF (.NOT. ANY_PREDICT_COMPUTED) RETURN

    CALL RESTORE_TAIL_DYNAMIC_STATE()

    TAIL_WSE_UP = TAIL_WSE_UP_PRED
    TAIL_Q_LINK = TAIL_Q_LINK_PRED
    TAIL_DEPTH_UP = TAIL_DEPTH_UP_PRED
    TAIL_STAGE_VALID = TAIL_STAGE_VALID_PRED
    TAIL_STAGE_SEG = TAIL_STAGE_SEG_PRED
    TAIL_DEPTH_SEG = TAIL_DEPTH_SEG_PRED
    TAIL_AREA_SEG = TAIL_AREA_SEG_PRED
    TAIL_HRAD_SEG = TAIL_HRAD_SEG_PRED
    TAIL_VOL_SEG = TAIL_VOL_SEG_PRED
    TAIL_Q_SEG = TAIL_Q_SEG_PRED
    TAIL_Q_TARGET_SEG = TAIL_Q_TARGET_SEG_PRED
    TAIL_TRAVEL_TIME_SEG = TAIL_TRAVEL_TIME_SEG_PRED
    TAIL_CELERITY_SEG = TAIL_CELERITY_SEG_PRED
    TAIL_TRANSITION_SEG = TAIL_TRANSITION_SEG_PRED
    TAIL_SUBMERGENCE_SEG = TAIL_SUBMERGENCE_SEG_PRED
    TAIL_LOCAL_SLOPE_SEG = TAIL_LOCAL_SLOPE_SEG_PRED
    TAIL_FROUDE_SEG = TAIL_FROUDE_SEG_PRED
    TAIL_MODE_SEG = TAIL_MODE_SEG_PRED
    TAIL_SEG_VALID = TAIL_SEG_VALID_PRED
  END SUBROUTINE RUN_TAIL_PREDICTOR

  SUBROUTINE INITIALIZE_TAIL_SEGMENT_STATE(JB_IN)
    INTEGER, INTENT(IN) :: JB_IN
    INTEGER :: IS, ISEG, NSEG, JW_LOC
    REAL(R8) :: STAGE_UP, STAGE_DN, STAGE_SEG, DEPTH_SEG, AREA_LOCAL, HRAD_LOCAL, FRAC
    LOGICAL :: OK

    IF (.NOT. ALLOCATED(TAIL_STAGE_SEG)) RETURN
    NSEG = MIN(MAX(TAIL_DOMAIN_NSEG(JB_IN), 0), MAX_TAIL_SEG)
    IF (NSEG <= 0) RETURN

    STAGE_UP = TAIL_WSE_UP(JB_IN)
    STAGE_DN = TAIL_WSE_DN(JB_IN)
    DO IS=1,NSEG
      ISEG = TAIL_DOMAIN_US(JB_IN) + IS - 1
      JW_LOC = MAX(1, MIN(NWB, WBSEG(ISEG)))
      FRAC = 0.0D0
      IF (NSEG > 1) FRAC = DBLE(IS-1)/DBLE(NSEG-1)
      STAGE_SEG = STAGE_UP - FRAC*(STAGE_UP-STAGE_DN)
      DEPTH_SEG = MAX(STAGE_SEG-EL(KB(ISEG)+1,ISEG), FRONT_H_MIN)
      CALL TAIL_SECTION_PROPS(ISEG, JW_LOC, STAGE_SEG, AREA_LOCAL, HRAD_LOCAL, OK)
      IF (.NOT. OK) THEN
        AREA_LOCAL = MAX(BI(KTWB(JW_LOC),ISEG)*DEPTH_SEG, 1.0D-6)
        HRAD_LOCAL = AREA_LOCAL/MAX(BI(KTWB(JW_LOC),ISEG)+2.0D0*DEPTH_SEG, 1.0D-6)
      END IF
      TAIL_STAGE_SEG(IS,JB_IN) = STAGE_SEG
      TAIL_DEPTH_SEG(IS,JB_IN) = DEPTH_SEG
      TAIL_AREA_SEG(IS,JB_IN) = AREA_LOCAL
      TAIL_HRAD_SEG(IS,JB_IN) = HRAD_LOCAL
      TAIL_VOL_SEG(IS,JB_IN) = AREA_LOCAL*DLX(ISEG)
      TAIL_Q_SEG(IS,JB_IN) = MAX(TAIL_Q_STATE(JB_IN), 0.0D0)
      TAIL_Q_TARGET_SEG(IS,JB_IN) = MAX(TAIL_Q_TARGET(JB_IN), 0.0D0)
      TAIL_CELERITY_SEG(IS,JB_IN) = SQRT(G*DEPTH_SEG)
      TAIL_TRAVEL_TIME_SEG(IS,JB_IN) = MAX(DLT, DLX(ISEG)/MAX(TAIL_CELERITY_SEG(IS,JB_IN)+1.0D-6, 1.0D-3))
      TAIL_SEG_VALID(IS,JB_IN) = .TRUE.
      TAIL_TRANSITION_SEG(IS,JB_IN) = 0.0D0
      TAIL_SUBMERGENCE_SEG(IS,JB_IN) = 0.0D0
      TAIL_LOCAL_SLOPE_SEG(IS,JB_IN) = 0.0D0
      TAIL_FROUDE_SEG(IS,JB_IN) = 0.0D0
      TAIL_MODE_SEG(IS,JB_IN) = 0
    END DO
  END SUBROUTINE INITIALIZE_TAIL_SEGMENT_STATE

  SUBROUTINE ADVANCE_TAIL_SEGMENT_STATES(JB_IN, JW_IN)
    INTEGER, INTENT(IN) :: JB_IN, JW_IN
    INTEGER :: IS, ISEG, NSEG
    REAL(R8) :: QUP, QDN

    IF (.NOT. ALLOCATED(TAIL_STAGE_SEG)) RETURN
    NSEG = MIN(MAX(TAIL_DOMAIN_NSEG(JB_IN), 0), MAX_TAIL_SEG)
    IF (NSEG <= 0) RETURN

    IF (.NOT. TAIL_SEG_VALID(1,JB_IN)) CALL INITIALIZE_TAIL_SEGMENT_STATE(JB_IN)
    QUP = MAX(TAIL_Q_STATE(JB_IN), 0.0D0)

    DO IS=1,NSEG
      ISEG = TAIL_DOMAIN_US(JB_IN) + IS - 1
      CALL UPDATE_ONE_TAIL_SEGMENT(JB_IN, JW_IN, IS, QUP, QDN)
      QUP = QDN
    END DO

    TAIL_TRANSITION_STATE(JB_IN) = TAIL_TRANSITION_SEG(NSEG,JB_IN)
    TAIL_SUBMERGENCE(JB_IN) = TAIL_SUBMERGENCE_SEG(NSEG,JB_IN)
    TAIL_LOCAL_SLOPE(JB_IN) = TAIL_LOCAL_SLOPE_SEG(NSEG,JB_IN)
    TAIL_FROUDE(JB_IN) = TAIL_FROUDE_SEG(NSEG,JB_IN)
    TAIL_CONTROL_MODE(JB_IN) = TAIL_MODE_SEG(NSEG,JB_IN)

    TAIL_Q_LINK(JB_IN) = QUP
    TAIL_Q_STATE(JB_IN) = QUP
    TAIL_Q_OUTFLOW(JB_IN) = QUP
    TAIL_WSE_UP(JB_IN) = TAIL_STAGE_SEG(1,JB_IN)
    TAIL_WSE_DN(JB_IN) = TAIL_STAGE_SEG(NSEG,JB_IN)
    TAIL_DEPTH_UP(JB_IN) = MAX(TAIL_WSE_UP(JB_IN)-EL(KB(TAIL_DOMAIN_US(JB_IN))+1,TAIL_DOMAIN_US(JB_IN)), FRONT_H_MIN)
    TAIL_STAGE_VALID(JB_IN) = ALL(TAIL_SEG_VALID(1:NSEG,JB_IN))
  END SUBROUTINE ADVANCE_TAIL_SEGMENT_STATES

  SUBROUTINE UPDATE_ONE_TAIL_SEGMENT(JB_IN, JW_IN, IS, QUP, QDN)
    INTEGER, INTENT(IN) :: JB_IN, JW_IN, IS
    REAL(R8), INTENT(IN) :: QUP
    REAL(R8), INTENT(OUT) :: QDN
    INTEGER :: ISEG
    REAL(R8) :: BED_ELEV, STAGE_UP, DEPTH_SEG, AREA_LOCAL, HRAD_LOCAL
    REAL(R8) :: SEG_SHIFT, SEG_LOSS, FLOW_SCALE, STAGE_DROP, TARGET_STAGE
    LOGICAL :: OK

    ISEG = TAIL_DOMAIN_US(JB_IN) + IS - 1
    BED_ELEV = EL(KB(ISEG)+1,ISEG)
    STAGE_UP = TAIL_STAGE_SEG(MAX(1,IS-1),JB_IN)
    DEPTH_SEG = MAX(STAGE_UP-BED_ELEV, FRONT_H_MIN)

    CALL TAIL_SECTION_PROPS(ISEG, JW_IN, STAGE_UP, AREA_LOCAL, HRAD_LOCAL, OK)
    IF (.NOT. OK) THEN
      AREA_LOCAL = MAX(BI(KTWB(JW_IN),ISEG)*DEPTH_SEG, 1.0D-6)
      HRAD_LOCAL = AREA_LOCAL/MAX(BI(KTWB(JW_IN),ISEG)+2.0D0*DEPTH_SEG, 1.0D-6)
    END IF

    FLOW_SCALE = MAX(QUP, 0.0D0)/MAX(AREA_LOCAL, 1.0D-6)
    SEG_SHIFT = 0.0005D0*DBLE(IS-1) + 0.0010D0*MIN(1.0D0, DLX(ISEG)/MAX(TAIL_REACH_LENGTH(JB_IN), 1.0D0))
    SEG_LOSS = MIN(0.012D0, SEG_SHIFT + 0.0002D0*MIN(FLOW_SCALE, 20.0D0))
    QDN = MAX(0.0D0, QUP*(1.0D0-SEG_LOSS))

    STAGE_DROP = MAX(0.0D0, (QUP-QDN)/MAX(AREA_LOCAL, 1.0D-6)*0.015D0)
    TARGET_STAGE = MAX(BED_ELEV+FRONT_H_MIN, STAGE_UP-STAGE_DROP)
    TAIL_STAGE_SEG(IS,JB_IN) = MAX(TAIL_STAGE_SEG(IS,JB_IN), TARGET_STAGE)
    TAIL_DEPTH_SEG(IS,JB_IN) = MAX(TAIL_STAGE_SEG(IS,JB_IN)-BED_ELEV, FRONT_H_MIN)
    TAIL_AREA_SEG(IS,JB_IN) = MAX(AREA_LOCAL*(1.0D0-0.15D0*SEG_LOSS), 1.0D-6)
    TAIL_HRAD_SEG(IS,JB_IN) = MAX(HRAD_LOCAL*(1.0D0-0.10D0*SEG_LOSS), 1.0D-6)
    TAIL_VOL_SEG(IS,JB_IN) = TAIL_AREA_SEG(IS,JB_IN)*DLX(ISEG)
    TAIL_Q_SEG(IS,JB_IN) = QDN
    TAIL_Q_TARGET_SEG(IS,JB_IN) = MAX(TAIL_Q_TARGET(JB_IN), 0.0D0)
    TAIL_CELERITY_SEG(IS,JB_IN) = SQRT(G*TAIL_DEPTH_SEG(IS,JB_IN))
    TAIL_TRAVEL_TIME_SEG(IS,JB_IN) = MAX(DLT, DLX(ISEG)/MAX(TAIL_CELERITY_SEG(IS,JB_IN)+1.0D-6, 1.0D-3))
    TAIL_SEG_VALID(IS,JB_IN) = .TRUE.
    CALL UPDATE_TAIL_SEGMENT_TRANSITION(JB_IN, JW_IN, IS)
    IF (NIT <= 10 .OR. MOD(NIT,200) == 0) THEN
      WARNING_OPEN = .TRUE.
      WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,I0,1X,A,F0.3,1X,A,F0.3)') '[V16_SEGMENT_Q_STATE]', &
        'JB=',JB_IN, 'IS=',IS, 'ISEG=',ISEG, 'Q=',TAIL_Q_SEG(IS,JB_IN), 'STAGE=',TAIL_STAGE_SEG(IS,JB_IN)
    END IF
  END SUBROUTINE UPDATE_ONE_TAIL_SEGMENT

  SUBROUTINE UPDATE_TAIL_SEGMENT_TRANSITION(JB_IN, JW_IN, IS)
    INTEGER, INTENT(IN) :: JB_IN, JW_IN, IS
    INTEGER :: ISEG, NSEG, NEXT_ISEG
    REAL(R8) :: AREA_LOCAL, HRAD_LOCAL, DEPTH_LOCAL, DEPTH_NEXT, FLOW_LOCAL
    REAL(R8) :: SLOPE_LOCAL, SUB_SCORE, SLOPE_SCORE, FROUDE_SCORE, POS_SCORE, TRANS_SCORE
    REAL(R8) :: TRANS_SCALE, HRAD_SCALE, CELERITY_SCALE
    LOGICAL :: OK

    NSEG = MIN(MAX(TAIL_DOMAIN_NSEG(JB_IN), 0), MAX_TAIL_SEG)
    IF (NSEG <= 0) RETURN
    IF (IS < 1 .OR. IS > NSEG) RETURN

    ISEG = TAIL_DOMAIN_US(JB_IN) + IS - 1
    DEPTH_LOCAL = MAX(TAIL_DEPTH_SEG(IS,JB_IN), FRONT_H_MIN)
    AREA_LOCAL = TAIL_AREA_SEG(IS,JB_IN)
    HRAD_LOCAL = TAIL_HRAD_SEG(IS,JB_IN)
    FLOW_LOCAL = ABS(TAIL_Q_SEG(IS,JB_IN))
    IF (AREA_LOCAL <= 0.0D0 .OR. HRAD_LOCAL <= 0.0D0) THEN
      CALL TAIL_SECTION_PROPS(ISEG, JW_IN, TAIL_STAGE_SEG(IS,JB_IN), AREA_LOCAL, HRAD_LOCAL, OK)
      IF (.NOT. OK) THEN
        AREA_LOCAL = MAX(BI(KTWB(JW_IN),ISEG)*DEPTH_LOCAL, 1.0D-6)
        HRAD_LOCAL = AREA_LOCAL/MAX(BI(KTWB(JW_IN),ISEG)+2.0D0*DEPTH_LOCAL, 1.0D-6)
      END IF
    END IF

    IF (IS < NSEG) THEN
      NEXT_ISEG = TAIL_DOMAIN_US(JB_IN) + IS
      DEPTH_NEXT = MAX(TAIL_DEPTH_SEG(IS+1,JB_IN), FRONT_H_MIN)
      SLOPE_LOCAL = MAX((TAIL_STAGE_SEG(IS,JB_IN)-TAIL_STAGE_SEG(IS+1,JB_IN))/MAX(DLX(ISEG), 1.0D0), 0.0D0)
    ELSE
      NEXT_ISEG = TAIL_DNSEG(JB_IN)
      DEPTH_NEXT = MAX(TAIL_WSE_DN(JB_IN)-EL(KB(NEXT_ISEG)+1,NEXT_ISEG), FRONT_H_MIN)
      SLOPE_LOCAL = MAX((TAIL_WSE_UP(JB_IN)-TAIL_WSE_DN(JB_IN))/MAX(TAIL_REACH_LENGTH(JB_IN), 1.0D0), 0.0D0)
    END IF

    SUB_SCORE = MIN(MAX(DEPTH_NEXT/MAX(DEPTH_LOCAL, FRONT_H_MIN), 0.0D0), 1.0D0)
    SLOPE_SCORE = 1.0D0 - MIN(SLOPE_LOCAL/MAX(SLOPEC(JB_IN), 1.0D-6), 1.0D0)
    FROUDE_SCORE = 1.0D0 - MIN(FLOW_LOCAL/MAX(AREA_LOCAL*SQRT(G*DEPTH_LOCAL), 1.0D-6), 1.0D0)
    POS_SCORE = 0.0D0
    IF (NSEG > 1) POS_SCORE = DBLE(IS-1)/DBLE(NSEG-1)

    TRANS_SCORE = MIN(MAX(0.40D0*SUB_SCORE + 0.30D0*SLOPE_SCORE + 0.20D0*FROUDE_SCORE + 0.10D0*POS_SCORE, 0.0D0), 1.0D0)
    TAIL_SUBMERGENCE_SEG(IS,JB_IN) = SUB_SCORE
    TAIL_LOCAL_SLOPE_SEG(IS,JB_IN) = SLOPE_LOCAL
    TAIL_FROUDE_SEG(IS,JB_IN) = MAX(FLOW_LOCAL/MAX(AREA_LOCAL*SQRT(G*DEPTH_LOCAL), 1.0D-6), 0.0D0)
    TAIL_TRANSITION_SEG(IS,JB_IN) = TRANS_SCORE
    IF (TRANS_SCORE < 0.33D0) THEN
      TAIL_MODE_SEG(IS,JB_IN) = 0
    ELSEIF (TRANS_SCORE < 0.66D0) THEN
      TAIL_MODE_SEG(IS,JB_IN) = 1
    ELSE
      TAIL_MODE_SEG(IS,JB_IN) = 2
    END IF

    TRANS_SCALE = 1.0D0 - 0.18D0*TRANS_SCORE
    HRAD_SCALE = 1.0D0 - 0.12D0*TRANS_SCORE
    CELERITY_SCALE = 1.0D0 - 0.08D0*TRANS_SCORE
    TAIL_AREA_SEG(IS,JB_IN) = MAX(AREA_LOCAL*TRANS_SCALE, 1.0D-6)
    TAIL_HRAD_SEG(IS,JB_IN) = MAX(HRAD_LOCAL*HRAD_SCALE, 1.0D-6)
    TAIL_CELERITY_SEG(IS,JB_IN) = MAX(SQRT(G*DEPTH_LOCAL)*CELERITY_SCALE, 1.0D-6)
    TAIL_VOL_SEG(IS,JB_IN) = TAIL_AREA_SEG(IS,JB_IN)*DLX(ISEG)

    IF (NIT <= 10 .OR. MOD(NIT,200) == 0 .OR. (TAIL_MODE_SEG(IS,JB_IN) == 0 .AND. MOD(NIT,20) == 0)) THEN
      WARNING_OPEN = .TRUE.
      WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') '[V17_SEGMENT_TRANSITION]', &
        'JB=',JB_IN, 'IS=',IS, 'MODE=',TAIL_MODE_SEG(IS,JB_IN), 'TRANS=',TAIL_TRANSITION_SEG(IS,JB_IN), &
        'SUB=',TAIL_SUBMERGENCE_SEG(IS,JB_IN), 'SLOPE=',TAIL_LOCAL_SLOPE_SEG(IS,JB_IN), 'FR=',TAIL_FROUDE_SEG(IS,JB_IN)
    END IF
  END SUBROUTINE UPDATE_TAIL_SEGMENT_TRANSITION

  SUBROUTINE UPDATE_TAIL_STAGE(JB_IN, JW_IN, ETA_INTERFACE_GUESS)
    INTEGER, INTENT(IN) :: JB_IN, JW_IN
    REAL(R8), INTENT(IN), OPTIONAL :: ETA_INTERFACE_GUESS
    INTEGER :: IUP_SEG, IDN_SEG
    REAL(R8) :: QABS, WSE_NORMAL, WSE_HYD, WSE_SOLVED, WSE_STORAGE, BLEND
    REAL(R8) :: QPHYS, QLINK_RAW, QTARGET_OLD, QTARGET_NEW, QSTATE_PREV, QSTATE_NEW
    REAL(R8) :: VOL_TARGET, VOL_MIN, STORAGE_OLD, QALPHA, DEPTH_STAGE
    LOGICAL :: SOLVED

    IUP_SEG = TAIL_UPSEG(JB_IN)
    IDN_SEG = TAIL_DNSEG(JB_IN)
    TAIL_STAGE_VALID(JB_IN) = .FALSE.
    TAIL_STAGE_MODE(JB_IN) = 0
    TAIL_DEPTH_UP(JB_IN) = 0.0D0
    TAIL_Q_INFLOW(JB_IN) = 0.0D0
    TAIL_Q_OUTFLOW(JB_IN) = 0.0D0

    IF (.NOT. TAIL_COUPLED(JB_IN)) RETURN
    IF (IUP_SEG <= 0 .OR. IDN_SEG <= 0) RETURN

    IF (PRESENT(ETA_INTERFACE_GUESS)) THEN
      TAIL_WSE_DN(JB_IN) = MAX(ETA_INTERFACE_GUESS, EL(KB(IDN_SEG)+1,IDN_SEG)+FRONT_H_MIN)
    ELSE
      TAIL_WSE_DN(JB_IN) = ELWS(IDN_SEG)
    END IF
    QPHYS = MAX(QIN(JB_IN), 0.0D0)
    TAIL_Q_INFLOW(JB_IN) = QPHYS
    QABS = ABS(QC(IDN_SEG))

    IF (QABS <= 1.0D-6) THEN
      WSE_HYD = MAX(TAIL_WSE_DN(JB_IN), EL(KB(IUP_SEG)+1,IUP_SEG)+FRONT_H_MIN)
      TAIL_STAGE_MODE(JB_IN) = 1
    ELSE
      CALL COMPUTE_TAIL_NORMAL_STAGE(IUP_SEG, JB_IN, JW_IN, QABS, WSE_NORMAL)
      WSE_NORMAL = MAX(WSE_NORMAL, TAIL_WSE_DN(JB_IN))
      WSE_NORMAL = MIN(WSE_NORMAL, TAIL_WSE_DN(JB_IN)+20.0D0)
      CALL SOLVE_TAIL_STANDARD_STEP(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, TAIL_WSE_DN(JB_IN), WSE_NORMAL, WSE_HYD, SOLVED)
      IF (SOLVED) THEN
        TAIL_STAGE_MODE(JB_IN) = 2
      ELSE
        BLEND = MIN(MAX(FRONT_TRANSITION(JB_IN), 0.0D0), 1.0D0)
        WSE_HYD = (1.0D0-BLEND)*WSE_NORMAL + BLEND*TAIL_WSE_DN(JB_IN)
        WSE_HYD = MAX(WSE_HYD, TAIL_WSE_DN(JB_IN))
        TAIL_STAGE_MODE(JB_IN) = 3
      END IF
    END IF

    WSE_HYD = MAX(WSE_HYD, EL(KB(IUP_SEG)+1,IUP_SEG)+FRONT_H_MIN)
    WSE_HYD = MAX(WSE_HYD, TAIL_WSE_DN(JB_IN))
    WSE_HYD = MIN(WSE_HYD, TAIL_WSE_DN(JB_IN)+25.0D0)

    IF (.NOT. TAIL_REACH_INITIALIZED(JB_IN)) THEN
      TAIL_STORAGE_VOL(JB_IN) = TAIL_VOLUME_FROM_STAGE(IUP_SEG, JW_IN, WSE_HYD)
      TAIL_REACH_INITIALIZED(JB_IN) = .TRUE.
    END IF

    TAIL_REACH_LENGTH(JB_IN) = COMPUTE_TAIL_REACH_LENGTH(JB_IN, IUP_SEG)
    VOL_MIN = TAIL_VOLUME_FROM_STAGE(IUP_SEG, JW_IN, EL(KB(IUP_SEG)+1,IUP_SEG)+FRONT_H_MIN)
    CALL COMPUTE_TAIL_LINK_FLOW(IUP_SEG, IDN_SEG, JB_IN, JW_IN, MAX(TAIL_WSE_UP(JB_IN), WSE_HYD), TAIL_WSE_DN(JB_IN), QLINK_RAW)
    QTARGET_OLD = MAX(QLINK_RAW, 0.0D0)
    TAIL_Q_TARGET(JB_IN) = QTARGET_OLD
    STORAGE_OLD = TAIL_STORAGE_VOL(JB_IN)
    QSTATE_PREV = MAX(TAIL_Q_STATE(JB_IN), 0.0D0)
    IF (.NOT. TAIL_Q_STATE_INITIALIZED(JB_IN)) THEN
      QSTATE_PREV = QTARGET_OLD
      TAIL_Q_STATE_INITIALIZED(JB_IN) = .TRUE.
    END IF
    CALL ADVANCE_TAIL_Q_STATE(JB_IN, IUP_SEG, JW_IN, WSE_HYD, QSTATE_PREV, QTARGET_OLD, QSTATE_NEW, QALPHA)
    VOL_TARGET = MAX(VOL_MIN, STORAGE_OLD + DLT*(QPHYS-QSTATE_NEW))
    CALL INVERT_TAIL_STORAGE_STAGE(IUP_SEG, JW_IN, VOL_TARGET, WSE_STORAGE)
    WSE_SOLVED = MAX(WSE_STORAGE, TAIL_WSE_DN(JB_IN))
    CALL COMPUTE_TAIL_LINK_FLOW(IUP_SEG, IDN_SEG, JB_IN, JW_IN, WSE_SOLVED, TAIL_WSE_DN(JB_IN), QLINK_RAW)
    QTARGET_NEW = MAX(QLINK_RAW, 0.0D0)
    TAIL_Q_TARGET(JB_IN) = 0.5D0*(QTARGET_OLD + QTARGET_NEW)
    CALL ADVANCE_TAIL_Q_STATE(JB_IN, IUP_SEG, JW_IN, WSE_SOLVED, QSTATE_PREV, TAIL_Q_TARGET(JB_IN), QSTATE_NEW, QALPHA)
    TAIL_Q_STATE(JB_IN) = MAX(QSTATE_NEW, 0.0D0)
    TAIL_Q_OUTFLOW(JB_IN) = TAIL_Q_STATE(JB_IN)
    TAIL_Q_LINK(JB_IN) = TAIL_Q_STATE(JB_IN)
    VOL_TARGET = MAX(VOL_MIN, STORAGE_OLD + DLT*(QPHYS-TAIL_Q_OUTFLOW(JB_IN)))
    TAIL_STORAGE_VOL(JB_IN) = VOL_TARGET
    CALL INVERT_TAIL_STORAGE_STAGE(IUP_SEG, JW_IN, VOL_TARGET, WSE_STORAGE)
    WSE_SOLVED = MAX(WSE_STORAGE, TAIL_WSE_DN(JB_IN))

    WSE_SOLVED = MAX(WSE_SOLVED, EL(KB(IUP_SEG)+1,IUP_SEG)+FRONT_H_MIN)
    WSE_SOLVED = MAX(WSE_SOLVED, TAIL_WSE_DN(JB_IN))
    WSE_SOLVED = MIN(WSE_SOLVED, TAIL_WSE_DN(JB_IN)+25.0D0)
    TAIL_WSE_UP(JB_IN) = WSE_SOLVED
    DEPTH_STAGE = MAX(TAIL_WSE_UP(JB_IN)-EL(KB(IUP_SEG)+1,IUP_SEG), FRONT_H_MIN)
    TAIL_DEPTH_UP(JB_IN) = DEPTH_STAGE
    CALL UPDATE_TAIL_TRANSITION_STATE(JB_IN, IUP_SEG, IDN_SEG, JW_IN, DEPTH_STAGE)
    TAIL_STAGE_VALID(JB_IN) = .TRUE.
    CALL INITIALIZE_TAIL_SEGMENT_STATE(JB_IN)
    CALL ADVANCE_TAIL_SEGMENT_STATES(JB_IN, JW_IN)

    IF (NIT <= 10 .OR. FRONT_STATE(JB_IN) >= FRONT_STATE_WETTING) THEN
      WARNING_OPEN = .TRUE.
      WRITE (WRN,'(A,1X,A,I0,1X,A,I0,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,I0)') '[V7_TAIL_STAGE]', &
        'JB=',JB_IN, 'UPSEG=',IUP_SEG, 'DNSEG=',IDN_SEG, 'WSE_UP=',TAIL_WSE_UP(JB_IN), 'WSE_DN=',TAIL_WSE_DN(JB_IN), &
        'Q=',TAIL_Q_LINK(JB_IN), 'DEPTH=',TAIL_DEPTH_UP(JB_IN), 'MODE=',TAIL_STAGE_MODE(JB_IN)
      WRITE (WRN,'(A,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') '[V10_TAIL_REACH]', &
        'JB=',JB_IN, 'QPHYS=',TAIL_Q_INFLOW(JB_IN), 'QOUT=',TAIL_Q_OUTFLOW(JB_IN), 'VOL=',TAIL_STORAGE_VOL(JB_IN), &
        'WSE_HYD=',WSE_HYD, 'WSE_STOR=',WSE_STORAGE
      WRITE (WRN,'(A,1X,A,I0,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3,1X,A,F0.3)') '[V12_Q_STATE]', &
        'JB=',JB_IN, 'QSTATE=',TAIL_Q_STATE(JB_IN), 'QTARGET=',TAIL_Q_TARGET(JB_IN), 'TAU=',TAIL_TRAVEL_TIME(JB_IN), &
        'CEL=',TAIL_WAVE_CELERITY(JB_IN), 'LENGTH=',TAIL_REACH_LENGTH(JB_IN), 'ALPHA=',QALPHA
      WRITE (WRN,'(A,1X,A,I0,1X,A,F0.3,1X,A,F0.5,1X,A,F0.3,1X,A,F0.3,1X,A,I0)') '[V13_TRANSITION_REACH]', &
        'JB=',JB_IN, 'TRANS=',TAIL_TRANSITION_STATE(JB_IN), 'SLOPE=',TAIL_LOCAL_SLOPE(JB_IN), 'SUB=',TAIL_SUBMERGENCE(JB_IN), &
        'FR=',TAIL_FROUDE(JB_IN), 'MODE=',TAIL_CONTROL_MODE(JB_IN)
    END IF
  END SUBROUTINE UPDATE_TAIL_STAGE

  SUBROUTINE ADVANCE_TAIL_Q_STATE(JB_IN, ISEG, JW_IN, WSE_LOCAL, QSTATE_OLD, QTARGET_IN, QSTATE_NEW, ALPHA_USED)
    INTEGER, INTENT(IN) :: JB_IN, ISEG, JW_IN
    REAL(R8), INTENT(IN) :: WSE_LOCAL, QSTATE_OLD, QTARGET_IN
    REAL(R8), INTENT(OUT) :: QSTATE_NEW, ALPHA_USED
    REAL(R8) :: AREA_LOCAL, HRAD_LOCAL, DEPTH_LOCAL, VEL_LOCAL, TAU_LOCAL
    LOGICAL :: OK

    CALL TAIL_SECTION_PROPS(ISEG, JW_IN, WSE_LOCAL, AREA_LOCAL, HRAD_LOCAL, OK)
    DEPTH_LOCAL = MAX(WSE_LOCAL-EL(KB(ISEG)+1,ISEG), FRONT_H_MIN)
    IF (.NOT. OK) AREA_LOCAL = MAX(BI(KTWB(JW_IN),ISEG)*DEPTH_LOCAL, 1.0D-6)
    VEL_LOCAL = ABS(QSTATE_OLD)/MAX(AREA_LOCAL, 1.0D-6)
    TAIL_WAVE_CELERITY(JB_IN) = SQRT(G*DEPTH_LOCAL)
    TAU_LOCAL = TAIL_REACH_LENGTH(JB_IN)/MAX(TAIL_WAVE_CELERITY(JB_IN)+VEL_LOCAL, 1.0D-3)
    TAU_LOCAL = MAX(4.0D0*DLT, TAU_LOCAL)
    TAIL_TRAVEL_TIME(JB_IN) = TAU_LOCAL
    ALPHA_USED = MIN(MAX(DLT/MAX(TAU_LOCAL, DLT), TAIL_Q_STATE_RELAX_MIN), TAIL_Q_STATE_RELAX_MAX)
    QSTATE_NEW = MAX(0.0D0, QSTATE_OLD + ALPHA_USED*(MAX(QTARGET_IN, 0.0D0)-QSTATE_OLD))
  END SUBROUTINE ADVANCE_TAIL_Q_STATE

  SUBROUTINE UPDATE_TAIL_TRANSITION_STATE(JB_IN, IUP_SEG, IDN_SEG, JW_IN, DEPTH_STAGE)
    INTEGER, INTENT(IN) :: JB_IN, IUP_SEG, IDN_SEG, JW_IN
    REAL(R8), INTENT(IN) :: DEPTH_STAGE
    REAL(R8) :: AREA_LOCAL, HRAD_LOCAL, VEL_LOCAL, SUB_SCORE, SLOPE_SCORE, FROUDE_SCORE
    REAL(R8) :: DEPTH_DN, WIDTH_LOCAL
    LOGICAL :: OK

    CALL TAIL_SECTION_PROPS(IUP_SEG, JW_IN, TAIL_WSE_UP(JB_IN), AREA_LOCAL, HRAD_LOCAL, OK)
    WIDTH_LOCAL = MAX(BI(KTWB(JW_IN),IUP_SEG), 1.0D-6)
    IF (.NOT. OK) AREA_LOCAL = MAX(WIDTH_LOCAL*DEPTH_STAGE, 1.0D-6)
    VEL_LOCAL = TAIL_Q_STATE(JB_IN)/MAX(AREA_LOCAL, 1.0D-6)
    DEPTH_DN = MAX(TAIL_WSE_DN(JB_IN)-EL(KB(IDN_SEG)+1,IDN_SEG), FRONT_H_MIN)

    TAIL_LOCAL_SLOPE(JB_IN) = MAX((TAIL_WSE_UP(JB_IN)-TAIL_WSE_DN(JB_IN))/MAX(TAIL_REACH_LENGTH(JB_IN), 1.0D0), 0.0D0)
    TAIL_SUBMERGENCE(JB_IN) = MIN(MAX(DEPTH_DN/MAX(DEPTH_STAGE, FRONT_H_MIN), 0.0D0), 1.0D0)
    TAIL_FROUDE(JB_IN) = VEL_LOCAL/MAX(SQRT(G*DEPTH_STAGE), 1.0D-6)

    SUB_SCORE = TAIL_SUBMERGENCE(JB_IN)
    SLOPE_SCORE = 1.0D0 - MIN(TAIL_LOCAL_SLOPE(JB_IN)/MAX(SLOPEC(JB_IN), 1.0D-6), 1.0D0)
    FROUDE_SCORE = 1.0D0 - MIN(TAIL_FROUDE(JB_IN), 1.0D0)

    TAIL_TRANSITION_STATE(JB_IN) = MIN(MAX(0.45D0*SUB_SCORE + 0.35D0*SLOPE_SCORE + 0.20D0*FROUDE_SCORE, 0.0D0), 1.0D0)
    IF (TAIL_TRANSITION_STATE(JB_IN) < 0.33D0) THEN
      TAIL_CONTROL_MODE(JB_IN) = 0
    ELSEIF (TAIL_TRANSITION_STATE(JB_IN) < 0.66D0) THEN
      TAIL_CONTROL_MODE(JB_IN) = 1
    ELSE
      TAIL_CONTROL_MODE(JB_IN) = 2
    END IF
  END SUBROUTINE UPDATE_TAIL_TRANSITION_STATE

  REAL(R8) FUNCTION COMPUTE_TAIL_REACH_LENGTH(JB_IN, ISEG_FALLBACK)
    INTEGER, INTENT(IN) :: JB_IN, ISEG_FALLBACK
    INTEGER :: IT

    COMPUTE_TAIL_REACH_LENGTH = 0.0D0
    IF (TAIL_DOMAIN_DEFINED(JB_IN)) THEN
      DO IT=TAIL_DOMAIN_US(JB_IN),TAIL_DOMAIN_DS(JB_IN)
        COMPUTE_TAIL_REACH_LENGTH = COMPUTE_TAIL_REACH_LENGTH + DLX(IT)
      END DO
    END IF
    IF (COMPUTE_TAIL_REACH_LENGTH <= 0.0D0) COMPUTE_TAIL_REACH_LENGTH = MAX(DLX(ISEG_FALLBACK), 1.0D0)
  END FUNCTION COMPUTE_TAIL_REACH_LENGTH

  SUBROUTINE COMPUTE_TAIL_NORMAL_STAGE(ISEG, JB_IN, JW_IN, QABS, WSE_NORMAL)
    INTEGER, INTENT(IN) :: ISEG, JB_IN, JW_IN
    REAL(R8), INTENT(IN) :: QABS
    REAL(R8), INTENT(OUT) :: WSE_NORMAL
    REAL(R8) :: BED_ELEV, X1, X2, F1, F2, FMID, DX, XMID, RTBIS
    INTEGER :: J

    BED_ELEV = EL(KB(ISEG)+1,ISEG)
    X1 = BED_ELEV + FRONT_H_MIN
    X2 = X1 + 1.0D0
    CALL TAIL_MANNING_RESIDUAL(ISEG, JB_IN, JW_IN, QABS, X1, F1)
    CALL TAIL_MANNING_RESIDUAL(ISEG, JB_IN, JW_IN, QABS, X2, F2)

    DO J=1,40
      IF (F1*F2 <= 0.0D0) EXIT
      X2 = X2 + MAX(1.0D0, 1.5D0*(X2-X1))
      CALL TAIL_MANNING_RESIDUAL(ISEG, JB_IN, JW_IN, QABS, X2, F2)
    END DO

    IF (F1*F2 > 0.0D0) THEN
      WSE_NORMAL = X2
      RETURN
    END IF

    IF (F1 < 0.0D0) THEN
      RTBIS = X1
      DX = X2-X1
    ELSE
      RTBIS = X2
      DX = X1-X2
    END IF

    DO J=1,40
      DX = 0.5D0*DX
      XMID = RTBIS+DX
      CALL TAIL_MANNING_RESIDUAL(ISEG, JB_IN, JW_IN, QABS, XMID, FMID)
      IF (FMID <= 0.0D0) RTBIS = XMID
      IF (ABS(DX) < 0.01D0 .OR. FMID == 0.0D0) EXIT
    END DO

    WSE_NORMAL = MAX(RTBIS, BED_ELEV+FRONT_H_MIN)
  END SUBROUTINE COMPUTE_TAIL_NORMAL_STAGE

  SUBROUTINE SOLVE_TAIL_STANDARD_STEP(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, WSE_DN, WSE_NORMAL, WSE_SOLVED, SOLVED)
    INTEGER, INTENT(IN) :: IUP_SEG, IDN_SEG, JB_IN, JW_IN
    REAL(R8), INTENT(IN) :: QABS, WSE_DN, WSE_NORMAL
    REAL(R8), INTENT(OUT) :: WSE_SOLVED
    LOGICAL, INTENT(OUT) :: SOLVED
    REAL(R8) :: LOW_WSE, HIGH_WSE, MID_WSE, F_LOW, F_HIGH, F_MID, BED_ELEV
    LOGICAL :: OK_LOW, OK_HIGH, OK_MID
    INTEGER :: J

    BED_ELEV = EL(KB(IUP_SEG)+1,IUP_SEG)
    LOW_WSE = MAX(WSE_DN, BED_ELEV+FRONT_H_MIN)
    HIGH_WSE = MAX(WSE_NORMAL+1.0D0, LOW_WSE+1.0D0)
    CALL TAIL_STANDARD_RESIDUAL(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, WSE_DN, LOW_WSE, F_LOW, OK_LOW)
    CALL TAIL_STANDARD_RESIDUAL(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, WSE_DN, HIGH_WSE, F_HIGH, OK_HIGH)
    IF (.NOT. OK_LOW .OR. .NOT. OK_HIGH) THEN
      SOLVED = .FALSE.
      WSE_SOLVED = MAX(WSE_DN, BED_ELEV+FRONT_H_MIN)
      RETURN
    END IF

    DO J=1,25
      IF (F_LOW*F_HIGH <= 0.0D0) EXIT
      HIGH_WSE = HIGH_WSE + MAX(1.0D0, 0.5D0*(HIGH_WSE-LOW_WSE))
      CALL TAIL_STANDARD_RESIDUAL(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, WSE_DN, HIGH_WSE, F_HIGH, OK_HIGH)
      IF (.NOT. OK_HIGH) THEN
        SOLVED = .FALSE.
        WSE_SOLVED = MAX(WSE_DN, BED_ELEV+FRONT_H_MIN)
        RETURN
      END IF
    END DO

    IF (F_LOW*F_HIGH > 0.0D0) THEN
      SOLVED = .FALSE.
      WSE_SOLVED = MAX(WSE_DN, BED_ELEV+FRONT_H_MIN)
      RETURN
    END IF

    DO J=1,40
      MID_WSE = 0.5D0*(LOW_WSE+HIGH_WSE)
      CALL TAIL_STANDARD_RESIDUAL(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, WSE_DN, MID_WSE, F_MID, OK_MID)
      IF (.NOT. OK_MID) THEN
        SOLVED = .FALSE.
        WSE_SOLVED = MAX(WSE_DN, BED_ELEV+FRONT_H_MIN)
        RETURN
      END IF
      IF (ABS(HIGH_WSE-LOW_WSE) < 0.01D0 .OR. ABS(F_MID) < 1.0D-4) EXIT
      IF (F_LOW*F_MID <= 0.0D0) THEN
        HIGH_WSE = MID_WSE
        F_HIGH = F_MID
      ELSE
        LOW_WSE = MID_WSE
        F_LOW = F_MID
      END IF
    END DO

    WSE_SOLVED = 0.5D0*(LOW_WSE+HIGH_WSE)
    SOLVED = .TRUE.
  END SUBROUTINE SOLVE_TAIL_STANDARD_STEP

  SUBROUTINE TAIL_STANDARD_RESIDUAL(IUP_SEG, IDN_SEG, JB_IN, JW_IN, QABS, WSE_DN, WSE_UP, RESIDUAL, OK)
    INTEGER, INTENT(IN) :: IUP_SEG, IDN_SEG, JB_IN, JW_IN
    REAL(R8), INTENT(IN) :: QABS, WSE_DN, WSE_UP
    REAL(R8), INTENT(OUT) :: RESIDUAL
    LOGICAL, INTENT(OUT) :: OK
    REAL(R8) :: AREA_UP, HRAD_UP, AREA_DN, HRAD_DN, VEL_UP, VEL_DN, FMANN_UP, FMANN_DN, SF_UP, SF_DN, DX_REACH

    CALL TAIL_SECTION_PROPS(IUP_SEG, JW_IN, WSE_UP, AREA_UP, HRAD_UP, OK)
    IF (.NOT. OK) THEN
      RESIDUAL = 0.0D0
      RETURN
    END IF
    CALL TAIL_SECTION_PROPS(IDN_SEG, JW_IN, WSE_DN, AREA_DN, HRAD_DN, OK)
    IF (.NOT. OK) THEN
      RESIDUAL = 0.0D0
      RETURN
    END IF

    FMANN_UP = TAIL_FMANN(IUP_SEG, JW_IN, HRAD_UP)
    FMANN_DN = TAIL_FMANN(IDN_SEG, JW_IN, HRAD_DN)
    SF_UP = (QABS*FMANN_UP/MAX(AREA_UP*HRAD_UP**0.6666666666666667D0, 1.0D-6))**2
    SF_DN = (QABS*FMANN_DN/MAX(AREA_DN*HRAD_DN**0.6666666666666667D0, 1.0D-6))**2
    VEL_UP = QABS/MAX(AREA_UP, 1.0D-6)
    VEL_DN = QABS/MAX(AREA_DN, 1.0D-6)
    DX_REACH = 0.5D0*(DLX(IUP_SEG)+DLX(IDN_SEG))
    RESIDUAL = (WSE_UP + (VEL_UP*VEL_UP)/(2.0D0*G)) - (WSE_DN + (VEL_DN*VEL_DN)/(2.0D0*G) + 0.5D0*(SF_UP+SF_DN)*DX_REACH)
    OK = .TRUE.
  END SUBROUTINE TAIL_STANDARD_RESIDUAL

  SUBROUTINE TAIL_MANNING_RESIDUAL(ISEG, JB_IN, JW_IN, QABS, WSE, RESIDUAL)
    INTEGER, INTENT(IN) :: ISEG, JB_IN, JW_IN
    REAL(R8), INTENT(IN) :: QABS, WSE
    REAL(R8), INTENT(OUT) :: RESIDUAL
    REAL(R8) :: AREA, HRAD, FMANN
    LOGICAL :: OK

    CALL TAIL_SECTION_PROPS(ISEG, JW_IN, WSE, AREA, HRAD, OK)
    IF (.NOT. OK) THEN
      RESIDUAL = QABS
      RETURN
    END IF
    FMANN = TAIL_FMANN(ISEG, JW_IN, HRAD)
    RESIDUAL = QABS - AREA*HRAD**0.6666666666666667D0*SQRT(MAX(SLOPEC(JB_IN), 1.0D-8))/MAX(FMANN, 1.0D-8)
  END SUBROUTINE TAIL_MANNING_RESIDUAL

  SUBROUTINE TAIL_SECTION_PROPS(ISEG, JW_IN, WSE, AREA, HRAD, OK)
    INTEGER, INTENT(IN) :: ISEG, JW_IN
    REAL(R8), INTENT(IN) :: WSE
    REAL(R8), INTENT(OUT) :: AREA, HRAD
    LOGICAL, INTENT(OUT) :: OK
    INTEGER :: K, KTTOP
    REAL(R8) :: BED_ELEV, DEPTH_LOCAL, TOPW, WPER

    BED_ELEV = EL(KB(ISEG)+1,ISEG)
    DEPTH_LOCAL = MAX(WSE-BED_ELEV, FRONT_H_MIN)
    KTTOP = 2
    DO K=2,KMX-1
      IF (EL(K,ISEG) < WSE) THEN
        KTTOP = K-1
        EXIT
      END IF
      KTTOP = K
    END DO

    AREA = MAX((WSE-EL(KTTOP+1,ISEG))*BSAVE(KTTOP,ISEG), 0.0D0)
    DO K=KTTOP+1,KBI(ISEG)
      AREA = AREA + BSAVE(K,ISEG)*H(K,JW_IN)
    END DO
    TOPW = MAX(BSAVE(KTTOP,ISEG), 1.0D-6)
    WPER = TOPW + 2.0D0*DEPTH_LOCAL
    HRAD = AREA/MAX(WPER, 1.0D-6)
    OK = AREA > 1.0D-8 .AND. HRAD > 1.0D-8
  END SUBROUTINE TAIL_SECTION_PROPS

  SUBROUTINE COMPUTE_TAIL_LINK_FLOW(IUP_SEG, IDN_SEG, JB_IN, JW_IN, WSE_UP, WSE_DN, QOUT)
    INTEGER, INTENT(IN) :: IUP_SEG, IDN_SEG, JB_IN, JW_IN
    REAL(R8), INTENT(IN) :: WSE_UP, WSE_DN
    REAL(R8), INTENT(OUT) :: QOUT
    REAL(R8) :: AREA_UP, HRAD_UP, FMANN_UP, DX_REACH, SLOCAL
    LOGICAL :: OK

    CALL TAIL_SECTION_PROPS(IUP_SEG, JW_IN, WSE_UP, AREA_UP, HRAD_UP, OK)
    IF (.NOT. OK) THEN
      QOUT = 0.0D0
      RETURN
    END IF
    FMANN_UP = TAIL_FMANN(IUP_SEG, JW_IN, HRAD_UP)
    DX_REACH = MAX(0.5D0*(DLX(IUP_SEG)+DLX(IDN_SEG)), 1.0D0)
    SLOCAL = (WSE_UP-WSE_DN)/DX_REACH
    IF (SLOCAL <= 1.0D-8) THEN
      QOUT = 0.0D0
      RETURN
    END IF
    QOUT = AREA_UP*HRAD_UP**0.6666666666666667D0*SQRT(SLOCAL)/MAX(FMANN_UP, 1.0D-8)
  END SUBROUTINE COMPUTE_TAIL_LINK_FLOW

  REAL(R8) FUNCTION TAIL_VOLUME_FROM_STAGE(ISEG, JW_IN, WSE)
    INTEGER, INTENT(IN) :: ISEG, JW_IN
    REAL(R8), INTENT(IN) :: WSE
    REAL(R8) :: AREA, HRAD
    LOGICAL :: OK

    CALL TAIL_SECTION_PROPS(ISEG, JW_IN, WSE, AREA, HRAD, OK)
    IF (.NOT. OK) THEN
      TAIL_VOLUME_FROM_STAGE = 0.0D0
    ELSE
      TAIL_VOLUME_FROM_STAGE = AREA*DLX(ISEG)
    END IF
  END FUNCTION TAIL_VOLUME_FROM_STAGE

  SUBROUTINE INVERT_TAIL_STORAGE_STAGE(ISEG, JW_IN, TARGET_VOL, WSE_OUT)
    INTEGER, INTENT(IN) :: ISEG, JW_IN
    REAL(R8), INTENT(IN) :: TARGET_VOL
    REAL(R8), INTENT(OUT) :: WSE_OUT
    REAL(R8) :: BED_ELEV, WLOW, WHIGH, WMID, VLOW, VHIGH, VMID
    INTEGER :: J

    BED_ELEV = EL(KB(ISEG)+1,ISEG)
    WLOW = BED_ELEV + FRONT_H_MIN
    VLOW = TAIL_VOLUME_FROM_STAGE(ISEG, JW_IN, WLOW)
    WHIGH = WLOW + 1.0D0
    VHIGH = TAIL_VOLUME_FROM_STAGE(ISEG, JW_IN, WHIGH)
    DO J=1,40
      IF (VHIGH >= TARGET_VOL) EXIT
      WHIGH = WHIGH + MAX(1.0D0, 0.5D0*(WHIGH-WLOW))
      VHIGH = TAIL_VOLUME_FROM_STAGE(ISEG, JW_IN, WHIGH)
    END DO
    IF (TARGET_VOL <= VLOW) THEN
      WSE_OUT = WLOW
      RETURN
    END IF
    DO J=1,40
      WMID = 0.5D0*(WLOW+WHIGH)
      VMID = TAIL_VOLUME_FROM_STAGE(ISEG, JW_IN, WMID)
      IF (ABS(WHIGH-WLOW) < 0.01D0 .OR. ABS(VMID-TARGET_VOL) < 1.0D-3) EXIT
      IF (VMID >= TARGET_VOL) THEN
        WHIGH = WMID
      ELSE
        WLOW = WMID
      END IF
    END DO
    WSE_OUT = 0.5D0*(WLOW+WHIGH)
  END SUBROUTINE INVERT_TAIL_STORAGE_STAGE

  REAL(R8) FUNCTION EFFECTIVE_UPSTREAM_INFLOW(JB_IN)
    INTEGER, INTENT(IN) :: JB_IN
    REAL(R8) :: QPHYS

    QPHYS = MAX(QIN(JB_IN), 0.0D0)
    EFFECTIVE_UPSTREAM_INFLOW = QPHYS
    IF (UPSTREAM_DOMAIN_LOCK(JB_IN) .AND. TAIL_STAGE_VALID(JB_IN) .AND. TAIL_Q_LINK(JB_IN) > 0.0D0) THEN
      EFFECTIVE_UPSTREAM_INFLOW = (1.0D0-TAIL_FLOW_COUPLING_RELAX)*QPHYS + TAIL_FLOW_COUPLING_RELAX*TAIL_Q_LINK(JB_IN)
    END IF
  END FUNCTION EFFECTIVE_UPSTREAM_INFLOW

  REAL(R8) FUNCTION TAIL_FMANN(ISEG, JW_IN, HRAD)
    INTEGER, INTENT(IN) :: ISEG, JW_IN
    REAL(R8), INTENT(IN) :: HRAD

    IF (MANNINGS_N(JW_IN)) THEN
      TAIL_FMANN = MAX(FRIC(ISEG), 1.0D-6)
    ELSE
      TAIL_FMANN = MAX(HRAD**0.1666666666666667D0/MAX(FRIC(ISEG), 1.0D-6), 1.0D-6)
    END IF
  END FUNCTION TAIL_FMANN

END PROGRAM W2_MAIN
