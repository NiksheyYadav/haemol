$ErrorActionPreference = "Stop"

$envMap = @{}
Get-Content C:\dcai\.env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
    $envMap[$matches[1]] = $matches[2]
  }
}

$optionSettings = @(
  @{
    Namespace  = "aws:elasticbeanstalk:environment"
    OptionName = "EnvironmentType"
    Value      = "SingleInstance"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:environment"
    OptionName = "ServiceRole"
    Value      = "aws-elasticbeanstalk-service-role"
  },
  @{
    Namespace  = "aws:autoscaling:launchconfiguration"
    OptionName = "IamInstanceProfile"
    Value      = "aws-elasticbeanstalk-ec2-role"
  },
  @{
    Namespace  = "aws:autoscaling:launchconfiguration"
    OptionName = "InstanceType"
    Value      = "t3.small"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:environment:process:default"
    OptionName = "HealthCheckPath"
    Value      = "/health"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "APP_ENV"
    Value      = "production"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "TASK_MODE"
    Value      = "sync"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "DATABASE_URL"
    Value      = "sqlite:////tmp/biomarkly.db"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "SECRET_KEY"
    Value      = $envMap["SECRET_KEY"]
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "ADMIN_METRICS_TOKEN"
    Value      = $envMap["ADMIN_METRICS_TOKEN"]
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "AWS_REGION"
    Value      = "ap-south-1"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "S3_BUCKET_NAME"
    Value      = "biomarkly-uploads"
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "SARVAM_API_KEY"
    Value      = $envMap["SARVAM_API_KEY"]
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "POSTHOG_API_KEY"
    Value      = $envMap["POSTHOG_API_KEY"]
  },
  @{
    Namespace  = "aws:elasticbeanstalk:application:environment"
    OptionName = "POSTHOG_HOST"
    Value      = $envMap["POSTHOG_HOST"]
  }
) | ConvertTo-Json -Depth 3

$optionsPath = "C:\dcai\eb-options.json"
Set-Content -Path $optionsPath -Value $optionSettings -Encoding UTF8

aws elasticbeanstalk create-environment `
  --application-name biomarkly-api `
  --environment-name biomarkly-api-prod `
  --cname-prefix biomarkly-api-prod-013943758705 `
  --solution-stack-name "64bit Amazon Linux 2023 v4.12.1 running Docker" `
  --version-label initial-20260412 `
  --option-settings file://C:/dcai/eb-options.json `
  --region ap-south-1

Remove-Item $optionsPath -Force
