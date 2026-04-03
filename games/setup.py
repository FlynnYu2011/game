from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": [],
    "excludes": [],
    "include_files": []
}

setup(
    name="StockRush",
    version="1.0",
    description="股票大冒险 - 模拟炒股游戏",
    options={"build_exe": build_exe_options},
    executables=[Executable("stock_game.py", base="GUI")]
)
