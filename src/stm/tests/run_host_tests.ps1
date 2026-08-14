$ErrorActionPreference = 'Stop'

$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$installation = & $vswhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -property installationPath
if (-not $installation) {
    throw 'Visual Studio C++ Build Tools are required for STM host tests.'
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$build = Join-Path $scriptRoot 'build'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$vcvars = Join-Path $installation 'VC\Auxiliary\Build\vcvars64.bat'
$sources = @(
    '..\firmware\protocol.c',
    '..\firmware\kinematics.c',
    '..\firmware\runtime.c',
    '..\firmware\runtime_rx.c',
    '..\firmware\telemetry.c',
    '..\firmware\wheel_control.c',
    'firmware_test.c'
) -join ' '
$command = "cd /d `"$scriptRoot`" && `"$vcvars`" >nul && " +
    "cl /nologo /W4 /WX /std:c11 " +
    "/I..\firmware $sources /Fo:build\ /Fe:build\test_firmware.exe && " +
    "build\test_firmware.exe"
try {
    cmd.exe /d /c $command
    if ($LASTEXITCODE -ne 0) {
        throw "STM host tests failed with exit code $LASTEXITCODE."
    }
}
finally {
    if (Test-Path -LiteralPath $build) {
        Remove-Item -LiteralPath $build -Recurse -Force
    }
}
