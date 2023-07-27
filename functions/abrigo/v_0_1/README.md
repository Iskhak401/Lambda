# How to deploy

1. Package all the dependencies into .zip file
```shell
$ cd <project>/lambdas/abrigo/v_0_1
$ mkdir -p package/python
# Note: Python 3.10 should be used
$ pip3 install -r requirements.txt -t ./package/python/
$ cd package
$ zip -r dependencies.zip .
```
 
2. [Create AWS Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-create) using `dependencies.zip`
</br>_Note_: I suggest creating two layers: DB related dependency and Requests dependency   

3. Deploy a new (or update existing) AWS Lambda Function (`lambda_function.py` contains required lambda code)

4. Configure Lambda
</br> 4.1. Set environment variables: `REGION` (AWS region to use) and `DATABASE_URI` (as follows `postgresql://<user>:<password>@<hostname>:<port>/<db_name>`)
</br> 4.2. Add layers (deployed previously)
</br> 4.3. Increase Lambda Timeout to 10 seconds (Configuration -> General Configuration -> Edit)
</br> 4.4. Grant all required permission to Lambda role (read data from SecretsManager)
