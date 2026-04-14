program test_read
  integer :: NOD
  character(8) :: SELECTC, HABTATC, ENVIRPC, AERATEC, INITUWL, ORGCC
  real :: DZMAX
  open(10, file='C:/Users/NING/Desktop/v455/temp_compile/test_read.csv', status='old')
  read(10,*) NOD, SELECTC, HABTATC, ENVIRPC, AERATEC, INITUWL, ORGCC, DZMAX
  print *, 'NOD=', NOD
  print *, 'SELECTC=', SELECTC
  print *, 'HABTATC=', HABTATC
  print *, 'ENVIRPC=', ENVIRPC
  print *, 'AERATEC=', AERATEC
  print *, 'INITUWL=', INITUWL
  print *, 'ORGCC=', ORGCC
  print *, 'DZMAX=', DZMAX
  close(10)
end program test_read