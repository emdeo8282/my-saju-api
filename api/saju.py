from http.server import BaseHTTPRequestHandler
from korean_lunar_calendar import KoreanLunarCalendar
import json
import urllib.parse
import re

# 💡 시간에 따른 시주(時柱) 계산 함수
def get_time_ganji(day_ganji, hour):
    if not day_ganji or hour is None:
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
            
            # 안전한 hour 파라미터 숫자 추출
            hour_param = params.get('hour', [None])[0]
            hour = None
            if hour_param is not None and str(hour_param).strip() != "":
                numbers = re.findall(r'\d+', str(hour_param))
                if numbers:
                    hour = int(numbers[0])

            calendar = KoreanLunarCalendar()
            calendar.setSolarDate(year, month, day)

            lunar_year = calendar.lunarYear
            lunar_month = calendar.lunarMonth
            lunar_day = calendar.lunarDay

            ganji = calendar.getGapJaString()
            ganji_list = ganji.split()

            day_ganji = ganji_list[2] if len(ganji_list) > 2 else ""
            time_ganji = get_time_ganji(day_ganji, hour)

            response_data = {
                "status": "success",
                "solar": f"{year}-{month:02d}-{day:02d}",
                "lunar": f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                "year_ganji": ganji_list[0] if len(ganji_list) > 0 else "",
                "month_ganji": ganji_list[1] if len(ganji_list) > 1 else "",
                "day_ganji": day_ganji,
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
