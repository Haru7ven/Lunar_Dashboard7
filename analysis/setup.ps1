# Preparacao do projecto SOL: instala bibliotecas e descarrega os kernels SPICE.
# Correr dentro da pasta do projecto:  powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'
$base = $PSScriptRoot
pip install -r "$base\requirements.txt"
New-Item -ItemType Directory -Force "$base\data\raw","$base\data\kernels" | Out-Null

$k = [ordered]@{
 "naif0012.tls"             = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls"
 "de440s.bsp"               = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp"
 "pck00011.tpc"             = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc"
 "moon_pa_de440_200625.bpc" = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc"
 "moon_de440_250416.tf"     = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_de440_250416.tf"
}
foreach ($n in $k.Keys) {
    $dest = "$base\data\kernels\$n"
    if (Test-Path $dest) { Write-Host "Ja existe: $n"; continue }
    Write-Host "A descarregar $n"
    Invoke-WebRequest -Uri $k[$n] -OutFile $dest
}

$img = "$base\data\raw\ldem_875s_20m.img"
$lbl = "$base\data\raw\ldem_875s_20m.lbl"
if ((Test-Path $img) -and (Test-Path $lbl)) { Write-Host "DEM encontrado." }
else { Write-Host "FALTA o DEM: copiar ldem_875s_20m.img e ldem_875s_20m.lbl para data\raw (ver LEIA-ME.txt)." }

python -c "import spiceypy, rasterio, numpy, astroquery; print('BIBLIOTECAS OK')"
Get-ChildItem "$base\data\kernels","$base\data\raw" | Select-Object Name, @{n='MB';e={[math]::Round($_.Length/1MB,2)}}
