@echo off
echo Instalando dependencias...
pip install -r requirements.txt

echo Construyendo ejecutable...
python build.py

echo Proceso completado.
pause 