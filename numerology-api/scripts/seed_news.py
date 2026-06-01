"""Seed sample numerology blog/news articles.

Idempotent: check-then-insert by title.
Category 1 = blog (shown on home swiper via /api/news-top AND on /blog list).
Run: python -m scripts.seed_news
"""

import asyncio
import sys

from sqlalchemy import select

from app.db.models.news import News
from scripts._db import get_session

# Image paths are served by the API at /media/... (StaticFiles mount).
# The frontend prefixes these with BASE_URL.
IMG = "/media/blog"

NEWS: list[dict] = [
    {
        "title": "Số chủ đạo là gì? Cách tính và ý nghĩa con số đường đời",
        "short_content": (
            "Số chủ đạo (Life Path) là chỉ số quan trọng nhất trong thần số học, "
            "tiết lộ sứ mệnh và con đường cốt lõi của cuộc đời bạn."
        ),
        "content": (
            "<p>Số chủ đạo (Life Path Number) được xem là chỉ số quan trọng nhất "
            "trong thần số học Pythagoras. Nó được tính từ tổng các chữ số trong "
            "ngày, tháng, năm sinh và rút gọn về một chữ số từ 1 đến 9 (hoặc giữ "
            "nguyên các số bậc thầy 11, 22, 33).</p>"
            "<h2>Cách tính số chủ đạo</h2>"
            "<p>Cộng tất cả các chữ số trong ngày tháng năm sinh cho đến khi được "
            "một chữ số duy nhất. Ví dụ sinh ngày 02/09/2001: "
            "0+2+0+9+2+0+0+1 = 14 → 1+4 = 5. Vậy số chủ đạo là 5.</p>"
            "<h2>Ý nghĩa của số chủ đạo</h2>"
            "<p>Mỗi số chủ đạo mang một archetype riêng: Số 1 là người lãnh đạo, "
            "Số 2 người hòa giải, Số 5 người tự do, Số 8 người quyền lực, Số 9 "
            "người nhân ái… Hiểu số chủ đạo giúp bạn nhận ra điểm mạnh, điểm yếu "
            "và hướng phát triển phù hợp nhất với chính mình.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/cach_tinh_so_chu_dao.png",
    },
    {
        "title": "Cách tính thần số học chuẩn Pythagoras theo tên và ngày sinh",
        "short_content": (
            "Hướng dẫn chi tiết cách tính các chỉ số thần số học từ họ tên khai "
            "sinh và ngày tháng năm sinh theo chuẩn Pythagoras."
        ),
        "content": (
            "<p>Thần số học Pythagoras đã có tuổi đời hơn 2500 năm. Mỗi người đều "
            "được liên kết với những con số tính từ ngày sinh và họ tên.</p>"
            "<h2>Quy tắc rút gọn</h2>"
            "<p>Mọi con số đều có thể rút gọn về một chữ số đơn bằng cách cộng các "
            "chữ số lại với nhau. Ví dụ số 19: 1+9 = 10 → 1+0 = 1.</p>"
            "<h2>Bảng quy đổi chữ cái sang số</h2>"
            "<p>Trong cách tính theo tên, mỗi chữ cái tương ứng với một con số từ "
            "1 đến 9 (A=1, B=2, … I=9, J=1…). Từ đó ta tính được Số sứ mệnh, Số "
            "linh hồn và Số nhân cách.</p>"
            "<p>Kết hợp cả tên và ngày sinh sẽ cho bạn bức tranh thần số học toàn "
            "diện và chính xác nhất.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/cach-tinh-than-so-hoc.jpg",
    },
    {
        "title": "Ý nghĩa 12 con số trong thần số học bạn nên biết",
        "short_content": (
            "Từ số 1 đến số 9 cùng các số bậc thầy 11, 22, 33 — mỗi con số mang "
            "một tần số rung động và ý nghĩa riêng biệt."
        ),
        "content": (
            "<p>Trong thần số học, mỗi con số mang một định nghĩa riêng không thay "
            "đổi dù xuất hiện ở vị trí nào trong bản đồ.</p>"
            "<h2>Các số cơ bản 1-9</h2>"
            "<p>Số 1 – độc lập, tiên phong. Số 2 – hòa hợp, hợp tác. Số 3 – sáng "
            "tạo, biểu đạt. Số 4 – kỷ luật, ổn định. Số 5 – tự do, đổi thay. Số 6 "
            "– yêu thương, trách nhiệm. Số 7 – trí tuệ, nội tâm. Số 8 – quyền lực, "
            "thịnh vượng. Số 9 – nhân ái, vị tha.</p>"
            "<h2>Các số bậc thầy</h2>"
            "<p>Số 11 (trực giác), 22 (kiến tạo) và 33 (chữa lành) là những con số "
            "đặc biệt, mang năng lượng mạnh mẽ và sứ mệnh cao cả hơn.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/y_nghia_nhung_con_so.png",
    },
    {
        "title": "Biểu đồ ngày sinh và những mũi tên sức mạnh",
        "short_content": (
            "Biểu đồ ngày sinh sắp xếp các chữ số vào lưới 9 ô, tiết lộ điểm mạnh "
            "và những khía cạnh còn khuyết thiếu của bạn."
        ),
        "content": (
            "<p>Biểu đồ ngày sinh (Birth Chart) là công cụ trực quan sắp xếp các "
            "chữ số trong ngày sinh vào một lưới 3x3 theo trục Pythagoras.</p>"
            "<h2>Mũi tên sức mạnh</h2>"
            "<p>Khi ba ô trên một hàng, cột hoặc đường chéo đều có số, ta có một "
            "'mũi tên sức mạnh' thể hiện tài năng nổi trội. Ngược lại, hàng trống "
            "là 'mũi tên trống' chỉ ra điểm cần bồi đắp.</p>"
            "<p>Đọc biểu đồ ngày sinh giúp bạn hiểu rõ tư duy, cảm xúc và hành động "
            "của bản thân ở mức sâu sắc hơn.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/tuoi_doi_than_so_hoc.png",
    },
    {
        "title": "Năm cá nhân: Bí quyết chọn đúng thời điểm hành động",
        "short_content": (
            "Năm cá nhân vận hành theo chu kỳ 1-9, giúp bạn biết khi nào nên khởi "
            "đầu, xây dựng, bứt phá hay buông bỏ."
        ),
        "content": (
            "<p>Năm cá nhân (Personal Year) là chu kỳ năng lượng lặp lại theo vòng "
            "từ 1 đến 9, tính từ ngày, tháng sinh kết hợp với năm hiện tại.</p>"
            "<h2>Ý nghĩa từng năm</h2>"
            "<p>Năm 1 – khởi đầu mới. Năm 2 – hợp tác, kiên nhẫn. Năm 3 – sáng tạo, "
            "giao tiếp. Năm 4 – xây dựng nền tảng. Năm 5 – thay đổi, tự do. Năm 6 – "
            "gia đình, trách nhiệm. Năm 7 – nội tâm, học hỏi. Năm 8 – thành tựu, "
            "tài chính. Năm 9 – hoàn tất, buông bỏ.</p>"
            "<p>Biết mình đang ở năm cá nhân nào giúp bạn hành động thuận theo dòng "
            "chảy năng lượng thay vì đi ngược lại nó.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/bg-blog-numberology.png",
    },
    {
        "title": "4 đỉnh cao cuộc đời trong thần số học Pitago",
        "short_content": (
            "4 đỉnh cao chia cuộc đời thành bốn giai đoạn lớn, mỗi giai đoạn mang "
            "một con số và bài học trọng tâm riêng."
        ),
        "content": (
            "<p>4 đỉnh cao (Pinnacles) là bốn giai đoạn lớn của cuộc đời, mỗi giai "
            "đoạn được đại diện bởi một con số và một loại năng lượng riêng.</p>"
            "<h2>Cách phân chia</h2>"
            "<p>Đỉnh cao thứ nhất kéo dài từ khi sinh ra đến khoảng 30-35 tuổi, "
            "tiếp theo là ba đỉnh cao mỗi chặng 9 năm. Mỗi đỉnh cao tiết lộ cơ hội, "
            "thử thách và bài học chính của giai đoạn đó.</p>"
            "<p>Hiểu 4 đỉnh cao giúp bạn chuẩn bị tâm thế và tận dụng đúng thời "
            "điểm để vươn tới thành công.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/cach_tinh_so_chu_dao.png",
    },
    {
        "title": "Số sứ mệnh: Khám phá tài năng và mục tiêu sống của bạn",
        "short_content": (
            "Số sứ mệnh (Destiny/Expression) tính từ toàn bộ họ tên, cho biết tài "
            "năng bẩm sinh và con đường bạn được sinh ra để theo đuổi."
        ),
        "content": (
            "<p>Số sứ mệnh (còn gọi là Số định mệnh hoặc Expression Number) được "
            "tính từ toàn bộ các chữ cái trong họ tên khai sinh.</p>"
            "<h2>Ý nghĩa</h2>"
            "<p>Nếu số chủ đạo cho biết con đường cuộc đời, thì số sứ mệnh tiết lộ "
            "những tài năng và khả năng tự nhiên bạn mang theo để hoàn thành con "
            "đường ấy. Đây chính là 'món quà' bạn được sinh ra để chia sẻ với thế "
            "giới.</p>"
            "<p>Kết hợp số sứ mệnh với số chủ đạo và số linh hồn sẽ giúp bạn định "
            "hướng nghề nghiệp và phát triển bản thân hiệu quả nhất.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/y_nghia_nhung_con_so.png",
    },
    {
        "title": "Thần số học trong tình yêu: Xem độ hợp đôi qua các con số",
        "short_content": (
            "So sánh số chủ đạo và các chỉ số cốt lõi giúp bạn hiểu mức độ hòa hợp "
            "và cách dung hòa khác biệt trong một mối quan hệ."
        ),
        "content": (
            "<p>Thần số học không chỉ giúp hiểu bản thân mà còn là công cụ thú vị "
            "để khám phá độ hợp đôi trong tình yêu, tình bạn và công việc.</p>"
            "<h2>Cách xem độ hợp</h2>"
            "<p>Bằng cách so sánh số chủ đạo của hai người, ta nhận diện những điểm "
            "tương đồng tự nhiên cũng như khác biệt cần dung hòa. Ví dụ số 2 và số "
            "6 thường rất hợp vì cùng coi trọng tình cảm, trong khi số 1 và số 5 "
            "cần học cách tôn trọng sự độc lập của nhau.</p>"
            "<p>Hiểu nhau qua các con số giúp xây dựng mối quan hệ bền vững và sâu "
            "sắc hơn.</p>"
        ),
        "category": 1,
        "image": f"{IMG}/tuoi_doi_than_so_hoc.png",
    },
]


async def main() -> int:
    """Insert missing news articles. Returns count of newly inserted rows."""
    inserted = 0
    async with get_session() as db:
        for n in NEWS:
            result = await db.execute(select(News).where(News.title == n["title"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(News(**n))
                inserted += 1
                print(f"  [INSERT] News: {n['title'][:50]}...")
            else:
                print(f"  [SKIP]   News: {n['title'][:50]}... (exists id={existing.id})")
        await db.commit()
    print(f"  News: {inserted} inserted, {len(NEWS) - inserted} skipped")
    return inserted


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    asyncio.run(main())
