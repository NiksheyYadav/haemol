[CmdletBinding()]
param(
  [string]$VersionLabel = "initial-20260412"
)

$ErrorActionPreference = "Stop"

Start-Sleep -Seconds 10

try {
  aws iam add-role-to-instance-profile `
    --instance-profile-name aws-elasticbeanstalk-ec2-role `
    --role-name aws-elasticbeanstalk-ec2-role | Out-Null
} catch {
  if ($_ -notmatch "LimitExceeded") {
    throw
  }
}

$bundleDir = "C:\dcai\eb-bundle"
$zipPath = "C:\dcai\biomarkly-eb.zip"

if (Test-Path $bundleDir) {
  Remove-Item $bundleDir -Recurse -Force
}

if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Path "$bundleDir\apps" -Force | Out-Null
Copy-Item C:\dcai\Dockerfile "$bundleDir\Dockerfile"
Copy-Item C:\dcai\.dockerignore "$bundleDir\.dockerignore"
Copy-Item C:\dcai\apps\api "$bundleDir\apps\api" -Recurse

Compress-Archive -Path "$bundleDir\*" -DestinationPath $zipPath

$s3Key = "$VersionLabel.zip"

aws s3 cp $zipPath "s3://biomarkly-eb-deploys-013943758705-ap-south-1/$s3Key" --region ap-south-1

aws elasticbeanstalk create-application-version `
  --application-name biomarkly-api `
  --version-label $VersionLabel `
  --source-bundle "S3Bucket=biomarkly-eb-deploys-013943758705-ap-south-1,S3Key=$s3Key" `
  --region ap-south-1

Remove-Item $zipPath -Force
Remove-Item $bundleDir -Recurse -Force
