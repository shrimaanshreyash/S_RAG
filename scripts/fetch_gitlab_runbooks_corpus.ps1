param(
    [string]$Destination = (
        Join-Path $PSScriptRoot "..\data\reference-corpora\gitlab-runbooks-4ac275d"
    )
)

$ErrorActionPreference = "Stop"
$projectId = 1148549
$commit = "4ac275d086328d8e94555ac9ee853c7fb9d66a09"
$repository = "https://gitlab.com/gitlab-com/runbooks"
$files = @(
    "LICENSE",
    "README.md",
    "docs/incidents/README.md",
    "docs/incidents/when-gitlab-com-is-down.md",
    "docs/uncategorized/upgrade-and-rollback.md",
    "docs/sidekiq/README.md",
    "docs/sidekiq/sidekiq-survival-guide-for-sres.md",
    "docs/sidekiq/sidekiq-inspection.md",
    "docs/sidekiq/sidekiq-queue-not-being-processed.md",
    "docs/sidekiq/sidekiq-concurrency-limit.md"
)

$destinationRoot = [IO.Path]::GetFullPath($Destination)
[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
$records = foreach ($file in $files) {
    $encodedPath = [Uri]::EscapeDataString($file)
    $rawUrl = (
        "https://gitlab.com/api/v4/projects/$projectId/repository/files/" +
        "$encodedPath/raw?ref=$commit"
    )
    $target = Join-Path $destinationRoot $file
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
    Invoke-WebRequest -Uri $rawUrl -OutFile $target
    $item = Get-Item -LiteralPath $target
    [ordered]@{
        path = $file
        bytes = $item.Length
        sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        source = "$repository/-/blob/$commit/$file"
    }
}

$manifest = [ordered]@{
    name = "GitLab public production runbooks evaluation corpus"
    repository = $repository
    project_id = $projectId
    commit = $commit
    license = "MIT"
    retrieved_at_utc = [DateTime]::UtcNow.ToString("o")
    use_boundary = (
        "Real public operational documents. Any test incident, missing-document " +
        "variant, tool response, or verifier state created by S_RAG remains synthetic."
    )
    files = @($records)
}
$manifestPath = Join-Path $destinationRoot "corpus-manifest.json"
$manifestJson = $manifest | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText(
    $manifestPath,
    $manifestJson,
    [Text.UTF8Encoding]::new($false)
)

Write-Output "Saved $($files.Count) source files and manifest to $destinationRoot"
