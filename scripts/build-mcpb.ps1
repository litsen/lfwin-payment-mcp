param(
    [string]$OutputName = "",
    [switch]$ZipFallbackOnly
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$stage = Join-Path $root "build\mcpb"
$nodeProject = Join-Path $root "node-mcp"
$dist = Join-Path $nodeProject "dist"
$nodeModules = Join-Path $nodeProject "node_modules"
$manifest = Get-Content -LiteralPath (Join-Path $root "mcpb\manifest.json") -Raw | ConvertFrom-Json

if (-not $OutputName) {
    $OutputName = "lfwin-payment-mcp-$($manifest.version).mcpb"
}

if (-not (Test-Path $dist)) {
    throw "node-mcp/dist not found. Run: cd node-mcp; npm install; npm run build"
}

if (-not (Test-Path $nodeModules)) {
    throw "node-mcp/node_modules not found. Run: cd node-mcp; npm install"
}

if (Test-Path $stage) {
    Remove-Item -LiteralPath $stage -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $stage | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $stage "node-mcp") | Out-Null

Copy-Item -LiteralPath (Join-Path $root "mcpb\manifest.json") -Destination (Join-Path $stage "manifest.json")
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination (Join-Path $stage "README.md")
Copy-Item -LiteralPath (Join-Path $nodeProject "package.json") -Destination (Join-Path $stage "node-mcp\package.json")
Copy-Item -LiteralPath (Join-Path $nodeProject "package-lock.json") -Destination (Join-Path $stage "node-mcp\package-lock.json")
Copy-Item -LiteralPath $dist -Destination (Join-Path $stage "node-mcp\dist") -Recurse
Copy-Item -LiteralPath $nodeModules -Destination (Join-Path $stage "node-mcp\node_modules") -Recurse

Push-Location (Join-Path $stage "node-mcp")
try {
    npm prune --omit=dev --ignore-scripts
}
finally {
    Pop-Location
}

Push-Location $stage
try {
    $output = Join-Path $root "dist\$OutputName"
    New-Item -ItemType Directory -Force -Path (Split-Path $output) | Out-Null

    if (-not $ZipFallbackOnly) {
        try {
            npx -y @anthropic-ai/mcpb pack
            $generated = Get-ChildItem -Filter *.mcpb | Select-Object -First 1
            if ($generated) {
                Move-Item -LiteralPath $generated.FullName -Destination $output -Force
                Write-Host "Created $output"
                return
            }
            Write-Warning "mcpb pack completed but no .mcpb file was found. Falling back to zip packaging."
        }
        catch {
            Write-Warning "mcpb pack failed: $($_.Exception.Message)"
            Write-Warning "Falling back to zip packaging."
        }
    }

    $zipOutput = [System.IO.Path]::ChangeExtension($output, ".zip")
    if (Test-Path $zipOutput) {
        Remove-Item -LiteralPath $zipOutput -Force
    }
    if (Test-Path $output) {
        Remove-Item -LiteralPath $output -Force
    }
    Compress-Archive -Path * -DestinationPath $zipOutput -Force
    Move-Item -LiteralPath $zipOutput -Destination $output -Force
    Write-Host "Created $output"
}
finally {
    Pop-Location
}
