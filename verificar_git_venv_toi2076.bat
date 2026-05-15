@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo  VERIFICACAO DO PROJETO TOI-2076 - GIT + VENV
echo ============================================================
echo.

echo [1] Pasta atual:
echo     %CD%
echo.

echo [2] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo     ERRO: Git nao foi encontrado no PATH.
    echo     Instale o Git ou abra um terminal onde o Git funcione.
    goto :END
) else (
    for /f "delims=" %%A in ('git --version') do echo     OK: %%A
)
echo.

echo [3] Verificando repositorio Git...
if not exist ".git" (
    echo     ERRO: Esta pasta nao contem .git.
    echo     Entre na pasta principal do projeto e rode: git init
    goto :END
) else (
    echo     OK: repositorio Git encontrado.
)
echo.

echo [4] Branch atual:
git branch --show-current
echo.

echo [5] Remotos configurados:
git remote -v
echo.

echo [6] Status resumido:
git status -sb
echo.

echo [7] Verificando .gitignore...
if not exist ".gitignore" (
    echo     ALERTA: .gitignore nao encontrado.
) else (
    echo     OK: .gitignore encontrado.

    findstr /C:".venv/" .gitignore >nul
    if errorlevel 1 (echo     ALERTA: .gitignore nao contem .venv/) else (echo     OK: .venv/ esta no .gitignore)

    findstr /C:"raw/" .gitignore >nul
    if errorlevel 1 (echo     ALERTA: .gitignore nao contem raw/) else (echo     OK: raw/ esta no .gitignore)

    findstr /C:"*.fits" .gitignore >nul
    if errorlevel 1 (echo     ALERTA: .gitignore nao contem *.fits) else (echo     OK: *.fits esta no .gitignore)

    findstr /C:"*.zip" .gitignore >nul
    if errorlevel 1 (echo     ALERTA: .gitignore nao contem *.zip) else (echo     OK: *.zip esta no .gitignore)
)
echo.

echo [8] Verificando se .venv, raw, FITS ou ZIP foram rastreados pelo Git...
git ls-files > "%TEMP%\git_files_toi2076.txt"
findstr /R /C:"^\.venv/" /C:"^raw/" /C:"\.fits$" /C:"\.fit$" /C:"\.zip$" "%TEMP%\git_files_toi2076.txt" > "%TEMP%\git_forbidden_toi2076.txt"

for %%A in ("%TEMP%\git_forbidden_toi2076.txt") do set size=%%~zA
if "%size%"=="0" (
    echo     OK: nenhum arquivo proibido esta rastreado pelo Git.
) else (
    echo     ALERTA: existem arquivos proibidos rastreados pelo Git:
    type "%TEMP%\git_forbidden_toi2076.txt"
    echo.
    echo     Para corrigir, rode:
    echo         git rm -r --cached .venv
    echo         git rm -r --cached raw
    echo         git rm --cached *.fits
    echo         git rm --cached *.zip
    echo         git add .gitignore
    echo         git commit -m "Remove arquivos grandes e venv do controle do Git"
)
echo.

echo [9] Verificando ambiente virtual .venv...
if not exist ".venv" (
    echo     ERRO: pasta .venv nao encontrada.
    echo     Para criar: py -m venv .venv
) else (
    echo     OK: pasta .venv encontrada.
)

if not exist ".venv\Scripts\python.exe" (
    echo     ERRO: .venv\Scripts\python.exe nao encontrado.
) else (
    echo     OK: Python da venv encontrado.
    ".venv\Scripts\python.exe" --version
)
echo.

echo [10] Verificando pip da venv...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m pip --version
) else (
    echo     Pulando: Python da venv nao encontrado.
)
echo.

echo [11] Verificando pacotes cientificos principais...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import importlib.util; mods=['astropy','numpy','pandas','matplotlib']; missing=[m for m in mods if importlib.util.find_spec(m) is None]; print('OK: astropy, numpy, pandas, matplotlib encontrados' if not missing else 'FALTANDO: ' + ', '.join(missing))"
) else (
    echo     Pulando: Python da venv nao encontrado.
)
echo.

echo [12] Verificando requirements.txt...
if not exist "requirements.txt" (
    echo     ALERTA: requirements.txt nao encontrado.
    echo     Gere com: .venv\Scripts\python.exe -m pip freeze ^> requirements.txt
) else (
    echo     OK: requirements.txt encontrado.
    echo     Primeiras linhas:
    powershell -NoProfile -Command "Get-Content requirements.txt -TotalCount 10" 2>nul
)
echo.

echo [13] Verificando pastas principais...
for %%D in (raw run scripts processed metadata docs) do (
    if exist "%%D" (
        echo     OK: %%D\
    ) else (
        echo     AVISO: %%D\ nao encontrada
    )
)
echo.

echo [14] Contando FITS locais em raw/...
if exist "raw" (
    for /f %%A in ('dir /S /B raw\*.fits 2^>nul ^| find /C /V ""') do echo     FITS encontrados em raw/: %%A
) else (
    echo     Pasta raw/ nao encontrada.
)
echo.

echo ============================================================
echo  FIM DA VERIFICACAO
echo ============================================================
echo.
echo Interprete assim:
echo - OK = correto.
echo - AVISO = nao trava, mas pode ser bom organizar.
echo - ALERTA/ERRO = precisa corrigir antes de continuar.
echo.
echo Comandos normais depois de alterar scripts:
echo     git status
echo     git add .
echo     git commit -m "Descreva a alteracao"
echo     git push
echo.

:END
endlocal
pause
