@echo Calculating detrended DEM ... 

call "%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\propy" "%cd%\master_gui.py" "%cd%\make_det.py"
exit
