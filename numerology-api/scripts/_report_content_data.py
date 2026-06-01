"""Authored Vietnamese numerology content for report tables (DATA file).

This is a pure-data module (no logic) — it intentionally exceeds 200 lines
because it holds authored prose. Consumed by scripts/seed_report_content.py.

`NUMBER_MEANINGS`: real, accurate Pythagorean numerology meanings keyed by the
number (as str). Each number carries the standard archetype fields used by the
report builder to compose differentiated content per indicator.

`INDICATOR_SPECS`: maps each report indicator (one per DB table) to its model
class name, Vietnamese label, an `intro` framing sentence, and which
NUMBER_MEANINGS field(s) compose the row `content`.
"""

# ---------------------------------------------------------------------------
# Core authored meanings per number (Pythagorean numerology, tiếng Việt)
# ---------------------------------------------------------------------------

NUMBER_MEANINGS: dict[str, dict[str, str]] = {
    "1": {
        "keyword": "Người Lãnh Đạo",
        "overview": (
            "Số 1 mang năng lượng của sự khởi đầu, độc lập và ý chí tiên phong. "
            "Đây là con số của người dẫn đầu, dám nghĩ dám làm và luôn muốn tự "
            "mình mở ra con đường riêng. Bạn có nội lực mạnh mẽ, quyết đoán và "
            "khao khát được công nhận như một cá nhân nổi bật."
        ),
        "desire": (
            "Sâu thẳm bên trong, số 1 khao khát được tự chủ và đứng đầu, được "
            "khẳng định bản thân mà không phụ thuộc vào ai. Bạn mong muốn để lại "
            "dấu ấn cá nhân và được tôn trọng vì năng lực thật sự của mình."
        ),
        "outer": (
            "Bên ngoài, số 1 toát ra phong thái tự tin, mạnh mẽ và có phần cứng "
            "rắn. Người khác thường nhìn bạn như một người dẫn dắt đáng tin cậy, "
            "chủ động và không dễ bị lung lay trước áp lực."
        ),
        "talent": (
            "Tài năng thiên bẩm của số 1 là khả năng khởi xướng, ra quyết định "
            "nhanh và truyền cảm hứng hành động cho người khác. Bạn giỏi biến ý "
            "tưởng thành hiện thực và dẫn dắt một tập thể đi đúng hướng."
        ),
        "action": (
            "Số 1 hành động trực diện, dứt khoát và độc lập. Bạn thích tự mình "
            "bắt tay vào việc thay vì chờ đợi, và luôn tiến về phía trước với sự "
            "kiên định cao."
        ),
        "challenge": (
            "Bài học của số 1 là học cách lắng nghe, hợp tác và bớt độc đoán. "
            "Khi mất cân bằng, bạn dễ trở nên ích kỷ, bảo thủ hoặc nóng vội. "
            "Hãy mềm mại hơn và tin tưởng vào sức mạnh của tập thể."
        ),
        "year": (
            "Đây là giai đoạn của khởi đầu mới, gieo hạt và đặt nền móng. Năng "
            "lượng số 1 thúc đẩy bạn bắt đầu dự án, tự lập và mạnh dạn nắm lấy "
            "cơ hội tiên phong. Hãy chủ động và can đảm bước đi."
        ),
        "advice": (
            "Hãy giữ vững sự độc lập nhưng đừng quên kết nối với người khác. Tự "
            "tin tiến lên nhưng biết lắng nghe, đó là chìa khóa để số 1 tỏa sáng "
            "bền vững."
        ),
        "career": (
            "Số 1 phù hợp với vai trò lãnh đạo, khởi nghiệp, quản lý, kinh doanh "
            "độc lập hoặc bất kỳ lĩnh vực nào cần sự tiên phong và ra quyết định "
            "mạnh mẽ."
        ),
        "love": (
            "Trong tình yêu, số 1 chân thành và bảo vệ người mình yêu, nhưng cần "
            "học cách nhường nhịn và chia sẻ quyền kiểm soát. Một mối quan hệ "
            "bình đẳng sẽ giúp bạn hạnh phúc lâu dài."
        ),
    },
    "2": {
        "keyword": "Người Hòa Giải",
        "overview": (
            "Số 2 mang năng lượng của sự hợp tác, nhạy cảm và cân bằng. Đây là "
            "con số của người kiến tạo hòa bình, tinh tế trong cảm xúc và giỏi "
            "kết nối con người. Bạn coi trọng các mối quan hệ và luôn tìm kiếm "
            "sự hài hòa trong mọi việc."
        ),
        "desire": (
            "Số 2 khao khát yêu thương, sự gắn kết và một môi trường hòa thuận. "
            "Bạn mong muốn được thuộc về, được sẻ chia và sống trong những mối "
            "quan hệ chân thành, ấm áp."
        ),
        "outer": (
            "Bên ngoài, số 2 dịu dàng, lịch thiệp và dễ gần. Người khác cảm thấy "
            "an toàn và được lắng nghe khi ở bên bạn, vì bạn toát ra sự ân cần và "
            "tinh tế."
        ),
        "talent": (
            "Tài năng của số 2 là sự đồng cảm, khả năng làm trung gian hòa giải "
            "và phối hợp nhịp nhàng với người khác. Bạn nhạy bén với cảm xúc và "
            "biết cách dung hòa các quan điểm đối lập."
        ),
        "action": (
            "Số 2 hành động bằng sự kiên nhẫn, khéo léo và hợp tác. Bạn ưu tiên "
            "làm việc cùng người khác, lắng nghe rồi mới quyết định, và luôn chú "
            "ý đến cảm nhận của tập thể."
        ),
        "challenge": (
            "Bài học của số 2 là vượt qua sự nhút nhát và phụ thuộc cảm xúc. Khi "
            "mất cân bằng, bạn dễ tự ti, ngại va chạm hoặc quá nhạy cảm. Hãy học "
            "cách khẳng định bản thân và đặt ranh giới lành mạnh."
        ),
        "year": (
            "Đây là giai đoạn của sự kiên nhẫn, vun đắp quan hệ và chờ thời. Năng "
            "lượng số 2 nhắc bạn hợp tác, lắng nghe và chăm sóc các mối liên kết "
            "thay vì vội vàng. Sự nhẫn nại lúc này sẽ được đền đáp."
        ),
        "advice": (
            "Hãy trân trọng sự nhạy cảm của mình như một món quà, đồng thời học "
            "cách tự tin và độc lập hơn. Biết yêu thương bản thân là nền tảng để "
            "bạn yêu thương người khác trọn vẹn."
        ),
        "career": (
            "Số 2 phù hợp với công việc cần sự phối hợp và tinh tế: ngoại giao, "
            "tư vấn, nhân sự, chăm sóc khách hàng, điều phối, tâm lý hoặc nghệ "
            "thuật hợp tác."
        ),
        "love": (
            "Trong tình yêu, số 2 lãng mạn, tận tụy và giàu sự thấu hiểu. Bạn cần "
            "một người bạn đời biết trân trọng sự dịu dàng của mình, nhưng hãy "
            "tránh đánh mất chính mình vì người kia."
        ),
    },
    "3": {
        "keyword": "Người Sáng Tạo",
        "overview": (
            "Số 3 mang năng lượng của sáng tạo, biểu đạt và niềm vui. Đây là con "
            "số của nghệ sĩ, người giao tiếp và lan tỏa cảm hứng. Bạn lạc quan, "
            "giàu trí tưởng tượng và có sức hút tự nhiên qua lời nói cùng nụ cười."
        ),
        "desire": (
            "Số 3 khao khát được thể hiện bản thân, được sáng tạo và được sống "
            "trong niềm vui. Bạn mong muốn truyền cảm hứng, mang tiếng cười và "
            "vẻ đẹp đến cho cuộc sống xung quanh."
        ),
        "outer": (
            "Bên ngoài, số 3 rạng rỡ, hoạt ngôn và đầy sức sống. Người khác bị "
            "cuốn hút bởi sự vui tươi, dí dỏm và năng lượng tích cực mà bạn lan "
            "tỏa."
        ),
        "talent": (
            "Tài năng của số 3 là khả năng diễn đạt, sáng tạo nghệ thuật và "
            "truyền cảm hứng. Bạn có thiên hướng về ngôn ngữ, hình ảnh, âm nhạc "
            "và mọi hình thức biểu đạt cái đẹp."
        ),
        "action": (
            "Số 3 hành động đầy cảm hứng, linh hoạt và giàu màu sắc. Bạn làm việc "
            "tốt nhất khi được tự do sáng tạo và thể hiện cá tính của mình."
        ),
        "challenge": (
            "Bài học của số 3 là sự tập trung và kỷ luật. Khi mất cân bằng, bạn "
            "dễ phân tán, hời hợt hoặc bỏ dở giữa chừng. Hãy học cách kiên trì "
            "đi đến cùng một mục tiêu."
        ),
        "year": (
            "Đây là giai đoạn của sáng tạo, giao tiếp và mở rộng xã hội. Năng "
            "lượng số 3 mang đến niềm vui, cơ hội thể hiện bản thân và những kết "
            "nối mới. Hãy mạnh dạn sáng tạo và tận hưởng cuộc sống."
        ),
        "advice": (
            "Hãy nuôi dưỡng tài năng sáng tạo nhưng đừng để cảm xúc cuốn đi quá "
            "xa. Kết hợp niềm vui với sự kiên định, bạn sẽ biến mọi ý tưởng thành "
            "tác phẩm thật sự."
        ),
        "career": (
            "Số 3 phù hợp với nghệ thuật, viết lách, truyền thông, marketing, "
            "biểu diễn, thiết kế hay bất kỳ lĩnh vực nào tôn vinh sự sáng tạo và "
            "giao tiếp."
        ),
        "love": (
            "Trong tình yêu, số 3 lãng mạn, vui vẻ và đầy bất ngờ. Bạn cần một "
            "người biết trân trọng sự tự do và cá tính nghệ sĩ của mình, đồng thời "
            "cùng bạn chia sẻ tiếng cười."
        ),
    },
    "4": {
        "keyword": "Người Kiến Tạo",
        "overview": (
            "Số 4 mang năng lượng của sự ổn định, kỷ luật và xây dựng. Đây là con "
            "số của người thực tế, đáng tin cậy và bền bỉ. Bạn coi trọng nền tảng "
            "vững chắc, làm việc có hệ thống và luôn hoàn thành điều mình cam kết."
        ),
        "desire": (
            "Số 4 khao khát sự an toàn, trật tự và những thành quả lâu bền. Bạn "
            "mong muốn xây dựng một cuộc sống ổn định, có cấu trúc rõ ràng và "
            "được làm việc một cách thực chất."
        ),
        "outer": (
            "Bên ngoài, số 4 nghiêm túc, đáng tin và chừng mực. Người khác xem "
            "bạn như một chỗ dựa vững chắc, một người làm việc cẩn thận và giữ "
            "lời hứa."
        ),
        "talent": (
            "Tài năng của số 4 là khả năng tổ chức, lập kế hoạch và thực thi tỉ "
            "mỉ. Bạn giỏi biến một ý tưởng thành quy trình cụ thể và kiên trì xây "
            "dựng từng bước cho đến khi vững chắc."
        ),
        "action": (
            "Số 4 hành động bài bản, kiên trì và có phương pháp. Bạn tiến từng "
            "bước chắc chắn, chú trọng chi tiết và không bỏ qua nền tảng."
        ),
        "challenge": (
            "Bài học của số 4 là sự linh hoạt và cởi mở. Khi mất cân bằng, bạn "
            "dễ cứng nhắc, bảo thủ hoặc quá khắt khe. Hãy học cách thích nghi và "
            "chấp nhận những điều chưa hoàn hảo."
        ),
        "year": (
            "Đây là giai đoạn của xây dựng, lao động chăm chỉ và củng cố nền "
            "tảng. Năng lượng số 4 đòi hỏi sự kỷ luật và bền bỉ; thành quả đến từ "
            "nỗ lực thực chất chứ không phải may mắn."
        ),
        "advice": (
            "Hãy giữ kỷ luật và sự bền bỉ làm thế mạnh, nhưng đừng quên thư giãn "
            "và đón nhận cái mới. Một chút linh hoạt sẽ giúp nền móng bạn xây nên "
            "trở nên sống động hơn."
        ),
        "career": (
            "Số 4 phù hợp với kỹ thuật, kế toán, quản lý dự án, xây dựng, công "
            "nghệ, luật hay bất kỳ lĩnh vực nào đề cao sự chính xác và bền vững."
        ),
        "love": (
            "Trong tình yêu, số 4 chung thủy, đáng tin và trách nhiệm. Bạn thể "
            "hiện tình cảm qua hành động cụ thể hơn lời nói, và cần một mối quan "
            "hệ ổn định, đáng tin cậy."
        ),
    },
    "5": {
        "keyword": "Người Tự Do",
        "overview": (
            "Số 5 mang năng lượng của tự do, thay đổi và phiêu lưu. Đây là con số "
            "của người ưa khám phá, linh hoạt và tràn đầy sức sống. Bạn yêu sự đa "
            "dạng, ghét gò bó và luôn khao khát trải nghiệm những điều mới mẻ."
        ),
        "desire": (
            "Số 5 khao khát tự do và trải nghiệm. Bạn mong muốn được khám phá thế "
            "giới, được thử thách giới hạn của bản thân và sống một cuộc đời "
            "không bị ràng buộc."
        ),
        "outer": (
            "Bên ngoài, số 5 năng động, cuốn hút và đầy sức sống. Người khác thấy "
            "bạn linh hoạt, hiện đại và luôn mang đến luồng gió mới cho mọi tình "
            "huống."
        ),
        "talent": (
            "Tài năng của số 5 là khả năng thích nghi, giao tiếp đa dạng và nắm "
            "bắt cơ hội nhanh nhạy. Bạn học hỏi nhanh, xoay xở giỏi và dễ dàng "
            "kết nối với nhiều kiểu người."
        ),
        "action": (
            "Số 5 hành động linh hoạt, nhanh nhạy và phóng khoáng. Bạn thích thử "
            "nhiều hướng đi, thích nghi tức thì và không ngại thay đổi kế hoạch."
        ),
        "challenge": (
            "Bài học của số 5 là sự kiên định và trách nhiệm. Khi mất cân bằng, "
            "bạn dễ bốc đồng, sa đà vào cám dỗ hoặc thiếu cam kết. Hãy học cách "
            "tự do trong khuôn khổ và đi đến cùng điều mình bắt đầu."
        ),
        "year": (
            "Đây là giai đoạn của thay đổi, tự do và cơ hội bất ngờ. Năng lượng "
            "số 5 mang đến những bước ngoặt, chuyến đi và trải nghiệm mới. Hãy "
            "linh hoạt nắm bắt nhưng giữ cho mình một điểm tựa vững vàng."
        ),
        "advice": (
            "Hãy tận hưởng tự do nhưng đừng để nó biến thành sự bất ổn. Biết cam "
            "kết và kỷ luật bản thân sẽ giúp năng lượng phiêu lưu của bạn tạo ra "
            "thành quả thực sự."
        ),
        "career": (
            "Số 5 phù hợp với kinh doanh, du lịch, truyền thông, bán hàng, "
            "marketing, báo chí hay bất kỳ công việc nào năng động, đa dạng và "
            "nhiều di chuyển."
        ),
        "love": (
            "Trong tình yêu, số 5 nồng nhiệt, thú vị nhưng cần không gian riêng. "
            "Bạn cần một người bạn đời tôn trọng sự tự do và cùng bạn khám phá "
            "cuộc sống, tránh sự ràng buộc ngột ngạt."
        ),
    },
    "6": {
        "keyword": "Người Chăm Sóc",
        "overview": (
            "Số 6 mang năng lượng của tình yêu thương, trách nhiệm và sự chăm "
            "sóc. Đây là con số của người nuôi dưỡng, tận tụy với gia đình và "
            "cộng đồng. Bạn giàu lòng trắc ẩn, coi trọng sự hài hòa và luôn muốn "
            "che chở cho người thân yêu."
        ),
        "desire": (
            "Số 6 khao khát yêu thương và được yêu thương, khao khát một gia đình "
            "ấm áp và sự hài hòa. Bạn mong muốn được chăm lo cho người khác và "
            "tạo ra một mái ấm an toàn."
        ),
        "outer": (
            "Bên ngoài, số 6 ấm áp, đáng tin và giàu trách nhiệm. Người khác cảm "
            "thấy được quan tâm, chở che khi ở bên bạn, vì bạn toát ra sự bao "
            "dung và tận tâm."
        ),
        "talent": (
            "Tài năng của số 6 là khả năng chăm sóc, dạy dỗ và mang lại sự cân "
            "bằng cho người xung quanh. Bạn có gu thẩm mỹ, biết tạo dựng môi "
            "trường ấm cúng và giải quyết mâu thuẫn bằng tình yêu thương."
        ),
        "action": (
            "Số 6 hành động vì người khác, tận tụy và có trách nhiệm. Bạn sẵn "
            "sàng gánh vác, chăm lo và đặt lợi ích của gia đình, tập thể lên hàng "
            "đầu."
        ),
        "challenge": (
            "Bài học của số 6 là cân bằng giữa cho đi và nhận lại. Khi mất cân "
            "bằng, bạn dễ ôm đồm, kiểm soát hoặc hy sinh quá mức. Hãy học cách "
            "chăm sóc bản thân và để người khác tự lập."
        ),
        "year": (
            "Đây là giai đoạn của gia đình, trách nhiệm và tình yêu thương. Năng "
            "lượng số 6 hướng bạn về tổ ấm, các mối quan hệ thân thiết và những "
            "cam kết quan trọng. Hãy chăm sóc nhưng đừng quên chính mình."
        ),
        "advice": (
            "Hãy yêu thương và chăm sóc bằng cả trái tim, nhưng nhớ giữ lại phần "
            "cho bản thân. Sự cân bằng giữa cho và nhận là chìa khóa hạnh phúc "
            "của số 6."
        ),
        "career": (
            "Số 6 phù hợp với giáo dục, y tế, tư vấn, chăm sóc sức khỏe, dịch vụ, "
            "thiết kế nội thất hay bất kỳ lĩnh vực nào liên quan đến chăm sóc và "
            "tạo dựng sự hài hòa."
        ),
        "love": (
            "Trong tình yêu, số 6 tận tụy, ấm áp và sẵn sàng hy sinh. Bạn là "
            "người bạn đời lý tưởng, nhưng cần tránh kiểm soát hay yêu thương đến "
            "mức quên mình."
        ),
    },
    "7": {
        "keyword": "Người Tìm Kiếm",
        "overview": (
            "Số 7 mang năng lượng của trí tuệ, chiều sâu và tâm linh. Đây là con "
            "số của nhà tư tưởng, người tìm kiếm chân lý và sự thật ẩn giấu. Bạn "
            "thích quan sát, phân tích và đào sâu vào bản chất của mọi điều."
        ),
        "desire": (
            "Số 7 khao khát hiểu biết, sự thật và bình an nội tâm. Bạn mong muốn "
            "được khám phá những điều sâu xa, được sống đúng với chân lý mình tin "
            "và có không gian riêng để suy ngẫm."
        ),
        "outer": (
            "Bên ngoài, số 7 trầm tĩnh, bí ẩn và sâu sắc. Người khác cảm nhận ở "
            "bạn một sự uyên bác, điềm đạm và đôi khi hơi xa cách, khó đoán."
        ),
        "talent": (
            "Tài năng của số 7 là tư duy phân tích, trực giác sắc bén và khả năng "
            "nghiên cứu chuyên sâu. Bạn nhìn thấy điều người khác bỏ lỡ và giỏi "
            "tìm ra quy luật ẩn sau hiện tượng."
        ),
        "action": (
            "Số 7 hành động sau khi suy ngẫm kỹ lưỡng, độc lập và có chiều sâu. "
            "Bạn cần thời gian một mình để phân tích trước khi đưa ra quyết định."
        ),
        "challenge": (
            "Bài học của số 7 là kết nối và tin tưởng. Khi mất cân bằng, bạn dễ "
            "thu mình, hoài nghi hoặc cô lập. Hãy học cách mở lòng, chia sẻ và "
            "tin vào người khác."
        ),
        "year": (
            "Đây là giai đoạn của nội tâm, học hỏi và phát triển tinh thần. Năng "
            "lượng số 7 mời bạn lùi lại, suy ngẫm và đào sâu hiểu biết thay vì "
            "vội vã hành động. Hãy lắng nghe trực giác của mình."
        ),
        "advice": (
            "Hãy nuôi dưỡng trí tuệ và đời sống tinh thần, nhưng đừng để mình quá "
            "cô lập. Mở lòng với người khác sẽ giúp chiều sâu của bạn trở nên ấm "
            "áp và trọn vẹn."
        ),
        "career": (
            "Số 7 phù hợp với nghiên cứu, khoa học, phân tích, công nghệ, tâm "
            "linh, triết học hay bất kỳ lĩnh vực nào cần tư duy sâu và sự độc lập."
        ),
        "love": (
            "Trong tình yêu, số 7 sâu sắc, chung thủy nhưng cần khoảng riêng. Bạn "
            "cần một người bạn đời tinh tế, tôn trọng không gian nội tâm và đủ "
            "kiên nhẫn để thấu hiểu bạn."
        ),
    },
    "8": {
        "keyword": "Người Quyền Lực",
        "overview": (
            "Số 8 mang năng lượng của quyền lực, tham vọng và thành tựu vật chất. "
            "Đây là con số của nhà điều hành, người làm chủ tài chính và quyền "
            "lực. Bạn có khát vọng lớn, tư duy chiến lược và khả năng biến mục "
            "tiêu thành kết quả cụ thể."
        ),
        "desire": (
            "Số 8 khao khát thành công, sự thịnh vượng và quyền tự chủ về tài "
            "chính. Bạn mong muốn đạt được vị thế, làm chủ cuộc đời mình và để "
            "lại di sản đáng kể."
        ),
        "outer": (
            "Bên ngoài, số 8 mạnh mẽ, uy quyền và đầy bản lĩnh. Người khác nhìn "
            "bạn như một người có năng lực lãnh đạo, quyết đoán và có tầm ảnh "
            "hưởng."
        ),
        "talent": (
            "Tài năng của số 8 là khả năng quản lý, tổ chức quy mô lớn và nhạy "
            "bén với tiền bạc, quyền lực. Bạn giỏi nhìn bức tranh tổng thể và đưa "
            "ra quyết định chiến lược mang lại hiệu quả cao."
        ),
        "action": (
            "Số 8 hành động mạnh mẽ, có chiến lược và hướng đến kết quả. Bạn dám "
            "đặt mục tiêu lớn và kiên quyết theo đuổi đến cùng để đạt được."
        ),
        "challenge": (
            "Bài học của số 8 là cân bằng giữa vật chất và tinh thần. Khi mất cân "
            "bằng, bạn dễ tham vọng quá mức, độc đoán hoặc xem trọng tiền bạc hơn "
            "tình cảm. Hãy dùng quyền lực một cách công bằng và bao dung."
        ),
        "year": (
            "Đây là giai đoạn của thành tựu, quyền lực và gặt hái về vật chất. "
            "Năng lượng số 8 thúc đẩy bạn vươn tới mục tiêu lớn, mở rộng sự nghiệp "
            "và tài chính. Hãy hành động bản lĩnh nhưng giữ sự liêm chính."
        ),
        "advice": (
            "Hãy theo đuổi thành công với bản lĩnh, nhưng đừng đánh đổi các giá "
            "trị tinh thần. Quyền lực thực sự đến từ sự cân bằng giữa thành tựu "
            "và lòng nhân ái."
        ),
        "career": (
            "Số 8 phù hợp với kinh doanh, tài chính, đầu tư, quản trị doanh "
            "nghiệp, bất động sản hay bất kỳ lĩnh vực nào cần tầm nhìn chiến lược "
            "và khả năng làm chủ nguồn lực."
        ),
        "love": (
            "Trong tình yêu, số 8 mạnh mẽ, che chở và đáng tin về vật chất. Bạn "
            "cần học cách thể hiện sự mềm mại, dành thời gian cho người mình yêu "
            "thay vì chỉ tập trung vào sự nghiệp."
        ),
    },
    "9": {
        "keyword": "Người Nhân Ái",
        "overview": (
            "Số 9 mang năng lượng của lòng nhân ái, sự bao dung và lý tưởng cao "
            "cả. Đây là con số của người phụng sự, giàu tình thương với nhân loại "
            "và sống vì những giá trị lớn lao. Bạn có tâm hồn rộng mở, vị tha và "
            "khao khát làm cho thế giới tốt đẹp hơn."
        ),
        "desire": (
            "Số 9 khao khát được cống hiến, được yêu thương và phụng sự cho điều "
            "lớn lao hơn bản thân. Bạn mong muốn chữa lành, giúp đỡ và để lại "
            "những giá trị ý nghĩa cho cộng đồng."
        ),
        "outer": (
            "Bên ngoài, số 9 nhân hậu, cao thượng và cuốn hút. Người khác cảm "
            "nhận ở bạn sự bao dung, độ lượng và một tầm nhìn vượt lên những lợi "
            "ích nhỏ nhặt."
        ),
        "talent": (
            "Tài năng của số 9 là khả năng thấu cảm, truyền cảm hứng và lan tỏa "
            "lòng nhân ái. Bạn giỏi nhìn nhận con người bằng sự bao dung và dẫn "
            "dắt người khác hướng đến những giá trị tốt đẹp."
        ),
        "action": (
            "Số 9 hành động vì lý tưởng, vị tha và bao quát. Bạn đặt lợi ích "
            "chung lên trên, sẵn sàng buông bỏ cái tôi để phụng sự điều lớn lao."
        ),
        "challenge": (
            "Bài học của số 9 là học cách buông bỏ và thiết lập ranh giới. Khi "
            "mất cân bằng, bạn dễ ôm nỗi đau của người khác, lý tưởng hóa quá mức "
            "hoặc khó dứt khỏi quá khứ. Hãy học cách cho đi mà không kiệt sức."
        ),
        "year": (
            "Đây là giai đoạn của hoàn tất, buông bỏ và khép lại một chu kỳ. Năng "
            "lượng số 9 mời bạn dọn dẹp những gì không còn phù hợp, tha thứ và "
            "chuẩn bị cho khởi đầu mới. Hãy cho đi và bao dung."
        ),
        "advice": (
            "Hãy sống vì lý tưởng và lòng nhân ái, nhưng nhớ chăm sóc cho chính "
            "mình. Biết buông bỏ đúng lúc sẽ giúp bạn cống hiến bền lâu mà không "
            "kiệt sức."
        ),
        "career": (
            "Số 9 phù hợp với hoạt động xã hội, giáo dục, nghệ thuật, y tế, tư "
            "vấn, từ thiện hay bất kỳ lĩnh vực nào phụng sự con người và lan tỏa "
            "giá trị nhân văn."
        ),
        "love": (
            "Trong tình yêu, số 9 vị tha, lãng mạn và giàu lý tưởng. Bạn yêu sâu "
            "sắc và bao dung, nhưng cần học cách sống thực tế và không lý tưởng "
            "hóa người bạn đời quá mức."
        ),
    },
    "11": {
        "keyword": "Bậc Thầy Trực Giác",
        "overview": (
            "Số 11 là số bậc thầy, mang năng lượng được nâng cao của số 2 với "
            "trực giác và sự nhạy cảm tâm linh phi thường. Đây là con số của "
            "người truyền cảm hứng, có khả năng soi sáng và dẫn dắt tinh thần cho "
            "người khác. Bạn vừa nhạy bén, vừa lý tưởng, mang sứ mệnh thức tỉnh."
        ),
        "desire": (
            "Số 11 khao khát soi sáng, truyền cảm hứng và kết nối với những giá "
            "trị tinh thần cao cả. Bạn mong muốn nâng đỡ tâm hồn người khác và "
            "sống đúng với sứ mệnh thức tỉnh của mình."
        ),
        "outer": (
            "Bên ngoài, số 11 cuốn hút, nhạy cảm và toát ra một nguồn năng lượng "
            "đặc biệt. Người khác cảm nhận ở bạn sự tinh tế, trực giác mạnh và "
            "một sức hút khó lý giải."
        ),
        "talent": (
            "Tài năng của số 11 là trực giác siêu nhạy, khả năng truyền cảm hứng "
            "và nhìn thấu bản chất con người. Bạn có thể soi sáng, dẫn dắt và "
            "đánh thức tiềm năng tinh thần của người khác."
        ),
        "action": (
            "Số 11 hành động theo trực giác và lý tưởng, vừa nhạy cảm vừa đầy cảm "
            "hứng. Bạn dẫn dắt bằng tấm gương và nguồn năng lượng tinh thần hơn "
            "là bằng mệnh lệnh."
        ),
        "challenge": (
            "Bài học của số 11 là làm chủ năng lượng cao và sự nhạy cảm của mình. "
            "Khi mất cân bằng, bạn dễ lo âu, căng thẳng hoặc dao động cảm xúc. "
            "Hãy học cách tiếp đất, giữ vững nội tâm và biến trực giác thành hành "
            "động thực tế."
        ),
        "year": (
            "Đây là giai đoạn của thức tỉnh tinh thần, trực giác và cảm hứng. "
            "Năng lượng số 11 nâng cao độ nhạy cảm và khả năng kết nối tâm linh, "
            "mời bạn lắng nghe nội tâm và truyền cảm hứng cho người khác."
        ),
        "advice": (
            "Hãy tin vào trực giác và sứ mệnh truyền cảm hứng của mình, đồng thời "
            "giữ cho tâm trí cân bằng, vững vàng. Biến năng lượng cao thành hành "
            "động cụ thể sẽ giúp bạn tỏa sáng đúng nghĩa."
        ),
        "career": (
            "Số 11 phù hợp với giảng dạy, diễn thuyết truyền cảm hứng, tâm linh, "
            "nghệ thuật, tư vấn, chữa lành hay bất kỳ lĩnh vực nào nâng đỡ tinh "
            "thần con người."
        ),
        "love": (
            "Trong tình yêu, số 11 sâu sắc, lãng mạn và giàu trực giác. Bạn cần "
            "một người bạn đời thấu hiểu sự nhạy cảm và lý tưởng tinh thần của "
            "mình, cùng bạn nuôi dưỡng một mối quan hệ sâu sắc."
        ),
    },
    "22": {
        "keyword": "Bậc Thầy Kiến Tạo",
        "overview": (
            "Số 22 là số bậc thầy quyền năng nhất, mang năng lượng được nâng cao "
            "của số 4 kết hợp tầm nhìn lớn lao. Đây là con số của người kiến tạo "
            "vĩ đại, có khả năng biến những giấc mơ lớn thành hiện thực mang tầm "
            "ảnh hưởng rộng. Bạn vừa thực tế vừa giàu lý tưởng."
        ),
        "desire": (
            "Số 22 khao khát xây dựng những điều lớn lao, để lại di sản bền vững "
            "cho thế giới. Bạn mong muốn hiện thực hóa tầm nhìn vĩ đại của mình "
            "và tạo ra giá trị có ích cho cộng đồng rộng lớn."
        ),
        "outer": (
            "Bên ngoài, số 22 vững vàng, có tầm vóc và đáng tin cậy. Người khác "
            "cảm nhận ở bạn sự kết hợp hiếm có giữa tầm nhìn lớn và khả năng thực "
            "thi thực tế."
        ),
        "talent": (
            "Tài năng của số 22 là khả năng biến tầm nhìn lớn thành công trình cụ "
            "thể, tổ chức nguồn lực quy mô và lãnh đạo những dự án có tầm ảnh "
            "hưởng. Bạn vừa mơ lớn vừa biết cách xây từng viên gạch."
        ),
        "action": (
            "Số 22 hành động có tầm nhìn chiến lược, kỷ luật và bền bỉ. Bạn theo "
            "đuổi mục tiêu lớn bằng kế hoạch bài bản và sự kiên định phi thường."
        ),
        "challenge": (
            "Bài học của số 22 là tin vào tầm vóc của mình và không bị áp lực đè "
            "nặng. Khi mất cân bằng, bạn dễ tự nghi ngờ, ôm đồm hoặc bị choáng "
            "ngợp bởi trách nhiệm lớn. Hãy bước từng bước và tin vào sứ mệnh."
        ),
        "year": (
            "Đây là giai đoạn của kiến tạo lớn, hiện thực hóa tầm nhìn và xây "
            "dựng di sản. Năng lượng số 22 mang đến cơ hội thực hiện những dự án "
            "tầm vóc, đòi hỏi cả lý tưởng lẫn sự bền bỉ thực tế."
        ),
        "advice": (
            "Hãy dám mơ lớn và kiên trì biến giấc mơ thành hiện thực từng bước "
            "một. Tin vào tầm vóc của mình nhưng giữ đôi chân trên mặt đất, đó là "
            "sức mạnh của số 22."
        ),
        "career": (
            "Số 22 phù hợp với lãnh đạo doanh nghiệp lớn, kiến trúc, quy hoạch, "
            "công trình tầm cỡ, tổ chức xã hội hay bất kỳ lĩnh vực nào cần biến "
            "tầm nhìn lớn thành hiện thực."
        ),
        "love": (
            "Trong tình yêu, số 22 vững vàng, tận tâm và đáng tin cậy. Bạn cần "
            "một người bạn đời đồng hành với tầm nhìn lớn của mình, đồng thời "
            "giúp bạn cân bằng giữa sự nghiệp và đời sống tình cảm."
        ),
    },
    "33": {
        "keyword": "Bậc Thầy Yêu Thương",
        "overview": (
            "Số 33 là số bậc thầy của tình yêu thương vô điều kiện, mang năng "
            "lượng được nâng cao của số 6 kết hợp lý tưởng phụng sự cao cả. Đây "
            "là con số của người thầy tâm linh, người chữa lành và lan tỏa lòng "
            "từ bi đến với nhân loại. Bạn sống vì sự an lành của người khác."
        ),
        "desire": (
            "Số 33 khao khát yêu thương vô điều kiện, chữa lành và nâng đỡ nhân "
            "loại. Bạn mong muốn cống hiến trọn vẹn cho hạnh phúc của người khác "
            "và lan tỏa lòng từ bi đến mọi nơi."
        ),
        "outer": (
            "Bên ngoài, số 33 ấm áp, bao dung và toát ra một tình yêu thương sâu "
            "rộng. Người khác cảm thấy được chữa lành, được nâng đỡ và an yên khi "
            "ở bên bạn."
        ),
        "talent": (
            "Tài năng của số 33 là khả năng yêu thương, chữa lành và truyền cảm "
            "hứng bằng tấm gương phụng sự. Bạn có thể nâng đỡ tinh thần của cả "
            "một cộng đồng bằng lòng từ bi và sự thấu hiểu sâu sắc."
        ),
        "action": (
            "Số 33 hành động bằng tình yêu thương, sự tận tụy và lý tưởng phụng "
            "sự. Bạn đặt hạnh phúc của người khác làm trọng tâm và dẫn dắt bằng "
            "lòng từ bi."
        ),
        "challenge": (
            "Bài học của số 33 là yêu thương mà không hy sinh chính mình đến kiệt "
            "sức. Khi mất cân bằng, bạn dễ gánh quá nhiều trách nhiệm hoặc mang "
            "gánh nặng của cả thế giới. Hãy học cách chăm sóc bản thân để cho đi "
            "bền lâu."
        ),
        "year": (
            "Đây là giai đoạn của tình yêu thương, chữa lành và phụng sự cao cả. "
            "Năng lượng số 33 nâng cao lòng từ bi và trách nhiệm với cộng đồng, "
            "mời bạn lan tỏa yêu thương và nâng đỡ những người xung quanh."
        ),
        "advice": (
            "Hãy lan tỏa tình yêu thương và phụng sự bằng cả trái tim, nhưng nhớ "
            "rằng bạn cũng cần được yêu thương. Chăm sóc bản thân là cách để bạn "
            "tiếp tục chữa lành cho người khác."
        ),
        "career": (
            "Số 33 phù hợp với giảng dạy, chữa lành, tư vấn tâm lý, hoạt động xã "
            "hội, y tế, tâm linh hay bất kỳ lĩnh vực nào nâng đỡ và chữa lành con "
            "người."
        ),
        "love": (
            "Trong tình yêu, số 33 bao dung, ấm áp và yêu thương vô điều kiện. "
            "Bạn cần một người bạn đời trân trọng tấm lòng rộng lớn của mình và "
            "nhắc bạn cũng được chăm sóc, yêu thương."
        ),
    },
}

# Generic intro paragraph for LifePeak code "1000" (no specific number).
LIFE_PEAK_INTRO = (
    "<p><strong>Các đỉnh cao cuộc đời</strong> (kim tự tháp đỉnh cao) là bốn "
    "giai đoạn lớn đánh dấu những bước ngoặt và cơ hội phát triển trong hành "
    "trình của bạn. Mỗi đỉnh cao mang một con số chủ đề riêng, hé lộ bài học, "
    "năng lượng và thời cơ nổi bật của giai đoạn đó.</p>"
    "<p>Đỉnh cao thứ nhất kéo dài từ thời thơ ấu đến khoảng giữa độ tuổi 30, là "
    "giai đoạn khám phá và định hình bản thân. Ba đỉnh cao tiếp theo, mỗi đỉnh "
    "kéo dài chín năm rồi đỉnh cuối cùng kéo dài đến hết đời, lần lượt mở ra "
    "những chủ đề trưởng thành, gặt hái và viên mãn. Hiểu các đỉnh cao giúp bạn "
    "sống thuận theo dòng chảy năng lượng của từng chặng đường.</p>"
)

# Special PersonalYearNumber meanings for codes 10 and 11.
PERSONAL_YEAR_SPECIAL = {
    "10": (
        "Đây là giai đoạn viên mãn cuối chu kỳ, khi mọi nỗ lực được kết tinh và "
        "gặt hái. Năng lượng số 10 (1+0=1) khép lại một vòng tròn chín năm và "
        "đồng thời mở ra hạt giống cho khởi đầu mới. Hãy tận hưởng thành quả, "
        "tổng kết bài học và chuẩn bị tinh thần cho một chu kỳ tiếp theo."
    ),
    "11": (
        "Đây là giai đoạn đầu đời học hỏi, mang năng lượng bậc thầy của trực "
        "giác và nhạy cảm. Năm cá nhân 11 đánh thức tiềm năng tinh thần, khơi "
        "dậy cảm hứng và những bài học sâu sắc về bản thân. Hãy lắng nghe trực "
        "giác, mở lòng học hỏi và tin vào những tín hiệu nội tâm của mình."
    ),
}


# ---------------------------------------------------------------------------
# Indicator specifications — one entry per report DB table.
# Each: model (class name), label (Vietnamese), intro (framing sentence),
# fields (list of NUMBER_MEANINGS keys composed into `content`).
# Master-number sets use _MASTER codes; basic sets use _BASIC codes.
# ---------------------------------------------------------------------------

_MASTER = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "11", "22", "33"]
_BASIC = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

INDICATOR_SPECS: dict[str, dict] = {
    "MainNumber": {
        "model": "MainNumber",
        "label": "Số Chủ Đạo",
        "codes": _MASTER,
        "intro": "Số Chủ Đạo (Đường Đời) là con số quan trọng nhất, tiết lộ con đường cốt lõi và sứ mệnh cả đời của bạn.",
        "fields": ["overview", "advice"],
    },
    "MissionNumber": {
        "model": "MissionNumber",
        "label": "Số Sứ Mệnh",
        "codes": _MASTER,
        "intro": "Số Sứ Mệnh cho biết mục tiêu lớn và sứ mệnh bạn cần hoàn thành trong cuộc đời này.",
        "fields": ["overview"],
    },
    "SoulsNumber": {
        "model": "SoulsNumber",
        "label": "Số Linh Hồn",
        "codes": _MASTER,
        "intro": "Số Linh Hồn hé lộ khát khao sâu thẳm bên trong, điều thật sự thúc đẩy trái tim bạn.",
        "fields": ["desire"],
    },
    "MatureNumber": {
        "model": "MatureNumber",
        "label": "Số Nhân Cách",
        "codes": _MASTER,
        "intro": "Số Nhân Cách phản ánh hình ảnh bên ngoài và ấn tượng bạn để lại trong mắt người khác.",
        "fields": ["outer"],
    },
    "AttitudeNumber": {
        "model": "AttitudeNumber",
        "label": "Số Thái Độ",
        "codes": _MASTER,
        "intro": "Số Thái Độ thể hiện ấn tượng đầu tiên và cách bạn phản ứng tự nhiên trước cuộc sống.",
        "fields": ["outer"],
    },
    "BalanceNumber": {
        "model": "BalanceNumber",
        "label": "Số Cân Bằng",
        "codes": _MASTER,
        "intro": "Số Cân Bằng chỉ ra cách bạn nên hành xử để lấy lại sự ổn định khi rơi vào căng thẳng hay khủng hoảng.",
        "fields": ["advice"],
    },
    "DevelopmentNumber": {
        "model": "DevelopmentNumber",
        "label": "Số Trưởng Thành",
        "codes": _BASIC,
        "intro": "Số Trưởng Thành cho biết mục tiêu và phiên bản tốt nhất bạn hướng tới trong nửa sau cuộc đời.",
        "fields": ["overview"],
    },
    "BirthdayNumber": {
        "model": "BirthdayNumber",
        "label": "Số Ngày Sinh",
        "codes": _BASIC,
        "intro": "Số Ngày Sinh tiết lộ một tài năng thiên bẩm đặc biệt mà bạn mang theo từ khi chào đời.",
        "fields": ["talent"],
    },
    "ExecutionNumber": {
        "model": "ExecutionNumber",
        "label": "Số Thực Thi",
        "codes": _BASIC,
        "intro": "Số Thực Thi cho biết cách bạn bắt tay vào hành động và biến ý tưởng thành kết quả.",
        "fields": ["action"],
    },
    "KarmicNumber": {
        "model": "KarmicNumber",
        "label": "Số Nội Cảm",
        "codes": _BASIC,
        "intro": "Số Nội Cảm phản ánh nét tính cách nội tâm chủ đạo chi phối thế giới bên trong bạn.",
        "fields": ["overview"],
    },
    "PersonalMonthNumber": {
        "model": "PersonalMonthNumber",
        "label": "Số Tháng Cá Nhân",
        "codes": _BASIC,
        "intro": "Số Tháng Cá Nhân cho biết chủ đề năng lượng nổi bật của bạn trong tháng này.",
        "fields": ["year"],
    },
    "MissNumber": {
        "model": "MissNumber",
        "label": "Số Thiếu",
        "codes": _BASIC,
        "intro": "Số Thiếu là con số vắng mặt trong biểu đồ ngày sinh, chỉ ra bài học và phẩm chất bạn cần rèn luyện.",
        "fields": ["challenge"],
    },
    "ChallengeLife": {
        "model": "ChallengeLife",
        "label": "Số Thử Thách",
        "codes": _BASIC,
        "intro": "Số Thử Thách cho biết những khó khăn và bài học bạn cần vượt qua để trưởng thành.",
        "fields": ["challenge"],
    },
    "PersonalYearNumber": {
        "model": "PersonalYearNumber",
        "label": "Số Năm Cá Nhân",
        "codes": _BASIC + ["10", "11"],
        "intro": "Số Năm Cá Nhân cho biết chủ đề năng lượng chủ đạo của bạn trong năm nay.",
        "fields": ["year"],
    },
    "LifePeak": {
        "model": "LifePeak",
        "label": "Đỉnh Cao Cuộc Đời",
        "codes": _MASTER + ["1000"],
        "intro": "Đỉnh Cao Cuộc Đời cho biết chủ đề, cơ hội và năng lượng nổi bật của giai đoạn này trong hành trình của bạn.",
        "fields": ["year", "overview"],
    },
}
