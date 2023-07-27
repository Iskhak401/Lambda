# How to deploy

1. Package all the dependencies into .zip file
```shell
$ cd <project>/lambdas/cognito_auth
$ mkdir -p package/python
# Note: Python 3.10 should be used
$ pip3 install -r requirements.txt -t ./package/python/
$ cd package
$ zip -r dependencies.zip .
```
 
2. [Create AWS Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-create) using `dependencies.zip`

3. Deploy a new (or update existing) AWS Lambda Function (`lambda_function.py` contains required lambda code)

4. Configure Lambda
</br> 4.1. Add the DB layer (deployed previously)
</br> 4.2. Grant all required permission to Lambda role (read data from SecretsManager)
