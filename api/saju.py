from http.server import BaseHTTPRequestHandler
from korean_lunar_calendar import KoreanLunarCalendar
import json
import urllib.parse
import re

def get_time_ganji(day_ganji, hour_str):
    if not day_ganji or not hour_str:
        return ""
    
    hour_str = urllib.parse.unquote(str(hour_str)).strip()
    hour_str = hour_str.replace("시", "").strip()
    
    jiji_map = {
        "자": 0, "자시": 0, "축": 1, "축시": 1, "인": 3, "인시": 3,
        "묘": 5, "묘시": 5, "진": 7, "진시": 7, "사": 9, "사시": 9,
        "오": 11, "오시": 11, "미": 13, "미시": 13, "신": 15, "신시": 15,
        "유": 17, "유시": 17, "술": 19, "술시": 19, "해": 21, "해시": 21
    }
    
    hour = None
    for name, h_val in jiji_map.items():
        if name in hour_str:
            hour = h_val
            break
            
    if hour is None:
        numbers = re.findall(r'\d+', hour_str)
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

def calculate_saju(year_val, month_val, day_val, hour_val):
    try:
        y = int(year_val)
        m = int(month_val)
        d = int(day_val)
        
        calendar = KoreanLunarCalendar()
        calendar.setSolarDate(y, m, d)

        ganji = calendar.getGapJaString()
        ganji_list = ganji.split()

        raw_day_ganji = ganji_list[2] if len(ganji_list) > 2 else ""
        day_ganji_clean = raw_day_ganji[0:2]
        time_ganji = get_time_ganji(day_ganji_clean, hour_val)

        return {
            "solar": f"{y}-{m:02d}-{d:02d}",
            "lunar": f"{calendar.lunarYear}-{calendar.lunarMonth:02d}-{calendar.lunarDay:02d}",
            "year_ganji": ganji_list[0] if len(ganji_list) > 0 else "",
            "month_ganji": ganji_list[1] if len(ganji_list) > 1 else "",
            "day_ganji": raw_day_ganji,
            "time_ganji": time_ganji,
            "raw_gapja": ganji
        }
    except Exception:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        try:
            # 내 정보: 어떤 파라미터 이름으로 들어오든 다 잡아냄 (우선순위 부여)
            y = params.get('self_year', params.get('year', [1990]))[0]
            m = params.get('self_month', params.get('month', [1]))[0]
            d = params.get('self_day', params.get('day', [1]))[0]
            h = params.get('self_hour', params.get('hour', params.get('birthtime', [''])) )[0]

            self_result = calculate_saju(y, m, d, h)
            
            # 만약 계산 실패 시 절대 기본값으로 안 빠지고 에러를 띄우도록 처리
            if not self_result:
                raise ValueError(f"Invalid self date parameters: {y}-{m}-{d}")

            response_data = {
                "status": "success",
                "self": self_result
            }
            response_data.update(self_result) # 구버전 호환용 최상위 주입

            # 상대방 정보 확인
            py = params.get('partner_year', params.get('p_year', [None]))[0]
            pm = params.get('partner_month', params.get('p_month', [None]))[0]
            pd = params.get('partner_day', params.get('p_day', [None]))[0]
            ph = params.get('partner_hour', params.get('partner_birthtime', [None]))[0]

            if py and pm and pd:
                partner_result = calculate_saju(py, pm, pd, ph or '')
                if partner_result:
                    response_data["partner"] = partner_result

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
