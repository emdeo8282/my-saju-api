from http.server import BaseHTTPRequestHandler
from korean_lunar_calendar import KoreanLunarCalendar
import json
import urllib.parse
import re

def get_time_ganji(day_ganji, hour_str):
    if not day_ganji or not hour_str:
        return ""
    
    # 한글 시간명 매핑 (축시 -> 1시, 인시 -> 3시 등)
    jiji_map = {
        "자": 0, "축": 1, "인": 3, "묘": 5, "진": 7, "사": 9,
        "오": 11, "미": 13, "신": 15, "유": 17, "술": 19, "해": 21
    }
    
    hour = None
    # 1. 한글 십이지시(자/축/인/묘...) 이름이 들어왔는지 확인
    for name, h_val in jiji_map.items():
        if name in str(hour_str):
            hour = h_val
            break
            
    # 2. 한글 이름이 없다면 숫자를 자동 추출
    if hour is None:
        numbers = re.findall(r'\d+', str(hour_str))
        if numbers:
            hour = int(numbers[0])

    if hour is None:
        return ""

    cheongan = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    jiji = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    jiji_idx = ((hour + 1) % 24) // 2
    day_stem = day_ganji[0]
    
    if day_stem not in cheongan:
        return ""
    
    stem_idx = cheongan.index(day_stem)
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
            
            # hour 또는 birthtime 파라미터 수신
            hour_param = params.get('hour', params.get('birthtime', [None]))[0]

            calendar = KoreanLunarCalendar()
            calendar.setSolarDate(year, month, day)

            lunar_year = calendar.lunarYear
            lunar_month = calendar.lunarMonth
            lunar_day = calendar.lunarDay

            ganji = calendar.getGapJaString()
            ganji_list = ganji.split()

            raw_day_ganji = ganji_list[2] if len(ganji_list) > 2 else ""
            day_ganji_clean = raw_day_ganji[0:2]
            
            time_ganji = get_time_ganji(day_ganji_clean, hour_param)

            response_data = {
                "status": "success",
                "solar": f"{year}-{month:02d}-{day:02d}",
                "lunar": f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                "year_ganji": ganji_list[0] if len(ganji_list) > 0 else "",
                "month_ganji": ganji_list[1] if len(ganji_list) > 1 else "",
                "day_ganji": raw_day_ganji,
                "time_ganji": time_ganji,
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
