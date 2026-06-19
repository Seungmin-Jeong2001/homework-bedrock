# Cost Analysis

예산 목표: $50 이하. 신규 프리티어 계정에서는 더 보수적으로 AWS Budget $30 알림을 먼저 설정합니다.

## PDF 실습 원형 비용 항목

- API Gateway HTTP API: webhook 요청 수 기준
- Lambda: 실행 횟수와 실행 시간 기준
- Bedrock Agent: foundation model 호출 비용
- Bedrock Knowledge Base: ingestion과 retrieve 과정의 embedding/model 사용 비용
- OpenSearch Serverless: Knowledge Base 벡터 저장소 OCU 비용
- CloudWatch Logs: 로그 수집과 저장 비용

## 가장 중요한 비용 경고

OpenSearch Serverless와 Knowledge Base는 이 제출 기준의 PDF 실습 원형에는 포함됩니다. 다만 신규 프리티어 계정에서는 OpenSearch Serverless OCU와 Knowledge Base ingestion 비용이 예상보다 커질 수 있습니다.

비용 확인과 삭제 확인은 실제 배포 리전인 `ap-northeast-2` 기준으로 진행합니다.

비용을 줄이려면:

- 시연 직전에만 stack을 생성합니다.
- Knowledge Base 문서는 작은 샘플만 사용합니다.
- 테스트 PR diff를 작게 유지합니다.
- 시연 직후 `./scripts/destroy.sh`로 삭제합니다.

## 대체 가능한 경량 구현안

비용을 줄이려면 시연 시간을 짧게 유지하고 Knowledge Base 문서를 작게 유지하세요. 본 구현은 Bedrock Agent, Knowledge Base, OpenSearch Serverless를 실제로 사용합니다.

## 삭제 후 확인

```bash
aws opensearchserverless list-collections --region ap-northeast-2
aws bedrock-agent list-agents --region ap-northeast-2
aws lambda get-function --function-name codebuddy-orchestrator --region ap-northeast-2
aws apigatewayv2 get-apis --region ap-northeast-2
```

If you previously tested another region such as `us-east-1`, check both regions. The default deployment region for this project remains `ap-northeast-2`.

```bash
aws cloudformation describe-stacks --region us-east-1
aws opensearchserverless list-collections --region ap-northeast-2
aws opensearchserverless list-collections --region us-east-1
aws bedrock-agent list-agents --region ap-northeast-2
aws bedrock-agent list-agents --region us-east-1
```
