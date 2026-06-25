[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId,

    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$Location,

    [Parameter(Mandatory = $true)]
    [string]$ContainerAppEnvironment,

    [Parameter(Mandatory = $true)]
    [string]$ContainerAppName,

    [Parameter(Mandatory = $true)]
    [string]$AcrName,

    [Parameter(Mandatory = $true)]
    [string]$StorageAccountName,

    [Parameter(Mandatory = $true)]
    [string]$JwtSecret,

    [Parameter(Mandatory = $true)]
    [string]$GeminiApiKey,

    [string]$ImageRepository = "shorts-generator",
    [string]$ImageTag = "",
    [string]$MongoConnectionString = "",
    [string]$DbName = "realestate_shorts",
    [string]$AllowedOrigins = "",
    [string]$CosmosAccountName = "",
    [bool]$EnableBlobOutput = $true,
    [string]$BlobContainerName = "reels",
    [switch]$CreateCosmosMongo,
    [switch]$EnableRedisCache,
    [string]$RedisUrl = "",
    [switch]$UseLocalDockerBuild,
    [switch]$SkipImageBuild,
    [switch]$SkipSmokeTests,
    [switch]$SkipProviderRegistration
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# In PowerShell 7+, native-command stderr can be promoted to terminating errors.
# Azure CLI writes informational "WARNING:" lines to stderr, so disable that behavior
# and rely on native exit codes ($LASTEXITCODE) instead.
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$script:AzPythonExe = $null
try {
    $azCmd = Get-Command az.cmd -ErrorAction SilentlyContinue
    if ($azCmd -and $azCmd.Source) {
        $candidatePython = Join-Path (Split-Path -Parent $azCmd.Source) "..\python.exe"
        if (Test-Path -LiteralPath $candidatePython) {
            $script:AzPythonExe = (Resolve-Path -LiteralPath $candidatePython).Path
        }
    }
} catch {
    $script:AzPythonExe = $null
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-AzOutput {
    param([AllowNull()][object[]]$Output = @())
    if ($null -eq $Output) {
        return
    }
    foreach ($line in $Output) {
        if ($line -is [System.Management.Automation.ErrorRecord]) {
            Write-Host $line.Exception.Message
        } else {
            Write-Host $line
        }
    }
}

function Get-AzOutputText {
    param([AllowNull()][object[]]$Output = @())
    if ($null -eq $Output) {
        return ""
    }
    $lines = foreach ($line in $Output) {
        if ($line -is [System.Management.Automation.ErrorRecord]) {
            $line.Exception.Message
        } else {
            "$line"
        }
    }
    return (($lines -join "`n").Trim())
}

function Test-AzTransientFailure {
    param([AllowNull()][object[]]$Output = @())
    $outputText = (Get-AzOutputText -Output $Output)
    if ([string]::IsNullOrWhiteSpace($outputText)) {
        return $false
    }

    $lower = $outputText.ToLowerInvariant()
    $needles = @(
        "connection reset by peer",
        "connectionreseterror",
        "requests.exceptions.connectionerror",
        "connection aborted",
        "remote disconnected",
        "read timed out",
        "econnreset",
        "socket hang up",
        "temporarily unavailable",
        "service unavailable",
        "too many requests",
        "status code: 429",
        "http 429",
        "502 bad gateway",
        "503 service unavailable",
        "504 gateway timeout",
        "gatewaytimeout",
        "internal server error"
    )
    foreach ($needle in $needles) {
        if ($lower.Contains($needle)) {
            return $true
        }
    }
    return $false
}

function Run-Az {
    param(
        [Parameter(Position = 0, ValueFromRemainingArguments = $true)][string[]]$Args,
        [int]$MaxAttempts = 4,
        [int]$InitialRetryDelaySec = 5
    )

    if ($MaxAttempts -lt 1) {
        $MaxAttempts = 1
    }
    if ($InitialRetryDelaySec -lt 1) {
        $InitialRetryDelaySec = 1
    }

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        if ($attempt -eq 1) {
            Write-Host "az $($Args -join ' ')" -ForegroundColor DarkCyan
        } else {
            Write-Host "az $($Args -join ' ') (attempt $attempt/$MaxAttempts)" -ForegroundColor DarkCyan
        }

        $result = Invoke-AzRaw @Args
        Write-AzOutput -Output $result.Output

        if ($result.ExitCode -eq 0) {
            return
        }

        $retryable = Test-AzTransientFailure -Output $result.Output
        if ((-not $retryable) -or ($attempt -eq $MaxAttempts)) {
            throw "Azure CLI command failed: az $($Args -join ' ')"
        }

        $delay = [Math]::Min(60, [int]($InitialRetryDelaySec * [Math]::Pow(2, $attempt - 1)))
        Write-Warning "Transient Azure CLI failure detected. Retrying in $delay seconds..."
        Start-Sleep -Seconds $delay
    }
}

function Invoke-AzRaw {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = @()
    try {
        if (-not [string]::IsNullOrWhiteSpace($script:AzPythonExe)) {
            $output = & $script:AzPythonExe -IBm azure.cli @Args 2>&1
        } else {
            $output = & az @Args 2>&1
        }
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($null -eq $output) {
        $output = @()
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output   = $output
    }
}

function Test-Az {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $result = Invoke-AzRaw @Args
    return $result.ExitCode -eq 0
}

function Get-AzTsv {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $result = Invoke-AzRaw @Args
    if ($result.ExitCode -ne 0) {
        throw "Azure CLI command failed: az $($Args -join ' ')"
    }
    $stdoutLines = foreach ($line in $result.Output) {
        if ($line -isnot [System.Management.Automation.ErrorRecord]) {
            "$line"
        }
    }
    return (($stdoutLines -join "`n").Trim())
}

function Get-AzText {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $result = Invoke-AzRaw @Args
    if ($result.ExitCode -ne 0) {
        throw "Azure CLI command failed: az $($Args -join ' ')"
    }
    $stdoutLines = foreach ($line in $result.Output) {
        if ($line -isnot [System.Management.Automation.ErrorRecord]) {
            "$line"
        }
    }
    return (($stdoutLines -join "`n"))
}

function Run-Docker {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    Write-Host "docker $($Args -join ' ')" -ForegroundColor DarkCyan
    & docker @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed: docker $($Args -join ' ')"
    }
}

function Assert-DockerReady {
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $dockerCmd) {
        throw "Docker CLI not found. Install Docker Desktop (or Docker Engine), then rerun with -UseLocalDockerBuild."
    }

    $versionOutput = & docker version --format "{{.Server.Version}}" 2>&1
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($versionOutput | Out-String).Trim())) {
        throw @"
Docker daemon is not available.
Start Docker Desktop and wait until it is running, then rerun the script.
Tip: Use -UseLocalDockerBuild to force local build/push mode.
"@
    }
}

function Invoke-WebCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSec = 20
    )
    try {
        return Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec $TimeoutSec -UseBasicParsing
    } catch {
        try {
            return Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSec -MaximumRedirection 5 -UseBasicParsing
        } catch {
            $response = $_.Exception.Response
            if ($null -ne $response) {
                $statusCode = 0
                try { $statusCode = [int]$response.StatusCode } catch {}
                $content = ""
                try {
                    $stream = $response.GetResponseStream()
                    if ($null -ne $stream) {
                        $reader = New-Object System.IO.StreamReader($stream)
                        $content = $reader.ReadToEnd()
                        $reader.Close()
                        $stream.Close()
                    }
                } catch {}

                return [pscustomobject]@{
                    StatusCode = $statusCode
                    Content    = $content
                }
            }
            throw
        }
    }
}

function Assert-FileExists {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file not found: $Path"
    }
}

function Test-BlobContainerExists {
    param(
        [Parameter(Mandatory = $true)][string]$StorageAccountName,
        [Parameter(Mandatory = $true)][string]$StorageAccountKey,
        [Parameter(Mandatory = $true)][string]$ContainerName
    )
    try {
        $exists = Get-AzTsv storage container exists `
            --account-name $StorageAccountName `
            --account-key $StorageAccountKey `
            --name $ContainerName `
            --query "exists" `
            --output tsv
        return ($exists -eq "true")
    } catch {
        return $false
    }
}

function Ensure-BlobContainer {
    param(
        [Parameter(Mandatory = $true)][string]$StorageAccountName,
        [Parameter(Mandatory = $true)][string]$StorageAccountKey,
        [Parameter(Mandatory = $true)][string]$ContainerName
    )

    # Try to create with public read for simple direct URL access.
    # If account policy disallows public access, fall back to private container.
    $createPublic = Invoke-AzRaw storage container create `
        --account-name $StorageAccountName `
        --account-key $StorageAccountKey `
        --name $ContainerName `
        --public-access blob
    Write-AzOutput -Output $createPublic.Output

    if ($createPublic.ExitCode -ne 0) {
        $createText = Get-AzOutputText -Output $createPublic.Output
        if ($createText -match "PublicAccessNotPermitted|Public access is not permitted") {
            Write-Warning "Storage account blocks public blob access. Creating private container '$ContainerName' instead."
            Run-Az storage container create `
                --account-name $StorageAccountName `
                --account-key $StorageAccountKey `
                --name $ContainerName
        } else {
            throw "Azure CLI command failed while ensuring blob container '$ContainerName'."
        }
    }

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        if (Test-BlobContainerExists `
            -StorageAccountName $StorageAccountName `
            -StorageAccountKey $StorageAccountKey `
            -ContainerName $ContainerName) {
            return
        }
        Start-Sleep -Seconds 2
    }

    Write-Warning "Blob container '$ContainerName' not visible yet. Retrying explicit create and verify."
    Run-Az storage container create `
        --account-name $StorageAccountName `
        --account-key $StorageAccountKey `
        --name $ContainerName

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        if (Test-BlobContainerExists `
            -StorageAccountName $StorageAccountName `
            -StorageAccountKey $StorageAccountKey `
            -ContainerName $ContainerName) {
            return
        }
        Start-Sleep -Seconds 2
    }

    throw "Blob container '$ContainerName' still not found after create attempts."
}

function Upload-BlobWithContainerRetry {
    param(
        [Parameter(Mandatory = $true)][string]$StorageAccountName,
        [Parameter(Mandatory = $true)][string]$StorageAccountKey,
        [Parameter(Mandatory = $true)][string]$ContainerName,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string]$BlobName
    )

    Ensure-BlobContainer `
        -StorageAccountName $StorageAccountName `
        -StorageAccountKey $StorageAccountKey `
        -ContainerName $ContainerName

    $uploadResult = Invoke-AzRaw storage blob upload `
        --account-name $StorageAccountName `
        --account-key $StorageAccountKey `
        --container-name $ContainerName `
        --file $FilePath `
        --name $BlobName
    Write-AzOutput -Output $uploadResult.Output
    if ($uploadResult.ExitCode -eq 0) {
        return
    }

    $uploadText = Get-AzOutputText -Output $uploadResult.Output
    if ($uploadText -match "ContainerNotFound|specified container does not exist") {
        Write-Warning "Blob upload reported container not found. Re-ensuring container and retrying once."
        Ensure-BlobContainer `
            -StorageAccountName $StorageAccountName `
            -StorageAccountKey $StorageAccountKey `
            -ContainerName $ContainerName

        Run-Az storage blob upload `
            --account-name $StorageAccountName `
            --account-key $StorageAccountKey `
            --container-name $ContainerName `
            --file $FilePath `
            --name $BlobName
        return
    }

    throw "Azure CLI command failed: az storage blob upload --account-name $StorageAccountName --container-name $ContainerName --file $FilePath --name $BlobName"
}

function Resolve-FirstExistingPath {
    param([Parameter(Mandatory = $true)][string[]]$CandidatePaths)
    foreach ($candidate in $CandidatePaths) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

if ([string]::IsNullOrWhiteSpace($ImageTag)) {
    $ImageTag = (Get-Date -Format "yyyyMMddHHmmss")
}

$scriptRoot = Split-Path -Parent $PSCommandPath
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
$dockerfilePath = Join-Path $repoRoot "Dockerfile"
$demoVideoPath = Resolve-FirstExistingPath -CandidatePaths @(
    (Join-Path $repoRoot "frontend/public/demo/how-it-works.mp4"),
    (Join-Path $repoRoot "frontend/public/demo/how-it-work.mp4")
)
$tutorialVideoPath = Resolve-FirstExistingPath -CandidatePaths @(
    (Join-Path $repoRoot "frontend/public/tutorials/how-it-works.mp4"),
    (Join-Path $repoRoot "frontend/public/tutorials/how-it-work.mp4")
)

Write-Step "Preflight checks"
Assert-FileExists -Path $dockerfilePath
if ([string]::IsNullOrWhiteSpace($demoVideoPath)) {
    Write-Warning "Demo video file not found in frontend/public/demo. Deployment will continue."
}
if ([string]::IsNullOrWhiteSpace($tutorialVideoPath)) {
    Write-Warning "Tutorial video file not found in frontend/public/tutorials. Deployment will continue."
}

if ([string]::IsNullOrWhiteSpace($MongoConnectionString)) {
    $CreateCosmosMongo = $true
} else {
    $mongoLower = $MongoConnectionString.ToLowerInvariant()
    if ($mongoLower -match "(localhost|127\.0\.0\.1|host\.docker\.internal)") {
        throw "Mongo URI points to localhost. Azure Container Apps cannot reach your laptop's local MongoDB. Use Azure Cosmos Mongo/Atlas/public Mongo URI."
    }
    if ($mongoLower -match "mongodb(\+srv)?://(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)") {
        Write-Warning "Mongo URI appears to be a private LAN address. Ensure Azure can route to it (VPN/Private Endpoint)."
    }
}

if ($null -eq $BlobContainerName) {
    $BlobContainerName = ""
}
$BlobContainerName = $BlobContainerName.Trim().ToLowerInvariant()
if ($EnableBlobOutput -and [string]::IsNullOrWhiteSpace($BlobContainerName)) {
    throw "BlobContainerName cannot be empty when EnableBlobOutput=true."
}
if ($EnableBlobOutput -and ($BlobContainerName -notmatch "^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")) {
    throw "BlobContainerName '$BlobContainerName' is invalid. Use 3-63 chars, lowercase letters/numbers/hyphen."
}

Write-Step "Azure login and subscription setup"
if (-not (Test-Az account show)) {
    Run-Az login
}

Run-Az account set --subscription $SubscriptionId
Run-Az extension add --name containerapp --upgrade
if ($SkipProviderRegistration) {
    Write-Warning "Skipping Azure provider registration as requested (-SkipProviderRegistration)."
} else {
    Run-Az provider register --namespace Microsoft.App
    Run-Az provider register --namespace Microsoft.OperationalInsights
    Run-Az provider register --namespace Microsoft.ContainerRegistry
    Run-Az provider register --namespace Microsoft.Storage
    Run-Az provider register --namespace Microsoft.DocumentDB
}

Write-Step "Create resource group"
Run-Az group create --name $ResourceGroup --location $Location

if ($CreateCosmosMongo) {
    Write-Step "Create Azure Cosmos DB (MongoDB API) and database"
    if ([string]::IsNullOrWhiteSpace($CosmosAccountName)) {
        $base = ("cosmos" + ($ContainerAppName -replace "[^a-z0-9]", "")).ToLower()
        if ($base.Length -gt 40) {
            $base = $base.Substring(0, 40)
        }
        $CosmosAccountName = $base
    }

    if (-not (Test-Az cosmosdb show --name $CosmosAccountName --resource-group $ResourceGroup)) {
        Run-Az cosmosdb create `
            --name $CosmosAccountName `
            --resource-group $ResourceGroup `
            --kind MongoDB `
            --locations "regionName=$Location failoverPriority=0 isZoneRedundant=False"
    }

    Run-Az cosmosdb mongodb database create `
        --account-name $CosmosAccountName `
        --resource-group $ResourceGroup `
        --name $DbName

    $MongoConnectionString = Get-AzTsv cosmosdb keys list `
        --name $CosmosAccountName `
        --resource-group $ResourceGroup `
        --type connection-strings `
        --query "connectionStrings[0].connectionString" `
        --output tsv

    if ([string]::IsNullOrWhiteSpace($MongoConnectionString)) {
        throw "Failed to retrieve MongoDB connection string from Cosmos account '$CosmosAccountName'."
    }
}

Write-Step "Create storage account and file shares"
Run-Az storage account create `
    --name $StorageAccountName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2

$shares = @("data", "outputs", "downloads", "logs")
foreach ($share in $shares) {
    Run-Az storage share-rm create `
        --resource-group $ResourceGroup `
        --storage-account $StorageAccountName `
        --name $share
}

$storageKey = Get-AzTsv storage account keys list `
    --resource-group $ResourceGroup `
    --account-name $StorageAccountName `
    --query "[0].value" `
    --output tsv

if ([string]::IsNullOrWhiteSpace($storageKey)) {
    throw "Failed to fetch storage account key for '$StorageAccountName'."
}

$storageConnectionString = Get-AzTsv storage account show-connection-string `
    --name $StorageAccountName `
    --resource-group $ResourceGroup `
    --query "connectionString" `
    --output tsv

if ([string]::IsNullOrWhiteSpace($storageConnectionString)) {
    throw "Failed to fetch storage connection string for '$StorageAccountName'."
}

if ($EnableBlobOutput) {
    Write-Step "Create Blob container for rendered reels"
    Ensure-BlobContainer `
        -StorageAccountName $StorageAccountName `
        -StorageAccountKey $storageKey `
        -ContainerName $BlobContainerName
}

Write-Step "Create Azure Container Registry"
Run-Az acr create `
    --name $AcrName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Standard `
    --admin-enabled true

$acrLoginServer = Get-AzTsv acr show --name $AcrName --resource-group $ResourceGroup --query "loginServer" --output tsv
$acrUser = Get-AzTsv acr credential show --name $AcrName --query "username" --output tsv
$acrPassword = Get-AzTsv acr credential show --name $AcrName --query "passwords[0].value" --output tsv

if ([string]::IsNullOrWhiteSpace($acrLoginServer) -or [string]::IsNullOrWhiteSpace($acrUser) -or [string]::IsNullOrWhiteSpace($acrPassword)) {
    throw "Failed to fetch ACR credentials for '$AcrName'."
}

if (-not $SkipImageBuild) {
    Write-Step "Build and push Docker image to ACR"
    $buildWithLocalDocker = $UseLocalDockerBuild.IsPresent

    if (-not $buildWithLocalDocker) {
        $acrBuildResult = Invoke-AzRaw acr build `
            --registry $AcrName `
            --image "$ImageRepository`:$ImageTag" `
            --file $dockerfilePath `
            $repoRoot
        $acrBuildOutput = $acrBuildResult.Output
        $acrBuildExit = $acrBuildResult.ExitCode
        $acrBuildOutput | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.Exception.Message
            } else {
                Write-Host $_
            }
        }

        if ($acrBuildExit -ne 0) {
            $acrBuildText = (
                $acrBuildOutput |
                ForEach-Object {
                    if ($_ -is [System.Management.Automation.ErrorRecord]) {
                        $_.Exception.Message
                    } else {
                        "$_"
                    }
                } |
                Out-String
            )
            if ($acrBuildText -match "TasksOperationsNotAllowed") {
                Write-Warning "ACR Tasks are blocked for this subscription/registry. Falling back to local Docker build + push."
                $buildWithLocalDocker = $true
            } else {
                throw "Azure CLI command failed: az acr build --registry $AcrName --image $ImageRepository`:$ImageTag --file $dockerfilePath $repoRoot"
            }
        }
    }

    if ($buildWithLocalDocker) {
        Assert-DockerReady
        Write-Step "Local Docker build and push to ACR"
        $imageRef = "$acrLoginServer/$ImageRepository`:$ImageTag"
        $acrPassword | & docker login $acrLoginServer --username $acrUser --password-stdin
        if ($LASTEXITCODE -ne 0) {
            throw "Docker login failed for $acrLoginServer."
        }
        Run-Docker build --file $dockerfilePath --tag $imageRef $repoRoot
        Run-Docker push $imageRef
    }
}

$imageRef = "$acrLoginServer/$ImageRepository`:$ImageTag"

Write-Step "Create Container Apps environment"
if (-not (Test-Az containerapp env show --name $ContainerAppEnvironment --resource-group $ResourceGroup)) {
    Run-Az containerapp env create `
        --name $ContainerAppEnvironment `
        --resource-group $ResourceGroup `
        --location $Location
}

Write-Step "Attach Azure File shares to Container Apps environment"
$envStorages = @(
    @{ StorageName = "rfdata"; ShareName = "data" },
    @{ StorageName = "rfoutputs"; ShareName = "outputs" },
    @{ StorageName = "rfdownloads"; ShareName = "downloads" },
    @{ StorageName = "rflogs"; ShareName = "logs" }
)

foreach ($storage in $envStorages) {
    Run-Az containerapp env storage set `
        --name $ContainerAppEnvironment `
        --resource-group $ResourceGroup `
        --storage-name $storage.StorageName `
        --azure-file-account-name $StorageAccountName `
        --azure-file-account-key $storageKey `
        --azure-file-share-name $storage.ShareName `
        --access-mode ReadWrite
}

Write-Step "Create or update Container App"
$appExists = Test-Az containerapp show --name $ContainerAppName --resource-group $ResourceGroup

if (-not $appExists) {
    Run-Az containerapp create `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --environment $ContainerAppEnvironment `
        --image $imageRef `
        --ingress external `
        --target-port 8000 `
        --registry-server $acrLoginServer `
        --registry-username $acrUser `
        --registry-password $acrPassword `
        --cpu 1.0 `
        --memory 2Gi `
        --min-replicas 1 `
        --max-replicas 1 `
        --revisions-mode single
} else {
    Run-Az containerapp update `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --image $imageRef `
        --min-replicas 1 `
        --max-replicas 1
}

Write-Step "Configure application secrets"
$secretArgs = @(
    "containerapp", "secret", "set",
    "--name", $ContainerAppName,
    "--resource-group", $ResourceGroup,
    "--secrets",
    "mongodb-url=$MongoConnectionString",
    "jwt-secret=$JwtSecret",
    "gemini-api-key=$GeminiApiKey",
    "acr-password=$acrPassword"
)

if ($EnableBlobOutput) {
    $secretArgs += "azure-storage-connection-string=$storageConnectionString"
}

if ($EnableRedisCache) {
    if ([string]::IsNullOrWhiteSpace($RedisUrl)) {
        throw "EnableRedisCache is set but RedisUrl is empty."
    }
    $secretArgs += "redis-url=$RedisUrl"
}

Run-Az @secretArgs

$fqdn = Get-AzTsv containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" `
    --output tsv

if ([string]::IsNullOrWhiteSpace($fqdn)) {
    throw "Failed to resolve Container App FQDN."
}

if ([string]::IsNullOrWhiteSpace($AllowedOrigins)) {
    $AllowedOrigins = "https://$fqdn"
}

Write-Step "Configure app environment variables"
$enableRedisLiteral = if ($EnableRedisCache) { "true" } else { "false" }
$enableBlobLiteral = if ($EnableBlobOutput) { "true" } else { "false" }
$envVarPairs = @(
    "SERVICE_ENV=production",
    "MONGODB_URL=secretref:mongodb-url",
    "DB_NAME=$DbName",
    "JWT_SECRET=secretref:jwt-secret",
    "GEMINI_API_KEY=secretref:gemini-api-key",
    "ENABLE_REDIS_CACHE=$enableRedisLiteral",
    "ENABLE_AZURE_BLOB_OUTPUT=$enableBlobLiteral",
    "AZURE_BLOB_OUTPUT_CONTAINER=$BlobContainerName",
    "LOG_TO_FILE=true",
    "LOG_FILE_PATH=/app/backend/logs/reelforge_debug.log",
    "ALLOWED_ORIGINS=$AllowedOrigins",
    "STARTUP_RETRY_ATTEMPTS=5",
    "STARTUP_RETRY_BASE_DELAY_SEC=2",
    "STARTUP_RETRY_MAX_DELAY_SEC=15",
    "ENABLE_RATE_LIMITING=true"
)

if ($EnableRedisCache) {
    $envVarPairs += "REDIS_URL=secretref:redis-url"
}
if ($EnableBlobOutput) {
    $envVarPairs += "AZURE_STORAGE_CONNECTION_STRING=secretref:azure-storage-connection-string"
}

$envArgs = @(
    "containerapp", "update",
    "--name", $ContainerAppName,
    "--resource-group", $ResourceGroup,
    "--set-env-vars"
) + $envVarPairs + @(
    "--min-replicas", "1",
    "--max-replicas", "1"
)

Run-Az @envArgs

Write-Step "Configure persistent volume mounts"
$volumesSpec = @(
    @{ name = "data-volume"; storageType = "AzureFile"; storageName = "rfdata" },
    @{ name = "outputs-volume"; storageType = "AzureFile"; storageName = "rfoutputs" },
    @{ name = "downloads-volume"; storageType = "AzureFile"; storageName = "rfdownloads" },
    @{ name = "logs-volume"; storageType = "AzureFile"; storageName = "rflogs" }
)

$volumeMountSpec = @(
    @{ mountPath = "/app/backend/data"; volumeName = "data-volume" },
    @{ mountPath = "/app/backend/outputs"; volumeName = "outputs-volume" },
    @{ mountPath = "/app/backend/downloads"; volumeName = "downloads-volume" },
    @{ mountPath = "/app/backend/logs"; volumeName = "logs-volume" }
)

$currentYamlPath = Join-Path $env:TEMP "ca-current-$ContainerAppName-$ImageTag.yaml"
$patchedYamlPath = Join-Path $env:TEMP "ca-patched-$ContainerAppName-$ImageTag.yaml"
$volumesJsonPath = Join-Path $env:TEMP "ca-volumes-$ContainerAppName-$ImageTag.json"
$mountsJsonPath = Join-Path $env:TEMP "ca-mounts-$ContainerAppName-$ImageTag.json"
$yamlPatchScriptPath = Join-Path $env:TEMP "ca-yaml-patch-$ContainerAppName-$ImageTag.py"

$currentYaml = Get-AzText containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --output yaml
Set-Content -Path $currentYamlPath -Value $currentYaml -Encoding utf8

Set-Content -Path $volumesJsonPath -Value ($volumesSpec | ConvertTo-Json -Compress) -Encoding utf8
Set-Content -Path $mountsJsonPath -Value ($volumeMountSpec | ConvertTo-Json -Compress) -Encoding utf8

$yamlPatchScript = @'
import json
import sys
import yaml

input_yaml, output_yaml, volumes_json, mounts_json, container_name = sys.argv[1:6]

with open(input_yaml, "r", encoding="utf-8-sig") as f:
    doc = yaml.safe_load(f.read().replace("\x00", ""))

template = doc.setdefault("properties", {}).setdefault("template", {})

with open(volumes_json, "r", encoding="utf-8-sig") as f:
    template["volumes"] = json.load(f)

with open(mounts_json, "r", encoding="utf-8-sig") as f:
    mounts = json.load(f)

containers = template.get("containers") or []
if not containers:
    raise SystemExit("No containers found in Container App template.")

target = None
for c in containers:
    if isinstance(c, dict) and c.get("name") == container_name:
        target = c
        break

if target is None:
    target = containers[0]

target["volumeMounts"] = mounts

with open(output_yaml, "w", encoding="utf-8", newline="\n") as f:
    yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False)
'@

Set-Content -Path $yamlPatchScriptPath -Value $yamlPatchScript -Encoding utf8

$pythonForYaml = $script:AzPythonExe
if ([string]::IsNullOrWhiteSpace($pythonForYaml)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCmd) {
        throw "Python interpreter not found for YAML patching step."
    }
    $pythonForYaml = $pythonCmd.Source
}

& $pythonForYaml $yamlPatchScriptPath $currentYamlPath $patchedYamlPath $volumesJsonPath $mountsJsonPath $ContainerAppName
if ($LASTEXITCODE -ne 0) {
    throw "Failed to patch Container App YAML for persistent volume mounts."
}

Run-Az containerapp update `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --yaml $patchedYamlPath

$baseUrl = "https://$fqdn"

if (-not $SkipSmokeTests) {
    Write-Step "Smoke tests"

    $liveUrl = "$baseUrl/api/v1/health/live"
    $readyUrl = "$baseUrl/api/v1/health/ready"
    $demoUrl = "$baseUrl/demo/how-it-works.mp4"
    $tutorialUrl = "$baseUrl/tutorials/how-it-works.mp4"

    $maxAttempts = 20
    $attempt = 0
    $ready = $false
    while (-not $ready -and $attempt -lt $maxAttempts) {
        $attempt += 1
        try {
            $res = Invoke-WebRequest -Uri $liveUrl -TimeoutSec 15 -UseBasicParsing
            if ($res.StatusCode -ge 200 -and $res.StatusCode -lt 300) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 10
        }
        Start-Sleep -Seconds 10
    }

    if (-not $ready) {
        throw "Container App did not become healthy in time. Check Azure logs for app '$ContainerAppName'."
    }

    $liveCheck = Invoke-WebCheck -Url $liveUrl
    $readyCheck = Invoke-WebCheck -Url $readyUrl
    $demoCheck = Invoke-WebCheck -Url $demoUrl
    $tutorialCheck = Invoke-WebCheck -Url $tutorialUrl

    if ($liveCheck.StatusCode -ge 400 -or $readyCheck.StatusCode -ge 400) {
        throw "Health checks failed. live=$($liveCheck.StatusCode), ready=$($readyCheck.StatusCode)"
    }
    if ($demoCheck.StatusCode -ge 400) {
        Write-Warning "Demo video route check failed at $demoUrl (status $($demoCheck.StatusCode)). Continuing deployment."
    }
    if ($tutorialCheck.StatusCode -ge 400) {
        Write-Warning "Tutorial video route check failed at $tutorialUrl (status $($tutorialCheck.StatusCode)). Continuing deployment."
    }

    $probeLocalPath = Join-Path $env:TEMP "rf-data-probe-$ImageTag.txt"
    $probeContent = "reelforge-persistent-storage-ok-$ImageTag"
    Set-Content -Path $probeLocalPath -Value $probeContent -Encoding utf8

    Run-Az storage directory create `
        --account-name $StorageAccountName `
        --account-key $storageKey `
        --share-name "data" `
        --name "deployment"

    Run-Az storage file upload `
        --account-name $StorageAccountName `
        --account-key $storageKey `
        --share-name "data" `
        --source $probeLocalPath `
        --path "deployment/probe.txt"

    Start-Sleep -Seconds 5

    $probeUrl = "$baseUrl/data/deployment/probe.txt"
    $probeVerified = $false
    for ($probeAttempt = 1; $probeAttempt -le 6; $probeAttempt++) {
        try {
            $probeResponse = Invoke-WebRequest -Uri $probeUrl -TimeoutSec 20 -UseBasicParsing
            $probeBody = $probeResponse.Content.Trim()
            if ($probeResponse.StatusCode -lt 400 -and $probeBody -like "*$probeContent*") {
                $probeVerified = $true
                break
            }
        } catch {}
        Start-Sleep -Seconds 5
    }

    if (-not $probeVerified) {
        throw "Persistent data mount validation failed for $probeUrl."
    }

    if ($EnableBlobOutput) {
        $blobProbeLocalPath = Join-Path $env:TEMP "rf-blob-probe-$ImageTag.txt"
        $blobProbeContent = "reelforge-blob-output-ok-$ImageTag"
        Set-Content -Path $blobProbeLocalPath -Value $blobProbeContent -Encoding utf8

        Ensure-BlobContainer `
            -StorageAccountName $StorageAccountName `
            -StorageAccountKey $storageKey `
            -ContainerName $BlobContainerName

        $blobProbeName = "deployment/probe-$ImageTag.txt"
        Upload-BlobWithContainerRetry `
            -StorageAccountName $StorageAccountName `
            -StorageAccountKey $storageKey `
            -ContainerName $BlobContainerName `
            -FilePath $blobProbeLocalPath `
            -BlobName $blobProbeName

        $blobVerified = $false
        for ($blobAttempt = 1; $blobAttempt -le 6; $blobAttempt++) {
            try {
                $blobExists = Get-AzTsv storage blob exists `
                    --account-name $StorageAccountName `
                    --account-key $storageKey `
                    --container-name $BlobContainerName `
                    --name $blobProbeName `
                    --query "exists" `
                    --output tsv
                if ($blobExists -eq "true") {
                    $blobVerified = $true
                    break
                }
            } catch {}
            Start-Sleep -Seconds 5
        }

        if (-not $blobVerified) {
            throw "Blob output validation failed for container '$BlobContainerName' and blob '$blobProbeName'."
        }
    }
}

Write-Step "Deployment complete"
Write-Host "Container App URL: $baseUrl" -ForegroundColor Green
Write-Host "Health Live: $baseUrl/api/v1/health/live" -ForegroundColor Green
Write-Host "Health Ready: $baseUrl/api/v1/health/ready" -ForegroundColor Green
Write-Host "Demo Video URL: $baseUrl/demo/how-it-works.mp4" -ForegroundColor Green
Write-Host "Tutorial Video URL: $baseUrl/tutorials/how-it-works.mp4" -ForegroundColor Green
Write-Host "Data Route Probe: $baseUrl/data/deployment/probe.txt" -ForegroundColor Green
if ($EnableBlobOutput) {
    Write-Host "Blob Container URL: https://$StorageAccountName.blob.core.windows.net/$BlobContainerName/" -ForegroundColor Green
}
