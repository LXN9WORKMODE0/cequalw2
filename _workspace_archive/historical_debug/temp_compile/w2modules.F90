!***********************************************************************************************************************************
!**                                                                                                                               **
!**                                                         CE-QUAL-W2                                                            **
!**                                            A Two-dimensional, Laterally Averaged,                                             **
!**                                             Hydrodynamic and Water Quality Model                                              **
!**                                                            for                                                                **
!**                                           Rivers, Lakes, Reservoirs, and Estuaries                                            **
!**                                                                                                                               **
!**                                                       Version 4.5.5                                                             **
!**                                                                                                                               **
!**                                                 Currently maintained by:                                                      **
!**                                                        Scott A. Wells                                                         **
!**                                       Department of Civil and Environmental Engineering                                       **
!**                                                  Portland State University                                                    **
!**                                                         PO Box 751                                                            **
!**                                                 Portland, Oregon  97207-0751                                                  **
!**                                                 phone number: (503) 725-4276                                                  **
!**                                                 e-mail: wellss@pdx.edu                                                        **
!**                                       Major contributors to this version include                                              ** 
!**                                           Dr. Zhong Zhang <zz3@pdx.edu>, Portland State University                            **
!**                                           Dr. Stewart Rounds, USGS                                                            **
!**  Main contributors to CE-QUAL-W2 are shown in User Manual Part 1.                                                             **
!**                                                                                                                               **
!**                                                                                                                               **
!***********************************************************************************************************************************

!***********************************************************************************************************************************
!**                                                                                                                               **
!**                  The long arm of the lawyers has found its way into the water quality modeling arena, so:                     **
!**                                                                                                                               **
!**  This model was developed by the U.S. Army Engineer Waterways Experiment Station, Vicksburg, MS and is maintained by          **
!**  Portland State University.  Portland State University and the US government and its components are not responsible           **
!**  for any damages,including incidental or consequential damages, arising                                                       **
!**  from use or misuse of this model, or from results achieved or conclusions drawn by others.  Distribution of this model is    **
!**  restricted by the Export Administration Act of 1969,  50 app. USC subsections 2401-2420, as amended, and other applicable    **
!**  laws or regulations.                                            
!
!MIT License Copyright (c) 2023 drswells
!Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
!The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
!THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
!OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                                             **
!**                                                                                                                               **
!***********************************************************************************************************************************

!***********************************************************************************************************************************
!**                                                      Module Declaration                                                       **
!***********************************************************************************************************************************
MODULE MSCLIB
  INTEGER(8) :: HTHREAD
  LOGICAL :: STOP_PUSHED, STOPPED, RESTART_PUSHED, RESTART_EXISTS
  INCLUDE "RESOURCE.FD"
  INTERFACE
    FUNCTION $BEGINTHREADEX (SECURITY,STACK_SIZE,START_ADDRESS,ARGLIST,INITFLAG,THRDADDR)
      USE DFWINTY, RENAMED => DLT
      !DEC$ ATTRIBUTES C,ALIAS : "__BEGINTHREADEX" :: $BEGINTHREADEX
      !DEC$ ATTRIBUTES REFERENCE,ALLOW_NULL        :: SECURITY
      !DEC$ ATTRIBUTES REFERENCE,IGNORE_LOC        :: THRDADDR
      INTEGER(UINT)                                :: $BEGINTHREADEX
      INTEGER(UINT),               INTENT(IN)      :: STACK_SIZE, INITFLAG
      INTEGER(PVOID),              INTENT(IN)      :: START_ADDRESS, ARGLIST
      INTEGER(UINT),               INTENT(OUT)     :: THRDADDR
      TYPE(T_SECURITY_ATTRIBUTES), INTENT(IN)      :: SECURITY
    END FUNCTION $BEGINTHREADEX
  END INTERFACE
  INTERFACE
    SUBROUTINE $ENDTHREADEX (RETVAL)
      USE DFWINTY, RENAMED => DLT
      !DEC$ ATTRIBUTES C, ALIAS : "__ENDTHREADEX" :: $ENDTHREADEX
      INTEGER(UINT), INTENT(IN) :: RETVAL
    END SUBROUTINE $ENDTHREADEX
  END INTERFACE
END MODULE MSCLIB
MODULE PREC
  INTEGER, PARAMETER :: I2=SELECTED_INT_KIND (3)
  INTEGER, PARAMETER :: R8=SELECTED_REAL_KIND(15)
END MODULE PREC
MODULE RSTART
  USE PREC
  REAL(R8)                                           :: DLTS,   CURMAX, DLTFF, DLTMAXX    ! SW 7/13/2010
  INTEGER                                            :: RSODP,  DLTDP,  TSRDP,  WDODP,  RSO=31    ! CUF,
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: SNPDP,  VPLDP,  CPLDP,  PRFDP,  SCRDP,  SPRDP,  FLXDP, NSPRF
  REAL                                               :: CUF 
  REAL(R8)                                           :: NXTMRS, NXTMWD, NXTMTS, NXTMWD_sec, NXTMUK    ! cb 4/6/17
  REAL,              ALLOCATABLE, DIMENSION(:)       :: NXTMSN, NXTMPR, NXTMSP, NXTMCP, NXTMVP, NXTMSC, NXTMFL
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: SBKT,   ELTMF
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: TSSUH2, TSSDH2, SAVH2,  SAVHR,  SU,     SW,     SAZ
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:,:)   :: CSSUH2, CSSDH2
  REAL(R8)                                           :: ELTM
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: VOLIN,  VOLOUT, VOLUH,  VOLDH,  VOLPR,  VOLTRB, VOLDT, VOLWD,  VOLEV,VOLICE, ICEBANK
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: VOLSBR, VOLTBR, VOLSR,  VOLTR
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: TSSEV,  TSSPR,  TSSTR,  TSSDT,  TSSWD,  TSSUH,  TSSDH, TSSIN,  TSSOUT
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: TSSS,   TSSB,   TSSICE
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: ESBR,   ETBR,   EBRI,   SZ
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: CMBRT
END MODULE RSTART
MODULE GLOBAL
  USE PREC
  REAL*4                                             :: W2VER=4.55
  REAL(R8),   PARAMETER                              :: DAY=86400.0D0,  NONZERO=1.0D-20, REFL=0.94D0, FRAZDZ=0.14D0, DZMIN=1.4D-7
  REAL(R8),   PARAMETER                              :: AZMIN=1.4D-6, RHOW=1000.0D0   !DZMAX=1.0D3,     
  REAL(R8)                                           :: DLT,    DLTMIN, DLTTVD,DZMAX=1.0D2     
  REAL(R8)                                           :: BETABR, START,  HMAX2,  CURRENT
  REAL(R8),   POINTER,            DIMENSION(:,:)     :: U,      W,      T2,     AZ,     RHO,    ST,     SB
  REAL(R8),   POINTER,            DIMENSION(:,:)     :: DLTLIM, VSH,    ADMX,   DM,     ADMZ,   HDG,    HPG,    GRAV
  REAL(R8),   TARGET,ALLOCATABLE, DIMENSION(:,:)     :: T1,     TSS
  REAL(R8),   TARGET,ALLOCATABLE, DIMENSION(:,:,:)   :: C1,     C2,     C1S,    CSSB,   CSSK
  REAL(R8),   TARGET,ALLOCATABLE, DIMENSION(:,:,:)   :: KF,     CD
  REAL(R8),   TARGET,ALLOCATABLE, DIMENSION(:,:,:)   :: HYD
  REAL(R8),       TARGET,ALLOCATABLE, DIMENSION(:,:,:,:) :: AF,     EF
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: ICETH,  ELKT,   HMULT,  CMULT,  CDMULT, WIND2,  AZMAX,  PALT, Z0
  REAL,              ALLOCATABLE, DIMENSION(:)       :: TN_SEDSOD_NH4,NH3GASLOSS,TP_SEDSOD_PO4,TPOUT,TPTRIB,TPDTRIB,TPWD,TPPR,TPIN,TNOUT,TNTRIB,TNDTRIB,TNWD,TNPR,TNIN,ATMDEP_P,ATMDEP_N   !TP_SEDBURIAL,TN_SEDBURIAL,
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: QSS,    VOLUH2, VOLDH2, QUH1,   QDH1,   UXBR,   UYBR,   VOL
  REAL,              ALLOCATABLE, DIMENSION(:,:,:)   :: ALLIM,  APLIM,  ANLIM,  ASLIM,  KFS
  REAL,              ALLOCATABLE, DIMENSION(:,:,:)   :: ELLIM,  EPLIM,  ENLIM,  ESLIM
  INTEGER                                            :: W2ERR=33,  WRN=32
  INTEGER                                            :: IMX,    KMX,    NBR,    NTR,    NWD,    NWB,    NCT,    NBOD, NTR1     ! SW 2/17/2021
  INTEGER                                            :: NST,    NSP,    NGT,    NPI,    NPU,    NWDO,   NIKTSR, NUNIT
  INTEGER                                            :: JW,     JB,     JC,     IU,     ID,     KT,     I,      JJB
  INTEGER                                            :: NOD,    NDC=27, NAL,    NSS,    NHY=15, NFL=142,NEP,    NEPT
  INTEGER                                            :: NZP,    NZPT,   JZ,     NZOOS,  NZOOE,  NMC,    NMCT  ! number of zooplankton groups, CONSTIUENT NUMBER FOR ZOOPLANKTON, START AND END
  INTEGER                                            :: NGCS,   NGCE   
  INTEGER, POINTER,               DIMENSION(:)       :: SNP,    PRF,    VPL,    CPL,    SPR,    FLX,    FLX2,   SPRV  ! SE 9/28/2018
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: BS,     BE,     US,     CUS,    DS,     JBDN
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: KB,     KTI,    SKTI,   KTWB,   KBMIN,  CDHS
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: UHS,    DHS,    UQB,    DQB
  INTEGER, TARGET,   ALLOCATABLE, DIMENSION(:,:)     :: OPT
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: NBODC, NBODN, NBODP        ! CB 6/6/10
  LOGICAL,           ALLOCATABLE, DIMENSION(:)       :: ICE,    ICE_CALC,LAYERCHANGE, BR_INACTIVE, BR_NOTECPLOT
  CHARACTER(10)                                      :: CCTIME
  CHARACTER(12)                                      :: CDATE
  CHARACTER(72)                                      :: RSIFN
  CHARACTER(180)                                     :: MODDIR                     ! CURRENT WORKING DIRECTORY
  REAL(R8),     SAVE, ALLOCATABLE, DIMENSION(:,:)    :: RATZ,   CURZ1,  CURZ2,  CURZ3    ! SW 5/15/06
  REAL(R8)                                           :: G=9.81D0,PI=3.14159265359D0
  REAL(R8)                                           :: DENSITY
  EXTERNAL DENSITY
END MODULE GLOBAL
MODULE GEOMC
  USE PREC
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: JBUH,   JBDH,   JWUH,   JWDH
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: ALPHA,  SINA,   COSA,   SLOPE,  BKT,    DLX,    DLXR, SLOPEC, SINAC
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: H,      H1,     H2,     BH1,    BH2,    BHR1,    BHR2,   AVHR, BHRATIO
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: B,      BI,     BB,     BH,     BHR,    BR,      EL,     AVH1,  AVH2, BNEW ! SW 1/23/06
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: DEPTHB, DEPTHM, FETCHU, FETCHD
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: CW      ! Column widths - also used by MACROPHYTEC
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: Z, ELWS, SELWS
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: BCONSTRICTION
  REAL(R8)                                           :: HTMP1,  HTMP2      ! temporary variables    SR 7/2024
  LOGICAL,           ALLOCATABLE, DIMENSION(:,:)     :: CONSTRICTION
END MODULE GEOMC
MODULE NAMESC
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: LNAME
  CHARACTER(9),      ALLOCATABLE, DIMENSION(:)       :: CUNIT,  CUNIT2, CUNIT3    ! (6) SW 8/24/2023
  CHARACTER(15),      ALLOCATABLE, DIMENSION(:)      :: CNAME2, CDNAME2
  CHARACTER(9),      ALLOCATABLE, DIMENSION(:)       :: FMTH,   FMTC,   FMTCD
  CHARACTER(43),     ALLOCATABLE, DIMENSION(:)       :: CNAME1, CDNAME1
  CHARACTER(43),     ALLOCATABLE, DIMENSION(:)       :: CNAME,  CNAME3, CDNAME, CDNAME3, HNAME
  CHARACTER(72),     ALLOCATABLE, DIMENSION(:)       :: TITLE
  CHARACTER(10),     ALLOCATABLE, DIMENSION(:,:)     :: CONV
END MODULE NAMESC
MODULE STRUCTURES
  USE PREC
  REAL(R8)                                           :: DIA,    FMAN,   CLEN,   CLOSS,  UPIE,   DNIE
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: QOLD,   QOLDS,  VMAX,   DTP,    DTPS
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: EGT,    A1GT,   B1GT,   G1GT,   A2GT,   B2GT,   G2GT, EGT2
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: QGT,    GTA1,   GTB1,   GTA2,   GTB2,   BGT
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: QSP,    A1SP,   B1SP,   A2SP,   B2SP,   ESP
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: EUPI,   EDPI,   WPI,    DLXPI,  FPI,    FMINPI, QPI, BP
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: YS,     VS,     YSS,    VSS,    YST,    VST,    YSTS,   VSTS
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: IUPI,   IDPI,   JWUPI,  JWDPI,  JBDPI,  JBUPI
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: IUSP,   IDSP,   JWUSP,  JWDSP,  JBUSP,  JBDSP
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: IUGT,   IDGT,   JWUGT,  JWDGT,  JBUGT,  JBDGT
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: IWR,    KTWR,   KBWR
  REAL,              ALLOCATABLE, DIMENSION(:)       :: EKTWR,  EKBWR     ! SW 3/18/16
  LOGICAL,           ALLOCATABLE, DIMENSION(:)       :: LATERAL_SPILLWAY, LATERAL_PIPE, LATERAL_GATE, LATERAL_PUMP, BEGIN, WLFLAG, PUMP_DOWNSTREAM
  CHARACTER(8),      ALLOCATABLE, DIMENSION(:)       :: LATGTC, LATSPC, LATPIC, LATPUC, DYNGTC, DYNPIPE, DYNPUMP                         ! SW 5/10/10
  CHARACTER(8)                                       :: GT2CHAR 
  REAL(R8),      ALLOCATABLE, DIMENSION(:)           :: EPU,    STRTPU, ENDPU,  EONPU,  EOFFPU, QPU
  INTEGER,       ALLOCATABLE, DIMENSION(:)           :: IUPU,   IDPU,   KTPU,   KBPU,   JWUPU,  JWDPU,  JBUPU,  JBDPU
  REAL(R8)                                           :: THR=0.01D0, OMEGA=0.8D0, EPS2=0.0001D0
  INTEGER                                            :: NN=19, NNPIPE=19, NC=7
  REAL,              ALLOCATABLE, DIMENSION(:)       :: EGTO,BGTO       
  CHARACTER(8),      ALLOCATABLE, DIMENSION(:)       :: GTIC            
  LOGICAL,      ALLOCATABLE, DIMENSION(:,:)          :: ACTIVE_RULE_W2SELECTIVE
END MODULE STRUCTURES
MODULE TRANS
  USE PREC
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: THETA
  REAL(R8),POINTER,               DIMENSION(:,:)     :: COLD,   CNEW,   SSB,    SSK
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: DX,     DZ,     DZQ
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: ADX,    ADZ,    AT,     VT,     CT,     DT
END MODULE TRANS
MODULE SURFHE
USE PREC
  REAL(R8)                                           :: RHOWCP     !, PHISET
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: ET,     CSHE,   LAT,    LONGIT, SHADE,  RB,     RE,     RC
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: WIND,   WINDH,  WSC,    AFW,    BFW,    CFW,    PHI0
  LOGICAL,       ALLOCATABLE, DIMENSION(:)       :: RH_EVAP
  INTEGER,       ALLOCATABLE, DIMENSION(:)       :: IWIND  !MLM 08/12/05
END MODULE SURFHE
MODULE TVDC
  USE PREC
  REAL(R8),              ALLOCATABLE, DIMENSION(:)       :: QIN,    QTR,    QDTR,   PR,     ELUH,   ELDH,   QSUM
  REAL(R8),              ALLOCATABLE, DIMENSION(:)       :: TIN,    TTR,    TDTR,   TPR,    TOUT,   TWDO,   TIND,   QIND
  REAL(R8),              ALLOCATABLE, DIMENSION(:)       :: TAIR,   TDEW,   CLOUD,  PHI,    SRON,   PALT_JW,ELWS_INI                              ! systdg PALT_JW, ELWS_INI
  REAL(R8),              ALLOCATABLE, DIMENSION(:,:)     :: CIN,    CTR,    CDTR,   CPR,    CIND,   TUH,    TDH,    QOUT
  REAL(R8),              ALLOCATABLE, DIMENSION(:,:,:)   :: CUH,    CDH
  REAL(R8),              ALLOCATABLE, DIMENSION(:)       :: QWD,    QWDSAV                                                !SR 06/29/2021
  INTEGER                                            :: NAC,    NOPEN
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: NACPR,  NACIN,  NACDT,  NACTR,  NACD,   CN, CDNN
  INTEGER,           ALLOCATABLE, DIMENSION(:,:)     :: TRCN,   INCN,   DTCN,   PRCN
  LOGICAL                                            :: CONSTITUENTS
  CHARACTER(72)                                      :: QGTFN,  QWDFN,  WSCFN,  SHDFN
  CHARACTER(72),     ALLOCATABLE, DIMENSION(:)       :: METFN,  QOTFN,  QINFN,  TINFN,  CINFN,  QTRFN,  TTRFN,  CTRFN,  QDTFN
  CHARACTER(72),     ALLOCATABLE, DIMENSION(:)       :: TDTFN,  CDTFN,  PREFN,  TPRFN,  CPRFN,  EUHFN,  TUHFN,  CUHFN,  EDHFN
  CHARACTER(72),     ALLOCATABLE, DIMENSION(:)       :: EXTFN,  CDHFN,  TDHFN
  INTEGER                                            :: WAIT_TIME,      TIME_BUFFER                                     !SR 11/26/19
  LOGICAL,           ALLOCATABLE, DIMENSION(:)       :: WAIT_FOR_TRIB_INPUT,    WAIT_FOR_BRANCH_INPUT                   !SR 11/26/19
  CHARACTER(240),    ALLOCATABLE, DIMENSION(:)       :: TR_FILEDIR,     BR_FILEDIR
END MODULE TVDC
MODULE KINETIC
  USE PREC
  REAL                                               :: KDO, PCO2,PCO2ATMPPM   ! SW 8/16/2020          
  REAL(R8)                                           :: O2CH4, O2H2S, O2FE2, O2MN2
  REAL(R8),    ALLOCATABLE, DIMENSION(:)             :: CoeffA_Turb, CoeffB_Turb,SECC_PAR 
  REAL(R8),    ALLOCATABLE, DIMENSION(:)             :: H2SQ10, H2S1DK, CH4Q10, CH41DK
  REAL(R8),    ALLOCATABLE, DIMENSION(:)             :: CH4R, H2SR, FEIIR, MNIIR, SO4R
  REAL(R8),    ALLOCATABLE, DIMENSION(:)             :: KFE_OXID, KFE_RED, KFEOOH_HalfSat, FeSetVel, KMN_OXID, KMN_RED, KMNO2_HalfSat, MnSetVel
  REAL(R8),    ALLOCATABLE, DIMENSION(:)             :: BACTQ10, BACT1DK, BACTLDK, BACTS  !A_DISG, B_DISG, C_DISG              
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: TDS,    COL,    NH4,    NO3,    PO4,   DSI,    PSI,    LDOM
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: N2, H2S, CH4, SO4, FEII, FEOOH, MNII, MNO2
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: WAGE, BACT, DGP
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: RDOM,   LPOM,   RPOM,   O2,     TIC,    ALK
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: COLSS,  NH4SS,  NO3SS,  PO4SS,  FESS,   DSISS,  PSISS,  LDOMSS
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: N2SS, H2SSS, CH4SS, SO4SS, FEIISS, FEOOHSS, MNIISS, MNO2SS
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: AGESS, BACTSS, DISGSS
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: RDOMSS, LPOMSS, RPOMSS, DOSS,   TICSS,  CASS
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: ALKSS          ! enhanced pH buffering
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: PH,     CO2   ,    HCO3,   CO3
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: TN,     TP,     TKN
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: DON,    DOP,    DOC,    NH3
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: PON,    POP,    POC
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: TON,    TOP,    TOC
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: APR,    CHLA,   ATOT
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: O2DG, TDG, TURB, SECCHID
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SSSI,   SSSO,   TISS,   TOTSS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: PO4AR,  PO4AG,  PO4AP,  PO4SD,  PO4SR,  PO4NS,  PO4POM, PO4DOM, PO4OM
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: CH4SR, H2SSR, FEIISR, MNIISR
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: PO4ER,  PO4EG,  PO4EP,  TICEP,  DOEP,   DOER
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: NH4ER,  NH4EG,  NH4EP,  NO3EG,  DSIEG,  LDOMEP, LPOMEP
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: NH4AR,  NH4AG,  NH4AP,  NH4SD,  NH4SR,  NH4D,   NH4POM, NH4DOM, NH4OM, NH3GAS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: NO3AG,  NO3D,   NO3SED
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: DSIAG,  DSID,   DSISD,  DSISR,  DSIS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: PSIAM,  PSID,   PSINS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: FENS,   FESR
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: LDOMAP, LDOMD,  LRDOMD, RDOMD
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: LPOMAP, LPOMD,  LRPOMD, RPOMD,  LPOMNS, RPOMNS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: DOAP,   DOAR,   DODOM,  DOPOM,  DOOM,   DONIT
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: DOSED,  DOSOD,  DOBOD,  DOAE
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: CBODU,  CBODDK, TICAP
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SEDD,   SODD,   SEDAS,  SEDOMS, SEDNS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SEDD1,SEDD2   
  REAL(R8),POINTER,               DIMENSION(:,:,:)   :: SS,     ALG,    CBOD,   CG
  REAL(R8),POINTER,               DIMENSION(:,:,:)   :: SSSS,   ASS,    CBODSS, CGSS
  REAL(R8),    POINTER,               DIMENSION(:,:,:)   :: AGR,    ARR,    AER,    AMR,    ASR
  REAL(R8),    POINTER,               DIMENSION(:,:,:)   :: EGR,    ERR,    EER,    EMR,    EBR
  REAL(R8),POINTER,               DIMENSION(:,:)     :: LDOMP,  RDOMP,  LPOMP,  RPOMP,  LDOMN,  RDOMN,  LPOMN,  RPOMN
  REAL(R8),POINTER,               DIMENSION(:,:)     :: LDOMPSS,  RDOMPSS, LPOMPSS, RPOMPSS, LDOMNSS, RDOMNSS
  REAL(R8),POINTER,               DIMENSION(:,:)     :: LPOMNSS,  RPOMNSS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: LDOMPAP,  LDOMPEP, LPOMPAP, LPOMPNS, RPOMPNS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: LDOMNAP,  LDOMNEP, LPOMNAP, LPOMNNS, RPOMNNS
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SEDDP,    SEDASP,  SEDOMSP, SEDNSP,  LPOMEPP
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SEDDN,    SEDASN,  SEDOMSN, SEDNSN,  LPOMEPN, SEDNO3
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SEDDC,    SEDASC,  SEDOMSC, SEDNSC,  LPOMEPC
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: CBODNS,   SEDCB,   SEDCBP,  SEDCBN,  SEDCBC
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: SEDBR,    SEDBRP,  SEDBRC,  SEDBRN, CO2REAER        !CB 11/30/06
  REAL(R8),POINTER,               DIMENSION(:,:,:)   :: CBODP,    CBODN       ! CB 6/6/10
  REAL(R8),POINTER,               DIMENSION(:,:,:)   :: CBODPSS,    CBODNSS       ! CB 6/6/10
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: CBODNSP,  CBODNSN          ! cb 6/6/10
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: DOH2S,DOCH4,DOSEDIA, DOFE2
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: H2SREAER,CH4REAER,CH4D,H2SD,SDINC,SDINP,SDINN,H2SSEDD
  REAL(R8),    POINTER,               DIMENSION(:,:)     :: FE2D,SDINFEOOH,SDINMNO2,MN2D,DOMN2
  REAL,              ALLOCATABLE, DIMENSION(:,:,:)   :: EPM,    EPD,    EPC
  REAL,              ALLOCATABLE, DIMENSION(:)       :: CGQ10,  CG0DK,  CG1DK,  CGS, CGLDK, CGKLF, CGCS, CGR  !LCJ 2/26/15 SW 10/16/15
  REAL,              ALLOCATABLE, DIMENSION(:)       :: SOD,    SDK,    LPOMDK, RPOMDK, LDOMDK, RDOMDK, LRDDK,  LRPDK
  REAL,              ALLOCATABLE, DIMENSION(:)       :: SDK1,sdk2    ! amaila
  REAL,              ALLOCATABLE, DIMENSION(:)       :: SSS,    TAUCR,  POMS,   seds, sedb, SSCS  !  , SSFLOC   cb 11/27/06   SR 04/21/13
  REAL,              ALLOCATABLE, DIMENSION(:)       :: AG,     AR,     AE,     AM,     AS,     AHSN,   AHSP,   AHSSI,  ASAT
  REAL,              ALLOCATABLE, DIMENSION(:)       :: AP,     AN,     AC,     ASI,    ACHLA,  APOM,   ANPR
  REAL,              ALLOCATABLE, DIMENSION(:)       :: EG,     ER,     EE,     EM,     EB
  REAL,              ALLOCATABLE, DIMENSION(:)       :: EHSN,   EHSP,   EHSSI,  ESAT,   EHS,    ENPR
  REAL,              ALLOCATABLE, DIMENSION(:)       :: EP,     EN,     EC,     ESI,    ECHLA,  EPOM
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: BETA,   EXH2O,  EXSS,   EXOM,   EXA
  REAL,              ALLOCATABLE, DIMENSION(:)       :: DSIR,   PSIS,   PSIDK,  PARTSI
  REAL,              ALLOCATABLE, DIMENSION(:)       :: ORGP,   ORGN,   ORGC,   ORGSI
  REAL,              ALLOCATABLE, DIMENSION(:)       :: pbiom,nbiom,cbiom  ! Amaila, cb 6/8/17
  REAL,              ALLOCATABLE, DIMENSION(:)       :: BODP,   BODN,   BODC
  REAL,              ALLOCATABLE, DIMENSION(:)       :: PO4R,   PARTP
  REAL,              ALLOCATABLE, DIMENSION(:)       :: NH4DK,  NH4R,   NO3DK,  NO3S, FNO3SED
  REAL,              ALLOCATABLE, DIMENSION(:)       :: O2AG,   O2AR,   O2OM,   O2NH4
  REAL,              ALLOCATABLE, DIMENSION(:)       :: O2EG,   O2ER
  REAL,              ALLOCATABLE, DIMENSION(:)       :: CO2R
  REAL,              ALLOCATABLE, DIMENSION(:)       :: KBOD,   TBOD,   RBOD
  REAL,              ALLOCATABLE, DIMENSION(:)       :: CAQ10,  CADK,   CAS
  REAL,              ALLOCATABLE, DIMENSION(:)       :: OMT1,   OMT2,   SODT1,  SODT2,  NH4T1,  NH4T2,  NO3T1,  NO3T2
  REAL,              ALLOCATABLE, DIMENSION(:)       :: OMK1,   OMK2,   SODK1,  SODK2,  NH4K1,  NH4K2,  NO3K1,  NO3K2, KG_H2O_CONSTANT
  REAL,              ALLOCATABLE, DIMENSION(:)       :: AT1,    AT2,    AT3,    AT4
  REAL,              ALLOCATABLE, DIMENSION(:)       :: AK1,    AK2,    AK3,    AK4
  REAL,              ALLOCATABLE, DIMENSION(:)       :: ET1,    ET2,    ET3,    ET4
  REAL,              ALLOCATABLE, DIMENSION(:)       :: EK1,    EK2,    EK3,    EK4
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: WIND10, CZ,     QC,     QERR
  REAL,              ALLOCATABLE, DIMENSION(:)       :: REAER,  RCOEF1, RCOEF2, RCOEF3, RCOEF4, DGPO2, MINKL
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: DO1,    DO2,    DO3,    GAMMA, F_NH3
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: SED,    FPSS,   FPFE, FE
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: SED1,sed2,SED1ic,sed2ic   ! cb 6/17/17
  REAL,              ALLOCATABLE, DIMENSION(:,:,:)   :: CBODD
  REAL,              ALLOCATABLE, DIMENSION(:)       :: CBODS,PFLUXIN,NFLUXIN
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: ORGPLD,  ORGPRD,   ORGPLP,    ORGPRP,  ORGNLD,  ORGNRD, ORGNLP, ORGNRP
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: LDOMPMP, LDOMNMP,  LPOMPMP,   LPOMNMP, RPOMPMP, RPOMNMP
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: LPZOOINP,LPZOOINN, LPZOOOUTP, LPZOOOUTN
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: SEDC,    SEDN, SEDP, SEDNINFLUX, SEDPINFLUX  ! SW 4/2016
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: SEDVPC,  SEDVPP, SEDVPN
  REAL,              ALLOCATABLE, DIMENSION(:,:)     :: SDKV,    SEDDKTOT
  INTEGER                                            :: NLDOMP,NRDOMP,NLPOMP,NRPOMP,NLDOMN,NRDOMN,NLPOMN,NRPOMN
  INTEGER,           ALLOCATABLE, DIMENSION(:)       :: NAF,    NEQN,   ANEQN,  ENEQN  !, FLOCEQN   ! SR 04/21/13
  INTEGER,           ALLOCATABLE, DIMENSION(:,:)     :: KFCN
  LOGICAL,           ALLOCATABLE, DIMENSION(:)       :: SEDIMENT_RESUSPENSION
  CHARACTER(8),      ALLOCATABLE, DIMENSION(:)       :: CAC,    REAERC, AVERTM
  CHARACTER(10),     ALLOCATABLE, DIMENSION(:,:)     :: LFPR
  ! enhanced pH buffering start
  CHARACTER(8)                                       :: nh4bufc,po4bufc,ombufc,omtype,pombufc,phbufc,ncalkc,CO2YEARLYPPM
  INTEGER                                            :: nag,nagi
  LOGICAL                                            :: ammonia_buffering, phosphate_buffering, om_buffering, pom_buffering, pH_buffering, NONCON_ALKALINITY, ALGAE_SETTLING_EXIST  
  Logical,              ALLOCATABLE, DIMENSION(:,:)  :: sdfirstadd
  REAL,              ALLOCATABLE, DIMENSION(:)       :: sdeni,pki,pksd,sden,pk,fract
  ! enhanced pH buffering end
  !
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: LDOMC,   RDOMC,   LPOMC,   RPOMC            ! ORGANIC CARBON STATE VARIABLES
  REAL(R8),    POINTER,           DIMENSION(:,:)     :: LDOMCSS, RDOMCSS, LPOMCSS, RPOMCSS                                             
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: PSIEM,   SEDEB                                                                  
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LPOMPEP, LPOMNEP, LPOMCEP
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LPOMHD,  RPOMHD
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LDOMCAP, LDOMCEP, LPOMCAP, LPOMCNS, RPOMCNS
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LDOMPD,  LRDOMPD, RDOMPD,  LPOMPD,  LRPOMPD, RPOMPD,  LPOMPHD, RPOMPHD 
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LDOMND,  LRDOMND, RDOMND,  LPOMND,  LRPOMND, RPOMND,  LPOMNHD, RPOMNHD 
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LDOMCD,  LRDOMCD, RDOMCD,  LPOMCD,  LRPOMCD, RPOMCD,  LPOMCHD, RPOMCHD
  REAL,        ALLOCATABLE,       DIMENSION(:)       :: LPOMHK,  RPOMHK                                                                
  REAL,        ALLOCATABLE,       DIMENSION(:)       :: LDOMPDK, LRDOMPDK,RDOMPDK, LDOMNDK, LRDOMNDK,RDOMNDK, LDOMCDK, LRDOMCDK,RDOMCDK
  REAL,        ALLOCATABLE,       DIMENSION(:)       :: LPOMPDK, LRPOMPDK,RPOMPDK, LPOMNDK, LRPOMNDK,RPOMNDK, LPOMCDK, LRPOMCDK,RPOMCDK
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LDOMCMP, LPOMCMP, RPOMCMP
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LPZOOINC,LPZOOOUTC
  REAL,        ALLOCATABLE,       DIMENSION(:,:)     :: LDOP,    RDOP,    LPOP,    RPOP,    LDON,    RDON,    LPON,    RPON,    LDOC,   RDOC,   LPOC,  RPOC 
  INTEGER                                            :: NLDOMC,  NRDOMC,  NLPOMC,  NRPOMC  
  !  
  CONTAINS
  REAL    FUNCTION SATO (T,SAL,P,SALT_WATER)
      REAL(R8) :: T,SAL
      REAL(R8) :: P
      LOGICAL  :: SALT_WATER
      SATO = EXP(7.7117-1.31403*(LOG(T+45.93)))*P
      IF (SALT_WATER) THEN
          SATO = EXP(LOG(SATO)-SAL*(1.7674E-2-1.0754E1/(T+273.15)+2.1407E3/(T+273.15)**2))            ! SAL is in ppt
      ELSEIF(SAL > 100.)THEN
          SATO = EXP(LOG(SATO)-(SAL/1000.)*(1.7674E-2-1.0754E1/(T+273.15)+2.1407E3/(T+273.15)**2))    ! SAL is in mg/l
      ENDIF
    END FUNCTION SATO
  REAL  FUNCTION FR (TT,TT1,TT2,SK1,SK2)
      REAL(R8) :: TT
      REAL     :: TT1,TT2,SK1,SK2
      FR = SK1*EXP(LOG(SK2*(1.0-SK1)/(SK1*(1.0-SK2)))/(TT2-TT1)*(TT-TT1))
    END FUNCTION FR
  REAL  FUNCTION FF (TT,TT3,TT4,SK3,SK4)
      REAL     :: TT3,TT4,SK3,SK4
      REAL(R8) :: TT
      FF = SK4*EXP(LOG(SK3*(1.0-SK4)/(SK4*(1.0-SK3)))/(TT4-TT3)*(TT4-TT))
    END FUNCTION FF
END MODULE KINETIC
MODULE SELWC
  USE PREC
  REAL(R8),              ALLOCATABLE, DIMENSION(:)    :: VNORM,  QNEW
  REAL(R8),              ALLOCATABLE, DIMENSION(:,:)  :: QDSW                                                         !SR 12/19/2022 Output
  !REAL,                  ALLOCATABLE, DIMENSION(:)    :: EWD, TAVGW                   ! cb 1/16/13
  real,                  allocatable, dimension(:)    :: ewd
  REAL(R8),              ALLOCATABLE, DIMENSION(:,:)  :: QSTR, QSTRSAV,  QSW     ! SR 10/1/2023
  !REAL,                  ALLOCATABLE, DIMENSION(:,:)  :: ESTR,   WSTR, TAVG            ! SW Selective 7/30/09
  real,                  allocatable, dimension(:,:)  :: estr,   wstr                  ! cb 1/16/13
  real(r8),              allocatable, dimension(:,:)  :: tavg                  ! cb 1/16/13
  real(r8),              allocatable, dimension(:)    :: tavgw                  ! cb 1/16/13
  REAL(R8),                  ALLOCATABLE, DIMENSION(:,:)  :: CAVGW,  CDAVGW
  REAL(R8),                  ALLOCATABLE, DIMENSION(:,:,:):: CAVG,   CDAVG
  INTEGER,               ALLOCATABLE, DIMENSION(:)    :: NSTR,   NOUT,   KTWD,   KBWD,   KTW,   KBW
  INTEGER,               ALLOCATABLE, DIMENSION(:,:)  :: KTSW,   KBSW,   KOUT
  CHARACTER(8),          ALLOCATABLE, DIMENSION(:)    :: DYNSTRUC
END MODULE SELWC
MODULE GDAYC
  REAL                                           :: DAYM,   EQTNEW
  INTEGER                                        :: JDAYG,  IMON,      YEAR,   GDAY, YEAROLD
  LOGICAL                                        :: LEAP_YEAR
  CHARACTER(9)                                   :: MONTH
END MODULE GDAYC
MODULE SCREENC
  USE PREC
  REAL(R8)                                       :: JDAY,   DLTS1,  JDMIN,  MINDLT, DLTAV,  ELTMJD
  REAL,              ALLOCATABLE, DIMENSION(:)   :: ZMIN,   CMIN,   CMAX,   HYMIN,  HYMAX,  CDMIN,  CDMAX
  INTEGER                                        :: ILOC,   KLOC,   IMIN,   KMIN,   NIT,    NV,     JTT,     JWW
  INTEGER,           ALLOCATABLE, DIMENSION(:)   :: IZMIN
  CHARACTER(8),      ALLOCATABLE, DIMENSION(:)   :: ACPRC,  AHPRC,  ACDPRC
END MODULE SCREENC
MODULE TRIDIAG_V
USE PREC
!INTEGER,                             INTENT(IN)  :: S, E, N
!  REAL(R8),              DIMENSION(:), INTENT(IN)  :: A(E),V(E),C(E),D(E)
!  REAL(R8),              DIMENSION(:), INTENT(OUT) :: U(N)
  REAL(R8), ALLOCATABLE, DIMENSION(:)              :: BTA1, GMA1
  !REAL(R8), DIMENSION(1000)              :: BTA, GMA
!  INTEGER                                          :: I
END MODULE TRIDIAG_V
MODULE TDGAS
  REAL,              ALLOCATABLE, DIMENSION(:)   :: AGASSP, BGASSP, CGASSP, AGASGT, BGASGT, CGASGT, DGASGT, DGASSP  !SW 12/1/2025 
  INTEGER,           ALLOCATABLE, DIMENSION(:)   :: EQSP,   EQGT
END MODULE TDGAS
MODULE LOGICC
  LOGICAL                                        :: SUSP_SOLIDS,        OXYGEN_DEMAND,    UPDATE_GRAPH,     INITIALIZE_GRAPH
  LOGICAL                                        :: WITHDRAWALS,        TRIBUTARIES,      GATES, PIPES  
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: NO_WIND,            NO_INFLOW,        NO_OUTFLOW,       NO_HEAT
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: UPWIND,             ULTIMATE,         FRESH_WATER,      SALT_WATER
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: LIMITING_DLT,       TERM_BY_TERM,     MANNINGS_N,       PH_CALC
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: ONE_LAYER,          DIST_TRIBS,       PRECIPITATION
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: PRINT_SEDIMENT,     LIMITING_FACTOR,  READ_EXTINCTION,  READ_RADIATION
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: PRINT_SEDIMENT1, PRINT_SEDIMENT2  ! Amaila
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: UH_INTERNAL,        DH_INTERNAL,      UH_EXTERNAL,      DH_EXTERNAL
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: UQ_INTERNAL,        DQ_INTERNAL,      UQ_EXTERNAL,      DQ_EXTERNAL
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: UP_FLOW,            DN_FLOW,          INTERNAL_FLOW
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: DAM_INFLOW,         DAM_OUTFLOW                                    !TC 08/03/04
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: INTERP_METEOROLOGY, INTERP_INFLOW,    INTERP_DTRIBS,    INTERP_TRIBS
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: INTERP_WITHDRAWAL,  INTERP_HEAD,      INTERP_EXTINCTION
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: VISCOSITY_LIMIT,    CELERITY_LIMIT,   IMPLICIT_AZ,      TRAPEZOIDAL !SW 07/16/04
!  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: HYDRO_PLOT,         CONSTITUENT_PLOT, DERIVED_PLOT
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: INTERP_GATE     ! cb 8/13/2010
  LOGICAL,           ALLOCATABLE, DIMENSION(:,:) :: PRINT_DERIVED,      PRINT_HYDRO,      PRINT_CONST,      PRINT_EPIPHYTON
  LOGICAL,           ALLOCATABLE, DIMENSION(:,:) :: POINT_SINK,         INTERNAL_WEIR,    INTERP_OUTFLOW
  LOGICAL,       ALLOCATABLE, DIMENSION(:)       :: HEAD_FLOW
  LOGICAL,       ALLOCATABLE, DIMENSION(:)       :: UP_HEAD
END MODULE LOGICC
MODULE SHADEC
  integer, PARAMETER :: IANG=18
  REAL,PARAMETER                                 :: GAMA=(3.1415926*2.)/REAL(IANG)                         ! SW 10/17/05
  REAL,                           DIMENSION(IANG):: ANG                                                    ! SW 10/17/05
  REAL,              ALLOCATABLE, DIMENSION(:)   :: A00,    DECL,   HH,     TTLB,   TTRB,   CLLB,   CLRB   ! SW 10/17/05
  REAL,              ALLOCATABLE, DIMENSION(:)   :: SRLB1,  SRRB1,  SRLB2,  SRRB2,  SRFJD1, SRFJD2, SHADEI
  REAL,              ALLOCATABLE, DIMENSION(:,:) :: TOPO
  LOGICAL,           ALLOCATABLE, DIMENSION(:)   :: DYNAMIC_SHADE
  DATA ANG  /0.00000, 0.34907, 0.69813, 1.04720, 1.39626, 1.74533, 2.09440, 2.44346, &
            2.79253, 3.14159, 3.49066, 3.83972, 4.18879, 4.53786, 4.88692, 5.23599, 5.58505, 5.93412/      ! SW 10/17/05
END MODULE SHADEC
MODULE EDDY
  USE PREC
  CHARACTER(8),      ALLOCATABLE, DIMENSION(:)      :: AZC,IMPTKE
  REAL(R8),          ALLOCATABLE, DIMENSION(:)      :: WSHY,   FRIC
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)    :: FRICBR, DECAY
  REAL(R8),          ALLOCATABLE, DIMENSION (:,:,:) :: TKE
  REAL(R8),          ALLOCATABLE, DIMENSION (:,:)   :: AZT, DZT
  REAL(R8),          ALLOCATABLE, DIMENSION(:)      :: USTARBTKE, E
  REAL(R8),          ALLOCATABLE, DIMENSION(:)      :: EROUGH, ARODI, TKELATPRDCONST, STRICK
  !INTEGER,           ALLOCATABLE, DIMENSION(:)      :: FIRSTI, LASTI, WALLPNT, TKEBC
  INTEGER,           ALLOCATABLE, DIMENSION(:)      :: WALLPNT, TKEBC
  LOGICAL,           ALLOCATABLE, DIMENSION(:)      :: STRICKON, TKELATPRD
END MODULE EDDY
! MACROPHYTEC module removed -大型植物模块已移除
MODULE POROSITYC
    REAL,              ALLOCATABLE, DIMENSION(:)     :: SAREA, VOLKTI
    REAL,              ALLOCATABLE, DIMENSION(:,:)   :: POR,   VOLI,   VSTEMKT
    REAL,              ALLOCATABLE, DIMENSION(:,:,:) :: VSTEM
END MODULE POROSITYC
! ZOOPLANKTONC module removed - 2026-03-30
MODULE INITIALVELOCITY
  USE PREC
  LOGICAL                                            :: INIT_VEL, ONCE_THROUGH
  REAL(R8),          ALLOCATABLE, DIMENSION(:)       :: QSSI,ELWSS,UAVG
  REAL(R8),          ALLOCATABLE, DIMENSION(:,:)     :: BSAVE
  LOGICAL,           ALLOCATABLE, DIMENSION(:)       :: LOOP_BRANCH
END MODULE INITIALVELOCITY
! ENVIRPMOD module removed - 2026-03-30

MODULE ALGAE_TOXINS
    USE PREC
    INTEGER, PARAMETER                                 :: NUMATOXINS=4
    INTEGER                                            :: NATS, NATE, ATOXIN_DEBUG_FN=2501
    LOGICAL                                            :: ALGAE_TOXIN    !,ALGAE_TOXIN_FILE
    REAL, ALLOCATABLE, DIMENSION (:,:)                 :: CTP,CTB
    REAL, DIMENSION (:)                                :: CTREL(NUMATOXINS),CTD(NUMATOXINS)
    REAL(R8),POINTER,               DIMENSION(:,:,:)   :: EX_TOXIN, CTESS  
    REAL(R8),ALLOCATABLE, DIMENSION(:,:,:)             :: IN_TOXIN
    CHARACTER(2)                                       :: ATOX, ATOX_DEBUG
END MODULE ALGAE_TOXINS
    
Module MAIN
  USE PREC
  ! Variable declaration
  Real(8), Allocatable, Dimension(:) :: IceQSS
  !INTEGER       :: J,NIW,NGC,NGCS,NTDS,NCCS,NGCE,NSSS,NSSE,NPO4,NNH4
  INTEGER       :: J,NIW,NGC,NTDS,NCCS,NSSS,NSSE,NPO4,NNH4
  INTEGER       :: NN2, NH2S, NCH4, NSO4, NFEII, NFEOOH, NMNII, NMNO2, NMFT
  INTEGER       :: NWAGE, NBACT, NDGP, I_LWAT, I_SW, TZONE   ! SW 9/12/2025 
  INTEGER       :: NNO3,NDSI,NPSI,NFE,NLDOM,NRDOM,NLPOM,NRPOM,NBODS
  INTEGER       :: KF_DO_SED,KF_DO_SOD,KF_SED_PBURIAL,KF_SED_NBURIAL,KF_NH4_SD,KF_NH4_SR,KF_PO4_SD,KF_PO4_SR,KF_CO2X
  INTEGER       :: KF_DOH2S,KF_SDINC,KF_DOCH4,KF_FE2D,KF_MN2D,KF_SEDD
  INTEGER       :: KF_NO3D,KF_NO3AG,KF_NO3EG,KF_NO3SED,KF_NH3GAS
  INTEGER       :: DOC_DER,POC_DER,TOC_DER,DON_DER,PON_DER,TON_DER,TKN_DER,TN_DER,NH3_DER,DOP_DER,POP_DER,TOP_DER,TP_DER,APR_DER
  INTEGER       :: CHLA_DER,ATOT_DER,O2DG_DER,TDG_DER,TURB_DER,TOTSS_DER,TISS_DER,CBODU_DER,PH_DER,CO2_DER,HCO3_DER,CO3_DER,SECCHI_DER
  INTEGER       :: NBODE, NAS, NAE, NDO, NTIC, NALK, NTRT, NWDT
  INTEGER       :: NDT, JS, JP, JG,JT, JH, NTSR, NIWDO, NRSO,JD
  INTEGER       :: NBODCS, NBODCE, NBODPS, NBODPE, NBODNS, NBODNE, IBOD, JCB       ! cb 6/6/10
  INTEGER       :: JF,JA,JM,JE,JJZ,K,L3,L1,L2,NTAC,NDSP,NTACMX,NTACMN,JFILE,M
  INTEGER       :: KBP,JWR,JJJB,JDAYNX,NIT1,JWD,L,IUT,IDT    !,KTIP - NOT NEEDED SW 7/8/2024
  INTEGER       :: INCRIS,IE,II,NDLT,NRS,INCR,IS,JAC
  REAL          :: JDAYTS, JDAY1, TMSTRT, TMEND,HMAX, DLXMAX,CELRTY,NXTVD,TTIME
  REAL(R8)      :: DLMR, TICE, CC_LW, CC_SW                        ! SW 4/19/10
  REAL(R8)      :: TAU1,TAU2, ELTMS, HMIN,DLXMIN, RHOICP
  REAL(R8)      :: WLF,FLOWBALF,NPBALF,NXWL,NXFLOWBAL,NXNPBAL
  REAL(R8)      :: HRAD, SW_ALBEDO,SW_BA,SW_K1,AOD380NM,AOD500NM     ! SW 9/12/2025
  REAL(R8)      :: ZB,WWT,DFC,GC2,UDR,UDL,AB, EFFRIC
  REAL(R8)      :: DEPKTI,COLB,COLDEP,SSTOT,RHOIN,VQIN,VQINI
  REAL(R8)      :: QINFR, ELT,RHOIRL1,V1,BHSUM,BHRSUM,WT1,WT2
  REAL(R8)      :: ICETHU, ICETH1, ICETH2, ICE_TOL=0.0050D0,DEL,HICE            ! SW 4/19/10
  REAL(R8)      :: DLTCAL,HEATEX,SROOUT,SROSED,SROIN,SRONET,TFLUX,HIA  
  REAL(R8)      :: TAIRV,EA,ES,DTV
  REAL(R8)      :: T2R4
  INTEGER       :: CON=10,    RSI,    GRF,  NDG=16,  FLOWBFN=9500, WLFN=9510, AERATEFN=9520, FISHHABFN=9530, MASSBFN=9501, LAKE_RIVER_CONTOUR=9540
  INTEGER       :: VSF,    SIF, JG_AGE  ! SR 7/27/2017
  INTEGER       :: JSG,    NNSG                         ! 1/16/13
  LOGICAL       :: ADD_LAYER,      SUB_LAYER,          WARNING_OPEN,    ERROR_OPEN,      VOLUME_WARNING, SURFACE_WARNING
  LOGICAL       :: PKSD_INPUT_WARNING                                                                                  !SR 11/09/19
  LOGICAL       :: END_RUN,        BRANCH_FOUND,       NEW_PAGE,        UPDATE_KINETICS, UPDATE_RATES
  LOGICAL       :: WEIR_CALC,      DERIVED_CALC,       RESTART_IN,      RESTART_OUT
  LOGICAL       :: SPILLWAY,       PUMPS, MWB_EXIST                  ! SW 12/2/2019
  LOGICAL       :: TIME_SERIES,    DOWNSTREAM_OUTFLOW, ICE_COMPUTATION
  LOGICAL       :: DSI_CALC, PO4_CALC, N_CALC             ! cb 10/12/11
  LOGICAL       :: TDGON , GAS_TRANSFER_UPDATE                              
  LOGICAL       :: WAIT_FOR_INFLOW_RESULTS  ! SW 2/9/2019; FISH_PARTICLE_EXIST removed - 2026-03-31
  CHARACTER(1)  :: ESC
  CHARACTER(2)  :: DEG
  CHARACTER(3)  :: GDCH
  CHARACTER(8)  :: WLC,FLOWBALC,NPBALC
  CHARACTER(8)  :: RSOC,   RSIC,   CCC,   LIMC,   WDOC,   TSRC,   EXT, SELECTC, CLOSEC, HABTATC,ENVIRPC, AERATEC, INITUWL, DLTINTER      ! SW 7/31/09; 8/24/09
  CHARACTER(10) :: BLANK='          ', SEDCH,   SEDPCH,   SEDNCH,   SEDCCH 
  CHARACTER(12) :: BLANK1='      -99.00'       ! SR 10/1/2023 
  CHARACTER(72) :: WDOFN,  RSOFN,  TSRFN, SEGNUM, LINE, SEGNUM2, TSRFN1
  LOGICAL       :: RETLOG, STANDING_BIOMASS_DECAY, PHBUFF_EXIST, WATER_AGE_ACTIVE ! SW 5/26/15  SR 7/27/2017
  LOGICAL       :: DYNPIPEADJUST            ! SW 2/18/2020
  CHARACTER(2)  :: DYNPAD
  INTEGER       :: DYNPAD_SEG,DYNPAD_PIPE,DYNPIPELOG=9505
  
  REAL          :: DYNPAD_WL,DYNPAD_MAXRATE,DYNPAD_PERCENTCHANGE
  INTEGER                                   :: N_WAITS, NWAIT                                                           !SR 11/26/19
  INTEGER,        ALLOCATABLE, DIMENSION(:) :: WAIT_INDEX                                                               !SR 11/26/19
  CHARACTER(2),   ALLOCATABLE, DIMENSION(:) :: WAIT_TYPE                                                                !SR 11/26/19
  CHARACTER(240), ALLOCATABLE, DIMENSION(:) :: FILEDIR

  LOGICAL       :: ORGC_CALC

! Allocatable array declarations

  REAL,          ALLOCATABLE, DIMENSION(:)     :: ETUGT,  EBUGT,  ETDGT,  EBDGT
  REAL,          ALLOCATABLE, DIMENSION(:)     :: ETUSP,  EBUSP,  ETDSP,  EBDSP
  REAL,          ALLOCATABLE, DIMENSION(:)     :: ETUPI,  EBUPI,  ETDPI,  EBDPI,  ETPU,   EBPU,   TSEDF
  REAL,          ALLOCATABLE, DIMENSION(:)     :: CSUM,   CDSUM,  X1
  REAL,          ALLOCATABLE, DIMENSION(:)     :: RSOD,   RSOF,   DLTD,   DLTF,   DLTMAX
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: QWDO
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: ICETHI, ALBEDO, HWI,    BETAI,  GAMMAI, ICEMIN, ICET2,  CBHE,   TSED
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: FI,     SEDCI,  FSOD,   FSED,   AX,     RANLW,    T2I,    ELBOT,  DXI
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: SEDCI1,SEDCI2,fsedc1,fsedc2 ! cb 6/7/17, Amaila
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: WSHX     ! QINT,   QOUTT,  
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: SROSH,  EV, RS, RN
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: QDT,    QPR,    ICESW
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: XBR,    QPRBR,  EVBR,   TPB
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: DLXRHO, Q,      QSSUM, Volume_WB, Surface_Area     ! SW 1/11/2026
  REAL,          ALLOCATABLE, DIMENSION(:)     :: ELTRT,  ELTRB
  REAL,          ALLOCATABLE, DIMENSION(:)     :: TSRD,   TSRF,   WDOD,   WDOF
  REAL,          ALLOCATABLE, DIMENSION(:)     :: QOAVR,  QIMXR,  QOMXR,  QTAVB,  QTMXB
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: FETCH,  ETSR
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: QINSUM, TINSUM
  REAL,          ALLOCATABLE, DIMENSION(:)     :: CDTOT
  REAL,          ALLOCATABLE, DIMENSION(:)     :: SEDCIP, SEDCIN, SEDCIC, SEDCIS
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: ESTRT,  WSTRT,  CINSUM, HAB
  REAL(R8),      ALLOCATABLE, DIMENSION(:,:)   :: P,      HSEG,   QTOT
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: CPB,    COUT,   CWDO,   CDWDO, KFJW
  REAL(R8),      ALLOCATABLE, DIMENSION(:,:)   :: C2I,    EPICI
  REAL(R8),      ALLOCATABLE, DIMENSION(:,:)   :: QTRF
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: SNPD,   SCRD,   PRFD,   SPRD,   CPLD,   VPLD,   FLXD
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: SNPF,   SCRF,   PRFF,   SPRF,   CPLF,   VPLF,   FLXF
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: TVP,    SEDVP,  QINF
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: SEDVP1,  SEDVP2    ! Amaila
  REAL(R8),      ALLOCATABLE, DIMENSION(:,:)   :: TSSUH1, TSSDH1, ATM_DEP_LOADING
  REAL(R8),      ALLOCATABLE, DIMENSION(:,:,:) :: CSSUH1, CSSDH1
  REAL,          ALLOCATABLE, DIMENSION(:,:,:) :: EPIVP,  CVP, macrcvp, macrclp   ! cb 8/21/15  
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: VOLB
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: DLVOL,  VOLG
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: A,      C,      D,      F,      V,      BTA,    GMA,    BHRHO
  REAL(R8),      ALLOCATABLE, DIMENSION(:)     :: DLVR,   ESR,    ETR
  REAL,          ALLOCATABLE, DIMENSION(:,:)   :: CMBRS
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: KTUGT,  KBUGT,  KTDGT,  KBDGT
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: KTUSP,  KBUSP,  KTDSP,  KBDSP
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: KTUPI,  KBUPI,  KTDPI,  KBDPI
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: NSNP,   NSCR,   NSPR,   NVPL,   NFLX,   NCPL,   BTH
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: VPR,    LPR,    NIPRF,  NISPR,  NPRF
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: NISNP
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: NBL,    KBMAX,  KBI
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: KBR,    IBPR
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: TSR
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: NPOINT, NL,     KTQIN,  KBQIN, ilayer    ! SW 1/23/06
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: ITR,    KTTR,   KBTR,   JBTR
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: IWD,    KWD,    JBWD
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: IWDO,   ITSR, JBTSR
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: ILAT,   JBDAM,  JSS
  INTEGER,       ALLOCATABLE, DIMENSION(:)     :: ICPL,   NACATD                                     
  INTEGER,       ALLOCATABLE, DIMENSION(:,:)   :: KTSWT,  KBSWT, ATMDCN
  INTEGER,       ALLOCATABLE, DIMENSION(:,:)   :: IPRF,   ISPR,   ISNP,   BL,     WDO,    CDN, WDO2
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: ALLOW_ICE,           PUMPON,        FETCH_CALC, ATM_DEPOSITION  ! ICE_IN,     RC/SW 4/28/11
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: DN_HEAD,        HEAD_BOUNDARY
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: PLACE_QIN,      PLACE_QTR,      SPECIFY_QTR
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: ISO_TEMP,       VERT_TEMP,      LONG_TEMP,     VERT_PROFILE,  LONG_PROFILE
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: SEDIMENT_CALC,  DETAILED_ICE,   IMPLICIT_VISC, SNAPSHOT,      PROFILE
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: SEDIMENT_CALC1, SEDIMENT_CALC2  ! Amaila
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: VECTOR,         CONTOUR,        SPREADSHEET,   SCREEN_OUTPUT
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: FLUX,           EVAPORATION,    ZERO_SLOPE
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: ISO_SEDIMENT,   VERT_SEDIMENT,  LONG_SEDIMENT
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: ISO_SEDIMENT1,   VERT_SEDIMENT1,  LONG_SEDIMENT1,ISO_SEDIMENT2,   VERT_SEDIMENT2,  LONG_SEDIMENT2  ! Amaila
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: VOLUME_BALANCE, ENERGY_BALANCE, MASS_BALANCE, BOD_CALC, ALG_CALC
  LOGICAL,       ALLOCATABLE, DIMENSION(:)     :: BOD_CALCP,BOD_CALCN                                                  ! cb 5/19/2011
  LOGICAL,       ALLOCATABLE, DIMENSION(:,:)   :: ISO_EPIPHYTON,  VERT_EPIPHYTON, LONG_EPIPHYTON, EPIPHYTON_CALC
  LOGICAL,       ALLOCATABLE, DIMENSION(:,:)   :: ISO_CONC,       VERT_CONC,      LONG_CONC,      TDG_SPILLWAY,   TDG_GATE
  LOGICAL,       ALLOCATABLE, DIMENSION(:,:)   :: iso_macrophyte,  vert_macrophyte, long_macrophyte   ! cb 8/21/15
  CHARACTER(4),  ALLOCATABLE, DIMENSION(:)     :: CUNIT1
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: SEG,    SEDRC,  TECPLOT
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: HPLTC,  CPLTC,  CDPLTC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: EXC,    EXIC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: GASGTC, GASSPC, ATM_DEPOSITIONC,ATM_DEPOSITION_INTERPOLATION
  CHARACTER(15),  ALLOCATABLE, DIMENSION(:)    :: CWDOC,  CDWDOC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: ICEC,   SEDCc,  SEDPRC, SNPC,   SCRC,   SPRC,   PRFC,DYNSEDK
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: SEDCc1,  SEDPRC1,SEDCc2,  SEDPRC2    ! Amaila
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: RHEVC,  VPLC,   CPLC,   AZSLC,  FETCHC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: DTRC,   SROC,   KFAC,   CDAC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: INCAC,  TRCAC,  DTCAC,  PRCAC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: WTYPEC, GRIDC                                                        !SW 07/16/04
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: PUSPC,  PDSPC,  PUGTC,  PDGTC,  PDPIC,  PUPIC,  PPUC,   TRC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: SLICEC, FLXC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: VBC,    MBC,    EBC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: PQC,    EVC,    PRC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: QINC,   QOUTC,  WINDC,  HEATC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: VISC,   CELC, DLTADD
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: SLTRC,  SLHTC,  FRICC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:)     :: QINIC,  TRIC,   DTRIC,  WDIC,   HDIC,   METIC   !, KFNAME2
  CHARACTER(14),  ALLOCATABLE, DIMENSION(:)    :: KFNAME2
  CHARACTER(14), ALLOCATABLE, DIMENSION(:)     :: C2CH,   CDCH,   EPCH,   macch, KFCH, APCH, ANCH, ALCH, ENCH, ELCH, EDCH  
  CHARACTER(45), ALLOCATABLE, DIMENSION(:)     :: KFNAME
  CHARACTER(72), ALLOCATABLE, DIMENSION(:)     :: SNPFN,  PRFFN,  VPLFN,  CPLFN,  SPRFN,  FLXFN,  FLXFN2, BTHFN,  VPRFN,  LPRFN, SPRVFN, ATMDEPFN   ! SW 9/28/2018
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:,:)   :: SINKC,  SINKCT
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:,:)   :: CPRBRC, CDTBRC, CPRWBC, CINBRC, CTRTRC, HPRWBC, STRIC,  CDWBC,  KFWBC
  CHARACTER(8),  ALLOCATABLE, DIMENSION(:,:)   :: EPIC,   EPIPRC, C_ATM_DEPOSITION
  CHARACTER(12), ALLOCATABLE, DIMENSION(:,:)   :: CONV1
  CHARACTER(72)                                :: CONFN='w2_con.npt'
  CHARACTER(72)                                :: TEXT
  INTEGER, ALLOCATABLE, DIMENSION(:)    :: WBSEG                        !  systdg
  INTEGER                               :: CONTDG                       ! systdg
  INTEGER                               :: TARGETFNNO                   ! systdg TDGtarget
  REAL(R8),ALLOCATABLE, DIMENSION(:)    :: GTPC                         ! systdg
  LOGICAL                               :: SYSTDG, N2BND, DOBND,DGPBND  ! systdg
  LOGICAL                               :: TDGTA                        ! systdg TDGtarget
  CHARACTER(8)                          :: SYSTDGC, N2BNDC, DOBNDC, TDG2BNDC    ! systdg
  CHARACTER(8)                          :: TDGTAC                       ! systdg TDGtarget
  CHARACTER(8),ALLOCATABLE, DIMENSION(:):: GTTYP                        ! systdg
!  CHARACTER(72), PARAMETER              :: CONTDGFN='w2_systdg.npt'   ! systdg
! Data declarations
  REAL(R8)  :: RK1=2.12D0, RL1=333507.0D0, RIMT=0.0D0, RHOA=1.25D0, RHOI=916.0D0, VTOL=1.0D3, CP=4186.0D0, THRKTI=0.10D0  ! RL1: Latent heat of melting for ice: 333507 J/kg, CP=4186 J/kg/oC; RHOI (density of ice)=916 kg/m3
  LOGICAL   :: LAKE_RIVER_CONTOURC       ! SW 2/27/2020
  CHARACTER(2) :: LAKE_RIVER_CONTOUR_ON
  CHARACTER(80):: FILE_LAKE_CONTOUR_T(20),FILE_LAKE_CONTOUR_DO(20),FILE_RIVER_CONTOUR_T(20),FILE_RIVER_CONTOUR_DO(20)
  INTEGER      :: NUM_LAKE_CONTOUR,NUM_RIVER_CONTOUR,LAKE_CONTOUR_SEG(20),RIVER_CONTOUR_BR1(20),RIVER_CONTOUR_BR2(20)
  INTEGER      :: JW_RIVER_CONTOUR(20), JW_LAKE_CONTOUR(20),LAKE_CONTOUR_FORMAT,RIVER_CONTOUR_FORMAT
  REAL         :: LAKE_CONTOUR_START(20),LAKE_CONTOUR_FREQ(20),RIVER_CONTOUR_START(20),RIVER_CONTOUR_FREQ(20),NXT_RIVER_CONTOUR(20), NXT_LAKE_CONTOUR(20)
  
  !DATA CON   /10/                      !,  RSI /11/
  !DATA FLOWBFN /9500/, WLFN /9510/, AERATEFN /9520/, FISHHABFN /9530/, MASSBFN /9501/        ! SW 5/25/15 NOTE THAT FISHHABFN INCREMENTS 3 TIMES SO 9531,9532,9533 ARE RESERVED 
  !DATA DYNPIPELOG /9505/, LAKE_RIVER_CONTOUR /9540/  ! ALSO 9540 TO 9550 to 9560 to 9570 to 9580 ARE TAKEN
! for fish habitat output filenames
  INTEGER     :: JBFILE1=9581, JWFILE1=9620  !ALSO JWFILE1=9620+NWB  JBFILE1=9581+NBR
  
  
END MODULE MAIN
! BIOENERGETICS module removed - 2026-03-30

Module Selective1TDGtarget
  CHARACTER(72)                                :: TITLETDGTARGET(10)
  INTEGER                                      :: NGFL, NGPH, NGSP, NOUTS, NGSPPH
  INTEGER                                      :: tsiteration, dygroup 
  INTEGER, ALLOCATABLE, DIMENSION(:)           :: SPGTNO, PHGTNO, SPPRIOR
  REAL                                         :: tsfreq, tsconv, NXTSPLIT, DAYTEST, NXTSPLIT2
  REAL                                         :: tstsrt, tstend, tstarget, tstarget2, nxtjday
  REAL,    ALLOCATABLE, DIMENSION(:)           :: SPMINFRAC, PHMAXFLOW
  CHARACTER(8)                                 :: tsyearly, tsdynsel,dyupdate
End Module Selective1TDGtarget
    
Module AlgaeReduceGasTransfer    
LOGICAL :: REDUCE_GAS_TRANSFER
REAL :: KHS_ALG
CHARACTER(2) :: ICHAR2
INTEGER :: ALGRED=24456,IOUTFREQ,IMM
INTEGER, ALLOCATABLE, DIMENSION(:) :: I_ALG

End Module AlgaeReduceGasTransfer
    