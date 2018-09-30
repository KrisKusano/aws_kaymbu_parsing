REM make deployment package via docker image
docker build -f Dockerfile --tag lambda:latest .
docker run --name lambda -itd lambda:latest
docker cp lambda:/tmp/deploy.zip deploy.zip
docker stop lambda
docker rm lambda

REM upload to s3
aws s3 cp deploy.zip s3://gretchens-house-emails/