from flask import Flask, request, send_file, render_template
import os

app = Flask(__name__)

# 의도적으로 debug=True로 설정 (A10: Server-Side Request Forgery + Insufficient Logging & Monitoring)
app.config['DEBUG'] = True

# 프로젝트 디렉토리 기준 경로
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.resolve()
UPLOAD_ROOT = f"{BASE_DIR}/backup/uploads/"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    의도적인 취약점: A10 - Server-Side Request Forgery (SSRF)
    에러 메시지에 내부 경로 정보 노출
    """
    # 항상 실패하도록 설계 - 에러 메시지에 내부 경로 노출
    return render_template('upload_error.html', upload_root=UPLOAD_ROOT), 500

@app.route('/download')
def download():
    """
    의도적인 취약점: A01 - Path Traversal (Broken Access Control)
    path 파라미터에 대한 검증이 없어 임의의 파일 접근 가능
    """
    path = request.args.get('path', '')
    
    if not path:
        return render_template('download.html'), 400
    
    try:
        # 의도적으로 path traversal 취약점 존재 (검증 없음)
        # 사용자가 ../../../etc/passwd 같은 경로로 시스템 파일 접근 가능
        
        # 파일이 존재하는지 확인
        if os.path.exists(path):
            # 파일인 경우 다운로드
            if os.path.isfile(path):
                return send_file(path, as_attachment=True, download_name=os.path.basename(path))
            else:
                return f"Error: {path} is a directory, not a file", 400
        else:
            return f"Error: File not found at path: {path}", 404
            
    except Exception as e:
        return f"Error accessing file: {str(e)}", 500

if __name__ == '__main__':
    # 0.0.0.0으로 바인딩하여 외부에서 접근 가능하도록 설정
    app.run(host='0.0.0.0', port=8080, debug=True)

