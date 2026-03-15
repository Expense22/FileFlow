import PyInstaller.__main__
import os
import shutil

print("🔨 Начало сборки FileFlow...")

# Очистка старых сборок
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

# Маркер портативности
with open('portable.mode', 'w', encoding='utf-8') as f:
    f.write('')

print("📦 Упаковка в .exe...")

# Сборка
PyInstaller.__main__.run([
    'main.py',
    '--onefile',              # Один exe файл
    '--name=FileFlow',        # Имя программы
    '--windowed',             # Без консоли
    '--add-data=config;config',  # Включаем папку config
    '--icon=icon.ico',  # ✅ ICO для .exe
    '--clean',                # Очистка перед сборкой
    '--noconfirm',            # Не спрашивать подтверждение
])

print("\n✅ Сборка завершена!")
print("📁 Файл: dist/FileFlow.exe")
print("\n📋 Инструкция:")
print("1. Скопируй dist/FileFlow.exe в любую папку")
print("2. Рядом создай папку config")
print("3. Скопируй в неё config/rules.json и settings.json")
print("4. Запусти и пользуйся!")