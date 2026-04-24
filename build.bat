@echo off
echo ==============================
echo  内存急救包 - 打包为 .exe
echo ==============================

pip install psutil pyinstaller -q

pyinstaller --onefile --windowed --name "内存急救包" ^
    --add-data "." ^
    memory_cleaner.py

echo.
echo ✅ 打包完成！文件在 dist\ 目录下
pause
