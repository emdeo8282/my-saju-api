from http.server import BaseHTTPRequestHandler
from korean_lunar_calendar import KoreanLunarCalendar
import json
import urllib.parse
import re

def get_time_ganji(day_ganji, hour_str):
    if not day_ganji or not hour_str:
        return ""
    
    # URL 인코딩 및 "시" 제거 처리
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

def calculate_single_saju(year, month, day, hour_raw):
    """사주 간지를 계산하는 단일 함수"""
    try:
        calendar = KoreanLunarCalendar()
        calendar.setSolarDate(int(year), int(month), int(day))

        ganji = calendar.getGapJaString()
        ganji_list = ganji.split()

        raw_day_ganji = ganji_list[2] if len(ganji_list) > 2 else ""
        day_ganji_clean = raw_day_ganji[0:2]
        
        time_ganji = get_time_ganji(day_ganji_clean, hour_raw)

        return {
            "solar": f"{year}-{int(month):02d}-{int(day):02d}",
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
            # 1. 내 정보 추출 (self_ 또는 일반 파라미터 모두 지원)
            year = params.get('year', params.get('self_year', [1990]))[0]
            month = params.get('month', params.get('self_month', [1]))[0]
            day = params.get('day', params.get('self_day', [1]))[0]
            hour_raw = params.get('hour', params.get('birthtime', params.get('self_hour', [''])))[0]

            self_saju = calculate_single_saju(year, month, day, hour_raw)

            response_data = {
                "status": "success",
                "self": self_saju
            }

            # 구버전 호환성을 위해 최상위에도 내 사주 정보 포함시켜줌
            if self_saju:
                response_data.update(self_saju)

            # 2. 상대방(partner) 정보가 존재할 경우에만 추가 계산
            partner_year = params.get('partner_year', params.get('p_year', [None]))[0]
            partner_month = params.get('partner_month', params.get('p_month', [None]))[0]
            partner_day = params.get('partner_day', params.get('p_day', [None]))[0]
            partner_hour = params.get('partner_hour', params.get('partner_birthtime', [None]))[0]

            if partner_year and partner_month and partner_day:
                partner_saju = calculate_single_saju(partner_year, partner_month, partner_day, partner_hour or '')
                if partner_saju:
                    response_data["partner"] = partner_saju

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
