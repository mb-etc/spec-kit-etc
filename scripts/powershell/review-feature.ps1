# review-feature.ps1 - Script for review commands to get feature context and create review outputs
# Usage: ./review-feature.ps1 [-Json] [-ReviewType TYPE] [-RequireSpec] [-RequirePlan] [-RequireTasks]
#
# Parameters:
#   -Json            Output JSON format for command parsing
#   -ReviewType      Type of review (uat, implementation, security, readiness, summary, fix, release-notes)
#   -RequireSpec     Require spec.md to exist
#   -RequirePlan     Require implementation-plan.md to exist
#   -RequireTasks    Require tasks.md to exist
#   -CreateOutput    Create the output directory/file structure
#
# Outputs JSON with:
#   FEATURE_DIR, FEATURE_NAME, BRANCH_NAME, REVIEW_TYPE, OUTPUT_FILE, OUTPUT_DIR,
#   AVAILABLE_DOCS (list of existing spec files), CONSTITUTION_PATH

param(
    [switch]$Json,
    [string]$ReviewType = "",
    [switch]$RequireSpec,
    [switch]$RequirePlan,
    [switch]$RequireTasks,
    [switch]$CreateOutput
)

$ErrorActionPreference = "Stop"

# Find repo root
function Find-RepoRoot {
    $dir = Get-Location
    while ($dir -and $dir.Path -ne [System.IO.Path]::GetPathRoot($dir.Path)) {
        if ((Test-Path (Join-Path $dir ".git")) -or (Test-Path (Join-Path $dir "specs"))) {
            return $dir.Path
        }
        $dir = Split-Path $dir -Parent
    }
    return (Get-Location).Path
}

$RepoRoot = Find-RepoRoot

# Get current branch name
function Get-BranchName {
    try {
        $isGitRepo = & git rev-parse --is-inside-work-tree 2>$null
        if ($isGitRepo) {
            $branch = & git branch --show-current 2>$null
            if ($branch) { return $branch }
        }
    } catch {}
    return "main"
}

$BranchName = Get-BranchName

# Derive feature directory from branch name
function Get-FeatureDir {
    param([string]$Branch)
    
    $specsDir = Join-Path $RepoRoot "specs"
    
    if (Test-Path $specsDir) {
        # Try exact match first
        $exactPath = Join-Path $specsDir $Branch
        if (Test-Path $exactPath) {
            return $exactPath
        }
        
        # Try to find feature by branch prefix
        $featureDirs = Get-ChildItem -Path $specsDir -Directory -ErrorAction SilentlyContinue
        foreach ($dir in $featureDirs) {
            if ($dir.Name -eq $Branch) {
                return $dir.FullName
            }
        }
    }
    
    # Return expected path
    return Join-Path $specsDir $Branch
}

$FeatureDir = Get-FeatureDir -Branch $BranchName
$FeatureName = if ($BranchName -match '^\d+-(.+)$') { $Matches[1] } else { $BranchName }

# Define output paths based on review type
function Get-OutputInfo {
    param(
        [string]$Type,
        [string]$Dir
    )
    
    switch ($Type) {
        "uat" {
            return @{
                OutputDir = Join-Path $Dir "uat"
                OutputFile = Join-Path $Dir "uat/plan.md"
            }
        }
        "implementation" {
            return @{
                OutputDir = $Dir
                OutputFile = Join-Path $Dir "review-implementation.md"
            }
        }
        "security" {
            return @{
                OutputDir = $Dir
                OutputFile = Join-Path $Dir "security-review.md"
            }
        }
        "readiness" {
            return @{
                OutputDir = $Dir
                OutputFile = Join-Path $Dir "release-readiness.md"
            }
        }
        "summary" {
            return @{
                OutputDir = Join-Path $Dir "docs"
                OutputFile = Join-Path $Dir "docs/SUMMARY.md"
            }
        }
        "fix" {
            return @{
                OutputDir = $Dir
                OutputFile = Join-Path $Dir "fix-report.md"
            }
        }
        "release-notes" {
            return @{
                OutputDir = $Dir
                OutputFile = Join-Path $Dir "release-notes.md"
            }
        }
        default {
            return @{
                OutputDir = $Dir
                OutputFile = Join-Path $Dir "review-output.md"
            }
        }
    }
}

$OutputInfo = Get-OutputInfo -Type $ReviewType -Dir $FeatureDir
$OutputDir = $OutputInfo.OutputDir
$OutputFile = $OutputInfo.OutputFile

# Check for required files
function Test-RequiredFiles {
    $errors = @()
    
    if ($RequireSpec -and -not (Test-Path (Join-Path $FeatureDir "spec.md"))) {
        $errors += "spec.md not found. Run /speckit.specify first."
    }
    
    if ($RequirePlan -and -not (Test-Path (Join-Path $FeatureDir "implementation-plan.md"))) {
        $errors += "implementation-plan.md not found. Run /speckit.plan first."
    }
    
    if ($RequireTasks -and -not (Test-Path (Join-Path $FeatureDir "tasks.md"))) {
        $errors += "tasks.md not found. Run /speckit.tasks first."
    }
    
    if ($errors.Count -gt 0) {
        if ($Json) {
            $errorJson = @{
                error = $true
                messages = $errors
            } | ConvertTo-Json -Compress
            Write-Output $errorJson
        } else {
            foreach ($err in $errors) {
                Write-Error "ERROR: $err"
            }
        }
        exit 1
    }
}

# Build list of available docs
function Get-AvailableDocs {
    $docs = @()
    
    if (Test-Path (Join-Path $FeatureDir "spec.md")) { $docs += "spec.md" }
    if (Test-Path (Join-Path $FeatureDir "implementation-plan.md")) { $docs += "implementation-plan.md" }
    if (Test-Path (Join-Path $FeatureDir "tasks.md")) { $docs += "tasks.md" }
    if (Test-Path (Join-Path $FeatureDir "quickstart.md")) { $docs += "quickstart.md" }
    if (Test-Path (Join-Path $FeatureDir "data-model.md")) { $docs += "data-model.md" }
    if (Test-Path (Join-Path $FeatureDir "checklists")) { $docs += "checklists/" }
    if (Test-Path (Join-Path $FeatureDir "uat")) { $docs += "uat/" }
    
    return $docs -join ","
}

# Get constitution path
function Get-ConstitutionPath {
    $paths = @(
        (Join-Path $RepoRoot ".specify/memory/constitution.md"),
        (Join-Path $RepoRoot "memory/constitution.md")
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return ""
}

$ConstitutionPath = Get-ConstitutionPath
$AvailableDocs = Get-AvailableDocs

# Check required files
Test-RequiredFiles

# Create output directory if requested
if ($CreateOutput -and $OutputDir) {
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
}

# Output results
if ($Json) {
    $output = @{
        REPO_ROOT = $RepoRoot
        FEATURE_DIR = $FeatureDir
        FEATURE_NAME = $FeatureName
        BRANCH_NAME = $BranchName
        REVIEW_TYPE = $ReviewType
        OUTPUT_DIR = $OutputDir
        OUTPUT_FILE = $OutputFile
        CONSTITUTION_PATH = $ConstitutionPath
        AVAILABLE_DOCS = $AvailableDocs
        SPEC_FILE = Join-Path $FeatureDir "spec.md"
        PLAN_FILE = Join-Path $FeatureDir "implementation-plan.md"
        TASKS_FILE = Join-Path $FeatureDir "tasks.md"
    }
    $output | ConvertTo-Json
} else {
    Write-Output "Repository Root: $RepoRoot"
    Write-Output "Feature Directory: $FeatureDir"
    Write-Output "Feature Name: $FeatureName"
    Write-Output "Branch: $BranchName"
    Write-Output "Review Type: $ReviewType"
    Write-Output "Output Directory: $OutputDir"
    Write-Output "Output File: $OutputFile"
    Write-Output "Constitution: $ConstitutionPath"
    Write-Output "Available Docs: $AvailableDocs"
}
