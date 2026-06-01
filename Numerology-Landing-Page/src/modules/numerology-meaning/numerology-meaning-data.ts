/**
 * Static numerology meaning content for core numbers.
 * Covers 1–9 plus master numbers 11, 22, 33 (Pythagorean system).
 *
 * Used by the home "Ý nghĩa các con số" explorer and the
 * /y-nghia-con-so/[so] detail pages. Content is FE-owned (no backend call).
 */

export interface MeaningSection {
  heading: string
  body: string
}

export interface NumberMeaning {
  /** Numeric value: 1..9, 11, 22, 33 */
  number: number
  /** URL slug == number as string */
  slug: string
  /** Archetype name shown as the headline */
  title: string
  /** Short keyword/tagline */
  keyword: string
  /** Public image path */
  image: string
  /** 2–3 sentence summary for the right-hand panel */
  summary: string
  /** Rich detail sections for the dedicated page */
  sections: MeaningSection[]
}

const img = (n: number) => `/assets/images/numbers/${n}.png`

export const NUMBER_MEANINGS: NumberMeaning[] = [
  {
    number: 1,
    slug: '1',
    title: 'Người Lãnh Đạo',
    keyword: 'Độc lập · Tiên phong · Khởi tạo',
    image: img(1),
    summary:
      'Số 1 là hiện thân của sự táo bạo, đổi mới và tinh thần tiên phong. Người mang số 1 có ý chí mạnh mẽ, khao khát độc lập và năng lực dẫn dắt bẩm sinh để mở ra những con đường mới.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 1 đại diện cho khởi đầu, ý chí và bản lĩnh tự thân. Đây là năng lượng của người dám đi đầu, tự đặt ra mục tiêu và theo đuổi đến cùng. Mục đích sống của người số 1 là phát triển sự độc lập, tự tin và mang đến nguồn năng lượng sáng tạo tích cực cho thế giới.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Quyết đoán, sáng tạo, giàu tham vọng và khả năng tự lực cao. Người số 1 dễ trở thành đầu tàu, biết biến ý tưởng thành hành động và truyền cảm hứng cho người khác bằng sự kiên định.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Cái tôi lớn dễ dẫn đến bướng bỉnh, độc đoán hoặc nóng vội. Số 1 cần học cách lắng nghe, hợp tác và chấp nhận rằng không phải lúc nào mình cũng đúng.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với vai trò lãnh đạo, khởi nghiệp, công việc đòi hỏi sáng kiến và sự tự chủ. Trong tình yêu, người số 1 chân thành và che chở nhưng cần tiết chế sự áp đặt để giữ sự cân bằng cho mối quan hệ.',
      },
    ],
  },
  {
    number: 2,
    slug: '2',
    title: 'Người Hòa Giải',
    keyword: 'Hợp tác · Nhạy cảm · Cân bằng',
    image: img(2),
    summary:
      'Số 2 mang năng lượng của sự kết nối, ngoại giao và thấu cảm. Người số 2 tinh tế, kiên nhẫn và là cầu nối hòa giải tự nhiên trong mọi mối quan hệ.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 2 là biểu tượng của sự hợp tác và hài hòa. Năng lượng này hướng tới việc lắng nghe, dung hòa và xây dựng những mối liên kết bền vững. Người số 2 sống vì các mối quan hệ và tìm thấy ý nghĩa trong sự sẻ chia.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Nhạy cảm, chu đáo, khéo léo trong giao tiếp và giỏi làm việc nhóm. Họ có trực giác mạnh, biết đặt mình vào vị trí người khác và tạo cảm giác an toàn cho những người xung quanh.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ phụ thuộc cảm xúc, ngại xung đột và đôi khi đánh mất chính kiến để làm hài lòng người khác. Số 2 cần học cách đặt ranh giới và tin vào giá trị bản thân.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Hợp với công việc tư vấn, chăm sóc, ngoại giao, nghệ thuật hay vai trò hỗ trợ – kết nối. Trong tình yêu, người số 2 lãng mạn, tận tụy và xem bạn đời là trung tâm của cuộc sống.',
      },
    ],
  },
  {
    number: 3,
    slug: '3',
    title: 'Người Sáng Tạo',
    keyword: 'Biểu đạt · Lạc quan · Truyền cảm hứng',
    image: img(3),
    summary:
      'Số 3 tràn đầy năng lượng sáng tạo, vui tươi và khả năng biểu đạt cuốn hút. Người số 3 mang đến niềm vui, màu sắc và cảm hứng cho mọi không gian họ bước vào.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 3 đại diện cho sự sáng tạo và giao tiếp. Đây là năng lượng của nghệ thuật, ngôn từ và niềm vui sống. Người số 3 có sứ mệnh lan tỏa sự lạc quan và truyền cảm hứng bằng tài năng biểu đạt của mình.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Giàu trí tưởng tượng, hoạt ngôn, hài hước và dễ mến. Họ có năng khiếu nghệ thuật, biết cách kể chuyện và khơi gợi cảm xúc tích cực ở người khác.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ phân tâm, thiếu kỷ luật và hời hợt khi gặp khó khăn. Số 3 cần học cách tập trung, kiên trì và đi đến tận cùng những gì đã bắt đầu.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Tỏa sáng trong nghệ thuật, truyền thông, sáng tạo nội dung, biểu diễn và giảng dạy. Trong tình yêu, người số 3 nồng nhiệt, vui vẻ nhưng cần sự sâu sắc để mối quan hệ thêm bền vững.',
      },
    ],
  },
  {
    number: 4,
    slug: '4',
    title: 'Người Kiến Tạo',
    keyword: 'Kỷ luật · Ổn định · Thực tế',
    image: img(4),
    summary:
      'Số 4 là nền tảng của sự bền vững, kỷ luật và trật tự. Người số 4 đáng tin cậy, chăm chỉ và xây dựng mọi thứ một cách chắc chắn, từng bước một.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 4 tượng trưng cho sự ổn định và xây dựng. Năng lượng này coi trọng kỷ luật, hệ thống và những giá trị lâu dài. Người số 4 là trụ cột vững chắc mà mọi người có thể dựa vào.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Cần cù, có tổ chức, trung thực và kiên trì. Họ giỏi lập kế hoạch, thực thi tỉ mỉ và biến những mục tiêu lớn thành hiện thực bằng nỗ lực bền bỉ.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ cứng nhắc, bảo thủ và ngại thay đổi. Số 4 cần học cách linh hoạt, cởi mở với cái mới và cho phép bản thân nghỉ ngơi thay vì làm việc quá sức.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với kỹ thuật, tài chính, quản lý, xây dựng và những lĩnh vực đòi hỏi sự chính xác. Trong tình yêu, người số 4 chung thủy, trách nhiệm và đề cao sự ổn định lâu dài.',
      },
    ],
  },
  {
    number: 5,
    slug: '5',
    title: 'Người Tự Do',
    keyword: 'Phiêu lưu · Linh hoạt · Đổi thay',
    image: img(5),
    summary:
      'Số 5 là năng lượng của tự do, trải nghiệm và thay đổi. Người số 5 năng động, tò mò và khao khát khám phá mọi khả năng mà cuộc sống mang lại.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 5 đại diện cho sự tự do và thích nghi. Đây là năng lượng của chuyển động, phiêu lưu và những trải nghiệm mới. Người số 5 học hỏi qua sự đa dạng và không chịu bó buộc trong khuôn khổ.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Linh hoạt, lanh lợi, can đảm và giỏi thích nghi. Họ giao tiếp tốt, nắm bắt cơ hội nhanh và mang đến luồng sinh khí mới mẻ cho mọi tập thể.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ thiếu kiên định, bốc đồng và khó cam kết lâu dài. Số 5 cần học cách tiết chế, chịu trách nhiệm và biến sự tự do thành nền tảng thay vì sự bất ổn.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Hợp với kinh doanh, du lịch, truyền thông, bán hàng và những công việc đa dạng, ít lặp lại. Trong tình yêu, người số 5 cuốn hút, phóng khoáng nhưng cần không gian riêng và sự tin tưởng.',
      },
    ],
  },
  {
    number: 6,
    slug: '6',
    title: 'Người Chăm Sóc',
    keyword: 'Yêu thương · Trách nhiệm · Hài hòa',
    image: img(6),
    summary:
      'Số 6 mang năng lượng của tình yêu thương, trách nhiệm và sự che chở. Người số 6 ấm áp, tận tâm và luôn đặt gia đình cùng cộng đồng lên hàng đầu.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 6 tượng trưng cho tình yêu, sự nuôi dưỡng và trách nhiệm. Năng lượng này hướng đến việc chăm lo, hàn gắn và tạo dựng tổ ấm. Người số 6 tìm thấy ý nghĩa cuộc sống qua sự cống hiến cho người khác.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Giàu lòng trắc ẩn, có trách nhiệm, đáng tin và biết hy sinh. Họ tạo ra cảm giác an toàn, ấm cúng và là điểm tựa tinh thần cho những người thân yêu.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ ôm đồm, hy sinh quá mức và can thiệp vào việc của người khác. Số 6 cần học cách chăm sóc bản thân và để người khác tự chịu trách nhiệm cho cuộc đời họ.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với y tế, giáo dục, tư vấn, dịch vụ và những nghề chăm sóc con người. Trong tình yêu, người số 6 chung thủy, bao dung và xem mái ấm là giá trị thiêng liêng nhất.',
      },
    ],
  },
  {
    number: 7,
    slug: '7',
    title: 'Người Tìm Kiếm',
    keyword: 'Trí tuệ · Nội tâm · Khám phá',
    image: img(7),
    summary:
      'Số 7 là năng lượng của trí tuệ, chiều sâu và sự chiêm nghiệm. Người số 7 ham hiểu biết, độc lập trong suy nghĩ và luôn tìm kiếm sự thật phía sau mọi hiện tượng.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 7 đại diện cho sự thông tuệ và khám phá nội tâm. Đây là năng lượng của tư duy, phân tích và tâm linh. Người số 7 đi tìm ý nghĩa sâu xa của cuộc sống thông qua tri thức và sự tĩnh lặng.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Sâu sắc, trực giác tốt, tư duy phân tích và độc lập. Họ giỏi nghiên cứu, quan sát tinh tế và đưa ra những nhận định vượt khỏi bề mặt thông thường.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ khép kín, hoài nghi và xa cách về cảm xúc. Số 7 cần học cách mở lòng, chia sẻ và cân bằng giữa thế giới nội tâm với các mối quan hệ thực tế.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Tỏa sáng trong nghiên cứu, khoa học, công nghệ, phân tích và các lĩnh vực tâm linh, triết học. Trong tình yêu, người số 7 kín đáo, sâu sắc và cần một người bạn đời thấu hiểu sự riêng tư của mình.',
      },
    ],
  },
  {
    number: 8,
    slug: '8',
    title: 'Người Quyền Lực',
    keyword: 'Tham vọng · Thịnh vượng · Bản lĩnh',
    image: img(8),
    summary:
      'Số 8 mang năng lượng của quyền lực, tham vọng và sự thịnh vượng. Người số 8 có tầm nhìn lớn, ý chí thép và năng lực biến mục tiêu thành thành tựu vật chất.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 8 tượng trưng cho quyền lực, tiền bạc và sự cân bằng giữa vật chất – tinh thần. Năng lượng này hướng đến thành công, địa vị và khả năng quản trị nguồn lực. Người số 8 sinh ra để xây dựng và lãnh đạo ở quy mô lớn.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Tham vọng, quyết đoán, giỏi tổ chức và có đầu óc kinh doanh. Họ kiên cường trước áp lực, biết nắm bắt cơ hội và có khả năng tạo ra của cải, ảnh hưởng.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ tham công tiếc việc, đặt nặng vật chất và độc đoán. Số 8 cần học cách cân bằng giữa sự nghiệp với đời sống tinh thần, và dùng quyền lực một cách nhân ái.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với quản trị, kinh doanh, tài chính, bất động sản và các vị trí lãnh đạo. Trong tình yêu, người số 8 mạnh mẽ, che chở nhưng cần dành thời gian và sự dịu dàng cho bạn đời.',
      },
    ],
  },
  {
    number: 9,
    slug: '9',
    title: 'Người Nhân Ái',
    keyword: 'Vị tha · Lý tưởng · Bao dung',
    image: img(9),
    summary:
      'Số 9 là năng lượng của lòng nhân ái, sự bao dung và lý tưởng phụng sự. Người số 9 giàu tình thương, sống vì cộng đồng và mang trong mình một tầm nhìn nhân văn rộng lớn.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 9 đại diện cho sự hoàn thiện, lòng vị tha và tinh thần phụng sự nhân loại. Đây là con số của sự cho đi vô điều kiện và trí tuệ được hun đúc từ trải nghiệm. Người số 9 hướng đến những giá trị lớn lao hơn bản thân mình.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Nhân hậu, rộng lượng, giàu lý tưởng và có sức ảnh hưởng tích cực. Họ thấu cảm sâu sắc, biết tha thứ và truyền cảm hứng cho người khác sống tử tế hơn.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ lý tưởng hóa, ôm nỗi buồn của thế giới và khó buông bỏ quá khứ. Số 9 cần học cách bảo vệ năng lượng của mình và chấp nhận sự không hoàn hảo.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Hợp với hoạt động xã hội, nghệ thuật, giáo dục, chữa lành và các công việc vì cộng đồng. Trong tình yêu, người số 9 bao dung, lãng mạn và yêu bằng cả tấm lòng rộng mở.',
      },
    ],
  },
  {
    number: 11,
    slug: '11',
    title: 'Bậc Thầy Trực Giác',
    keyword: 'Trực giác · Truyền cảm hứng · Tâm linh',
    image: img(11),
    summary:
      'Số 11 là số bậc thầy đầu tiên, mang năng lượng trực giác và tâm linh mạnh mẽ. Người số 11 nhạy bén phi thường, là nguồn cảm hứng và ánh sáng dẫn lối cho người khác.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 11 là phiên bản thăng hoa của số 2, cộng hưởng năng lượng trực giác và lý tưởng. Đây là con số của sự khai sáng, nhạy cảm tâm linh và sứ mệnh truyền cảm hứng. Người số 11 mang tiềm năng lớn nhưng cũng đối mặt với áp lực nội tâm cao.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Trực giác sắc bén, giàu cảm hứng, sáng tạo và có chiều sâu tâm linh. Họ có khả năng nhìn thấu, kết nối và nâng đỡ tinh thần cho những người xung quanh.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Dễ lo âu, nhạy cảm thái quá và mất cân bằng cảm xúc. Số 11 cần học cách tiếp đất, kiểm soát năng lượng và biến trực giác thành hành động cụ thể.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với nghệ thuật, cố vấn tinh thần, giảng dạy, chữa lành và truyền thông cảm hứng. Trong tình yêu, người số 11 sâu sắc, lãng mạn và cần một mối quan hệ nuôi dưỡng tâm hồn.',
      },
    ],
  },
  {
    number: 22,
    slug: '22',
    title: 'Bậc Thầy Kiến Tạo',
    keyword: 'Tầm nhìn · Hiện thực hóa · Di sản',
    image: img(22),
    summary:
      'Số 22 là số bậc thầy quyền năng nhất, kết hợp tầm nhìn lớn với năng lực hiện thực hóa. Người số 22 có thể biến những giấc mơ vĩ đại thành công trình để lại dấu ấn lâu dài.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 22 là phiên bản thăng hoa của số 4, hợp nhất lý tưởng của số 11 với khả năng xây dựng thực tế. Đây là con số của những nhà kiến tạo bậc thầy, có thể tạo nên những thành tựu mang tầm vóc xã hội. Sứ mệnh của số 22 là để lại di sản hữu ích cho nhân loại.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Tầm nhìn xa, thực tế, kỷ luật và giàu năng lực lãnh đạo. Họ kết hợp được sự bay bổng của ý tưởng với khả năng tổ chức, thực thi để biến điều bất khả thành hiện thực.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Áp lực kỳ vọng lớn dễ dẫn đến căng thẳng hoặc tự nghi ngờ. Số 22 cần học cách tin vào tiềm năng của mình, kiên nhẫn và không để nỗi sợ thất bại kìm hãm.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với kiến trúc, quản trị quy mô lớn, khởi nghiệp đột phá và các dự án có tầm ảnh hưởng. Trong tình yêu, người số 22 vững vàng, tận tâm và mong muốn xây dựng tương lai bền vững cùng bạn đời.',
      },
    ],
  },
  {
    number: 33,
    slug: '33',
    title: 'Bậc Thầy Chữa Lành',
    keyword: 'Yêu thương vô điều kiện · Phụng sự · Khai sáng',
    image: img(33),
    summary:
      'Số 33 là số bậc thầy của tình yêu thương và sự chữa lành. Người số 33 mang sứ mệnh phụng sự cao cả, nâng đỡ và lan tỏa lòng từ bi đến với muôn người.',
    sections: [
      {
        heading: 'Tổng quan',
        body: 'Số 33 là phiên bản thăng hoa của số 6, biểu trưng cho tình yêu thương vô điều kiện và sự khai sáng tinh thần. Đây là con số hiếm gặp nhất, gắn với những người thầy chữa lành và dẫn dắt nhân loại bằng lòng trắc ẩn.',
      },
      {
        heading: 'Điểm mạnh',
        body: 'Giàu lòng từ bi, tận hiến, có sức truyền cảm hứng và khả năng chữa lành tinh thần. Họ đặt hạnh phúc của người khác lên trên và sống vì những giá trị cao đẹp.',
      },
      {
        heading: 'Điểm cần lưu ý',
        body: 'Gánh nặng sứ mệnh dễ khiến họ kiệt sức hoặc hy sinh quá mức. Số 33 cần học cách chăm sóc bản thân, đặt ranh giới lành mạnh và cân bằng giữa cho đi với nhận lại.',
      },
      {
        heading: 'Sự nghiệp & tình yêu',
        body: 'Phù hợp với chữa lành, giáo dục, hoạt động nhân đạo, tâm linh và nghệ thuật vị nhân sinh. Trong tình yêu, người số 33 bao dung, ấm áp và yêu thương bằng một trái tim rộng mở vô điều kiện.',
      },
    ],
  },
]

/** Quick lookup by slug (e.g. "11"). */
export const getMeaningBySlug = (slug?: string | string[]): NumberMeaning | undefined => {
  if (!slug || Array.isArray(slug)) return undefined
  return NUMBER_MEANINGS.find((m) => m.slug === slug)
}
