@echo RIVER ARCHITECT
@echo Loading (please wait) ...
@echo off

SET _propy=""

IF EXIST "%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\" (
	SET _propy="%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\propy"
)

IF EXIST "%LOCALAPPDATA%\Programs\ArcGIS\Pro\bin\Python\Scripts\" (
	SET _propy="%LOCALAPPDATA%\Programs\ArcGIS\Pro\bin\Python\Scripts\propy"
)

IF %_propy%=="" (
	goto err_msg
)

@echo on
call %_propy% "%cd%\parent_gui.py"

exit

:err_msg
	@echo off
	@echo: 
	@echo ERROR: Cannot find ArcGIS Pro's Python installation. Make sure ArcGIS Pro is installed on your computer.
	pause
	exit