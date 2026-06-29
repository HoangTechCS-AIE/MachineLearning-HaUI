"""Thêm thư mục gốc project vào sys.path để `import src...` chạy được khi gọi script trực tiếp."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
