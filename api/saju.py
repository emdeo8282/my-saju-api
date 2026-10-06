from http.server import BaseHTTPRequestHandler
from korean_lunar_calendar import KoreanLunarCalendar
import json
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)
        
        try:
            year = int(params.get('year', [1990])[0])
            month = int(params.get('month', [1])[0])
            day = int(params.get('day', [1])[0])
            
            calendar = KoreanLunarCalendar()
            calendar.setSolarDate(year, month, day)
            
            lunar_year = calendar.lunarYear
            lunar_month = calendar.lunarMonth
            lunar_day = calendar.lunarDay
            
            ganji = calendar.getGapJaString()
            ganji_list = ganji.split()
            
            response_data = {
                "status": "success",
                "solar": f"{year}-{month:02d}-{day:02d}",
                "lunar": f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                "year_ganji": ganji_list[0] if len(ganji_list) > 0 else "",
                "month_ganji": ganji_list[1] if len(ganji_list) > 1 else "",
                "day_ganji": ganji_list[2] if len(ganji_list) > 2 else "",
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
