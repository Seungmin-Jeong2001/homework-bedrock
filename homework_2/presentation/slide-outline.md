# 5-Slide PPT Outline

## 1. Title

- CodeBuddy: AWS Bedrock Agent 기반 GitHub PR 자동 리뷰
- PDF 실습 원형 아키텍처 유지, 배포는 Terraform/Ansible

## 2. Architecture

- GitHub Webhook -> API Gateway -> Lambda -> Bedrock Agent
- Bedrock Agent가 Knowledge Base를 조회
- Knowledge Base 벡터 저장소는 OpenSearch Serverless

## 3. Implementation

- Terraform으로 API Gateway, Lambda, Bedrock Agent, Knowledge Base, OpenSearch Serverless 생성
- Ansible로 OpenSearch `codebuddy-index` 생성 단계를 Knowledge Base 전에 실행
- Lambda는 PR diff를 가져와 Bedrock Agent Runtime `InvokeAgent` 호출
- GitHub PR 댓글과 Slack 알림 등록

## 4. Demo

- `./scripts/deploy.sh`
- GitHub Webhook 등록
- 취약 샘플 코드 PR 생성
- PR 리뷰 댓글과 Slack 알림 확인

## 5. Retrospective and Cost

- OpenSearch Serverless와 Knowledge Base 비용 경고
- CloudFormation 시도 후 Terraform/Ansible로 전환
- 전환 이유: Knowledge Base 생성 전 OpenSearch vector index 생성 순서 제어
- 아키텍처 자체는 Bedrock Agent/Knowledge Base/OpenSearch 유지
