# EC2 Instance Starter

[![CI](https://github.com/Morichan/ec2-instance-starter/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/Morichan/ec2-instance-starter/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/Morichan/ec2-instance-starter/branch/main/graph/badge.svg?token=UBIJ60LWSS)](https://codecov.io/gh/Morichan/ec2-instance-starter)

本プロジェクトは、Amazon EC2インスタンスを起動するためのAPIを提供するSAMアーキテクチャです。

This project contains source code and supporting files for a serverless application that you can deploy with the SAM-CLI.
It includes the following files and folders.

- `src/` - Code for the application's Lambda function.
- `tests/` - Unit tests for the application code.
- `Pipfile` - Package management file by pipenv.
- `template.yaml` - A template that defines the application's AWS resources.



# How to use

## Deploy

デプロイにはSAM-CLIおよびpipenvを使用します。
また、SAM-CLIにはAWS-CLIを使います。
ローカルで動作確認する場合は、Dockerも利用します（こちら必須ではありません）。
pipenvはPython3で使用します。

To deploy use SAM-CLI (with AWS-CLI, and Docker if test was local) and pipenv (with Python3).

- SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Python 3 installed](https://www.python.org/downloads/)
- [Pipenv - GitHub](https://github.com/pypa/pipenv)
- Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

初回ビルドおよびデプロイには、以下コマンドを実行します。

To build and deploy this application for the first time, run the following in your shell:

```bash
pipenv lock --no-header --requirements > src/requirements.txt
pipenv run build
pipenv run deploy --guided
```

最初にモジュール読込み用requirements.txtを作成し、次にビルドして、そしてビルドしたパッケージをデプロイします。
その際、次の内容を聞かれます。

The first command will output requirements.txt of this application for SAM-CLI.
The second command will build the source of this application.
The third command will package and deploy this application to AWS, with a series of prompts:

- **Stack Name**:
    - CloudFormationスタック名です。
    - アカウントおよびリージョン内で一意な名前を設定する必要がありますが、難しく考える必要はありません。
- **AWS Region**:
    - CloudFormationスタックのデプロイ先リージョン名です。
- **Confirm changes before deploy**:
    - yesの場合、チェンジセット（CloudFormationスタックの差分一覧）を確認してからデプロイします。
    - noの場合、 `pipenv run deploy` ごとに確認する手間を省けます（が、差分が確認できないため思わぬリソースを作成してしまうかもしれません）。
- **Allow SAM CLI IAM role creation**:
    - IAMロールの作成を許可する必要があるため、こちらはyesを入力してください。
    - capabilities設定には `CAPABILITY_IAM` を指定してください。
- **Save arguments to samconfig.toml**:
    - yesにすると、次回以降はsamconfig.tomlファイルの設定内容を元にデプロイするため、 `pipenv run deploy` のみ（`--guided` オプション無し）でデプロイできます。保存することをオススメします。

デプロイ後はAPI GatewayエンドポイントURLを出力するため、そちらを叩いてください。

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

samconfig.tomlファイルを保存した場合、2回目以降のデプロイは、以下コマンドで可能です。

You chan deploy next command if you save samconfig.toml file.

```bash
pipenv run deploy
```


## Use the endpoint

次のコマンドを参考にしてください。

```bash
curl -X POST ${ENDPOINT}/start/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Basic $(echo -n "${AWS_USER_NAME}:${AWS_ACCESS_KEY_ID}" | base64)" \
  -d '{"instance_id": "i-00000000000000001", "dry_run": false}'
```

必要なパラメーターは、以下の通りです。

- instance_id: 起動対象のEC2インスタンスIDを文字列で指定します。設定がない場合は400系を返します。
- dry_run（任意）: trueの場合、EC2インスタンスを起動しませんが、起動対象のEC2インスタンスの存在については確認します。



# How to develop

## Tests

テストコードは `tests/` ディレクトリに存在します。
pipenvコマンドにてインストールとテストを実行してください。

Tests are defined in the `tests` folder in this project.
Use pipenv to install the test dependencies and run tests.

```bash
pipenv install --dev
# unit test
pipenv run test

# integration test, requiring deploying the stack first.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
AWS_SAM_STACK_NAME=<stack-name> pipenv run test-integration
```
