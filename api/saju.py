from http.server import BaseHTTPRequestHandler
from korean_lunar_calendar import KoreanLunarCalendar
import json
import urllib.parse

# 💡 시간에 따른 시주(時柱) 계산 함수
def get_time_ganji(day_ganji, hour):
    if not day_ganji or hour is None:
        return ""
    
    # 천간과 지지 목록
    cheongan = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    jiji = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 시간(0~23)에 해당하는 지지 인덱스 (자시: 23~01시 -> 0)
    jiji_idx = ((hour + 1) % 24) // 2
    
    # 일간(일주의 첫 글자) 찾기
    day_stem = day_ganji[0]
    if day_stem not in cheongan:
        return ""
    
    stem_idx = cheongan.index(day_stem)
    
    # 일간에 따른 자시(子時)의 천간 시작점 계산 (시두법)
    # 갑/기일 -> 갑자시(0), 을/경일 -> 병자시(2), 병/신일 -> 무자시(4), 정/임일 -> 경자시(6), 무/계일 -> 임자시(8)
    start_stem_idx = (stem_idx % 5) * 2
    time_stem_idx = (start_stem_idx + jiji_idx) % 10
    
    return f"{cheongan[time_stem_idx]}{jiji[jiji_idx]}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        try:
            year = int(params.get('year', [1990])[0])
            month = int(params.get('month', [1])[0])
            day = int(params.get('day', [1])[0])
            
            # 💡 hour 파라미터 추가 (기본값 None)
            hour_param = params.get('hour', [None])[0]
            hour = int(hour_param) if hour_param is not None and hour_param != "" else None

            calendar = KoreanLunarCalendar()
            calendar.setSolarDate(year, month, day)

            lunar_year = calendar.lunarYear
            lunar_month = calendar.lunarMonth
            lunar_day = calendar.lunarDay

            ganji = calendar.getGapJaString()
            ganji_list = ganji.split()

            day_ganji = ganji_list[2] if len(ganji_list) > 2 else ""
            
            # 💡 시주 계산 호출
            time_ganji = get_time_ganji(day_ganji, hour)

            response_data = {
                "status": "success",
                "solar": f"{year}-{month:02d}-{day:02d}",
                "lunar": f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                "year_ganji": ganji_list[0] if len(ganji_list) > 0 else "",
                "month_ganji": ganji_list[1] if len(ganji_list) > 1 else "",
                "day_ganji": day_ganji,
                "time_ganji": time_ganji,  # 👈 시간 간지 결과 추가!
                "raw_gapja": ganji
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
