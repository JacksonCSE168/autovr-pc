param([string]$UnityEditor = $env:UNITY_EDITOR)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if (!$UnityEditor) {
    $versions = Get-ChildItem "$env:ProgramFiles\Unity\Hub\Editor" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^6000\.' } |
        Sort-Object { [version](($_.Name -replace '[abfp].*$','')) } -Descending
    foreach ($v in $versions) {
        $candidate = Join-Path $v.FullName "Editor\Unity.exe"
        if (Test-Path $candidate) { $UnityEditor = $candidate; break }
    }
}
if (!$UnityEditor -or !(Test-Path -LiteralPath $UnityEditor)) {
    throw "Unity 6 Editor not found. For a custom installation set UNITY_EDITOR to the full Unity.exe path."
}
if (!(Test-Path .venv\Scripts\python.exe)) {
    $found = $false
    foreach ($name in @('py','python','python3',"$env:LocalAppData\Programs\Python\Python311\python.exe","$env:ProgramFiles\Python311\python.exe")) {
        $cmd = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if (!$cmd) { continue }
        $exe = $cmd.Source
        $selector = @()
        if ($name -eq 'py') { $selector = @('-3.11') }
        & $exe @selector -c "import sys,struct; sys.exit(0 if sys.version_info[:2]==(3,11) and struct.calcsize('P')==8 else 1)"
        if ($LASTEXITCODE -ne 0) { continue }
        & $exe @selector -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Python was found but could not create .venv." }
        $found = $true
        break
    }
    if (!$found) { throw "Python 3.11 x64 not found. Install it, then reopen Run-Test.cmd." }
}
& .\.venv\Scripts\python.exe -m pip install -r tool\AutoVR-PC\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Python dependencies failed." }
Write-Host "Building game. Unity build log: $PSScriptRoot\build.log"
$editorProcess = Start-Process -FilePath $UnityEditor -ArgumentList "-batchmode -nographics -quit -buildTarget Win64 -projectPath `"$PSScriptRoot\Game`" -executeMethod SwitchRoomBuild.Build -logFile `"$PSScriptRoot\build.log`"" -Wait -PassThru
if ($editorProcess.ExitCode -ne 0) { throw "Unity build failed. See build.log." }
& .\.venv\Scripts\python.exe verify.py
if ($LASTEXITCODE -ne 0) { throw "Player verification failed. See the run directory above." }
