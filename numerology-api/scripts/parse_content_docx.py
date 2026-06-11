"""Parse the `Nội dung` docx corpus → structured JSON for DB seeding.

HOST-SIDE step (needs python-docx + the docx files, which are NOT in the
container). Emits scripts/data/numerology_content.json consumed by
seed_content_from_docx.py inside the container.

Each docx group needs its own segmentation rule (the corpus is heterogeneous):
  - Group A: one file per code        (Số Chủ Đạo folder)
  - Group B: one file, many codes     (split by a per-file header regex)
  - Group C: Biểu đồ ngày sinh         (per-number files + arrow files)

Content is rendered to lightweight HTML (<p>, <h4>, <ul><li>) — `content`
columns are rendered with Jinja `| safe`.

Run:  python -m scripts.parse_content_docx        (from numerology-api/)
"""

from __future__ import annotations

import html
import io
import json
import re
from pathlib import Path

import docx

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = REPO_ROOT / "data" / "Nôi dung"
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_FILE = OUT_DIR / "numerology_content.json"


# ── HTML rendering ──────────────────────────────────────────────────────────
def _is_subheading(text: str) -> bool:
    """Heuristic: short, mostly-uppercase line → section sub-heading."""
    if not text or len(text) > 70:
        return False
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and text == text.upper()


def paras_to_html(paras: list) -> str:
    """Render a list of python-docx paragraphs to simple HTML."""
    out: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for p in paras:
        text = p.text.strip()
        if not text:
            continue
        style = (p.style.name or "").lower()
        esc = html.escape(text)
        if "list" in style:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{esc}</li>")
        elif _is_subheading(text):
            close_list()
            out.append(f"<h4>{esc}</h4>")
        else:
            close_list()
            out.append(f"<p>{esc}</p>")
    close_list()
    return "".join(out)


# ── helpers ─────────────────────────────────────────────────────────────────
def norm_code(raw: str) -> str:
    """Normalize a code token: '11/2' → '11', '13/4' → '13', '5' → '5'."""
    raw = raw.strip()
    if "/" in raw:
        raw = raw.split("/")[0]
    return raw.strip()


def load_paras(path: Path) -> list:
    return docx.Document(str(path)).paragraphs


records: list[dict] = []


def add(table: str, code: str, title: str, paras: list, prefix_text: str = ""):
    """Append a record; merge content if (table,code) already present.

    prefix_text: inline body that sat on the same line as the header
    (e.g. "SỐ ĐIỆN THOẠI LÀ 9. <content>") — prepended as a <p>.
    """
    code = str(code)
    body = (f"<p>{html.escape(prefix_text.strip())}</p>" if prefix_text.strip() else "") + paras_to_html(paras)
    for r in records:
        if r["table"] == table and r["code"] == code:
            r["content"] += body  # concat repeated blocks (e.g. Số Trưởng Thành)
            return
    records.append({"table": table, "code": code, "title": title.strip()[:250], "content": body})


# ── Group A: Số Chủ Đạo — one file per code ──────────────────────────────────
def parse_main_number():
    folder = BASE / "1 SỐ CHỦ ĐẠO - SỐ ĐƯỜNG ĐỜI"
    for f in folder.glob("*.docx"):
        if f.name.startswith("~$"):
            continue
        m = re.match(r"^(\d+)\b", f.name)
        if not m:
            continue
        code = m.group(1)
        paras = load_paras(f)
        title = next((p.text.strip() for p in paras if p.text.strip()), f"Số Chủ Đạo {code}")
        add("MainNumber", code, title, paras)


# ── Group B: single file, many codes (header-regex split) ────────────────────
# (filename, table, header_regex with one capture group, skip_regex|None)
GROUP_B = [
    ("4 SO THAI DO.docx", "AttitudeNumber",
     r"^SỐ THÁI ĐỘ\s+(\d+)\s*$", None),
    ("5 SỐ NGÀY SINH.docx", "BirthdayNumber",
     r"^(?:CON\s+)?SỐ NGÀY SINH\s+(\d+(?:/\d+)?)\s*$", None),
    ("6 SO SỨ MỆNH.docx", "MissionNumber",
     r"^SỐ SỨ MỆNH\s+(\d+(?:/\d+)?)\s*$", r"^TH[AĂ]M?\s*KHẢO|^THAO KHẢO"),
    ("7 SO LINH HON.docx", "SoulsNumber",
     r"^SỐ LINH HỒN\s+(\d+(?:/\d+)?)\s*$", r"^TH[AĂ]?O?\s*KHẢO|^THAM KHẢO"),
    ("8 SO NHAN CACH.docx", "MatureNumber",
     r"^SỐ NHÂN CÁCH\s+(\d+(?:/\d+)?)\s*$", r"^THAM KHẢO|^THAO KHẢO"),
    ("8 SỐ TRƯỞNG THÀNH.docx", "DevelopmentNumber",
     r"^SỐ TRƯỞNG THÀNH SỐ\s+(\d+)\s*$", None),
    ("9 SỐ PHÁT TRIỂN.docx", "GrowthNumber",
     r"^CHỈ SỐ PHÁT TRIỂN\s+Số\s+(\d+)\b", None),
    ("10 SỐ NỘI CẢM.docx", "KarmicNumber",
     r"^SỐ NỘI CẢM\s+(\d+)\s*$", None),
    ("11 SỐ NỢ NGHIỆP.docx", "KarmicDebtNumber",
     r"^NỢ NGHIỆP\s+(?:SỐ\s+)?(\d+/\d+)", None),
    ("12 SỐ THIẾU.docx", "MissNumber",
     r"^SỐ\s+(\d+)\s*$", None),
    ("14 THỂ NHÂN DẠNG.docx", "Identifiable",
     r"^THỂ NHÂN DẠNG\s+(\d+)\s*[–-]", None),
    ("15 SỐ ĐIỆN THOẠI.docx", "PhoneNumber",
     r"^SỐ ĐIỆN THOẠI LÀ\s+(\d+)\.", None),
    ("17 SỐ THÁNG CÁ NHÂN.docx", "PersonalMonthNumber",
     r"^THÁNG CÁ NHÂN SỐ\s+(\d+)\s*$", None),
    ("3.1 GIAI ĐOẠN CỦA CUỘC ĐỜI.docx", "StagesOfLife",
     r"^CHỈ SỐ GIAI ĐOẠN CUỘC ĐỜI\s+(\d+(?:/\d+)?)\s*$", None),
    ("3.2 BỐN ĐỈNH CAO CUỘC ĐỜI.docx", "LifePeak",
     r"^ĐỈNH CAO MANG SỐ\s+(\d+(?:/\d+)?)\s*$", None),
    ("3.3 BỐN THÁCH THỨC CUỘC ĐỜI.docx", "ChallengeLife",
     r"^THÁCH THỨC MANG SỐ\s+(\d+)\s*$", None),
]


def parse_group_b():
    for fname, table, header_re, skip_re in GROUP_B:
        path = BASE / fname
        if not path.exists():
            print(f"  [WARN] missing file: {fname}")
            continue
        hre = re.compile(header_re)
        sre = re.compile(skip_re) if skip_re else None
        cur_code = None
        cur_title = ""
        cur_prefix = ""
        buf: list = []
        skipping = False

        def flush():
            if cur_code is not None and (buf or cur_prefix):
                add(table, norm_code(cur_code), cur_title, list(buf), cur_prefix)

        for p in load_paras(path):
            t = p.text.strip()
            if sre and t and sre.match(t):
                flush(); cur_code = None; buf.clear(); cur_prefix = ""; skipping = True
                continue
            m = hre.match(t) if t else None
            if m:
                flush()
                cur_code = m.group(1)
                cur_title = t
                # capture any inline body following the header token on the same line
                cur_prefix = t[m.end():].strip(" :.–-")
                buf = []
                skipping = False
                continue
            if cur_code is not None and not skipping:
                buf.append(p)
        flush()


# ── Group C: Biểu đồ ngày sinh ────────────────────────────────────────────────
_ORDINAL = [
    (r"^MỘT (?:SỐ|CON)", "_1"), (r"^HAI (?:SỐ|CON)", "_2"), (r"^BA (?:SỐ|CON)", "_3"),
    (r"^BỐN (?:SỐ|CON)", "_4"), (r"^(?:TỪ\s+)?NĂM (?:SỐ|CON)", "_5"),
]
_ISOLATED = re.compile(r"(LẺ LOI|ĐƠN ĐỘC)")


def parse_birthday_chart():
    folder = BASE / "2 BIỂU ĐỒ NGÀY SINH"
    for f in folder.glob("*.docx"):
        n = f.name
        if n.startswith("~$"):
            continue
        # Arrow files: MŨI TÊN [TRỐNG] a-b-c ...
        if n.upper().startswith("MŨI TÊN"):
            empty = "TRỐNG" in n.upper()
            digits = "".join(re.findall(r"\d", n.split(".")[0]))
            if not digits:
                continue
            code = ("not_" if empty else "") + digits
            paras = load_paras(f)
            title = next((p.text.strip() for p in paras if p.text.strip()), code)
            add("BirthdayChart", code, title, paras)
            continue
        # Per-number files: SỐ N TRONG BDNS
        m = re.search(r"SỐ\s+(\d+)\s+TRONG", n.upper())
        if not m:
            continue  # skip DIEM DANH... overview
        base_num = m.group(1)
        paras = load_paras(f)
        # Segment: intro (code N) → ordinals (_1.._5) → isolated (_single)
        cur_suffix = ""  # "" = base intro
        cur_title = f"Số {base_num} trong biểu đồ ngày sinh"
        buf: list = []

        def flush(suffix, title):
            if buf:
                code = base_num + suffix
                add("BirthdayChart", code, title, list(buf))

        for p in paras:
            t = p.text.strip()
            matched = None
            for pat, suf in _ORDINAL:
                if t and re.match(pat, t):
                    matched = suf; break
            if matched is None and t and _ISOLATED.search(t):
                matched = "_single"
            if matched is not None:
                flush(cur_suffix, cur_title)
                cur_suffix = matched
                cur_title = t
                buf = []
                continue
            buf.append(p)
        flush(cur_suffix, cur_title)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parse_main_number()
    parse_group_b()
    parse_birthday_chart()

    OUT_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")

    # Coverage report
    by_table: dict[str, list[str]] = {}
    for r in records:
        by_table.setdefault(r["table"], []).append(r["code"])
    rep = io.StringIO()
    rep.write(f"TOTAL records: {len(records)}\n")
    for tbl in sorted(by_table):
        codes = sorted(by_table[tbl])
        rep.write(f"  {tbl:<22} {len(codes):>3}  codes={codes}\n")
    report = rep.getvalue()
    (OUT_DIR / "parse_report.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    main()
