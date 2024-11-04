$jdk17 = (Get-ChildItem 'C:\Program Files\Eclipse Adoptium' -Filter 'jdk-17*' -Directory | Sort-Object Name -Descending | Select-Object -First 1).FullName
$env:JAVA_HOME = $jdk17
$env:Path = "$jdk17\bin;$env:Path"
$env:HADOOP_HOME = "$env:USERPROFILE\hadoop"
$env:Path = "$env:HADOOP_HOME\bin;$env:Path"

Write-Host "JAVA_HOME  : $env:JAVA_HOME"
Write-Host "HADOOP_HOME: $env:HADOOP_HOME"
java -version 2>&1 | Select-String "version"

python -m pytest tests/ -v --tb=short 2>&1 | Tee-Object pytest_full_out.txt
Write-Host "PYTEST_DONE exit=$LASTEXITCODE"
