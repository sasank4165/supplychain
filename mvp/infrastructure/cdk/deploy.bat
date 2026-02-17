@echo off
REM Deploy CDK stack for Supply Chain MVP

echo Installing CDK dependencies...
pip install -r requirements.txt

echo.
echo Bootstrapping CDK (if not already done)...
cdk bootstrap

echo.
echo Synthesizing CDK stack...
cdk synth

echo.
echo Deploying CDK stack...
cdk deploy --require-approval never

echo.
echo Deployment complete! Check outputs above for resource ARNs.
