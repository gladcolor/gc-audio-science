# TTS transcript audit

Scanned **9,725 clips** in **231 transcript files** — 5,029 Mandarin clips in 228 files and 4,696 English clips in 229 files — using the exact text in ` send `. The arrow-removal rule also compares the corresponding display field. The index is metadata. The ` _shared ` bucket counts as one transcript ID in the lesson totals.

**8,386 clips** match at least one of the 87 classes. Counts measure detector hits. A hit can be a correctly written candidate for review. The same clip can match multiple classes. This audit did not synthesize or listen to audio.

The ranking multiplies total matched clips by estimated severity. Severity 5 covers possible truncation or a change to instructional meaning. Severity 4 covers likely loss or distortion of a term, symbol or value. Severity 3 covers ambiguity. Severity 2 covers pacing or conventional number readings. Severity 1 covers low-priority prosody. Inspect the severity column as well as the ranking when triaging rare errors.

## Summary

The table shows the ten highest-impact classes. All classes and their counts appear below.

| Class | Mandarin clips / lessons | English clips / lessons | Severity | Impact | Handling |
|---|---:|---:|---:|---:|---|
| [Full stops between heading and brief gloss](#term_card) | 734 / 136 | 1,888 / 180 | 2 | 5,244 | Context |
| [Long model request](#length) | 614 / 91 | 369 / 100 | 5 | 4,915 | Fixed |
| [Historical year, date, decade or century](#years) | 1,131 / 110 | 1,042 / 106 | 2 | 4,346 | Context |
| [Acronym or letter-by-letter sequence](#acronym) | 487 / 58 | 942 / 143 | 3 | 4,287 | Context |
| [Degree, latitude/longitude or bearing](#degree_geo) | 660 / 8 | 754 / 19 | 3 | 4,242 | Fixed |
| [Decimal and precision](#decimal) | 923 / 94 | 933 / 86 | 2 | 3,712 | Context |
| [Han/Latin code switch](#mixed_script) | 1,000 / 129 | 224 / 55 | 3 | 3,672 | Context |
| [Middle dot in separated fields, names or products](#middot) | 1,020 / 69 | 6 / 3 | 3 | 3,078 | Context |
| [Parenthetical or bracketed aside](#parentheses) | 1,438 / 201 | 1,559 / 207 | 1 | 2,997 | Context |
| [Plus between terms](#plus) | 368 / 36 | 330 / 51 | 4 | 2,792 | Context |

The high-severity checks also found **4** clips with [damaged exponents](#corrupt_exponent), **8** with [missing or distorted equation relations](#lost_relation), and **2** with [flattened repeating-decimal notation](#repeat_decimal).

## Applying the findings

- Fixed means deterministic within the field or guard described below. Context means review in context and, where helpful, use an LLM rewrite with human approval.
- Resolve corrupted expressions and lost relations against the source. Apply specialized rules for formulas, units, dates and fields before general symbol and punctuation handling. Run the length check after rewrites.
- Pass exact names, quotations and teaching notation through the approved pronunciation or segmentation path. Verify any split preserves clip order and every word.
- The Mandarin request cutoff uses 150 Unicode code points. Its strict Han-only companion count shows what a 150-Han cutoff would flag. English uses 400 code points. Exact cutoff values are allowed.
- Each class has up to five real examples. Classes with fewer than three observed clips show all available examples. Zero-hit rules are included so the scanner can catch those forms after a future publish. An added ellipsis indicates shortening.

## Classes

<a id="term_card"></a>
### Full stops between heading and brief gloss

**Hits** — 2/5 severity, 5,244 impact — 734 Mandarin clips in 136 lessons and 1,888 English clips in 180 lessons. 2,622 clips across 187 distinct lesson IDs.

**Detection** uses the following logic. zh starts with a 1–10 Han heading and a 2–18 character Han/、/， gloss, separated by 。. en has a 1–5 word heading and a 1–10 word fragment after a period, with no colon, semicolon, question or exclamation marks in either. English stop detection masks ABBR and skips decimal dots and ellipses.

**Reading and handling (Context)**  
“立冬。冬季开始。” → “立冬，表示冬季开始。” “Electron shell. Energy levels where electrons are found.” → “Electron shells are the energy levels where electrons are found.”

**False positives and limits**  
Common within lesson cards. May match two complete sentences. Avoid merging actual dialogue turns or steps.

**Observed examples**

- ` chemistry/atoms ` · en · ` 9d89dd0d ` · ` Electron shell. Energy levels where electrons are found. For elements 1–20: shell 1 holds up to 2 electrons, shell 2 up to 8, shell 3 up to 8 (the 2-8-8 rul… `
- ` yuwen/yw-idioms ` · zh · ` 73b4765e ` · ` 立冬。冬季开始。 `
- ` art/art-chinese ` · en · ` af1a95c8 ` · ` Four Treasures of the Study. Brush, ink, paper and inkstone — 笔, 墨, 纸, 砚. Brushes are made of animal hair (goat, weasel, rabbit) set in bamboo. Ink sticks o… `
- ` yuwen/yw-idioms ` · zh · ` 40f843c2 ` · ` 立夏。夏季开始。 `
- ` astronomy/big-bang ` · en · ` 291d9d70 ` · ` Galaxy GN-z11. Found by Hubble (2016), studied by Webb. We see it as it was about 400 million years after the Big Bang. Its light set out almost 9 billion y… `

<a id="length"></a>
### Long model request

**Hits** — 5/5 severity, 4,915 impact — 614 Mandarin clips in 91 lessons and 369 English clips in 100 lessons. 983 clips across 116 distinct lesson IDs.

**Detection** uses the following logic. len(send) > 150 for zh or > 400 for en. Python Unicode code points include spaces, punctuation and Latin text.

**Reading and handling (Fixed)**  
Split at complete sentence boundaries, after rewrites. Send each segment in order. Keep quoted speech, clauses, numbers, formulas and their units intact. E.g. end one sky segment after the Moon sentence, then start “Planets above the horizon…” as a new request.

**False positives and limits**  
These are supplied approximate limits. Crossing them flags truncation risk, and no audio was tested. Some long clipped examples begin at the opening of the request.

**Observed examples**

- ` astronomy/sky-tonight ` · zh · ` 1bf74c57 ` · ` 纬度 -78.5 度 ，2026-11-18 21:00：白天（太阳高度 12 度 ）。月球被照亮 百分之66，在北方 14 度 高。地平线以上的行星：水星（西南 2 度 ）、土星（北 11 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球… `
- ` biology/exocytosis ` · en · ` e296885c ` · ` Pancreas beta cell. Someone just ate a cookie and blood sugar is rising! Ship 3 packages of insulin OUT into the blood. 1. Ribosome builds it: A ribosome on… `
- ` astronomy/sky-tonight ` · zh · ` fe38e0d4 ` · ` 纬度 34.0 度 ，2026-11-18 19:57：完全的黑夜（太阳高度 -30 度 ）。月球被照亮 百分之65，在南方 51 度 高。地平线以上的行星：土星（东南 52 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，整… `
- ` chemistry/density ` · en · ` 29c0514c ` · ` Buoyancy. The upward push of a liquid. A liquid pushes up on anything placed in it. This upward push is the buoyant force. The buoyant force equals the weig… `
- ` ela/central-idea ` · zh · ` f0c7f057 ` · ` 蜜蜂做着地球上最重要的工作之一：帮助我们种出粮食。 蜜蜂吸花蜜时，花粉粘在它毛茸茸的身上，又蹭到下一朵花上。 被带走的花粉让植物结出果实和种子。 苹果、杏仁、蓝莓和许多其他作物都离不开蜜蜂的造访。 蜂巢里，一只蜂王一天能产下 1500 多枚卵。 年轻的工蜂清洁巢房、喂养幼虫，年长一些的筑蜡、守门，最年长的飞出去… `

<a id="years"></a>
### Historical year, date, decade or century

**Hits** — 2/5 severity, 4,346 impact — 1,131 Mandarin clips in 110 lessons and 1,042 English clips in 106 lessons. 2,173 clips across 117 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:公元前?\s*[0-9]+|[0-9]{1,4}\s*年\s*[0-9]{1,2}\s*月(?:\s*[0-9]{1,2}\s*[日号])?|(?<![0-9])[0-9]{3,4}\s*年|[0-9]{1,2}\s*世纪|[0-9]{2}\s*年代|\b(?:[0-9]{1,4}\s*(?:BCE|CE|BC|AD)|(?:BCE|CE|BC|AD)\s*[0-9]{1,4}|(?:1[0-9]{3}|20[0-9]{2})(?:s)?|[0-9]{1,2}(?:st|nd|rd|th)\s+century)\b|(?i:\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+[0-9]{1,2}(?:st|nd|rd|th)?(?:,?\s+[0-9]{4})?\b)|(?i:\b[0-9]{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b))
```

**Reading and handling (Context)**  
“1848年” → 一八四八年. “551–479 BCE” → from five hundred fifty-one to four hundred seventy-nine before the Common Era. “the 1800s” → the eighteen hundreds.

**False positives and limits**  
Bare four-digit English numbers can be quantities or IDs. A number plus 年 can be a duration. Year convention differs from cardinal reading.

**Observed examples**

- ` georgia/ga-modern ` · zh · ` 6ebe2ebe ` · ` 普莱恩斯。一个只有几百人的小镇走出了一位总统。卡特 1924 年 10 月 1 日出生在这里，离开海军后回乡种花生。 2024 年 12 月 29 日，他在普莱恩斯家中去世，享年 100 岁——是美国最长寿的总统。 吉米·卡特国家历史公园保存了他少年时的农场、学校和竞选总部。 `
- ` astronomy/small-bodies ` · en · ` 9214c833 ` · ` … times wider and made mostly of ice. On January 1, 2019, New Horizons flew past Arrokoth, a 36 km “snowman” made of two lumps that gently stuck together: an… `
- ` ushistory/us-civilwar ` · zh · ` e6a9c5fc ` · ` 谢尔曼“向海洋进军”，萨凡纳。1864年11月15日—12月21日 · 佐治亚。联邦战役。谢尔曼率6万大军从亚特兰大向萨凡纳进军约460千米（285英里），在宽达约96千米（60英里）的地带破坏铁路、农场和物资。目的是摧毁南方继续作战的能力和意志。成千上万被奴役的黑人跟随军队走向自由。谢尔曼给林肯发电报，把萨凡… `
- ` yuwen/yw-wenyan-basics ` · en · ` 8c6a5b26 ` · ` …ddhist caves carved from the 4th to the 14th century Today: southeast of Dunhuang, Gansu Over 700 caves with about 45,000 square meters of wall paintings. I… `
- ` china/natural-wonders ` · zh · ` 695ab79d ` · ` 四川九寨沟、黄龙。四川 · 钙华 · 彩池与湖泊。湖水清澈碧蓝，成千上万的彩池层层叠叠，被乳白色的钙华堤围起来。这些堤坝是钙华——水中析出的碳酸钙，和水壶里的白色水垢是同一种物质。2017 年 8 月九寨沟发生地震，火花海的钙华堤被冲垮，诺日朗瀑布受损；经过修复，景区已重新开放。地下溶解，出地表沉积。 `

<a id="acronym"></a>
### Acronym or letter-by-letter sequence

**Hits** — 3/5 severity, 4,287 impact — 487 Mandarin clips in 58 lessons and 942 English clips in 143 lessons. 1,429 clips across 144 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:[A-Z]{2,}|[A-Z](?:[ \t]+[A-Z]){1,}|pH|mRNA|tRNA|rRNA)(?![A-Za-z0-9])
```

**Reading and handling (Context)**  
“pH 8.3” → p H eight point three / p H 八点三. DNA → D N A or 脱氧核糖核酸 when appropriate. NASA and NATO use their customary pronunciations.

**False positives and limits**  
Caps include emphasis and chemical strings, and spaced letters can be variables or music notes. Approved acronym readings can be dictionary-driven.

**Observed examples**

- ` astronomy/tides ` · en · ` da022c1b ` · ` …han the far side, so it feels a stronger pull. The DIFFERENCE in pull across Earth stretches the oceans into two bulges. Scientists call it the tidal force. `
- ` ela/narrative-techniques ` · zh · ` d2af4a94 ` · ` 人物塑造，S T E A L。作者塑造人物的方法：直接告诉，或通过语言、心理、对他人的影响、动作、外貌间接展现。 间接：他把硬币数了两遍，又把最大的那枚悄悄塞回口袋。 作用：让读者自己推断人物性格，人物更真实。 `
- ` music/music-pitch ` · en · ` 75d56b2f ` · ` …tes. Count letter names, including both ends: C to G equals C D E F G equals a 5th. Small whole-number frequency ratios sound smooth: octave 2:1, fifth 3:2. `
- ` ushistory/us-civilrights ` · zh · ` fa653b82 ` · ` …级女孩琳达·布朗离白人学校很近，却必须走很远去上黑人学校。她的父亲加入了全国有色人种协进会，N A A C P，发起的诉讼。NAACP的律师瑟古德·马歇尔（Thurgood Marshall）在最高法院为此案（与另外四个案子合并）辩护。九位大法官一致裁定：“隔离的教育设施本质上就是不平等的。”学校隔离违反宪法。 `
- ` earth/fossils-time ` · en · ` 15abbd3c ` · ` …Petrified wood and insect in amber. The YOUNGEST layer: it is on top. Petrified wood: minerals replaced the wood cell by cell, keeping even the tree rings. … `

<a id="degree_geo"></a>
### Degree, latitude/longitude or bearing

**Hits** — 3/5 severity, 4,242 impact — 660 Mandarin clips in 8 lessons and 754 English clips in 19 lessons. 1,414 clips across 22 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[-−]?[0-9]+(?:\.[0-9]+)?\s*°(?!\s*[CF]\b)(?:\s*[NSEW]\b)?|(?:北纬|南纬|东经|西经|纬度|经度|方位角)\s*[-−]?\s*(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?\s*度
```

**Reading and handling (Fixed)**  
“45.6°N, 150.7°W” → forty-five point six degrees north, one hundred fifty point seven degrees west. “北纬 38.0 度” → 北纬三十八点零度.

**False positives and limits**  
Fixed in a coordinate/bearing field. Bare degrees may be temperature, angle or solar altitude. Match directional suffixes before handling generic degrees.

**Observed examples**

- ` geography/latitude-longitude ` · en · ` 35200f3f ` · ` 45.6°N, 150.7°W. Northern and Western Hemispheres. Pacific Ocean `
- ` geography/latitude-longitude ` · zh · ` 9a00d032 ` · ` 北纬 38.0 度 ,西经 156.0 度。北半球 · 西半球。太平洋 `
- ` earth/climate ` · en · ` ef07aea9 ` · ` Tropical zone. Between 23.5° N and 23.5° S. The noon Sun is high all year, and it is directly overhead at least once a year. Warm all year. Many places have… `
- ` astronomy/sky-tonight ` · zh · ` 13302ac9 ` · ` 纬度 -22.5 度 ，2026-11-18 21:00：完全的黑夜（太阳高度 -25 度 ）。月球被照亮 百分之66，在西北方 64 度 高。地平线以上的行星：土星（北 66 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，… `
- ` chemistry/elements-compounds ` · en · ` c2bfbc9d ` · ` … point to the corners of a tetrahedron, 109.5° apart, as far from each other as possible. Carbon usually forms 4 bonds. That is why it can build so many dif… `

<a id="decimal"></a>
### Decimal and precision

**Hits** — 2/5 severity, 3,712 impact — 923 Mandarin clips in 94 lessons and 933 English clips in 86 lessons. 1,856 clips across 102 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:[0-9]+\.[0-9]+|\.[0-9]+)(?![A-Za-z0-9])
```

**Reading and handling (Context)**  
“1.06” → one point zero six / 一点零六. “38.0” → thirty-eight point zero / 三十八点零 if precision is pedagogically relevant.

**False positives and limits**  
Decimals in coordinates, prices, version numbers and scientific notation need their own reading rules. Ordinary decimals may already be clear.

**Observed examples**

- ` china/dynasties ` · en · ` bfc70a8b ` · ` …ng, Qi, Liang, Chen — all ruling from Jiankang. Zu Chongzhi (祖冲之) calculated pi to between 3.1415926 and 3.1415927 — the world’s best for about 1,000 years. `
- ` worldhistory/wh-today ` · zh · ` 6301d041 ` · ` 罗马。罗马从一个小共和国发展成环地中海的大帝国。1582年，今天通用的公历在这里颁行，一年为365.2425天，和约300年前郭守敬的《授时历》相同。 `
- ` math/circles ` · en · ` 42b8034c ` · ` …is called pi: pi equals C over d equals 3.14159 and so on , a decimal that never ends or repeats. So C equals pi d , and because d equals 2r , also C equals… `
- ` astronomy/exoplanets ` · zh · ` e5bbed21 ` · ` …直径只有太阳的 109分之1，所以只挡住（109分之1） 的平方 约等于 百分之0.0084 的光，也就是百万分之 84。每 365 天凌星一次，每次约 13 小时。只有像开普勒这样的太空望远镜才足够稳定，能测出这么小的下陷。打开“加入噪声”，看看为什么小行星很难被发现。地球大小的行星 + 太阳大小的恒星 等于… `
- ` chemistry/elements-compounds ` · en · ` c2bfbc9d ` · ` … point to the corners of a tetrahedron, 109.5° apart, as far from each other as possible. Carbon usually forms 4 bonds. That is why it can build so many dif… `

<a id="mixed_script"></a>
### Han/Latin code switch

**Hits** — 3/5 severity, 3,672 impact — 1,000 Mandarin clips in 129 lessons and 224 English clips in 55 lessons. 1,224 clips across 167 distinct lesson IDs.

**Detection** uses the following logic. send contains at least one HAN character and at least one LAT character. The excerpt anchors on the other script relative to lang.

**Reading and handling (Context)**  
“文房四宝：笔、墨、纸、砚” can be a separately voiced Mandarin segment inside the English paragraph, or use “brush, ink, paper and inkstone” when the Chinese words are unnecessary. “Columbia 县” → use the approved Mandarin place-name reading or an English name segment plus 县.

**False positives and limits**  
This catches true bilingual text plus math, unit and acronym switches. A mixed-script hit does not establish a pronunciation failure.

**Observed examples**

- ` georgia/ga-government ` · zh · ` aa9fb1f8 ` · ` Chattahoochee 县。 `
- ` china/new-era ` · en · ` f3ab4583 ` · ` …ly prosperous society in all respects” (全面建成小康社会; xiǎokāng means “fairly well-off”). In February China had declared complete victory in the fight against po… `
- ` ela/argument-writing ` · zh · ` d32ee755 ` · ` 反方观点（Counterclaim）。公正地写出对方最有力的观点。写出反方观点会让你显得公正、自信，而不是软弱。要用对方最有力的观点，不要故意歪曲成可笑的版本，那叫“稻草人谬误”。英文常用：“Some people argue that…”“Critics may say…”“It is true that…”… `
- ` politics/constitution ` · en · ` 55cb2378 ` · ` …etails. The National People’s Congress (全国人民代表大会, NPC) and its Standing Committee make China’s national laws. Many laws open with the line “This Law is enac… `
- ` economics/econ-personal-finance ` · zh · ` 2485badc ` · ` 诈骗与欺诈。想骗走你的钱或密码的伎俩。 骗子冒充你信任的人，编造问题或奖品，催你快点，并要求奇怪的付款方式。 正规公司从不让你用礼品卡付款，也不会索要登录验证码。 在美国可到 ReportFraud.ftc.gov 举报；在中国，国家反诈中心有 App 和 96110 预警电话。 `

<a id="middot"></a>
### Middle dot in separated fields, names or products

**Hits** — 3/5 severity, 3,078 impact — 1,020 Mandarin clips in 69 lessons and 6 English clips in 3 lessons. 1,026 clips across 69 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[·・•‧]
```

**Reading and handling (Context)**  
“北半球 · 西半球” → 位于北半球和西半球. “卡尔·冯·弗里希” → speak the name continuously. “1.4·n·log2n” → 一点四乘以 n，再乘以以二为底的 n 的对数.

**False positives and limits**  
A middle dot may also be a decimal marker or a bullet. Separate name handling from field and multiplication handling.

**Observed examples**

- ` art/art-history ` · zh · ` 03258855 ` · ` 后印象派。1889 年 · 法国圣雷米。色彩和笔触表达感受，而不只是眼睛看到的样子。梵高的星空在旋转；修拉用无数小点组成画面（点彩法）。 同一时期的中国：任伯年等“海上画派”画家把传统水墨与鲜艳色彩结合起来，卖给城市里的买家。 `
- ` cs/cs-algorithms ` · en · ` 5302eec7 ` · ` …nto 4s, 4s into 8s…. To merge, compare the fronts of two piles and take the smaller. About n·log2n comparisons: 1,000 items about 10,000 instead of 500,000. `
- ` astronomy/gravity-orbits ` · zh · ` a558e2dd ` · ` 牛顿的高山。1687 年的思想实验。艾萨克·牛顿想象在一座高到伸出大气层的山顶上放一门大炮，这样就没有空气阻力。慢速的炮弹沿弧线下落，撞到地面。速度越快，落得越远，因为行星表面在它下方向下弯曲。速度足够快时，炮弹会永远绕着行星“下落”而落不了地：它进入了轨道！轨道就是一直在下落，却总是落不到地面。 `
- ` music/music-instruments ` · en · ` 1023c07b ` · ` Tanggu and gong 堂鼓·锣. Percussion, the energy of festivals and opera. 堂鼓 tánggǔ: a barrel drum played with two sticks. The gong 锣 and cymbals 镲 add crashes; … `
- ` biology/cell-theory ` · zh · ` 3cac3cb2 ` · ` 罗伯特·胡克。用自制的显微镜观察一片很薄的软木，看到许多排列整齐的小空格。它们让他想起小房间，于是他把它们命名为“细胞”。 `

<a id="parentheses"></a>
### Parenthetical or bracketed aside

**Hits** — 1/5 severity, 2,997 impact — 1,438 Mandarin clips in 201 lessons and 1,559 English clips in 207 lessons. 2,997 clips across 214 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[（(][^）)\r\n]{2,}[）)]|[【\[][^\]】\r\n]+[\]】]
```

**Reading and handling (Context)**  
“oxidation (a reaction with oxygen)” can be voiced “oxidation, which is a reaction with oxygen”. For “110 米（120 码）” say “一百一十米，约合一百二十码”.

**False positives and limits**  
A parenthesis may carry a unit conversion, formula grouping, coordinate or translation. Preserve grouping and avoid saying punctuation by default.

**Observed examples**

- ` astronomy/big-bang ` · en · ` a07c0cd8 ` · ` …of space balloons by an enormous factor (at least 10 squared ⁶ times). Tiny quantum jitters get stretched into the seeds of every future galaxy. This is the… `
- ` cs/cs-computers ` · zh · ` 117462f6 ` · ` 指令寄存器，I R。存放当前正在执行的指令，供控制器译码。在这台CPU里，第一位数字表示操作（1 等于 加，2 等于 减，3 等于 存，5 等于 取数，6 等于 跳转，7 等于 为零则跳转，900 等于 输出，000 等于 停机）。后两位数字是内存地址。 `
- ` biology/animals ` · en · ` 1e275a81 ` · ` …and five-part radial symmetry as adults (their larvae are bilateral!). Hundreds of tiny tube feet, moved by water pressure, help them crawl and grip. Many c… `
- ` politics/rights-duties ` · zh · ` d03244a9 ` · ` …义务。法定义务须履行：法律要求做的必须去做，法律禁止做的坚决不做。遵守宪法和法律（保守国家秘密，爱护公共财产，遵守劳动纪律，遵守公共秩序，尊重社会公德）。维护国家利益：维护国家统一和全国各民族团结；维护祖国的安全、荣誉和利益。依法服兵役：保卫祖国、抵抗侵略是每一个公民的神圣职责；依照法律服兵役和参加民兵组织是公… `
- ` chemistry/acids-bases ` · en · ` fe7b63d0 ` · ` Bleach. pH 12.6. Very basic. Bleach (sodium hypochlorite solution) is strongly basic and a powerful disinfectant. Bases feel slippery because they react wit… `

<a id="plus"></a>
### Plus between terms

**Hits** — 4/5 severity, 2,792 impact — 368 Mandarin clips in 36 lessons and 330 English clips in 51 lessons. 698 clips across 52 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<=[A-Za-z0-9\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF)）])\s*[+＋]\s*(?=[A-Za-z0-9\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF(（])
```

**Reading and handling (Context)**  
“花药 + 花丝” → 雄蕊由花药和花丝组成. “color + white” → mix the color with white. “H2 + O2” in a reaction → hydrogen reacts with oxygen, with coefficients voiced where present.

**False positives and limits**  
Also hits true addition, UTC offsets and compound abbreviations. Replacing every plus with “and” can change meaning.

**Observed examples**

- ` astronomy/eclipses ` · zh · ` 9d0f164c ` · ` 交点与食季。两个轨道面相交的地方。月球轨道穿过地球公转轨道面的两个点叫做交点。只有当新月或满月发生在交点附近时，才会出现食。交点大约每 6 个月与太阳排成一线一次，这段时间叫“食季”。每年至少发生两次日食（大多是日偏食）。食 等于 新月或满月 + 靠近交点。 `
- ` art/art-color ` · en · ` 0e782124 ` · ` Tertiary colors. A primary + its neighbouring secondary: red-orange, blue-green… There are six: red-orange, yellow-orange, yellow-green, blue-green, blue-vi… `
- ` biology/cell-theory ` · zh · ` 1ab95acd ` · ` 器官系统。多个器官协同工作。器官系统（简称系统）是由几个器官共同完成一项重要生理功能而组成的。循环系统 等于 心脏 + 血管 + 血液，负责把氧气和营养物质运送到每一个细胞。系统之间也会合作：呼吸系统吸入氧气，循环系统再把氧气送到全身。 `
- ` chemistry/acids-bases ` · en · ` 6464f209 ` · ` Neutralization. Acid + base, salt + water. When an acid and a base react, H⁺ and OH⁻ join to make water: H⁺ + OH⁻, H2O. The other ions form a salt. Example:… `
- ` china/natural-wonders ` · zh · ` feee9f36 ` · ` 桂林山水（漓江）。广西 · 石灰岩 · 喀斯特峰林。一座座陡峭的石灰岩山峰拔地而起，漓江在峰林间蜿蜒流过。山体内部有芦笛岩等许多溶洞——流水也在从里面“掏空”岩石。桂林山水的景色印在第五套人民币 20 元纸币的背面。石灰岩 + 雨水 + 时间 等于 峰林和溶洞。 `

<a id="quotes"></a>
### Quoted term or title with explicit boundaries

**Hits** — 1/5 severity, 2,547 impact — 1,576 Mandarin clips in 193 lessons and 971 English clips in 151 lessons. 2,547 clips across 200 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
“[^”]+”|‘[^’]+’|《[^》]+》|「[^」]+」|『[^』]+』|"[^"\r\n]{2,}"
```

**Reading and handling (Context)**  
“《记承天寺夜游》” → “苏轼的《记承天寺夜游》” with a title pause or title cue. Keep contrastive terms distinct in “blue-green”, “green-blue”.

**False positives and limits**  
Includes in-line quotations already supported by TTS. Quotation marks signal boundaries but need no spoken “quote” in ordinary narration.

**Observed examples**

- ` china/inventions ` · zh · ` 80e57095 ` · ` 影响：造纸术和印刷术促进了文化传播；指南针为远洋航行提供了条件；火药改变了作战方式。马克思说：“火药、指南针、印刷术——这是预告资产阶级社会到来的三项伟大发明。” `
- ` _shared ` · en · ` 8f4a6c0e ` · ` …. Today: Huanggang, Hubei. Su Shi wrote 《念奴娇·赤壁怀古》, the two Red Cliff rhapsodies and 《记承天寺夜游》 here. This is not the battlefield of 208 (that is in today’s C… `
- ` ela/character-pov ` · zh · ` 1f17183c ` · ` 第一章 · 守财奴。“唉，斯克鲁奇真是个一毛不拔的人！一个榨取、拧夺、攫取、刮削、紧抓不放、贪得无厌的老罪人！” 叙述者直接告诉我们斯克鲁奇是什么样的人——一连串表示贪婪的词。 `
- ` art/art-history ` · en · ` 91a6d2d8 ` · ` …bject, colors, shapes, materials, size. “A woman with folded hands in front of a hazy landscape.” Detectives Always Investigate Judiciously: Describe, Analy… `
- ` politics/constitution ` · zh · ` 795f88b0 ` · ` …法宣誓。每年12月4日是国家宪法日。现行宪法于1982年12月4日通过并公布施行；2014年，全国人大常委会决定将12月4日设立为国家宪法日。国家工作人员就职时应当依照法律规定公开进行宪法宣誓。誓词开头是：“我宣誓：忠于中华人民共和国宪法，维护宪法权威，履行法定职责……”。中学生要学习宪法、认同宪法、践行宪法。 `

<a id="grouped_numeric"></a>
### Grouped digits and large-number scale

**Hits** — 3/5 severity, 2,397 impact — 276 Mandarin clips in 78 lessons and 523 English clips in 102 lessons. 799 clips across 107 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![0-9.,])[0-9]{1,3}(?:,[0-9]{3})+(?![0-9])|(?<![0-9.,])[0-9]{5,}(?![0-9])|[0-9]+(?:\.[0-9]+)?\s*(?:万亿|亿|万)|(?i:\b(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?\s+(?:million|billion|trillion)\b)
```

**Reading and handling (Context)**  
“384,400 千米” → 三十八万四千四百千米. “5.3 million” → five point three million. Keep the correct scale, such as a hundred million for 亿.

**False positives and limits**  
Long strings can be IDs. A comma can divide coordinates or list values if written without a space. Already spoken magnitudes are audit candidates.

**Observed examples**

- ` astronomy/big-bang ` · en · ` 89b0d299 ` · ` Today: 13.8 billion years. Space between the galaxies is just 2.7 degrees above absolute zero, and the expansion is speeding up. If all of cosmic history we… `
- ` art/art-history ` · zh · ` 9c344cb6 ` · ` 洞穴艺术。约 17,000 年前 · 法国拉斯科。来自大地的颜料：红色和黄色的赭石、黑色的木炭——用苔藓蘸着涂，或用空心骨管吹喷。岩壁上的凸起被画成动物的肚子。 同一时期的中国：江西仙人洞的先民已经在制作世界上已知最古老的陶器之一（约 2 万年前）。 `
- ` china/new-era ` · en · ` 924c1094 ` · ` …d out of poverty. The BeiDou-3 satellite navigation system — China’s own GPS — went global, and China’s economy passed 100 trillion yuan for the first time. `
- ` earth/fossils-time ` · zh · ` 01f405a3 ` · ` …后形成一堵岩浆岩“墙”。它切穿了第 1到6 层，所以比这些岩层都年轻（交切关系）。第 7 层覆盖在它上面，所以第 7 层更年轻。岩浆岩可以利用以稳定速率衰变的放射性元素（半衰期）测出具体年龄，这就是绝对年代测定。岩墙有 5000 万年，所以第 6 层一定比 5000 万年老，第 7 层则比 5000 万年年轻。 `
- ` cs/cs-data-crypto ` · en · ` 9f0eb234 ` · ` …xel mixes red, green and blue light, each from 0 to 255 — about 16.7 million colours. (255, 255, 255) is white, (0, 0, 0) is black, (255, 255, 0) is yellow. `

<a id="dash"></a>
### Prose dash or dash-joined term

**Hits** — 2/5 severity, 2,338 impact — 439 Mandarin clips in 100 lessons and 730 English clips in 116 lessons. 1,169 clips across 135 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
—+|(?<=[A-Za-z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF])–(?=[A-Za-z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF])|[ \t]–[ \t]
```

**Reading and handling (Context)**  
“没养宠物——可……” → use a pause and keep the conjunction, or use a sentence break. “Earth–Sun distance” → the distance from Earth to the Sun.

**False positives and limits**  
The pattern also hits names, ranges, objects and chemical bonds. Normal punctuation may already read well.

**Observed examples**

- ` astronomy/telescopes-light ` · en · ` a468305d ` · ` X-rays. 0.01 – 10 nm. X-ray telescopes show the hottest places in the universe, from millions to hundreds of millions of degrees. X-rays would go straight i… `
- ` art/art-chinese ` · zh · ` fb0bdeda ` · ` 文房四宝。笔、墨、纸、砚。 毛笔用羊毫、狼毫（黄鼠狼毛）、兔毫等装在竹管上。 墨条由烟灰和胶制成，加水在砚台上研磨。 安徽出产的宣纸吸墨极快——下笔无法擦改！ 笔墨纸砚，书房四宝。 `
- ` china/dynasties ` · en · ` 6dd19977 ` · ` Western Han. 202 BCE – 8 CE. Zhang Qian opens the Silk Road. In 138 BCE Zhang Qian (张骞) set off west — and was captured for over ten years before getting ho… `
- ` biology/endocytosis ` · zh · ` 14a5a90d ` · ` 只抓胆固醇。受体（Y 形）只抓 LDL 颗粒——血液里橙色的“胆固醇包裹”。点击细胞外面可以加入更多 LDL。 1。结合: LDL 颗粒与相配的受体结合，就像钥匙插进锁里。 2。有被小窝: 受体装满后，一层蛋白质外衣（网格蛋白，灰色小刺）让细胞膜向内弯，形成一个小窝。 3。闭合脱离: 小窝脱离细胞膜，变成只装着… `
- ` ushistory/us-civilrights ` · en · ` d8411abb ` · ` Montgomery Bus Boycott. 5 Dec 1955 – 20 Dec 1956, Montgomery, Alabama. 1 December 1955: Rosa Parks refused to give her bus seat to a white man and was arres… `

<a id="utc"></a>
### UTC abbreviations and offsets

**Hits** — 4/5 severity, 2,332 impact — 326 Mandarin clips in 2 lessons and 257 English clips in 2 lessons. 583 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z])UTC\s*(?:(?:[+＋\-−]|加|减|plus\b|minus\b)\s*[0-9]{1,2}(?::[0-9]{2})?)?(?![A-Za-z])
```

**Reading and handling (Fixed)**  
“UTC+5:30” → coordinated universal time plus five hours and thirty minutes / 协调世界时加五小时三十分. “UTC减4” → 协调世界时减四小时.

**False positives and limits**  
Expand within a time-zone template. Do not read a UTC offset as a local time or add an unstated direction.

**Observed examples**

- ` geography/time-zones ` · zh · ` 1f11fc0c ` · ` UTC减10。你点击的位置：北纬 52.2 度 ,西经 152.5 度 · 太平洋 这个时区比 UTC 晚 10 小时(在本初子午线以西)。 “太阳时”经度每差 1 度 相差 4 分钟。而时区时间按整小时跳变，让相邻地区使用同一个时间。 官方时间可能不同：各国自己选择时区（例如全中国统一使用 UTC+8）。 `
- ` _shared ` · en · ` 72ee8a8d ` · ` Honolulu. The capital of Hawaii, on the island of Oahu in the middle of the Pacific. It uses UTC minus 10, 5 hours behind Atlanta in winter. `
- ` geography/time-zones ` · zh · ` 435f64af ` · ` UTC减10。你点击的位置：北纬 69.4 度 ,西经 148.8 度 · 北美洲 · 美国 这个时区比 UTC 晚 10 小时(在本初子午线以西)。 “太阳时”经度每差 1 度 相差 4 分钟。而时区时间按整小时跳变，让相邻地区使用同一个时间。 官方时间可能不同：各国自己选择时区（例如全中国统一使用 UTC+… `
- ` _shared ` · en · ` 94b79ff7 ` · ` Kiritimati (Christmas Island). A coral atoll in Kiribati that uses UTC+14 — one of the first places on Earth to start each new day. `
- ` geography/time-zones ` · zh · ` bfc155bd ` · ` UTC减10。你点击的位置：北纬 57.1 度 ,西经 143.8 度 · 太平洋 这个时区比 UTC 晚 10 小时(在本初子午线以西)。 “太阳时”经度每差 1 度 相差 4 分钟。而时区时间按整小时跳变，让相邻地区使用同一个时间。 官方时间可能不同：各国自己选择时区（例如全中国统一使用 UTC+8）。 `

<a id="spaced_stop"></a>
### Space before punctuation

**Hits** — 2/5 severity, 2,228 impact — 877 Mandarin clips in 52 lessons and 237 English clips in 54 lessons. 1,114 clips across 62 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[ \t]+(?=[。．.!！?？，,、：:；;])
```

**Reading and handling (Fixed)**  
“7.5 。” → “7.5。” and speak “七点五”. “equals 12 .” → “equals 12.”

**False positives and limits**  
Strip for confirmed punctuation boundaries. A space before a decimal-leading dot, an ellipsis or a teaching example can be intentional.

**Observed examples**

- ` astronomy/exoplanets ` · zh · ` 0d2f073f ` · ` 恒星。我们测量的是它的总亮度。在几光年之外，即使最大的望远镜也只能把恒星看成一个光点。我们看不到行星，只能看到恒星的亮度稍稍下降，然后恢复。拖动“恒星半径”滑块：同一颗行星挡住小恒星的比例更大。较小的恒星温度也更低、颜色更红（红矮星）；较大的恒星更热、更白。深度 等于 （行星半径 除以 恒星半径） 的平方 。 `
- ` biology/cell-theory ` · en · ` 489ecd03 ` · ` …rough. The eyepiece usually magnifies 10 times . Total magnification equals eyepiece power times objective power. 10 times times 40 times equals 400 times . `
- ` chemistry/density ` · zh · ` 4d728f64 ` · ` 植物油。0.92 g/ 立方厘米。植物油的密度约为 0.92 g/ 立方厘米 。油和水不相溶，密度较小的油浮在上面。所以海上的石油泄漏会在海面上扩散开。 `
- ` china/megaprojects ` · en · ` e31bdf95 ` · ` …ad climbs out of the tunnel and back onto a bridge. The two islands are each about 100,000 square meters . From here the Hong Kong Link Road continues east. `
- ` earth/atmosphere ` · zh · ` 1348d77a ` · ` …千米 · 极光和国际空间站。空气极其稀薄。少量气体粒子吸收 X 射线和紫外线，温度可达 500–2000 摄氏度 。但你并不会觉得热：粒子太少，传到皮肤上的热量非常少。来自太阳的带电粒子撞击气体原子时，会在这里发出极光。国际空间站在约 400 千米高的热层中运行。热层下部的电离层能反射无线电波，让它绕地球传播。 `

<a id="template_join"></a>
### Missing pause between generated fields

**Hits** — 4/5 severity, 2,184 impact — 306 Mandarin clips in 1 lessons and 240 English clips in 1 lessons. 546 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![。.!！?？:：])(?:[A-Za-z0-9°）)\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF])\s+(?:(?:This zone|Planets above the horizon|On this sky map)\b|这个时区|地平线以上的行星|这张星图)
```

**Reading and handling (Fixed)**  
“加拿大 这个时区比 UTC 晚” → 加拿大。这个时区比协调世界时晚. “Canada This zone is …” → Canada. This time zone is …

**False positives and limits**  
Insert the missing boundary in the identified field template. Generic letter-plus-space detection would damage normal sentences.

**Observed examples**

- ` geography/time-zones ` · zh · ` 8959e4b0 ` · ` …TC减4。你点击的位置：北纬 51.0 度 ,西经 66.0 度 · 北美洲 · 加拿大 这个时区比 UTC 晚 4 小时(在本初子午线以西)。 “太阳时”经度每差 1 度 相差 4 分钟。而时区时间按整小时跳变，让相邻地区使用同一个时间。 官方时间可能不同：各国自己选择时区（例如全中国统一使用 UTC+8）。 `
- ` geography/time-zones ` · en · ` b8a63ad4 ` · ` …ed: 53.6°N, 67.2°W, North America, Canada This zone is 4 hours BEHIND UTC (west of the prime meridian). “Sun time” changes 4 minutes for every 1° of longitu… `
- ` geography/time-zones ` · zh · ` 020865f8 ` · ` …TC减6。你点击的位置：北纬 62.6 度 ,西经 95.6 度 · 北美洲 · 加拿大 这个时区比 UTC 晚 6 小时(在本初子午线以西)。 “太阳时”经度每差 1 度 相差 4 分钟。而时区时间按整小时跳变，让相邻地区使用同一个时间。 官方时间可能不同：各国自己选择时区（例如全中国统一使用 UTC+8）。 `
- ` geography/time-zones ` · en · ` 01d9062b ` · ` …u clicked: 64.6°N, 53.3°E, Europe, Russia This zone is 4 hours AHEAD of UTC (east of the prime meridian). “Sun time” changes 4 minutes for every 1° of longi… `
- ` geography/time-zones ` · zh · ` 02b30f72 ` · ` UTC减1。你点击的位置：北纬 67.4 度 ,西经 16.8 度 · 北冰洋 这个时区比 UTC 晚 1 小时(在本初子午线以西)。 “太阳时”经度每差 1 度 相差 4 分钟。而时区时间按整小时跳变，让相邻地区使用同一个时间。 官方时间可能不同：各国自己选择时区（例如全中国统一使用 UTC+8）。 `

<a id="polyphonic_zh"></a>
### Mandarin polyphonic phrase watchlist

**Hits** — 4/5 severity, 2,176 impact — 536 Mandarin clips in 151 lessons and 8 English clips in 5 lessons. 544 clips across 151 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
龟兹|朝歌|行省|银行|行走|执行|重庆|重阳|重量|重心|重新|重复|长安|长乐|长城|长江|长大|成长|等长|西藏|宝藏|藏在|音乐|乐器|乐山|单于|尉迟|参差|参见|漂白|漂亮|湖泊|停泊|迫降|投降|降落|看守|出没|模样|模型|结实|打结|中弹|命中|划船|计划|得了|为了|数一数|数不清|乘车|千乘|咽喉|咽下|呜咽|血液|鲜血|殷墟|燕国|燕子|燕然|柏林|吐蕃|番禺|蚌埠|六安|厦门|秘鲁|华山|济南|济宁|宿迁|星宿|蒭藁|怒号|阴风怒号|颠沛|薄暮|单薄|系住|关系|数学|数轴|转身|转圈|转动|勒石|勒紧
```

**Reading and handling (Context)**  
“行省” → xíngshěng. “朝歌” → Zhāogē. “西藏” → Xīzàng. “阴风怒号” → yīnfēng nùháo. Use a pronunciation lexicon or controlled paraphrase and listen to the result.

**False positives and limits**  
Auditable phrase watchlist. Several common senses are low risk and will read correctly. Unlisted words and senses still require linguistic review.

**Observed examples**

- ` _shared ` · zh · ` 9b2f1b9c ` · ` 龟兹。今天：新疆库车。龟兹（读 cí）以音乐舞蹈闻名，克孜尔石窟的佛教壁画也很有名。 `
- ` china/dynasties ` · en · ` 2d0664a6 ` · ` Yuan. 1271–1368. The province system (行省制度). Yuan divided its huge empire into provinces (行省 xíngshěng). It was the start of China’s province system — the “… `
- ` _shared ` · zh · ` f42c004d ` · ` 朝歌。今天：河南淇县。商纣王住在朝歌（读 gē）。牧野之战后，周军攻入朝歌。 `
- ` yuwen/yw-hanzi ` · en · ` 04c46f54 ` · ` …s. Found in 1899; most come from Yinxu (殷墟) near Anyang, Henan. About 4,500 different characters have been found; only around a third can be read so far. Ve… `
- ` yuwen/yw-wenyan-classics ` · zh · ` e5147749 ` · ` 阴风怒号，浊浪排空； `

<a id="unit_symbol"></a>
### Abbreviated measurement unit

**Hits** — 3/5 severity, 1,770 impact — 63 Mandarin clips in 27 lessons and 527 English clips in 113 lessons. 590 clips across 114 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?\s*(?:km|cm|mm|nm|µm|μm|mL|ml|kg|mg|kJ|GHz|MHz|kHz|Hz|mph|rpm|BPM|ft|mi|AU|KB|MB|GB|TB|TEU|kWh|kW|MW|Pa|kPa|MPa|mol|kcal|cal|ms|min|hr|[ghsmLuNJWVAK]|°[CF]|[℃℉])(?![A-Za-z0-9])
```

**Reading and handling (Fixed)**  
“500 m” → five hundred meters / 五百米. “3 GHz” → three gigahertz / 三吉赫兹. “1.06 g” → one point zero six grams / 一点零六克.

**False positives and limits**  
Use a case-sensitive unit dictionary in measured fields, plus English number agreement. m, g, N and u can be variables, mass units or labels. Do not expand ambiguous tokens globally.

**Observed examples**

- ` astronomy/galaxies ` · en · ` c5b172d4 ` · ` …d its planets orbit the center at about 230 km/s, taking about 230 million years for one lap: one “galactic year”. The last time the Sun was at this spot in… `
- ` cs/cs-computers ` · zh · ` a5954471 ` · ` 时钟。一块每秒“滴答”几十亿次的晶体，每一下都让CPU前进一步。3 GHz 等于 每秒30亿次滴答。我们这台CPU每条指令用3个时钟周期（取指、译码、执行）。真实的CPU会让各步重叠（流水线），并且多个核心同时工作。 `
- ` china/natural-wonders ` · en · ` cf892ad2 ` · ` …t). Xizang (Tibet), China–Nepal border, 8,848.86 m. The world’s highest peak: 8,848.86 m (29,032 ft), measured jointly by China and Nepal in 2020. That’s ab… `
- ` chemistry/density ` · zh · ` ffba656a ` · ` 洗洁精。1.06 g/ 立方厘米。洗洁精的密度约为 1.06 g/ 立方厘米 ，只比水大一点点。100 mL 的质量约为 106 g。倒的时候要慢，否则会和水层混在一起。 `
- ` physics/light ` · en · ` 44c093ee ` · ` …t travels in straight lines. We draw these paths as rays with arrows. Light is the fastest thing in the universe: about 300,000 km every second in a vacuum. `

<a id="homograph_en"></a>
### English pronunciation depends on sense

**Hits** — 3/5 severity, 1,473 impact — 1 Mandarin clips in 1 lessons and 490 English clips in 145 lessons. 491 clips across 145 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?i:\b(?:lead|leads|live|lives|read|reads|record|records|close|wind|winds|wound|bow|bows|bass|minute|content|object|produce|conduct|present|project|tear|desert|row|use|does)\b)|\bPolish\b
```

**Reading and handling (Context)**  
“lead” as a metal → /lɛd/, or “the metal lead”. “wind” as moving air → /wɪnd/. “read” in the past tense → /rɛd/, or recast with “had read” where grammatical.

**False positives and limits**  
A watchlist hit is a review candidate. Most are ordinary occurrences whose surrounding syntax may already resolve the pronunciation.

**Observed examples**

- ` biology/classification ` · en · ` b78b2ec6 ` · ` …species is a group of organisms that can breed together and produce fertile offspring. Its scientific name has two words: Genus + species, like Canis lupus. `
- ` ela/research-media ` · zh · ` b4470c8f ` · ` …、娱乐，还是推销？公司介绍自家产品的页面是为了卖东西，只会说好话。“Sponsored content（赞助内容）”“paid post（付费帖子）”说明有人付了钱：这是穿着新闻外衣的广告。讽刺网站（标着“幽默”）是开玩笑，不是新闻。顺着钱找：如果我相信了，谁得好处？有说服目的不一定是假的，但必须检查它的证据。 `
- ` chemistry/periodic-table ` · en · ` 03dd3a4d ` · ` …tion metals. atomic number 40. Groups 3–12, the middle block. Hard, strong, shiny metals that conduct heat and electricity well: iron, copper, gold, silver. `
- ` china/inventions ` · en · ` 7151e4d5 ` · ` …alchemists invented it; a mid-Tang book records the recipe, and by the end of the Tang it was used in war. In the Song and Yuan came fire arrows, the Southe… `
- ` earth/plate-tectonics ` · en · ` 4c36af9a ` · ` …ield flips every so often. Cooling lava records it, leaving matching magnetic stripes on both sides of the ridge. Harry Hess proposed seafloor spreading in … `

<a id="percent"></a>
### Percent, permille and spoken-percent artifact

**Hits** — 3/5 severity, 1,086 impact — 185 Mandarin clips in 44 lessons and 177 English clips in 44 lessons. 362 clips across 46 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[%％‰‱]|百分之\s*[0-9]+|\b[0-9]+(?:\.[0-9]+)?\s+percent\b
```

**Reading and handling (Fixed)**  
“百分之0.0084” → 百分之零点零零八四. “月球被照亮 百分之66” → 月球受光面积占百分之六十六. “5‰” → five per thousand / 千分之五.

**False positives and limits**  
Already verbalized percentages are candidates. Keep percent changes distinct from percentage points and per mille. Some Mandarin sentences need sentence-level agreement.

**Observed examples**

- ` chemistry/solutions ` · zh · ` 49584d2d ` · ` …溶质含量的多少。浓度表示一定量的溶液里含有多少溶质。溶质的质量分数 等于 溶质质量 除以 溶液质量 乘 百分之100。例：100 g 水中溶解 20 g 糖，20 除以 120 约等于 百分之16.7。溶质多的叫浓溶液，溶质少的叫稀溶液。加水可以稀释溶液。有颜色的溶质（如硫酸铜）浓度越大，溶液颜色越深。试一试！ `
- ` astronomy/exoplanets ` · en · ` 4b4dd231 ` · ` … blocks only (1 over 109) squared about 0.0084 percent of the light: 84 parts per million. The transit lasts about 13 hours, once every 365 days. Only a tel… `
- ` math/percents ` · zh · ` ba05a39e ` · ` 百分数线段图把整体对齐到 百分之100 。求 80 的 百分之30 ：把线段平均分成 10 份，每份是 百分之10 ，等于 80 除以 10 等于 8 。三份就是 3 乘 8 等于 24 。 `
- ` biology/tonicity-labs ` · en · ` 30c6b2d9 ` · ` …2 to 38.5 g on Day 5, a change of minus 45.0 percent. In comparison, the simulated trials in distilled water changed by +16.8 percent on average. Reasoning:… `
- ` china/population-resources ` · zh · ` fb37ddbc ` · ` …35 年由地理学家胡焕庸提出，所以也叫“胡焕庸线”。 线的东南侧：面积约占全国 百分之43，人口约占 百分之94；西北侧：面积约占 百分之57，人口只占约 百分之6（约数）。 东南部地势较低平、气候湿润、开发历史悠久、交通便利、经济发达；西北部多高原、山地和荒漠，气候干旱或高寒。 黑河到腾冲画一线，东南人多西北… `

<a id="short_label"></a>
### Very short label or response

**Hits** — 2/5 severity, 928 impact — 202 Mandarin clips in 37 lessons and 262 English clips in 35 lessons. 464 clips across 43 distinct lesson IDs.

**Detection** uses the following logic. Trimmed zh consists of 2–5 HAN plus optional stop. Trimmed en consists of one or two words of at least two LAT letters each, with optional internal apostrophe/hyphen or terminal .?!

**Reading and handling (Context)**  
“细胞质。” → “细胞质，细胞内部的物质。” if a definition belongs in the exercise. “vacuole.” → “The vacuole.” For names, use a brief approved carrier phrase if playback clips the name.

**False positives and limits**  
Short place names and vocabulary cards can already sound fine. Keep answer-only items short and avoid giving away a response.

**Observed examples**

- ` biology/cells-review ` · en · ` d74c362d ` · ` concentration gradient. `
- ` economics/econ-systems ` · zh · ` 7d674437 ` · ` 哈萨克斯坦。 `
- ` georgia/ga-government ` · en · ` 0584bb8d ` · ` Taliaferro County. `
- ` ushistory/us-industrial ` · zh · ` 0602b6ee ` · ` 明尼苏达州。 `
- ` china/ancient-engineering ` · en · ` f89aafba ` · ` Inner Mongolia. `

<a id="number_dash"></a>
### Numeric dash or tilde range

**Hits** — 3/5 severity, 906 impact — 135 Mandarin clips in 46 lessons and 167 English clips in 57 lessons. 302 clips across 68 distinct lesson IDs.

**Detection** uses the following logic. Two standalone numbers joined by -, ‑, –, —, ~ or ～. Exclude alphanumeric ID/date-chain boundaries and spaced ASCII subtraction in math/physics.

**Reading and handling (Context)**  
“5–6 million years” → five to six million years. “2015—2022 年” → 从二零一五年到二零二二年.

**False positives and limits**  
Inspect dates, scorelines, binned values, subtraction, labels and units before using “to”. In BCE, preserve date order and the era.

**Observed examples**

- ` georgia/ga-modern ` · en · ` ec6cbf02 ` · ` …hannel was deepened from 42 to 47 feet (2015–2022) so bigger ships can come in more fully loaded. Fiscal 2021: 5.3 million TEU — the first Southeast or Gulf… `
- ` art/art-history ` · zh · ` 5e0b2188 ` · ` 日本浮世绘。约 1830–1832 年 · 日本江户（今东京）。浮世绘版画：每种颜色刻一块木版，可以印出成千上万份便宜的画。北斋用了一种新进口的颜料——普鲁士蓝。 同一时期的中国：清朝道光年间；1840 年鸦片战争即将爆发。 `
- ` earth/weathering-erosion ` · en · ` 9aa23cd2 ` · ` …iver carved the Grand Canyon over about 5–6 million years; it is about 1.8 km deep, and its walls show layers of rock. Georgia’s Providence Canyon (“Little … `
- ` astronomy/planets-moons ` · zh · ` b4c8272f ` · ` …9 克/厘米 的立方 ）。主环宽约 28 万千米，但大部分只有约 10 米厚，由水冰块组成。“卡西尼号”在 2004–2017 年绕土星运行，最后冲进土星大气，以免将来撞上可能有生命的卫星。土星：光环 + 已知卫星最多（293 颗）。光环不会真的消失：大约每 15 年我们会从侧面看到它们，因为太薄，几乎看不见。 `
- ` china/early-civilization ` · en · ` 49300cd0 ` · ` At Zhoukoudian near Beijing lived Peking Man, about 700,000–200,000 years ago. They made chipped stone tools, used natural fire and lived in groups. `

<a id="caps_emphasis"></a>
### All-caps emphasis in English prose

**Hits** — 2/5 severity, 704 impact — 0 Mandarin clips in 0 lessons and 352 English clips in 34 lessons. 352 clips across 34 distinct lesson IDs.

**Detection** uses the following logic. en includes a standalone all-caps token in the scanner's emphasis list, such as OUTSIDE, BEHIND, ONE or MEAN.

**Reading and handling (Fixed)**  
“the solution OUTSIDE” → “the solution outside”, with stress on outside if desired. “4 hours BEHIND UTC” → “four hours behind UTC”.

**False positives and limits**  
Uppercase on these common words can trigger spelling or exaggerated stress. Confirm the token is an ordinary word before lowercasing.

**Observed examples**

- ` biology/cells-review ` · en · ` c8e600df ` · ` …d isotonic. Always compare the solution OUTSIDE with the inside of the cell. Water follows solute. Hypertonic, water out (animal: shrivels; plant: plasmolys… `
- ` economics/econ-scarcity ` · en · ` 351f618d ` · ` …ent: all workers and machines are used. INSIDE equals inefficient: some resources sit idle (unemployment, closed factories). OUTSIDE equals unattainable wit… `
- ` geography/time-zones ` · en · ` 02f0494e ` · ` ….7°W, Arctic Ocean This zone is 7 hours BEHIND UTC (west of the prime meridian). “Sun time” changes 4 minutes for every 1° of longitude. Zone clocks jump in… `
- ` art/art-history ` · en · ` c98a3ce6 ` · ` Interpret. What does it MEAN? What mood or message? Use clues from the work AND its time and place. There can be more than one good interpretation — if you … `
- ` astronomy/tides ` · en · ` 6c27884a ` · ` …away from the Moon, the water is pulled LESS than Earth’s center. Earth gets pulled toward the Moon a little more than this water, so the water is left behi… `

<a id="han_length"></a>
### Dense Mandarin request

**Hits** — 5/5 severity, 675 impact — 135 Mandarin clips in 32 lessons and 0 English clips in 0 lessons. 135 clips across 32 distinct lesson IDs.

**Detection** uses the following logic. lang == zh and count of characters in HAN > 150.

**Reading and handling (Fixed)**  
Apply the same sentence-aware chunking as for long requests. E.g. end a chunk after “水星（西南二度）、土星（北十一度）。” then start “这张星图上有约五千颗真实恒星。”

**False positives and limits**  
A strict Han count is a diagnostic subset of the 150-character Mandarin rule. Do not add the counts together.

**Observed examples**

- ` astronomy/galaxies ` · zh · ` fae6ffb8 ` · ` 旋臂。新恒星诞生的地方。明亮的旋臂从棒的两端向外盘旋，最大的两条是英仙臂和盾牌、半人马臂。旋臂里有丰富的气体和尘埃，所以新恒星在这里形成；炽热的年轻蓝色恒星和粉红色发光星云让旋臂格外明亮。旋臂就像“交通堵塞”：恒星在绕中心运行时会进入旋臂，又离开旋臂。银河系的盘直径约 10 万光年，厚度却只有约 1000 光年… `
- ` biology/diffusion ` · zh · ` 3c3fc3be ` · ` 组织细胞：养料进，废物出。血液与细胞之间的扩散。细胞时时刻刻都在利用氧气和葡萄糖进行呼吸作用（在线粒体里），释放能量。因为不断被用掉，细胞里氧气和养料的浓度比周围血液“低”，所以它们扩散进入细胞。精选视频里有这个过程的示意图。呼吸作用产生二氧化碳和其他废物，细胞里它们的浓度比血液“高”，所以它们扩散出细胞，进入… `
- ` china/prc-founding ` · zh · ` d5a472d3 ` · ` 中华人民共和国成立。1949年10月1日。1949年9月，中国人民政治协商会议第一届全体会议在北平召开，通过了起临时宪法作用的《共同纲领》，选举毛泽东为中央人民政府主席。会议决定：以五星红旗为国旗，以《义勇军进行曲》为代国歌，改北平为北京并定为首都，采用公元纪年。1949年10月1日，开国大典在天安门广场隆重举… `
- ` economics/econ-systems ` · zh · ` 47e87f8d ` · ` 计划经济（指令型经济）。由中央政府决定。 生产什么？ 政府计划规定生产什么。怎样生产？ 计划者分配工厂、工人和生产指标。为谁生产？ 由政府决定谁得到什么（常用配给）。政府拥有或控制大部分土地、工厂和资源。 优点：能迅速集中大量资源实现目标（重工业、水坝、铁路）。 缺点：计划者很难知道千百万人想要什么——容易出现… `
- ` ela/central-idea ` · zh · ` f0c7f057 ` · ` 蜜蜂做着地球上最重要的工作之一：帮助我们种出粮食。 蜜蜂吸花蜜时，花粉粘在它毛茸茸的身上，又蹭到下一朵花上。 被带走的花粉让植物结出果实和种子。 苹果、杏仁、蓝莓和许多其他作物都离不开蜜蜂的造访。 蜂巢里，一只蜂王一天能产下 1500 多枚卵。 年轻的工蜂清洁巢房、喂养幼虫，年长一些的筑蜡、守门，最年长的飞出去… `

<a id="math_variable"></a>
### Algebraic letters and juxtapositions

**Hits** — 3/5 severity, 600 impact — 97 Mandarin clips in 35 lessons and 103 English clips in 38 lessons. 200 clips across 39 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9.])(?:[0-9]+\s*[xy](?![A-Za-z0-9])|(?:mx|kx|bh|lw|lh|wh|xy)(?![A-Za-z0-9])|[A-Za-z]\s*(?:加|减|乘|除以|等于|plus\b|minus\b|times\b|equals\b))
```

**Reading and handling (Context)**  
“y 等于 mx 加 b” → y 等于 m 乘以 x，再加 b. “3x plus 6” → three times x plus six.

**False positives and limits**  
Some letter strings are units, labels or acronyms. Equality can be used as a mnemonic, especially outside mathematics.

**Observed examples**

- ` astronomy/kepler-laws ` · en · ` 93f80b10 ` · ` …uared about a cubed . Example: Jupiter, a equals 5.2 AU: a cubed equals 141, so T equals the square root of 141 about 11.9 years. Newton showed the full rul… `
- ` chemistry/density ` · zh · ` 0f810a4a ` · ` 密度。单位体积的质量。密度 等于 质量 除以 体积（ρ 等于 m 除以 V），常用单位 g/ 立方厘米 （与 g/mL 相同）。密度表示物质有多“紧密”——每立方厘米里装了多少质量。密度是物质的物理性质：每种纯净物都有自己的密度，可以用来鉴别物质。把物体切成两半，质量和体积都减半，所以密度不变。 `
- ` cs/cs-data-crypto ` · en · ` e522de05 ` · ` …ives a different shift for each letter: C equals 2, O equals 14, D equals 3, E equals 4…. The same letter can turn into different letters, which hides the l… `
- ` math/angles ` · zh · ` d7e805b9 ` · ` 用起来：一个三角形有两个角是 47 度 和 68 度 。第三个角 x 等于 180 度 - 47 度 - 68 度 等于 65 度 。 `
- ` music/music-pitch ` · en · ` 75d56b2f ` · ` …tes. Count letter names, including both ends: C to G equals C D E F G equals a 5th. Small whole-number frequency ratios sound smooth: octave 2:1, fifth 3:2. `

<a id="arrow_source_gap"></a>
### Arrow removed between display and narration

**Hits** — 3/5 severity, 567 impact — 86 Mandarin clips in 56 lessons and 103 English clips in 65 lessons. 189 clips across 68 distinct lesson IDs.

**Detection** uses the following logic. Count tokens matching '[←→↔↑↓↗↘⇒⇌⇄⟶⟷➜]|(?:<=>|->|<-|=>)' in the clip's display text and its send. Flag if send has fewer. Align the strings to choose an excerpt near a removed arrow.

**Reading and handling (Context)**  
“2 water molecules, 2 H2 + 1 O2” → two water molecules split to form two hydrogen molecules and one oxygen molecule. “A, D, B, E…” in a letter-mapping exercise → A maps to D, B maps to E, and so on.

**False positives and limits**  
Some arrows were safely replaced by a sentence or natural pause. The difference counts removals, and a reviewer decides whether a relation or sequence must be restored.

**Observed examples**

- ` chemistry/reactions ` · en · ` eb0314ac ` · ` …e of hydrogen burning. 2 water molecules, 2 H2 + 1 O2. Count: 4 H and 2 O on each side. Mass: 36 u, 36 u. One reactant breaking into simpler substances is c… `
- ` biology/food-webs ` · zh · ` 7188d0f6 ` · ` 生产者。自己制造有机物（第 1 营养级）。植物、藻类和一些细菌是生产者。光合作用：二氧化碳 + 水 —（光能），有机物（葡萄糖）+ 氧气。生产者位于每座能量金字塔的最底层，储存的能量最多。模型中的生产者：草、树和野花。 `
- ` cs/cs-data-crypto ` · en · ` 43aa993e ` · ` …the same number of places: with key 3, A, D, B, E… X, A. Julius Caesar reportedly used a shift of 3 for military messages. There are only 25 useful keys — a… `
- ` biology/cells-review ` · zh · ` c3d06dfb ` · ` 高渗、低渗与等渗。永远拿细胞“外面”的溶液和细胞里面比。水往溶质多的地方流。 高渗，水流出（动物细胞皱缩；植物细胞质壁分离）。低渗，水流进（动物细胞胀大/胀破；植物细胞膨胀饱满）。 等渗，没有净移动（对血细胞来说是 百分之0.9 的生理盐水）。 `
- ` chemistry/atoms ` · en · ` c18423c8 ` · ` …al protons and electrons. Lose electrons, more protons than electrons, positive ion (cation), e.g. Na⁺. Gain electrons, more electrons than protons, negativ… `

<a id="ordinal"></a>
### Numeric ordinal and rank

**Hits** — 2/5 severity, 560 impact — 158 Mandarin clips in 21 lessons and 122 English clips in 24 lessons. 280 clips across 37 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])[0-9]+(?:st|nd|rd|th)(?![A-Za-z0-9])|第\s*[0-9]+
```

**Reading and handling (Fixed)**  
“5th” → fifth. “第 48 名” → 第四十八名. In a date, use the chosen date-reading style.

**False positives and limits**  
Some ordinals are product or military unit names. Expanding digits is safe inside a known ordinal field. Preserve the name and context.

**Observed examples**

- ` astronomy/moon-phases ` · zh · ` 0080fb59 ` · ` 满月（望）。地球位于太阳和月球之间。被照亮的一半完全朝向地球，我们看到一个完整的圆盘（约第 15 天）。它在日落时升起、日出时落下，整夜都能看到。地球的影子通常照不到月球，因为月球轨道倾斜约 5 度 。满月时，太阳和月亮分别在天空的两边。 `
- ` china/new-era ` · en · ` 1779592c ` · ` …oal. By the middle of the century — the 100th birthday of the People’s Republic in 2049 — build China into a great modern socialist country that is prospero… `
- ` georgia/ga-20th ` · zh · ` 2acd858f ` · ` 惠勒营（梅肯）。第 31“迪克西”师驻地。第 31“迪克西”师在这里受训，其中有 1.2 万多名佐治亚人。 二战时营地重新开放用于训练。 `
- ` ushistory/us-civilrights ` · en · ` c35d33f0 ` · ` …red. President Eisenhower sent soldiers of the 101st Airborne Division to escort the students — the federal government enforcing the Supreme Court’s ruling. `
- ` yuwen/yw-argumentative ` · zh · ` 3a2dad39 ` · ` …持，还能让人在失败中找到出路。屠呦呦和她的团队筛选了两千多个中药方，经历了一次又一次失败，终于在第191号样品中看到了青蒿提取物的显著效果；2015年，她获得了诺贝尔生理学或医学奖。反过来看，那些“三天打鱼，两天晒网”的人，往往一事无成。所以，无论学习还是做事，我们都要坚持到底，才能把平凡的努力变成不凡的成绩。 `

<a id="area_volume_unit"></a>
### Squared/cubed unit or malformed unit

**Hits** — 4/5 severity, 524 impact — 75 Mandarin clips in 15 lessons and 56 English clips in 18 lessons. 131 clips across 19 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[0-9]\s*(?:km|cm|mm|m|ft)[²³23](?![0-9])|(?:厘米|千米|米|英尺)\s*的\s*(?:平方|立方)|(?:km|cm|m|ft)\s*\^\s*[23]\b|\b(?:square|cubic) (?:meters?|centimeters?|kilometers?|feet)\b|(?:平方|立方)(?:毫米|厘米|千米|公里|米))
```

**Reading and handling (Fixed)**  
“克/厘米 的立方” → 每立方厘米多少克, with the measured value supplied. “10 cm²” → ten square centimeters / 十平方厘米.

**False positives and limits**  
Common fully verbalized units are included. Do not force a unit interpretation in algebra or in an object identifier.

**Observed examples**

- ` astronomy/planets-moons ` · zh · ` b4c8272f ` · ` 土星。气态巨行星。它的密度比水还小（0.69 克/厘米 的立方 ）。主环宽约 28 万千米，但大部分只有约 10 米厚，由水冰块组成。“卡西尼号”在 2004–2017 年绕土星运行，最后冲进土星大气，以免将来撞上可能有生命的卫星。土星：光环 + 已知卫星最多（293 颗）。光环不会真的消失：大约每 15 年我… `
- ` math/circles ` · en · ` bb064d14 ` · ` … pizza. The crust is C equals pi times 30 is about 94.2 cm. For area use the radius, 15 cm: A equals pi times 15 squared is about 706.9 square centimeters . `
- ` earth/earth-layers ` · zh · ` 22836085 ` · ` 内核。位于中心的铁镍固态球体。一个半径约 1220 千米的固态球体，大小约为月球的 百分之70。温度约 5200 摄氏度 ，和太阳表面差不多热。它之所以是固态，是因为压力约为海平面气压的 360 万倍。密度最大的一层：约 13 克/厘米 的立方 ，是地壳岩石的 4 倍多。 `
- ` chemistry/density ` · en · ` 0c5da94b ` · ` Ping-pong ball. 0.08 g/ cubic centimeters . It floats on top of the Rubbing alcohol, with about 10 percent of it under the surface. `
- ` china/population-resources ` · zh · ` 0131e620 ` · ` 云南省。 简称：滇/云 · 约 4721 万人。 面积：约 39.41 万平方千米。 人口密度：约 120 人/平方千米（34 个省级行政区中第 27 位）。 黑河、腾冲线从本省（区）穿过。 低于全国平均人口密度（约 147 人/平方千米）。 `

<a id="signed_numbers"></a>
### Raw signed number

**Hits** — 4/5 severity, 520 impact — 67 Mandarin clips in 4 lessons and 63 English clips in 8 lessons. 130 clips across 8 distinct lesson IDs.

**Detection** uses the following logic. Plus/minus glyph followed by an Arabic number at a non-ASCII-alphanumeric boundary. Skip preceding numeric/degree operands, leading signs, 碳/铀/开普勒 and trailing numeric dash segments.

**Reading and handling (Context)**  
“太阳高度 -34 度” → 太阳高度为负三十四度. “changed by +16.8 percent” → increased by sixteen point eight percent, where the metric actually increased.

**False positives and limits**  
A sign can encode direction, a signed change, a time-zone offset or an ID. Some binary minus forms require a math parser.

**Observed examples**

- ` astronomy/sky-tonight ` · zh · ` 05a3adf1 ` · ` 纬度 34.0 度 ，2026-11-18 20:15：完全的黑夜（太阳高度 -34 度 ）。月球被照亮 百分之65，在南方 50 度 高。地平线以上的行星：土星（东南 54 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，整… `
- ` biology/tonicity-labs ` · en · ` 30c6b2d9 ` · ` …ed trials in distilled water changed by +16.8 percent on average. Reasoning: The egg’s membrane is selectively permeable, so water can cross it but the suga… `
- ` chemistry/elements-compounds ` · zh · ` 1a2d5ddf ` · ` 甲烷。化合物 · 纯净物。正四面体形分子。甲烷是天然气的主要成分，用于做饭和取暖。4 个氢原子指向正四面体的 4 个顶点，彼此夹角为 109.5 度 ，尽量互相远离。碳原子通常形成 4 个化学键，所以碳能组成种类极多的分子。没有下标就表示 1 个：CH4 等于 1 个 C + 4 个 H 等于 5 个原子。 `
- ` astronomy/sky-tonight ` · en · ` fed3c817 ` · ` …°, 2026-11-18 at 21:00: full night (Sun -37°). The Moon is 66 percent lit and 71° up in the W. Planets up: Saturn (E 85°). About 5,000 real stars are on thi… `
- ` math/functions ` · zh · ` 5b3f9c32 ` · ` 再看 y 等于 x的平方 。它的输出 0、1、4、9 依次增加 +1、+3、+5：变化率越来越大，所以图像是弯曲的——这是非一次函数（非线性函数）。x 每次增加相同的量，y 的增加量也总相同，才是一次函数。 `

<a id="slash"></a>
### General slash with uncertain meaning

**Hits** — 3/5 severity, 513 impact — 87 Mandarin clips in 28 lessons and 84 English clips in 38 lessons. 171 clips across 40 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[/／\\]
```

**Reading and handling (Context)**  
“鼻/口” → 鼻子或嘴巴. “swells/bursts” → swells and may burst. For measurements, “km/h” → kilometers per hour.

**False positives and limits**  
Also hits URLs, fractions, chemical alternatives, bilingual glosses and duplicate units. Use those specific parses first.

**Observed examples**

- ` astronomy/gravity-orbits ` · zh · ` b801a4f7 ` · ` …横向运动（惯性）和把它拉向行星的引力。从这个高度（约 1100 千米）发射，速度约 7.3 千米/秒时，它会绕地球质量的行星做圆周运动。国际空间站的速度约为 7.7 千米/秒，每 90 分钟绕地球一圈。从这里发射，速度超过约 10.3 千米/秒时，引力就拉不回它了：它会逃逸。太慢，落地；刚好，绕行；太快，逃逸。 `
- ` art/art-history ` · en · ` edca25d9 ` · ` …elaxed, natural pose. Meanwhile in China: the late Spring and Autumn / early Warring States period — Confucius (551–479 BCE) had died a few decades earlier. `
- ` biology/body-systems ` · zh · ` 69b406e9 ` · ` 呼吸系统。吸入氧气，排出二氧化碳。空气的路线：鼻/口，气管，支气管，数以亿计的微小肺泡。在肺泡中，氧气进入血液，二氧化碳离开血液。呼吸运动主要靠膈肌的收缩和舒张。 `
- ` chemistry/density ` · en · ` 0c5da94b ` · ` Ping-pong ball. 0.08 g/ cubic centimeters . It floats on top of the Rubbing alcohol, with about 10 percent of it under the surface. `
- ` china/division-integration ` · zh · ` 13865557 ` · ` 建业/建康（今南京）。吴、东晋和南朝的都城。吴的都城建业，东晋时改称建康。东晋和南朝宋、齐、梁、陈都定都于此，建康成为繁华的商业都会。 `

<a id="proper_names"></a>
### Transliterated or specialized names on a pronunciation watchlist

**Hits** — 3/5 severity, 489 impact — 11 Mandarin clips in 7 lessons and 152 English clips in 42 lessons. 163 clips across 43 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?i:\b(?:Xiongnu|Xianbei|Qomolangma|Qaidam|Qin|Qinghai|Dujiangyan|Wuzhishan|Tsiolkovsky|Pleiades|Oort|Kuiper|Ocmulgee|Chattahoochee|Oconee|Etowah|Yazoo|Keweenaw|Xiaogang|Qufu|Qu Yuan|Zhang Qian|Shanhaiguan|Chicxulub|Aldebaran)\b)|克孜尔|蒭藁增二|乞力马扎罗|基奥尔科夫斯基|齐奥尔科夫斯基|可汗|大宛|月氏|阏氏
```

**Reading and handling (Context)**  
Approve the name-specific pronunciation. E.g. “Kuiper” as KYE-per, “Pleiades” as PLEE-uh-deez, and “大宛” as Dàyuān in the relevant historical passage.

**False positives and limits**  
A proper name may already sound right, and alternative pronunciations can be valid. The explicit watchlist is not a complete name inventory.

**Observed examples**

- ` geography/landforms ` · en · ` c2499e2e ` · ` …ry sediment (sand, silt and mud) and drop it where the water slows down. Nile (longest), Amazon (most water), Yangtze, Mississippi, Chattahoochee (Georgia). `
- ` georgia/ga-government ` · zh · ` aa9fb1f8 ` · ` Chattahoochee 县。 `
- ` astronomy/rocketry ` · en · ` 639c8e48 ` · ` …ded by m_f). Written down by Konstantin Tsiolkovsky in 1903. Δv is the total change in speed a rocket can make. It depends only on exhaust speed and the mas… `
- ` earth/climate ` · zh · ` 0dd5b93a ` · ` 高海拔。越高越冷。海拔每升高 1000 米，气温大约下降 6.5 摄氏度 。所以即使在赤道附近，山顶也可能有积雪（乞力马扎罗山、安第斯山脉）。厄瓜多尔的基多就在赤道上，但海拔 2850 米，四季如春。 `
- ` china/dynasties ` · en · ` 6dd19977 ` · ` Western Han. 202 BCE – 8 CE. Zhang Qian opens the Silk Road. In 138 BCE Zhang Qian (张骞) set off west — and was captured for over ten years before getting ho… `

<a id="durations"></a>
### Compact duration or short time unit

**Hits** — 2/5 severity, 444 impact — 83 Mandarin clips in 8 lessons and 139 English clips in 38 lessons. 222 clips across 38 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[0-9]+\s*(?:小时|分钟|分|秒)\s*[0-9]+\s*(?:分钟|分|秒)|(?<![A-Za-z0-9])(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?\s*(?:h|hr|hrs|min|ms|s)(?![A-Za-z0-9/])|\b[0-9]+\s*(?:hours?|minutes?)\s+[0-9]+\s*(?:minutes?|seconds?)\b|\b[0-9]+\s*(?:a\.m\.|p\.m\.|am\b|pm\b))
```

**Reading and handling (Context)**  
“8 分 20 秒” → 八分二十秒. “24 hours 50 minutes” → twenty-four hours and fifty minutes. “45 min” → forty-five minutes.

**False positives and limits**  
s may be a variable, h a height, and 分 may be a score or angle minute. Some durations are already fluent.

**Observed examples**

- ` astronomy/big-bang ` · en · ` 30ea61f2 ` · ` …un. 150 million km away. Sunlight takes 8 minutes 20 seconds to reach Earth. If the Sun suddenly vanished, we would keep seeing it (and orbiting it) for ove… `
- ` physics/newtons-laws ` · zh · ` b0dddc59 ` · ` 合力（推力）。非平衡力改变运动状态。力是推或拉，单位是牛顿，N。1 N 大约是一个小苹果受到的重力。红色箭头表示推力，只作用 0.5 s，之后合力为零。牛顿第二定律：F 等于 m 乘 a，即 a 等于 F 除以 m。力加倍，加速度也加倍。 `
- ` art/art-history ` · en · ` 0ebe4008 ` · ` … the East Side Gallery. Meanwhile in China: contemporary art was booming; Beijing’s 798 Art District turned old factories into galleries in the early 2000s. `
- ` astronomy/tides ` · zh · ` faf092c9 ` · ` 你的港口。海岸上的一个地点。红色图钉代表海岸上的一个港口，比如美国佐治亚州的萨凡纳。地球自转时，港口在每个“太阴日”（约 24 小时 50 分钟）里依次经过高潮、低潮、高潮、低潮。地球转动时，留意模型下方的“港口水位”条。 `
- ` biology/cells-review ` · en · ` 450c3c36 ` · ` …1665 (cork, named “cells”), Leeuwenhoek 1670s (first living cells), Schleiden 1838 (plants), Schwann 1839 (animals), Virchow 1855 (cells from cells). Better… `

<a id="fraction"></a>
### Fraction glyph or numeric fraction

**Hits** — 4/5 severity, 440 impact — 56 Mandarin clips in 29 lessons and 54 English clips in 26 lessons. 110 clips across 32 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[¼½¾⅐-⅞]|(?<![0-9/])[0-9]+\s*/\s*[0-9]+(?![0-9/])|[0-9]+\s*分之\s*[0-9]+|\b[0-9]+\s+over\s+[0-9]+\b
```

**Reading and handling (Context)**  
“7½ minutes” → seven and a half minutes. “3分之2” → 三分之二. “6 over 36” → six thirty-sixths, or six divided by thirty-six where division is being taught.

**False positives and limits**  
Slash can mark calendar dates, ratios or a unit. Numeric verbal fractions may already work. Preserve whole-number parts and grouping.

**Observed examples**

- ` astronomy/scale-universe ` · zh · ` 557bd85b ` · ` 一个橄榄球场。约 160 米宽。美式橄榄球场连端区长 120 码（110 米），宽 53⅓ 码（49 米）。你就是中间那个小点。滑块每走 1 格，视野就宽 10 倍。走 6 格就宽 100 万倍！ `
- ` astronomy/eclipses ` · en · ` 70161592 ` · ` …otality”. Totality lasts at most about 7½ minutes. When the Moon is far from Earth, the umbra ends before reaching Earth: people see an annular (ring) eclip… `
- ` math/fraction-division ` · zh · ` 378a3dad ` · ` 为什么这样算？把所有东西都用同一个单位—— 3分之1 ——来量。3 是 3分之9 ，一份是 3分之2 。9 里面有几个 2? 3分之9 除以 3分之2 等于 9 除以 2 等于 4又 2分之1 。分母相同，只要把分子相除。 `
- ` math/probability ` · en · ` 1fb4fc80 ` · ` …ikely outcomes. A total of 7 can happen in 6 ways, more than any other total, so P(7) equals 6 over 36 equals 1 over 6 . A total of 2 happens in only 1 way. `
- ` chemistry/atoms ` · zh · ` 21e59502 ` · ` 电子。在原子核外运动、带负电（减1）的粒子。电荷：减1。质量约为质子的 1836分之1，几乎可以忽略。电子分层排布在原子核外的电子层（能级）上。在不带电的原子中，电子数等于质子数。最外层电子（价电子）参与化学反应。 `

<a id="rate"></a>
### Slash unit or density

**Hits** — 4/5 severity, 440 impact — 64 Mandarin clips in 14 lessons and 46 English clips in 20 lessons. 110 clips across 21 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z])(?:km|cm|mm|mi|ft|m|kg|mg|g|N|r|人|次|克|千米|公里|米)\s*[/／]\s*(?:square\s+kilometers?|cubic\s+centimeters?|立方厘米|平方千米|平方公里|厘米\s*的立方|千米|小时|分钟|秒|时|毫升|km|kg|cm[²³23]?|m[²³23]|s|h|min|L|mL)(?![A-Za-z0-9])
```

**Reading and handling (Fixed)**  
“7.7 千米/秒” → 每秒七点七千米. “0.79 g/ cubic centimeters” → zero point seven nine grams per cubic centimeter. “3923 人/平方千米” → 每平方千米三千九百二十三人.

**False positives and limits**  
Use a whitelist of compound units and require quantity/lesson context for ambiguous short units. Preserve dimensions and say “per” for the denominator.

**Observed examples**

- ` astronomy/gravity-orbits ` · zh · ` b801a4f7 ` · ` …横向运动（惯性）和把它拉向行星的引力。从这个高度（约 1100 千米）发射，速度约 7.3 千米/秒时，它会绕地球质量的行星做圆周运动。国际空间站的速度约为 7.7 千米/秒，每 90 分钟绕地球一圈。从这里发射，速度超过约 10.3 千米/秒时，引力就拉不回它了：它会逃逸。太慢，落地；刚好，绕行；太快，逃逸。 `
- ` chemistry/density ` · en · ` f596cdf0 ` · ` Rubbing alcohol (dyed red). 0.79 g/ cubic centimeters . Rubbing (isopropyl) alcohol is about 0.79 g/ cubic centimeters — the least dense liquid here. It wou… `
- ` chemistry/density ` · zh · ` ffba656a ` · ` 洗洁精。1.06 g/ 立方厘米。洗洁精的密度约为 1.06 g/ 立方厘米 ，只比水大一点点。100 mL 的质量约为 106 g。倒的时候要慢，否则会和水层混在一起。 `
- ` earth/earth-layers ` · en · ` 3260c77e ` · ` …m and potassium. Low density (about 2.7 g/ cubic centimeters ), so it rides high and does not sink easily. Some continental rocks are about 4 billion years … `
- ` china/population-resources ` · zh · ` f8c44ff0 ` · ` 上海市。 简称：沪 · 约 2487 万人。 面积：约 0.634 万平方千米。 人口密度：约 3923 人/平方千米（34 个省级行政区中第 3 位）。 位于黑河、腾冲线东南侧（人口稠密的一侧）。 高于全国平均人口密度（约 147 人/平方千米）。 `

<a id="clock_time"></a>
### Clock time with context

**Hits** — 3/5 severity, 405 impact — 72 Mandarin clips in 2 lessons and 63 English clips in 3 lessons. 135 clips across 3 distinct lesson IDs.

**Detection** uses the following logic. 24-hour H:MM or HH:MM[:SS] with colon boundary and local clock cues (date, at/by/from/around, 学校/时间, AM/PM, 上课/下课/起床, or trailing Chinese colon).

**Reading and handling (Fixed)**  
“19:57” → 十九点五十七分 / nineteen fifty-seven. “7:45” → seven forty-five. Preserve a.m./p.m. only when shown or entailed by the selected convention.

**False positives and limits**  
Only numbers with clock cues match. Ambiguous bare colons and UTC offsets are handled elsewhere.

**Observed examples**

- ` astronomy/sky-tonight ` · zh · ` 05a3adf1 ` · ` 纬度 34.0 度 ，2026-11-18 20:15：完全的黑夜（太阳高度 -34 度 ）。月球被照亮 百分之65，在南方 50 度 高。地平线以上的行星：土星（东南 54 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，整… `
- ` ela/argument-writing ` · en · ` 0b0d4bf6 ` · ` …erson could disagree. “School starts at 7:45” is a fact, not a claim. Make it specific: who should do what? “Our school should add a 20-minute recess” beats… `
- ` astronomy/sky-tonight ` · zh · ` 0b4adb07 ` · ` 纬度 34.0 度 ，2026-11-18 20:51：完全的黑夜（太阳高度 -41 度 ）。月球被照亮 百分之65，在西南方 48 度 高。地平线以上的行星：土星（南 56 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，整… `
- ` _shared ` · en · ` 0be9b219 ` · ` …ite Sands Missile Range, New Mexico. At 5:29 a.m. on 16 July 1945, Manhattan Project scientists exploded the first atomic bomb in this New Mexico desert. Th… `
- ` ela/argument-writing ` · zh · ` 76afa73e ` · ` …你希望读者相信或去做的事。论点必须“可以争论”：讲道理的人也可能不同意。“学校 7:45 上课”是事实，不是论点。要具体：谁应该做什么？“我们学校应该增加 20 分钟课间休息”比“课间休息很好”强得多。有力的论点常常带着理由：“……因为学生休息后更专心。”。英文常用开头：“Our school should…”… `

<a id="iso_date"></a>
### ISO calendar date

**Hits** — 3/5 severity, 402 impact — 72 Mandarin clips in 2 lessons and 62 English clips in 2 lessons. 134 clips across 2 distinct lesson IDs.

**Detection** uses the following logic. ASCII-boundary YYYY-MM-DD, validated with date.fromisoformat.

**Reading and handling (Fixed)**  
“2026-11-18” → 二零二六年十一月十八日 / November eighteenth, twenty twenty-six.

**False positives and limits**  
Validated date shape. If a field is an identifier and happens to be a valid date, preserve its identifier reading.

**Observed examples**

- ` astronomy/scale-universe ` · zh · ` c05cfe23 ` · ` 内行星。约 12 个天文单位宽。四颗岩质行星和小行星带都在木星轨道（5.2 天文单位）以内。行星画在它们今天（2026-11-18）真实所在的位置。1 天文单位 等于 日地距离 约等于 1.5 亿千米。光走 1 天文单位要 8 分 20 秒。 `
- ` astronomy/sky-tonight ` · en · ` 021a9f68 ` · ` latitude 34.0°, 2026-11-18 at 18:13: twilight, getting dark (Sun -9°). The Moon is 64 percent lit and 45° up in the SE. Planets up: Saturn (SE 35°). About 5… `
- ` astronomy/sky-tonight ` · zh · ` 05a3adf1 ` · ` 纬度 34.0 度 ，2026-11-18 20:15：完全的黑夜（太阳高度 -34 度 ）。月球被照亮 百分之65，在南方 50 度 高。地平线以上的行星：土星（东南 54 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，整… `
- ` astronomy/scale-universe ` · en · ` 27095eda ` · ` …2 AU). Planets are shown where they really are today: 2026-11-18. 1 AU equals Earth–Sun distance about 150 million km. Light takes 8 min 20 s to cross 1 AU. `
- ` astronomy/sky-tonight ` · zh · ` 0b4adb07 ` · ` 纬度 34.0 度 ，2026-11-18 20:51：完全的黑夜（太阳高度 -41 度 ）。月球被照亮 百分之65，在西南方 48 度 高。地平线以上的行星：土星（南 56 度 ）。 这张星图上有约 5000 颗真实恒星：所有亮于 6 等的星，大约就是在黑暗的乡村用肉眼能看到的数量。 因为地球自西向东自转，整… `

<a id="clock_or_ratio"></a>
### Unresolved numeric colon

**Hits** — 2/5 severity, 308 impact — 84 Mandarin clips in 11 lessons and 70 English clips in 10 lessons. 154 clips across 13 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![0-9])(?:[0-9]{1,3}[ \t]*[:：][ \t]*[0-9]+)(?![0-9])
```

**Reading and handling (Context)**  
“7:45” can be seven forty-five in a school schedule. “2 : 1 ratio” is a two-to-one ratio. In “Fiscal 2021: 5.3 million” pause at the label boundary.

**False positives and limits**  
Broad fallback includes known clocks, ratios, offsets and a few label/quantity boundaries. Use higher-specificity matches first.

**Observed examples**

- ` math/percents ` · zh · ` 0efc8661 ` · ` 再给 45 美元加 百分之8 的销售税。现在 45 成了新的 百分之100 ，线段增长到 百分之108 ： 45 乘 1.08 等于 48.60 美元。增加 p ，就是乘 (1 加 p) 。 `
- ` astronomy/planets-moons ` · en · ` 5ed9a014 ` · ` …opa and Ganymede tug on each other in a 1 : 2 : 4 rhythm (an orbital resonance). Those regular tugs keep their orbits slightly oval, so Jupiter’s tides flex… `
- ` chemistry/elements-compounds ` · zh · ` 4a1e8ea8 ` · ` …学键结合在一起，所以水是化合物。水分子是弯曲的：H–O–H 键角约为 104.5 度 。每个水分子中 H 与 O 的原子个数比都是 2 : 1。化合物的组成总是固定的。水的性质和组成它的元素完全不同：氢气能燃烧，氧气能助燃，水却能灭火！右下角的小数字（下标）只表示它前面那种原子的个数：H2O 等于 H、H、O。 `
- ` ela/argument-writing ` · en · ` 0b0d4bf6 ` · ` …erson could disagree. “School starts at 7:45” is a fact, not a claim. Make it specific: who should do what? “Our school should add a 20-minute recess” beats… `
- ` geography/time-zones ` · zh · ` fac5d991 ` · ` 实际的时区界线。实际界线由各国政府划定。实际的时区界线会沿着国界、州界弯曲。中国东西跨约 5 个时区，但全国统一使用北京时间（UTC+8）。印度使用 UTC+5:30，是半小时时区。佐治亚州实行夏令时：夏天把时钟拨快 1 小时（UTC减4）。 `

<a id="dotted_abbrev"></a>
### Dotted abbreviation or shortened title

**Hits** — 3/5 severity, 282 impact — 2 Mandarin clips in 2 lessons and 92 English clips in 26 lessons. 94 clips across 26 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:(?<![A-Za-z])(?:[A-Za-z]\.){2,}|\b(?:Dr|Mr|Mrs|Ms|St|Mt|Jr|Sr|vs|etc|c)\.)
```

**Reading and handling (Context)**  
“e.g.” → “for example”. “St. John’s” → Saint John’s. “Washington, D.C.” → Washington, D C. “R.E.M.” → R E M.

**False positives and limits**  
St. can mean Saint or Street. c. can signal circa. Protect these periods before sentence splitting.

**Observed examples**

- ` art/art-color ` · en · ` 56afbc0c ` · ` …nd harmonious. Three hues side by side, e.g. yellow, yellow-green, green. Found everywhere in nature: autumn leaves, sunsets, oceans. Analogous equals a fam… `
- ` _shared ` · zh · ` 3aa96199 ` · ` 雅典（佐治亚州）。雅典城是佐治亚大学所在地，大学1801年开始上课；创办者以古代著名的学术中心雅典为这座城镇命名。今天，这里还以音乐闻名——R.E.M.等乐队就是从这里起步的。 `
- ` astronomy/space-exploration ` · en · ` e10ad68a ` · ` …ush, and spent stages fall into the sea. In the U.S., Cape Canaveral in Florida is a famous launch site; China uses sites such as Wenchang on Hainan Island. `
- ` ushistory/us-civilrights ` · zh · ` 60ec596f ` · ` …帕克斯（Rosa Parks）拒绝把公交车座位让给一名白人男子，因而被捕。黑人市民381天不坐公交车：他们步行、搭车，还组织了拼车系统。年轻的牧师马丁·路德·金（Martin Luther King Jr.）领导了蒙哥马利进步协会。1956年，最高法院裁定公交车隔离违宪；12月，蒙哥马利的公交车取消了种族隔离。 `
- ` biology/animals ` · en · ` 0bd95b05 ` · ` Sponges. e.g. tube sponge, bath sponge. The simplest animals: no tissues, organs, head or symmetry. Water flows in through thousands of pores; cells filter … `

<a id="verbal_glue"></a>
### Flattened sentence connectors around normalized math

**Hits** — 3/5 severity, 279 impact — 56 Mandarin clips in 36 lessons and 37 English clips in 27 lessons. 93 clips across 44 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[。.!?]\s*|^)(?:[A-Za-z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF ]{1,20})(?:\s等于\s|\sequals\s)(?=[A-Za-z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF][A-Za-z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF ]{2,}(?:\s*[+,;，。]))
```

**Reading and handling (Context)**  
“岩石圈 等于 地壳 + 上地幔顶部” → 岩石圈由地壳和上地幔顶部组成. When “equals” introduces a mnemonic or title, use a natural connective that conveys the same relationship.

**False positives and limits**  
Includes literal equations and some partly rewritten prose. Do not replace “equals” in a formal equality unless the replacement preserves it.

**Observed examples**

- ` math/circles ` · zh · ` bf08acf9 ` · ` 长方形的面积 等于 长 乘 宽 等于 派 r 乘 r 。它正是由圆的各块拼成的，所以圆的面积是 A 等于 派 r的平方 `
- ` astronomy/small-bodies ` · en · ` c35ed14b ` · ` …me satellites, and will be visible without a telescope. It will not hit us. Planetary defense equals find them early, track them, and (if needed) push them. `
- ` ela/grammar-sentences ` · zh · ` a3ddf46d ` · ` …or, but, or, yet, so（并列连词）。或者用分号连接：“The lights went out; we lit candles.”。人教版英语叫它“并列句”。FANBOYS 等于 for, and, nor, but, or, yet, so 的首字母。光用逗号不能连接两个句子，那叫逗号粘连句。 `
- ` physics/energy ` · en · ` 24c325d1 ` · ` …ation of energy. The total never changes. Mechanical energy equals KE + PE. Law of conservation of energy: energy cannot be created or destroyed, only trans… `
- ` biology/microorganisms ` · zh · ` c4a447a1 ` · ` 尾鞘。注射 DNA 的“注射器”。噬菌体（“吃细菌的”）只攻击细菌。尾鞘像注射器一样收缩，把 DNA 注入细菌。噬菌体的尾巴 等于 微型注射器。 `

<a id="math_group"></a>
### Implicit multiplication, subscript or function grouping

**Hits** — 4/5 severity, 260 impact — 24 Mandarin clips in 12 lessons and 41 English clips in 26 lessons. 65 clips across 28 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[₀-₉ₐₑₒₓ]|(?<![A-Za-z0-9])[A-Za-z]_[A-Za-z0-9]+|\b(?:ln|log|sin|cos|tan)\s*[(（]|(?<![A-Za-z0-9])[0-9]+\s*[(（]\s*[0-9a-z]|(?<![A-Za-z0-9])[a-z][0-9](?![A-Za-z0-9])|[A-Za-z]\([\s\S]{1,20}?[)）])
```

**Reading and handling (Context)**  
“2(3x 加 1)” → 二乘以括号内三乘以 x 加一. “ln(m0 除以 m_f)” → the natural logarithm of the ratio of initial mass to final mass. “P(7)” → the probability of rolling a total of seven when that is the given event.

**False positives and limits**  
Parentheses can be coordinates, ordinary asides or a function call. Subscript-looking strings can be model numbers.

**Observed examples**

- ` astronomy/rocketry ` · en · ` 639c8e48 ` · ` …ation. Δv equals exhaust velocity times ln(m0 divided by m_f). Written down by Konstantin Tsiolkovsky in 1903. Δv is the total change in speed a rocket can … `
- ` astronomy/rocketry ` · zh · ` 8ce9900c ` · ` 火箭方程。Δv 等于 喷气速度 乘 ln(m0 除以 m_f)。康斯坦丁·齐奥尔科夫斯基在 1903 年写下了这个方程。Δv 是火箭能产生的总速度变化，只取决于喷气速度和质量比：满载质量 m0 除以 燃料烧完后的质量 m_f。进入近地轨道需要约 9.4 千米/秒的 Δv（7.8 千米/秒的轨道速度，加上约 1.… `
- ` math/coordinate-plane ` · en · ` 3297df5d ` · ` Worked example: add C(3, negative1) and D(negative5, negative1) to make a rectangle. Counting down, BC equals 3 plus 1 equals 4 . So the perimeter is 2(8 pl… `
- ` math/expressions ` · zh · ` e4af34a8 ` · ` 例题：化简 2(3x 加 1) 加 4x 。先用分配律展开： 6x 加 2 加 4x ；再合并同类项： 10x 加 2 。用 x 等于 1 检验：两种写法都等于 12 。 `
- ` cs/cs-algorithms ` · en · ` 2874087b ` · ` …in its place. Repeat passes until a pass makes no swaps. Worst case for n items: n(n minus 1)/2 comparisons — 10 items equals 45, 1,000 items about 500,000. `

<a id="diacritics"></a>
### Latin name or word with diacritics

**Hits** — 2/5 severity, 228 impact — 4 Mandarin clips in 3 lessons and 110 English clips in 31 lessons. 114 clips across 33 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[À-ÖØ-öø-ÿĀ-žǍ-ǔǖ-ǜʻ]
```

**Reading and handling (Context)**  
“Reykjavík” → use the approved pronunciation of Reykjavík. “Guð…” and transliterated names need a pronunciation lexicon, with language and named sense when applicable.

**False positives and limits**  
Some English loans already read well. This overlaps pinyin and excludes transliterations spelled entirely in ASCII.

**Observed examples**

- ` art/art-history ` · en · ` 1212115c ` · ` Post-Impressionism. 1889, Saint-Rémy, France. Color and brushstroke show feeling, not just what the eye sees. Van Gogh’s sky swirls; Seurat built pictures f… `
- ` astronomy/small-bodies ` · zh · ` 752310c5 ` · ` …间的小行星带（那里太暖，冰保存不下来）。 彗星：冰 + 尘埃，来自寒冷的柯伊伯带 dài和奥尔特云。 流星体：从小行星和彗星上掉下来的小碎块。 记忆小窍门 里面是岩石，外面是冰：约 3 天文单位处的“雪线”把年轻的太阳系分成了两部分。 容易混淆：“流星”不是星星：它是在你头顶约 100 千米高处燃烧的一粒尘埃。 `
- ` biology/habitat-niche ` · en · ` e22bd8b9 ` · ` Ecological factors (生态因素, shēngtài yīnsù) affect how and where organisms live. Sunlight, water, and temperature are abiotic factors. The grass rabbits eat, … `
- ` _shared ` · zh · ` 9b2f1b9c ` · ` 龟兹。今天：新疆库车。龟兹（读 cí）以音乐舞蹈闻名，克孜尔石窟的佛教壁画也很有名。 `
- ` chemistry/atoms ` · en · ` 9825665f ` · ` Schrödinger and others. Electron-cloud (quantum) model. Electrons do not follow exact paths. We can only say where they are likely to be: a fuzzy electron c… `

<a id="chem_formula"></a>
### Chemical formula and coefficients

**Hits** — 4/5 severity, 216 impact — 19 Mandarin clips in 6 lessons and 35 English clips in 11 lessons. 54 clips across 11 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:(?:H[2₂]O[2₂]?|CO[2₂]|O[2₂]|N[2₂]|H[2₂]|Cl[2₂]|CH[4₄]|NH[3₃]|NaCl|HCl|NaOH|H[2₂]SO[4₄]|CaCO[3₃]|NaHCO[3₃]|C[6₆]H(?:12|₁₂)O[6₆]|Fe[2₂]O[3₃])|(?:[A-Z][a-z]?[0-9₀-₉]*){2,}[₀-₉]+)(?![A-Za-z0-9])
```

**Reading and handling (Context)**  
H2O → water / 水 when naming the substance, or “H two O” to teach notation. “2 H2 + 1 O2” → two hydrogen molecules react with one oxygen molecule when describing that step.

**False positives and limits**  
A token can be an ID. Distinguish coefficients, subscripts and names. The formula list covers observed common compounds and future canonical patterns.

**Observed examples**

- ` biology/photosynthesis ` · en · ` 739fb8f8 ` · ` Glucose (C6H12O6). Sugar that stores chemical energy. Glucose is built in the chloroplast and has 6 carbon atoms. Plants burn it for energy, use it to build… `
- ` chemistry/acids-bases ` · zh · ` 3a098f1f ` · ` 电池酸液。pH 0.8。强酸性。汽车电池里装的是硫酸（H2SO4）。它有强腐蚀性，能灼伤皮肤、在衣服上烧出洞。 `
- ` astronomy/planets-moons ` · en · ` 2304def3 ` · ` …t enough to melt lead. Venus: Earth-sized, but a greenhouse oven. Venus is not hot because it is close to the Sun; it is hot because its CO2 air traps heat. `
- ` chemistry/elements-compounds ` · zh · ` dc515e7b ` · ` …钠离子（Na⁺） 和氯离子（Cl⁻） 互相吸引，按立方体形状规则地重复排列，叫做晶格。食盐中没有单独的 NaCl 分子。化学式表示的是个数比：每 1 个 Na 对应 1 个 Cl。钠是一种遇水会剧烈反应的软金属，氯气是一种有毒气体。它们结合后，却成了我们吃的食盐！盐粒是小立方体，因为离子就是一层层堆成立方体的。 `
- ` earth/natural-resources ` · en · ` 37aeb9ca ` · ` …through photosynthesis, so biomass is stored solar energy. It is renewable only if we replant as fast as we use it. Burning it still releases CO2 and smoke. `

<a id="pinyin"></a>
### Pinyin, phonetic notation or detached reading hint

**Hits** — 4/5 severity, 188 impact — 4 Mandarin clips in 3 lessons and 43 English clips in 18 lessons. 47 clips across 20 distinct lesson IDs.

**Detection** uses the following logic. Pinyin-specific macron/caron vowels, selected observed grave/acute pinyin tokens, IPA block U+0250–02AF, or a combining diacritic U+0300–036F.

**Reading and handling (Context)**  
“龟兹（读 cí）” → pronounce 龟兹 as Qiūcí, then omit the inline hint unless teaching it. “高尔基体’ěrjītǐ” → speak 高尔基体 smoothly. “行省 xíngshěng” → pronounce xíngshěng intentionally in a Mandarin segment.

**False positives and limits**  
Some Latin diacritics belong to foreign names. A detached hint can be a fragment of a full reading. Preserve intentional pinyin instruction.

**Observed examples**

- ` china/dynasties ` · en · ` 2d0664a6 ` · ` …ts huge empire into provinces (行省 xíngshěng). It was the start of China’s province system — the “provinces” on today’s map come from it. Kublai Khan named h… `
- ` biology/cell-city ` · zh · ` 066a7390 ` · ` 高尔基体’ěrjītǐ对蛋白质进行加工、分类和包装，装进囊泡运到需要的地方。 `
- ` music/music-instruments ` · en · ` 1023c07b ` · ` … energy of festivals and opera. 堂鼓 tánggǔ: a barrel drum played with two sticks. The gong 锣 and cymbals 镲 add crashes; in Peking opera the percussion sectio… `
- ` _shared ` · zh · ` 9b2f1b9c ` · ` 龟兹。今天：新疆库车。龟兹（读 cí）以音乐舞蹈闻名，克孜尔石窟的佛教壁画也很有名。 `
- ` politics/constitution ` · en · ` f1f829f4 ` · ` …ution when they take office (宪法宣誓, xiànfǎ xuānshì). The oath begins: “I pledge to be loyal to the Constitution of the People’s Republic of China, safeguard … `

<a id="direction_tokens"></a>
### Compass abbreviation without a degree suffix

**Hits** — 3/5 severity, 186 impact — 0 Mandarin clips in 0 lessons and 62 English clips in 2 lessons. 62 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z])(?:in the|to the|from the|[Uu]p in the)\s+(?:NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW|NE|NW|SE|SW|N|E|S|W)\b|(?<![A-Za-z])(?:NNE|ENE|ESE|SSE|SSW|WSW|WNW|NNW|NE|NW|SE|SW|N|E|S|W)\s+[0-9]{1,3}°
```

**Reading and handling (Fixed)**  
“up in the W” → above the western horizon. “NW 33°” → northwest, thirty-three degrees above the horizon if the value expresses altitude.

**False positives and limits**  
N can be a force unit and W can be a unit or a name initial. Apply direction expansions in the sky/compass template.

**Observed examples**

- ` astronomy/sky-tonight ` · en · ` 021a9f68 ` · ` …9°). The Moon is 64 percent lit and 45° up in the SE. Planets up: Saturn (SE 35°). About 5,000 real stars are on this map: every star down to magnitude 6, r… `
- ` physics/magnetism ` · en · ` eaa918c2 ` · ` …come out of the N pole and curve around to the S pole. A freely hanging magnet turns so its N pole points roughly north. That is why it is called the “north… `
- ` astronomy/sky-tonight ` · en · ` 02ecc68e ` · ` …1°). The Moon is 66 percent lit and 65° up in the SW. Planets up: Saturn (SE 78°). About 5,000 real stars are on this map: every star down to magnitude 6, r… `
- ` astronomy/sky-tonight ` · en · ` 05dfa1ed ` · ` …1°). The Moon is 66 percent lit and 37° up in the SW. Planets up: Saturn (S 46°). About 5,000 real stars are on this map: every star down to magnitude 6, ro… `
- ` astronomy/sky-tonight ` · en · ` 139100f5 ` · ` …3°). The Moon is 69 percent lit and 62° up in the SW. Planets up: Saturn (SW 49°). About 5,000 real stars are on this map: every star down to magnitude 6, r… `

<a id="coordinates"></a>
### Ordered pair, interval or point prime

**Hits** — 4/5 severity, 184 impact — 23 Mandarin clips in 7 lessons and 23 English clips in 7 lessons. 46 clips across 7 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[（(\[]\s*(?:negative\s*|负\s*|[-−]\s*)?(?:[0-9]+(?:\.[0-9]+)?|[a-z])\s*[,，]\s*(?:negative\s*|负\s*|[-−]\s*)?(?:[0-9]+(?:\.[0-9]+)?|[a-z])\s*[)）\]]|(?<![A-Za-z0-9])[A-Z]['′]\s*[(（]
```

**Reading and handling (Context)**  
“B'(负1, 4)” → B 撇，坐标是负一、四. “(3, negative2)” → the point with x-coordinate three and y-coordinate negative two.

**False positives and limits**  
Parentheses may mark an open interval, a tuple or an aside. Preserve open and closed endpoints when the text describes an interval.

**Observed examples**

- ` math/scatter-plots ` · zh · ` 02b9956b ` · ` 把每一对数变成一个点。时长画在横轴（ x 轴）上，成绩画在纵轴（ y 轴）上，所以 (0.5, 55) 这名学生落在这里。12 名学生都这样画，就得到一张散点图。 `
- ` math/coordinate-plane ` · en · ` 3297df5d ` · ` Worked example: add C(3, negative1) and D(negative5, negative1) to make a rectangle. Counting down, BC equals 3 plus 1 equals 4 . So the perimeter is 2(8 pl… `
- ` math/functions ` · zh · ` d1f1ac2c ` · ` 把机器的每一组（输入，输出）画成点 (x, y) 。它们排成一条直线！中间的输入也一样： 2.5 mapsto 6 也落在这条直线上。图像就是整个函数的“画像”。 `
- ` math/proportional ` · en · ` 1525fb81 ` · ` …0 hours she has walked 0 km, so the line passes through the origin (0, 0) . A proportional relationship always graphs as a straight line through the origin. `
- ` math/slope ` · zh · ` 50e4e60d ` · ` 例题：求经过 (1, 3) 和 (3, 7) 的直线。斜率： m 等于 3 减 1分之7 减 3 等于 2分之4 等于 2 。代入一个点： 3 等于 2 乘 1 加 b ，得 b 等于 1 。所以直线是 y 等于 2x 加 1 。 `

<a id="single_character"></a>
### Single letter or Han character

**Hits** — 4/5 severity, 172 impact — 43 Mandarin clips in 4 lessons and 0 English clips in 0 lessons. 43 clips across 4 distinct lesson IDs.

**Detection** uses the following logic. After optional outer whitespace, exactly one HAN or LAT character and optionally one terminal 。.!！?？.

**Reading and handling (Context)**  
马 → 马，马匹的马. 骤 → 骤，步骤的骤. For a letter card use “the letter A” or “字母 A”.

**False positives and limits**  
A model may pronounce some single characters correctly. Use the lesson’s intended word or tone and preserve quiz design where the character is the prompt.

**Observed examples**

- ` yuwen/yw-hanzi ` · zh · ` 4f373ead ` · ` 书 `
- ` yuwen/yw-song-ci ` · zh · ` 0b4b4aa1 ` · ` 客 `
- ` yuwen/yw-wenyan-basics ` · zh · ` 0c1b7ac7 ` · ` 骤 `
- ` yuwen/yw-wenyan-classics ` · zh · ` 9845dc98 ` · ` 壑 `
- ` yuwen/yw-hanzi ` · zh · ` 122bd9a6 ` · ` 睛 `

<a id="ellipsis"></a>
### Ellipsis or continuation

**Hits** — 2/5 severity, 150 impact — 43 Mandarin clips in 29 lessons and 32 English clips in 22 lessons. 75 clips across 31 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
…|⋯|\.{3,}
```

**Reading and handling (Context)**  
“1, 2, 4, 8 …” → one, two, four, eight, and so on. A trailing literary ellipsis should usually become a deliberate pause.

**False positives and limits**  
An ellipsis can mean an omission, a series, suspense or a placeholder. Preserve quotations when exact wording is required.

**Observed examples**

- ` art/art-color ` · zh · ` e1955731 ` · ` 复色（三次色）。原色加相邻的间色：红橙、蓝绿…… 一共 6 个：红橙、黄橙、黄绿、蓝绿、蓝紫、红紫。 英语里原色的名字放前面：说 blue-green，不说 green-blue。 3加3加6等于色环上的 12 种颜色。 3 原色加3 间色加6 复色等于12 块“色彩披萨”。 `
- ` biology/exocytosis ` · en · ` 57c11048 ` · ` During exocytosis, the vesicle moves from the … (organelle) to the Golgi body. `
- ` astronomy/sky-tonight ` · zh · ` d8aa0ba0 ` · ` … · 星等 3.32。颜色与温度: 白色 · 约 9,300 K（16,200 度 F）。距离: 约 81 光年。你看到的光出发于……: 约公元 1945 年。和北极星比: 暗 3.4 倍。星表编号: HIP 59774 · HD 106591。此刻往哪看: 北方，地平线以上 1 度 （方位角 360 度 ）。 `
- ` china/spring-warring ` · en · ` ca433d71 ` · ` …ght great debate: Confucius, Laozi, Mencius, Zhuangzi, Mozi, Han Fei, Sun Wu… Thinkers wrote books and argued — the “Hundred Schools of Thought contending”. `
- ` cs/cs-algorithms ` · zh · ` 63ebf585 ` · ` 归并排序。把列表拆成很小的块，再把块按顺序合并回去——两堆已经排好的数合并起来很快。只有1个数的列表本来就是有序的。把1个1个合并成有序的2个，再把2个合并成4个，4个合并成8个……。合并时，比较两堆最前面的数，取小的那个。大约n·log2n次比较：1000个数约1万次，而不是50万次。 `

<a id="roman"></a>
### Roman numeral candidate

**Hits** — 3/5 severity, 147 impact — 4 Mandarin clips in 4 lessons and 45 English clips in 17 lessons. 49 clips across 18 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])[IVXLCDM]{2,6}(?![A-Za-z0-9])|[Ⅰ-Ⅼ]|\b(?:quadrants?|World War|Act|Part|Chapter|Type)\s+[IVX]\b
```

**Reading and handling (Context)**  
World War II → World War Two. Louis XIV → Louis the Fourteenth. Apple II → Apple Two. “quadrants I to IV” → quadrants one through four.

**False positives and limits**  
IV and CD can be abbreviations. A numeral can be read as an ordinal, cardinal or letters according to the name.

**Observed examples**

- ` math/coordinate-plane ` · en · ` 267b4567 ` · ` …lane into four quadrants, numbered I to IV going counterclockwise. The signs of the two coordinates tell you the quadrant at a glance. Points on an axis bel… `
- ` ushistory/us-modern ` · zh · ` 0012b614 ` · ` …用的硅而得名。1971年，英特尔推出第一款商用微处理器——把计算机的“大脑”做在一块芯片上。1976年，乔布斯和沃兹尼亚克创办苹果公司；Apple II（1977年）是最早流行的家用电脑之一。1981年，IBM推出个人电脑，P C。1998年，谷歌成立。2007年，苹果iPhone手机把互联网装进了人们的口袋。 `
- ` _shared ` · en · ` 6bad617f ` · ` …sippi valley and named it for King Louis XIV. The United States bought the huge land west of the river, with New Orleans, in the Louisiana Purchase of 1803. `
- ` biology/endocytosis ` · zh · ` 14a5a90d ` · ` 只抓胆固醇。受体（Y 形）只抓 LDL 颗粒——血液里橙色的“胆固醇包裹”。点击细胞外面可以加入更多 LDL。 1。结合: LDL 颗粒与相配的受体结合，就像钥匙插进锁里。 2。有被小窝: 受体装满后，一层蛋白质外衣（网格蛋白，灰色小刺）让细胞膜向内弯，形成一个小窝。 3。闭合脱离: 小窝脱离细胞膜，变成只装着… `
- ` biology/cells-review ` · en · ` 06499546 ` · ` …distilled water (hypotonic) swells it. percent change equals (final minus initial) divided by initial times 100. IV equals type of solution; DV equals mass. `

<a id="identifier"></a>
### Catalog, model, road or alphanumeric label

**Hits** — 3/5 severity, 141 impact — 22 Mandarin clips in 14 lessons and 25 English clips in 17 lessons. 47 clips across 18 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:(?:[A-Z]{1,8}-)+(?:[A-Za-z]*[0-9][A-Za-z0-9-]*|[a-z][0-9][A-Za-z0-9-]*)|(?:HIP|HD|NGC|IC|GJ|TOI|CFC|DDT|I|U|F|B|M|L)\s?[0-9]{1,8}[a-z]?(?![A-Za-z0-9])|[A-Za-z]{1,10}[0-9]{2,}[A-Za-z][0-9A-Za-z]*)|开普勒[-–][0-9]+[a-z]?
```

**Reading and handling (Context)**  
“HIP 59774” → H I P, five nine seven seven four. “开普勒-452b” → 开普勒四五二 B. Confirm a catalog’s conventional grouping before using it.

**False positives and limits**  
Matches can include unit or math tokens, laptop names or flight names. Do not blindly treat hyphens as “minus”.

**Observed examples**

- ` astronomy/big-bang ` · en · ` 3dec9f7f ` · ` …und galaxies seen just 290 million years after the Big Bang, such as JADES-GS-z14-0, already surprisingly bright. Small galaxies merge to build bigger ones. `
- ` astronomy/sky-tonight ` · zh · ` d8aa0ba0 ` · ` … · 星等 3.32。颜色与温度: 白色 · 约 9,300 K（16,200 度 F）。距离: 约 81 光年。你看到的光出发于……: 约公元 1945 年。和北极星比: 暗 3.4 倍。星表编号: HIP 59774 · HD 106591。此刻往哪看: 北方，地平线以上 1 度 （方位角 360 度 ）。 `
- ` china/new-era ` · en · ` 924c1094 ` · ` … big finishes. In 2020 China fought the COVID-19 epidemic. By November the last poor counties had been lifted out of poverty. The BeiDou-3 satellite navigat… `
- ` astronomy/big-bang ` · zh · ` 91b95507 ` · ` 星系 JADES-GS-z14-0。韦布望远镜 2024 年发现，2025 年以前的最远纪录保持者。我们看到的是它在大爆炸后仅约 2.9 亿年时的样子。它的光被拉长得太厉害，到达时已经是红外线，这正是韦布望远镜要看红外线的原因。 `
- ` georgia/ga-modern ` · en · ` 81172568 ` · ` …when a Chinese airport passed it during COVID-19. Record: about 110.5 million passengers in 2019; 108.1 million in 2024. Five runways; a 400-foot control to… `

<a id="joined_tokens"></a>
### Fused math words and operands

**Hits** — 4/5 severity, 136 impact — 0 Mandarin clips in 0 lessons and 34 English clips in 8 lessons. 34 clips across 8 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z])(?:negative|minus|plus|times|over|equals|to)(?=[0-9])|(?<![A-Za-z])(?:negative|minus|plus|times|equals)(?=[A-Za-z](?![A-Za-z]))
```

**Reading and handling (Fixed)**  
negative5 → negative five. negativea → negative a. “4 to6” → four to six, or “four to six” as a ratio once the surrounding construction establishes that meaning.

**False positives and limits**  
Safe to tokenize the observed word and operand in English math. Check the reading of “to” in the surrounding expression. Regex skips ordinary words such as “negative”.

**Observed examples**

- ` math/integers ` · en · ` d463eb2b ` · ` …ee rules in one place. Opposites: a and negativea are the same distance from 0. Absolute value: |a| is that distance, so |a| equals |negativea| . Order: a i… `
- ` math/ratios ` · en · ` 794fcba8 ` · ` … paint? Mix a second batch: now it is 4 to6 . A third batch gives 6 to9 . The amounts grow together, and the colour stays exactly the same. These are equiva… `
- ` math/transformations ` · en · ` 74250628 ` · ` …n the other side of the mirror, so x changes sign: (x, y) to (negativex, y) . Flipping across the x -axis changes the sign of y : (x, y) to (x, negativey) . `
- ` math/coordinate-plane ` · en · ` 02977e41 ` · ` … along the x -axis: (3, 2) lands on (3, negative2) . Only the sign of y flips. Fold along the y -axis instead and only the sign of x flips: (negative3, 2) . `
- ` math/equations ` · en · ` 482311b5 ` · ` One trap: 2 minus 6 . Multiplying or dividing both sides by a negative number reverses the inequality sign. So negative2x minus 3 . `

<a id="power"></a>
### Powers and superscript digits

**Hits** — 4/5 severity, 120 impact — 15 Mandarin clips in 5 lessons and 15 English clips in 5 lessons. 30 clips across 5 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[0-9A-Za-zΑ-ω]\^[-+]?\s*(?:[0-9]+|[A-Za-z]|\([^)]+\))|[⁰¹²³⁴⁵⁶⁷⁸⁹]|(?:[-0-9a-z]\s*的\s*负?[0-9a-z]+\s*次方)|\b(?:to the power of|raised to)\s+(?:negative\s*)?[0-9a-z]
```

**Reading and handling (Context)**  
“2⁸” → two to the eighth power / 二的八次方. “Theta¹ Orionis C” → Theta one Orionis C, using the catalog reading.

**False positives and limits**  
Superscripts also represent star labels and footnotes. Damaged powers have their own class. Spoken “to the power of” can already be fine.

**Observed examples**

- ` math/exponents ` · zh · ` 32548571 ` · ` 很小的数反过来做。一根头发约 0.00007 米粗。把小数点向右移 5 位，落到 7 的后面： 7 乘 10的负5次方 米。向右移动，指数就是负数。 `
- ` astronomy/kepler-laws ` · en · ` bee2f95a ` · ` …epler’s 3rd law its full period is 1.26 to the power of 1.5 about 1.42 years; the probe flies half of it: about 259 days, or 8.5 months. Real missions often… `
- ` cs/cs-data-crypto ` · zh · ` 6401a64e ` · ` 现代加密。今天，计算机用很长的数字作为密钥来打乱数据——通常是128位或256位。2¹ 的平方 ⁸种可能的密钥实在太多，全部试一遍所需的时间比宇宙的年龄还长。浏览器上的小锁和“https://”表示你和网站之间的连接是加密的。 `
- ` astronomy/big-bang ` · en · ` a07c0cd8 ` · ` …an enormous factor (at least 10 squared ⁶ times). Tiny quantum jitters get stretched into the seeds of every future galaxy. This is the least certain part o… `
- ` astronomy/star-life ` · zh · ` c63e33cc ` · ` 猎户座 θ¹ C。主序星。核心正在把氢聚变成氦，和太阳一样。约 百分之90 的恒星在这里。猎户四边形中最亮的星：它的紫外线让猎户座大星云发光。 `

<a id="list_marker"></a>
### Enumeration and list markers

**Hits** — 3/5 severity, 102 impact — 3 Mandarin clips in 3 lessons and 31 English clips in 11 lessons. 34 clips across 13 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:^|[。.!?！？]\s+|[；;：:]\s*|\n)\s*(?:[1-9][0-9]?[.)）](?![0-9])|[一二三四五六七八九十]+、|[（(][1-9][0-9]?[)）]|[①-⑳]|[-•]\s+)|(?:^|\s)[A-D][.)）]\s+(?=[A-Z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF])
```

**Reading and handling (Context)**  
“1. Ribosome builds it: … 2. Inside the ER: …” → “Step one. A ribosome builds the protein. Step two. It enters the E R.”

**False positives and limits**  
Digits may start sentences that are not list items. A. can be an initial, and “一、” can occur in a quotation.

**Observed examples**

- ` astronomy/star-life ` · en · ` 1789d083 ` · ` Castor A. Main-sequence star. Fusing hydrogen into helium in its core, like the Sun. About 90 percent of stars are here. `
- ` biology/cells-review ` · zh · ` 415949a4 ` · ` 细胞学说及其发展历程。一、所有生物都由一个或多个细胞构成；二、细胞是结构和功能的基本单位；三、所有细胞都来自已有的细胞。 胡克 1665（软木，命名“细胞”），列文虎克 17 世纪 70 年代（第一次看到活细胞），施莱登 1838（植物），施旺 1839（动物），菲尔绍 1855（细胞来自细胞）。 每一个发现都… `
- ` cs/cs-data-crypto ` · en · ` 43aa993e ` · ` …er of places: with key 3, A, D, B, E… X, A. Julius Caesar reportedly used a shift of 3 for military messages. There are only 25 useful keys — a patient pers… `
- ` ela/narrative-techniques ` · zh · ` 4ec61678 ` · ` 阿仁开始数：一、二、三……他在空当里吸了一口气，稳住船身，冲过了那排大浪。 `
- ` georgia/ga-reconstruction ` · en · ` 1c3d8260 ` · ` …iversity, Morehouse, Spelman, Clark. W. E. B. Du Bois taught at Atlanta University (1897–1910). Site of the 1906 race massacre and the 1913 Leo Frank trial. `

<a id="root"></a>
### Roots and radical grouping

**Hits** — 4/5 severity, 84 impact — 11 Mandarin clips in 3 lessons and 10 English clips in 3 lessons. 21 clips across 3 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[√∛∜]|\b(?:square|cube|nth) root of\b|(?:平方根|立方根|根号)\s*(?:[0-9A-Za-z(（])
```

**Reading and handling (Context)**  
“square root of 2” → the square root of two. For a sum say “the square root of the quantity …” and mark its ending when needed.

**False positives and limits**  
This includes already verbalized roots. Only group what was under the radical.

**Observed examples**

- ` math/roots-irrationals ` · zh · ` c533ebfd ` · ` 同样的想法也适用于立体。体积为 27 的正方体，棱长是 3，因为 3 乘 3 乘 3 等于 27 。所以 27 的立方根 sqrt[3]27 等于 3 。 `
- ` astronomy/kepler-laws ` · en · ` 93f80b10 ` · ` …AU: a cubed equals 141, so T equals the square root of 141 about 11.9 years. Newton showed the full rule: T squared equals 4 pi squared a cubed divided by (… `
- ` math/pythagorean ` · zh · ` 2f003f4a ` · ` 用起来！一个直角三角形的直角边是 6 和 8。那么 c的平方 等于 36 加 64 等于 100 ，所以 c 等于 根号100 等于 10 。知道两条边，就能求出第三条。 `
- ` astronomy/kepler-laws ` · en · ` ecaa0d7d ` · ` …ty is weaker there. Escape speed is the square root of 2 about 1.41 times the circular speed: about 11.2 km/s from the surface. The International Space Stat… `
- ` math/roots-irrationals ` · zh · ` 30c53c46 ` · ` 例题：解方程 x的平方 等于 40 ，得 x 等于 正负 根号40 。因为 36 小于 40 小于 49 , 根号40 在 6 和 7 之间，而且更接近 6。检验： 6.3的平方 等于 39.69 ，所以 根号40 约等于 6.3 。 `

<a id="chem_ion"></a>
### Chemical ion or signed charge

**Hits** — 4/5 severity, 64 impact — 8 Mandarin clips in 3 lessons and 8 English clips in 3 lessons. 16 clips across 3 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:H|OH|Na|Cl|NH[4₄]|Ca|Mg|Fe|K|Cu|SO[4₄]|O|NO[3₃]|HCO[3₃])(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]|[0-9]*[+-](?!\s*[A-Za-z0-9]))
```

**Reading and handling (Fixed)**  
Na⁺ → sodium ion / 钠离子. OH⁻ → hydroxide ion / 氢氧根离子. In lessons on charge, add “with a single negative charge” or “带一个单位的负电荷”.

**False positives and limits**  
Use a case-sensitive formula and charge dictionary in chemistry context. Plus or minus can connect operands and can be part of a grade.

**Observed examples**

- ` chemistry/acids-bases ` · zh · ` 01f385e2 ` · ` 碱。pH 大于 7。碱在水中会产生氢氧根离子（OH⁻）。碱有苦味、摸起来滑腻，就像肥皂。碱能使红色石蕊试纸变蓝，使无色酚酞溶液变红。 `
- ` chemistry/atoms ` · en · ` c18423c8 ` · ` … electrons, positive ion (cation), e.g. Na⁺. Gain electrons, more electrons than protons, negative ion (anion), e.g. Cl⁻. Table salt is made of Na⁺ and Cl⁻ … `
- ` chemistry/elements-compounds ` · zh · ` dc515e7b ` · ` 食盐（氯化钠）。化合物 · 纯净物。离子排列成晶体。钠离子（Na⁺） 和氯离子（Cl⁻） 互相吸引，按立方体形状规则地重复排列，叫做晶格。食盐中没有单独的 NaCl 分子。化学式表示的是个数比：每 1 个 Na 对应 1 个 Cl。钠是一种遇水会剧烈反应的软金属，氯气是一种有毒气体。它们结合后，却成了我们吃的食… `
- ` chemistry/acids-bases ` · en · ` 7d7736d9 ` · ` … above 7. Bases release hydroxide ions (OH⁻) in water. They taste bitter and feel slippery, like soap. Bases turn red litmus blue and turn phenolphthalein p… `
- ` chemistry/atoms ` · zh · ` f856bc71 ` · ` 离子。质子数与电子数不相等的原子。失去电子，质子多于电子，带正电的阳离子，如 Na⁺。得到电子，电子多于质子，带负电的阴离子，如 Cl⁻。食盐（氯化钠）就是由 Na⁺ 和 Cl⁻ 结合而成的。 `

<a id="greek"></a>
### Greek letters and delta shorthand

**Hits** — 3/5 severity, 63 impact — 14 Mandarin clips in 10 lessons and 7 English clips in 5 lessons. 21 clips across 11 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[Α-Ωα-ωϕϵ]|\bDelta\s+[a-z]\b
```

**Reading and handling (Context)**  
Δv → change in velocity / 速度变化量. When the lesson names the symbol, say “delta v”. “λ” → lambda or 波长 lambda, when it means wavelength.

**False positives and limits**  
Greek letters can also be star labels, prefixes or constants. Distinguish μ as a variable from the micro unit prefix.

**Observed examples**

- ` astronomy/measuring-distance ` · zh · ` 78a74ab8 ` · ` …红矮星，不用望远镜根本看不见。它的视差是 0.768 角秒，所以 d 等于 1 除以 0.768 等于 1.30 秒差距 等于 4.24 光年。它属于半人马座 α 星系统，在南半球可以看到这个系统。它至少有一颗行星：比邻星 b，位于它的宜居带里。连最近的恒星，视差都不到 1 角秒：比 5 千米外的一枚硬币还小。 `
- ` math/slope ` · en · ` d61950e9 ` · ` …itten m : m equals rise over run equals Delta y over Delta x equals y2 minus y1 over x2 minus x1 For our line m equals 2 over 3 : each 1 step right, it rise… `
- ` chemistry/atoms ` · zh · ` 337afbac ` · ` 卢瑟福。核式结构模型。原子内部大部分是空的，中心有一个很小、很重、带正电的原子核，电子在核外运动。金箔实验：大多数 α 粒子直接穿过，少数却被弹了回来。试试下面的模拟！ `
- ` physics/forces ` · en · ` 495b445b ` · ` …surface. On flat ground the normal force equals the weight. On a ramp it is smaller: N equals mg cos θ. It is a contact force: no touching, no normal force. `
- ` geography/landforms ` · zh · ` 2ea32fd5 ` · ` 三角洲。在河口堆积形成的新陆地。河流入海时流速减慢，泥沙沉积下来，日积月累形成扇形或三角形的三角洲。“三角洲”这个名字来自希腊字母 Δ（三角形）。三角洲土壤非常肥沃，农田和人口密集，但也很容易发生洪水。尼罗河三角洲、恒河、布拉马普特拉河三角洲（世界最大）、密西西比河三角洲、长江三角洲、珠江三角洲。 `

<a id="note"></a>
### Musical note, octave or clef symbol

**Hits** — 4/5 severity, 60 impact — 8 Mandarin clips in 4 lessons and 7 English clips in 3 lessons. 15 clips across 5 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[𝄞𝄢𝄡♪♫♩♬♭♯♮]|(?<![A-Za-z0-9])[A-G][#♯♭b]?[0-8](?![A-Za-z0-9])|\b[A-G]\s+[A-G]\s+[A-G]\b
```

**Reading and handling (Context)**  
“高音谱号 𝄞 绕着 G4” → 高音谱号绕着第四组的 G 音所在的线. “C D E F G” → “C, D, E, F and G”, with a short pause between notes.

**False positives and limits**  
A–G with a digit can be a grid label, highway, abbreviation or algebraic variable. Clef names already present may only need the decorative glyph omitted.

**Observed examples**

- ` music/music-pitch ` · zh · ` 90fa16bf ` · ` 五线谱与谱号。音高的地图。在五线谱上越高，音越高。 高音谱号 𝄞 绕着 G4 那条线；低音谱号 𝄢 的两个点夹着 F3 那条线。 `
- ` music/music-pitch ` · en · ` 75d56b2f ` · ` …tes. Count letter names, including both ends: C to G equals C D E F G equals a 5th. Small whole-number frequency ratios sound smooth: octave 2:1, fifth 3:2. `
- ` cs/cs-computers ` · zh · ` bd0f16f3 ` · ` 累加器，A C C。存放运算器正在处理的数。“取数”把数放进来，“加”改变它，“存”把它复制出去。寄存器是速度最快的存储器——就在CPU内部。现代CPU有几十个寄存器，每个64位宽。 `
- ` _shared ` · en · ` 58a5775c ` · ` …land is a small barrier island famous for its beach resort, opened in 1928. In 2004 the leaders of the world’s biggest economies met here for the G8 summit. `
- ` ushistory/us-civilrights ` · zh · ` fa653b82 ` · ` …级女孩琳达·布朗离白人学校很近，却必须走很远去上黑人学校。她的父亲加入了全国有色人种协进会，N A A C P，发起的诉讼。NAACP的律师瑟古德·马歇尔（Thurgood Marshall）在最高法院为此案（与另外四个案子合并）辩护。九位大法官一致裁定：“隔离的教育设施本质上就是不平等的。”学校隔离违反宪法。 `

<a id="symbolic_label"></a>
### Isolated letter in subject notation

**Hits** — 3/5 severity, 57 impact — 12 Mandarin clips in 7 lessons and 7 English clips in 4 lessons. 19 clips across 7 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:[A-Za-z]\s*(?:轴|点|键|基因|型|级|调|音)|(?:点|字母|基因|选项)\s*[A-Z](?![A-Za-z0-9])|[xy]\s+-\s*axis|\b(?:[A-Z] value|(?:gene|allele|point) [A-Z])\b)
```

**Reading and handling (Context)**  
“跟着 B(4, 1) 看” where B is a point → 观察 B 点，坐标是四、一. “x -axis” → the x axis. For “A 基因” say “字母 A 所代表的基因” when distinguishing the label matters.

**False positives and limits**  
Sometimes the letter is part of an abbreviation or a notation students must hear exactly. Verify the subject’s conventional pronunciation.

**Observed examples**

- ` chemistry/elements-compounds ` · zh · ` 156b0c3e ` · ` 氨。化合物 · 纯净物。三角锥形分子。1 个氮原子与 3 个氢原子结合。分子呈三角锥形，氮原子在顶端（H–N–H 键角约 107 度 ）。氨可用来制造化肥，一些清洁剂中也含有氨。它有强烈的刺激性气味。NH3:1 个氮，3 个氢。 `
- ` math/coordinate-plane ` · en · ` 02977e41 ` · ` Fold the plane along the x -axis: (3, 2) lands on (3, negative2) . Only the sign of y flips. Fold along the y -axis instead and only the sign of x flips: (n… `
- ` _shared ` · zh · ` 5e6fb502 ` · ` 底特律。亨利·福特让底特律成为“汽车城”：1908年推出T型车，1913年采用移动流水线。大迁徙中，许多黑人家庭来这里的工厂找工作；二战时，附近的柳树溪工厂还生产轰炸机。 `
- ` math/scatter-plots ` · en · ` eec9ff39 ` · ` …ir into a point. Hours go across on the x -axis and the score goes up on the y -axis, so the student with (0.5, 55) lands here. Do it for all 12 and we get … `
- ` chemistry/reactions ` · zh · ` 305a540e ` · ` 氢气燃烧。化合反应 · 燃烧。首先，H–H 键和 O 等于 O 键要断开。然后原子重新组合：每个氧原子与 2 个氢原子结合，生成 2 个 H2O。清点：反应前 4 个 H、2 个 O，反应后仍是 4 个 H、2 个 O。质量：36 u，36 u。这个反应放出大量能量，可以为火箭和燃料电池汽车提供动力。原子就像乐… `

<a id="chem_bond"></a>
### Bond or base-pair dash

**Hits** — 4/5 severity, 48 impact — 6 Mandarin clips in 4 lessons and 6 English clips in 4 lessons. 12 clips across 4 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])(?:[ATUCG]\s*[–−-]\s*[ATUCG]|[HONC]\s*[–=≡-]\s*[HONC])(?![A-Za-z0-9])
```

**Reading and handling (Context)**  
“G–C pair” → a guanine–cytosine pair / 鸟嘌呤与胞嘧啶配对. “H–H 键” → 两个氢原子之间的单键.

**False positives and limits**  
A–B could be generic labels. Decide from lesson context whether a dash expresses a pair, bond or span.

**Observed examples**

- ` biology/dna ` · zh · ` 4e68c791 ` · ` 鸟嘌呤，G。总是与 C 配对。鸟嘌呤只和胞嘧啶配对。G 和 C 之间有 3 个氢键，所以 G–C 对比 A–T 对更牢固一些。 `
- ` chemistry/elements-compounds ` · en · ` 90f4f73d ` · ` …e is a short pyramid with N at the top (H–N–H about 107°). Ammonia is used to make fertilizers and is found in some cleaners. It has a strong smell. NH3: on… `
- ` biology/protein-synthesis ` · zh · ` 1cdc22b0 ` · ` 氨基酸。组成蛋白质的“积木”。生物体内有 20 种氨基酸。氨基酸的“排列顺序”决定蛋白质的形状和功能。这里的链拼成 M-A-G-I-C：甲硫氨酸、丙氨酸、甘氨酸、异亮氨酸、半胱氨酸。 `
- ` chemistry/reactions ` · en · ` 7cab8310 ` · ` …burns. Synthesis, combustion. First the H–H and O equals O bonds must break. Then the atoms regroup: each O atom bonds to 2 H atoms, making 2 H2O. Count: 4 … `
- ` biology/protein-synthesis ` · zh · ` f7839335 ` · ` RNA 聚合酶。负责“抄写”的酶。这种酶在基因处解开 DNA，并把 RNA 核苷酸连接起来。它按照 A–U、T–A、G–C、C–G 的规则配对碱基。它本身也是一种蛋白质，由自己的基因编码！ `

<a id="text_literal"></a>
### Language example or spelling being mentioned

**Hits** — 3/5 severity, 48 impact — 8 Mandarin clips in 5 lessons and 8 English clips in 6 lessons. 16 clips across 10 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?i:\b(?:prefix|suffix|root word|cognate|homophone|pronounced|sounds like|spelled|the letter|the word)\b)|读作|读音|这个字|拼写|词根|词缀
```

**Reading and handling (Context)**  
“the prefix re-” → the prefix R E, meaning again, if spelling the prefix is central. If a lesson names a character’s pronunciation, use a reviewed pronunciation sample for that character.

**False positives and limits**  
Many hits already read fluently. Preserve the exact example and avoid substituting its definition where students need to hear its sounds.

**Observed examples**

- ` ela/vocabulary-roots ` · zh · ` 13972e19 ` · ` 前缀，Prefix。加在前面，改变意思。un-、in-、im-、dis- 常表示“不”：unhappy（不快乐）、invisible（看不见的）、impossible（不可能的）、dislike（不喜欢）。re- 等于 再、回；pre- 等于 在……之前；trans- 等于 穿过；sub- 等于 在……下面。t… `
- ` music/music-instruments ` · en · ` d5781f9c ` · ` …ingernails; the fast “wheel” tremolo 轮指 sounds like a shimmer. It has been in China for about 2,000 years. Famous piece: 《十面埋伏》 “Ambush from Ten Sides” — a … `
- ` math/expressions ` · zh · ` 5b3a66bb ` · ` 想象一个盒子，里面装着一些弹珠。我们不知道有几颗，而且数量还可能变化： 3 、 7 、 12 ……于是给这个盒子起个名字，用一个字母比如 x 来表示。这就是用字母表示数，这个字母叫作变量。 `
- ` cs/cs-data-crypto ` · en · ` e522de05 ` · ` …urn into different letters, which hides the letter pattern. It was called “the indecipherable cipher” for about 300 years — until people found ways to break… `
- ` physics/waves ` · zh · ` f54e6568 ` · ` 波长（λ）。一个完整波的长度。波长是相邻两个波峰（或两个波谷、两个密部）之间的距离。波长的符号是希腊字母 λ（读作“兰姆达”），单位是米。在同一种介质中，频率越高，波长越短，因为 v 等于 f 乘 λ 保持不变。 `

<a id="temperature"></a>
### Temperature scale symbols

**Hits** — 4/5 severity, 44 impact — 11 Mandarin clips in 5 lessons and 0 English clips in 0 lessons. 11 clips across 5 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[℃℉]|°\s*[CF](?![A-Za-z])|度\s+[CF](?![A-Za-z])
```

**Reading and handling (Fixed)**  
“-4 °C” → negative four degrees Celsius / 零下四摄氏度. “负4 度 C” → 零下四摄氏度.

**False positives and limits**  
Bare ° can be an angle. F and C can be direction or point labels. Keep the scale only where known.

**Observed examples**

- ` math/integers ` · zh · ` 94e41fa0 ` · ` 下午 3 点气温是 6 度 C。夜里降到 0 度 C，而且还在继续下降。到了清晨，已经是零下 4 度了。我们把它写成 负4 度 C：这是一个负数。 `
- ` astronomy/sky-tonight ` · zh · ` 70c9c23e ` · ` 40 御夫座。位于御夫座 · 星等 5.35。颜色与温度: 白色 · 约 7,800 K（13,600 度 F）。距离: 本页列表中没有。和北极星比: 暗 22.3 倍。星表编号: HIP 28946 · HD 41357。此刻往哪看: 东北方，地平线以上 22 度 （方位角 57 度 ）。 `
- ` georgia/ga-20th ` · zh · ` 13427e52 ` · ` 温泉镇。罗斯福游泳、筹划并去世的地方。1924 年罗斯福第一次来到这里，希望 88 度 F 的泉水能缓解小儿麻痹症。 1932 年他建起了“小白宫”。 1945 年 4 月 12 日他在这里去世，当时一位画家正在为他画像，那幅画就是“未完成的肖像”。 `
- ` ushistory/us-colonies ` · zh · ` 5f0440ae ` · ` 蒙茅斯。1778年6月28日。在约38℃（100℉）的酷热中打了一整天，双方都没有明显取胜。 `
- ` _shared ` · zh · ` 5727c48d ` · ` 温泉镇。这里的泉水从地下涌出时约有31 摄氏度 （88 度 F）。富兰克林·罗斯福得了小儿麻痹症后，1924年第一次来这里，希望温暖的泉水池能帮他恢复双腿，后来在这里建了“小白宫”，并于1945年4月12日在这里去世。附近的罗斯福州立公园是由民间资源保护队修建的。 `

<a id="lost_relation"></a>
### Missing equation relation

**Hits** — 5/5 severity, 40 impact — 4 Mandarin clips in 3 lessons and 4 English clips in 3 lessons. 8 clips across 3 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:二氧化碳|carbon dioxide).{0,44}\+.{0,32}(?:，|,)\s*(?:有机物|glucose|sugar)|(?:H[⁺+]\s*\+\s*OH[⁻−]\s*[,，]\s*H[2₂]O)|(?:酸\s*\+\s*碱\s*[,，]\s*盐|acid\s*\+\s*base\s*,\s*salt)|(?:H2\s*\+\s*(?:[0-9]+\s*)?O2|CH4\s*\+\s*(?:[0-9]+\s*)?O2|HCl\s*\+\s*NaOH)\s*[,，]\s*(?:[0-9]+\s*)?(?:CO2|H2O|NaCl)|(?:water molecules|水分子)[,，]\s*[0-9]+\s*(?:个\s*)?H[2₂]\s*(?:\+|加)\s*[0-9]+\s*(?:个\s*)?O[2₂]|O\s*(?:等于|equals)\s*O\s*(?:键|bonds?)
```

**Reading and handling (Context)**  
“二氧化碳 + 水 —（光能），有机物（葡萄糖）+ 氧气” → 在光能作用下，二氧化碳和水生成葡萄糖和氧气. “O equals O bonds” → oxygen–oxygen double bonds, or “双键” in Mandarin.

**False positives and limits**  
Phrase signatures catch known cases. A comma can simply separate a list. Confirm reaction direction, bonds, coefficients and terms using the original.

**Observed examples**

- ` biology/food-webs ` · zh · ` 7188d0f6 ` · ` 生产者。自己制造有机物（第 1 营养级）。植物、藻类和一些细菌是生产者。光合作用：二氧化碳 + 水 —（光能），有机物（葡萄糖）+ 氧气。生产者位于每座能量金字塔的最底层，储存的能量最多。模型中的生产者：草、树和野花。 `
- ` biology/food-webs ` · en · ` 0bee50ab ` · ` …bacteria are producers. Photosynthesis: carbon dioxide + water + light energy, sugar (glucose) + oxygen. Producers form the base of every energy pyramid and… `
- ` chemistry/acids-bases ` · zh · ` b451d8c6 ` · ` 中和反应。酸 + 碱，盐 + 水。酸和碱反应时，H⁺ 和 OH⁻ 结合成水：H⁺ + OH⁻，H2O。其余的离子组成盐。例如：HCl + NaOH，NaCl + H2O。如果酸和碱恰好完全反应，溶液就变成中性（pH 约等于 7）。生活中的应用：用抗酸药治疗胃酸过多；蚊虫叮咬（含蚁酸）后涂肥皂水止痒；用熟石灰改良… `
- ` chemistry/reactions ` · en · ` eb0314ac ` · ` …gas: the reverse of hydrogen burning. 2 water molecules, 2 H2 + 1 O2. Count: 4 H and 2 O on each side. Mass: 36 u, 36 u. One reactant breaking into simpler … `
- ` chemistry/reactions ` · zh · ` 305a540e ` · ` 氢气燃烧。化合反应 · 燃烧。首先，H–H 键和 O 等于 O 键要断开。然后原子重新组合：每个氧原子与 2 个氢原子结合，生成 2 个 H2O。清点：反应前 4 个 H、2 个 O，反应后仍是 4 个 H、2 个 O。质量：36 u，36 u。这个反应放出大量能量，可以为火箭和燃料电池汽车提供动力。原子就像乐… `

<a id="currency"></a>
### Money and currency signs

**Hits** — 3/5 severity, 36 impact — 0 Mandarin clips in 0 lessons and 12 English clips in 5 lessons. 12 clips across 5 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[$¥￥€£₹]\s*[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|\b(?:USD|CNY|RMB|EUR|GBP)\s*(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?|\b(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?\s*(?:USD|CNY|RMB|EUR|GBP)\b
```

**Reading and handling (Fixed)**  
“$1.87” → one dollar and eighty-seven cents. “$2.1 billion” → two point one billion dollars.

**False positives and limits**  
Identify currency from the field or lesson. A dollar sign or yen/yuan glyph is not globally unambiguous. Handle scale words before splitting cents.

**Observed examples**

- ` economics/econ-personal-finance ` · en · ` 93f44b5e ` · ` …rprise bill into a small problem instead of a debt. US bank deposits are insured by the FDIC up to $250,000 per depositor, per bank, per ownership category. `
- ` ela/theme-plot ` · en · ` 89c7a77e ` · ` …ong? In “The Gift of the Magi”: a small New York flat, Christmas Eve, only $1.87. Often ends with the inciting incident — the spark that starts the trouble. `
- ` georgia/ga-modern ` · en · ` 05311039 ` · ` …rt McPherson army base. Direct spending hit a record of about $4.4 billion in fiscal 2022, then fell to $2.6 billion in fiscal 2024 after Hollywood strikes. `
- ` _shared ` · en · ` 4d68bd72 ` · ` …S bought Alaska from Russia in 1867 for $7.2 million — about 2 cents an acre — and critics called it “Seward’s Folly.” It is by far the largest state, more … `
- ` economics/econ-trade ` · en · ` d8822a7a ` · ` … currency in terms of another. In 2024, $1 bought about ¥7.20 on average (World Bank). Most currencies move with supply and demand; China manages the yuan w… `

<a id="scientific"></a>
### Scientific notation and exponent base

**Hits** — 4/5 severity, 32 impact — 4 Mandarin clips in 2 lessons and 4 English clips in 2 lessons. 8 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?\s*(?:[×x·]\s*10\s*(?:\^[-+]?[0-9]+|[⁰¹²³⁴⁵⁶⁷⁸⁹]+)|[eE][+-][0-9]+)|(?:乘以?\s*10\s*(?:的|平方)|\btimes 10 (?:to the power of|squared|cubed))|10\s*(?:squared|的平方)\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]
```

**Reading and handling (Context)**  
“8 times 10 to the power of 5 km” → eight times ten to the fifth power kilometers. Pause so kilometers applies to the complete quantity.

**False positives and limits**  
Includes readable versions. Corrupt exponent matches must be resolved first. The letter x can be a variable.

**Observed examples**

- ` astronomy/big-bang ` · zh · ` e4cae1fa ` · ` 暴胀。在远远不到一万亿分之一的一万亿分之一秒里，一小块空间急剧膨胀了极其巨大的倍数（至少 10 的平方 ⁶ 倍）。微小的量子涨落被拉大，成了后来所有星系的“种子”。这是整个故事里最不确定的部分：有有力的线索，但还没被证实。 `
- ` math/exponents ` · en · ` 29dec852 ` · ` …about 0.00007 m thick. Hop the point right 5 places to land after the 7: 7 times 10 to the power of negative5 m. Hops to the right give a negative exponent. `
- ` math/exponents ` · zh · ` 32548571 ` · ` 很小的数反过来做。一根头发约 0.00007 米粗。把小数点向右移 5 位，落到 7 的后面： 7 乘 10的负5次方 米。向右移动，指数就是负数。 `
- ` astronomy/big-bang ` · en · ` a07c0cd8 ` · ` …alloons by an enormous factor (at least 10 squared ⁶ times). Tiny quantum jitters get stretched into the seeds of every future galaxy. This is the least cer… `
- ` math/exponents ` · zh · ` 40dd74cc ` · ` 科学记数法可以驯服很大的数。太阳离我们约 150 000 000 千米。把小数点向左移动，直到它前面只剩一个非零数字：移了 8 位，所以距离是 1.5 乘 10的8次方 千米。 `

<a id="programming"></a>
### Code-like inline construction

**Hits** — 3/5 severity, 30 impact — 4 Mandarin clips in 3 lessons and 6 English clips in 4 lessons. 10 clips across 4 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
\b(?:O\s*\(\s*n[^)]{0,24}\)|log[0-9]+[a-z]|\w+_\w+|[A-Za-z]0[xX][0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|[0-9][01]{5,}\s*(?:binary|二进制))\b|O\(n[^)]{0,24}\)
```

**Reading and handling (Context)**  
“O(n log n)” → big O of n log n. “log2n” in the sorting example → the base-two logarithm of n. “v_end” → final velocity or v sub end, depending on the instructional goal.

**False positives and limits**  
Underscores can mark subscripts instead of code. Spell source characters only if the lesson teaches what to type.

**Observed examples**

- ` physics/motion ` · en · ` 8ebf16ef ` · ` … in velocity divided by time: a equals (v_end minus v_start) divided by t. Unit: m/s squared (meters per second, every second). a equals 2.5 m/s squared mea… `
- ` cs/cs-algorithms ` · zh · ` 3038d644 ` · ` …大的都放到右边。再分别对两边做快速排序。围绕基准分一次，基准就到了它最终的位置。两边各是一个更小的问题：和归并排序一样分而治之，但不需要额外空间。平均：大约1.4·n·log2n次比较——O(n log n)。运气不好：如果基准总是最大或最小的（试试“已排好”！），就要n(n减1)/2次——O(n 的平方 )。 `
- ` biology/cells-review ` · en · ` 4b747920 ` · ` The sodium-potassium ____ uses ATP to move ions against their gradients. `
- ` astronomy/rocketry ` · zh · ` 8ce9900c ` · ` 火箭方程。Δv 等于 喷气速度 乘 ln(m0 除以 m_f)。康斯坦丁·齐奥尔科夫斯基在 1903 年写下了这个方程。Δv 是火箭能产生的总速度变化，只取决于喷气速度和质量比：满载质量 m0 除以 燃料烧完后的质量 m_f。进入近地轨道需要约 9.4 千米/秒的 Δv（7.8 千米/秒的轨道速度，加上约 1.… `
- ` cs/cs-algorithms ` · en · ` da9fb215 ` · ` …ger. Already sorted list: only n minus 1 comparisons and 0 moves — the best case. Reversed list: n(n minus 1)/2 comparisons — the worst case, O(n squared ). `

<a id="ratio_colon"></a>
### Colon in ratio

**Hits** — 3/5 severity, 27 impact — 5 Mandarin clips in 5 lessons and 4 English clips in 4 lessons. 9 clips across 5 distinct lesson IDs.

**Detection** uses the following logic. Colon-separated integers with nearby ratio/rhythm cues, or a spaced chain of three or more integers. Remove UTC offsets and clock-shaped unspaced two-part tokens.

**Reading and handling (Context)**  
“1 : 2 : 4” → one to two to four / 一比二比四. “octave 2:1” → an octave has a two-to-one frequency ratio.

**False positives and limits**  
Timestamp-like ratios can evade the cue filter. Colons in a year/value label or exercise numbering should get a pause instead.

**Observed examples**

- ` astronomy/planets-moons ` · zh · ` 06d21e60 ` · ` …卫星绕着另一颗行星转，说明并不是所有天体都绕地球转。 木卫一、木卫二和木卫三以 1 : 2 : 4 的节奏互相拉扯（轨道共振）。 这种规律的拉扯让轨道保持略呈椭圆，于是木星的潮汐反复弯曲它们、加热内部：木卫一有火山，木卫二的冰下有海洋。 用普通的双筒望远镜就能看到它们：木星旁边的四个小亮点。 记忆小窍门 由内向… `
- ` math/volume-solids ` · en · ` 13f0df5a ` · ` …empty cylinder: it fills two thirds. The cone fills the last third. Cone : sphere : cylinder equals 1 : 2 : 3, as Archimedes discovered over 2000 years ago. `
- ` chemistry/elements-compounds ` · zh · ` 4a1e8ea8 ` · ` …学键结合在一起，所以水是化合物。水分子是弯曲的：H–O–H 键角约为 104.5 度 。每个水分子中 H 与 O 的原子个数比都是 2 : 1。化合物的组成总是固定的。水的性质和组成它的元素完全不同：氢气能燃烧，氧气能助燃，水却能灭火！右下角的小数字（下标）只表示它前面那种原子的个数：H2O 等于 H、H、O。 `
- ` music/music-pitch ` · en · ` 75d56b2f ` · ` …tes. Count letter names, including both ends: C to G equals C D E F G equals a 5th. Small whole-number frequency ratios sound smooth: octave 2:1, fifth 3:2. `
- ` math/ratios ` · zh · ` b1f4818d ` · ` 1 杯蓝色要配多少黄色？把两个数都除以 2： 2比3 等于 1比1.5 。这就是单位比率：每杯蓝色配 1.5 杯黄色。有了它，什么量都好算：7 杯蓝色需要 7 乘 1.5 等于 10.5 杯黄色。 `

<a id="element_symbol"></a>
### Chemical element symbol with local cue

**Hits** — 3/5 severity, 21 impact — 4 Mandarin clips in 1 lessons and 3 English clips in 1 lessons. 7 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:元素符号|元素|原子)\s*[（(]?\s*(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Ag|Sn|I|Au|Hg|Pb|U)(?![A-Za-z0-9])|(?<![A-Za-z0-9])(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Ag|Sn|I|Au|Hg|Pb|U)(?:\s*(?:原子|元素)|\s+atoms?\b)|(?i:\b(?:symbol(?: for)?|atoms? of)\s+)(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Ag|Sn|I|Au|Hg|Pb|U)(?![A-Za-z0-9])|(?:[0-9]+\s*个\s*(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Ag|Sn|I|Au|Hg|Pb|U)[、，]|(?i:\b(?:Count|each side):\s*)[0-9]+\s+(?:H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Fe|Cu|Zn|Ag|Sn|I|Au|Hg|Pb|U)\s+(?:and|on)\b)
```

**Reading and handling (Context)**  
“4 H and 2 O atoms” → four hydrogen atoms and two oxygen atoms. When teaching the symbol, say “hydrogen, symbol H”.

**False positives and limits**  
Some symbols may be coordinates or exercise variables. The regex uses an element allowlist. Distinguish a letter label from the name of the element.

**Observed examples**

- ` chemistry/reactions ` · zh · ` 305a540e ` · ` …O 键要断开。然后原子重新组合：每个氧原子与 2 个氢原子结合，生成 2 个 H2O。清点：反应前 4 个 H、2 个 O，反应后仍是 4 个 H、2 个 O。质量：36 u，36 u。这个反应放出大量能量，可以为火箭和燃料电池汽车提供动力。原子就像乐高积木：拆开旧模型，拼出新模型。积木还是那些，只是形状变了。 `
- ` chemistry/reactions ` · en · ` 80aa7e38 ` · ` …use heat, high pressure and a catalyst. Count: 2 N and 6 H on each side. Mass: 34 u, 34 u. 4 molecules become 2 molecules, but the number of ATOMS stays 8. … `
- ` chemistry/reactions ` · zh · ` 4802a4d5 ` · ` 合成氨。化合反应。氮气和氢气结合生成氨，氨可以用来制造化肥。N2 中的三键很牢固，所以工厂要用高温、高压和催化剂。清点：两边都是 2 个 N、6 个 H。质量：34 u，34 u。4 个分子变成了 2 个分子，但原子总数始终是 8 个。分子个数可以改变，原子个数不会改变。 `
- ` chemistry/reactions ` · en · ` eb0314ac ` · ` …urning. 2 water molecules, 2 H2 + 1 O2. Count: 4 H and 2 O on each side. Mass: 36 u, 36 u. One reactant breaking into simpler substances is called decomposi… `
- ` chemistry/reactions ` · zh · ` a332cf25 ` · ` 电解水。分解反应。通电使水分解成氢气和氧气，正好是氢气燃烧的逆过程。2 个水分子，2 个 H2加1 个 O2。清点：两边都是 4 个 H、2 个 O。质量：36 u，36 u。一种反应物分解成几种更简单的物质，叫做分解反应。分解反应：一变多。 `

<a id="corrupt_exponent"></a>
### Exponent damaged by normalization

**Hits** — 5/5 severity, 20 impact — 2 Mandarin clips in 2 lessons and 2 English clips in 2 lessons. 4 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[0-9]+[⁰¹²³⁴⁵⁶⁷⁸⁹]*\s*(?:squared|的平方)\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]+)
```

**Reading and handling (Context)**  
10 squared ⁶ → ten to the twenty-sixth power. 2¹ 的平方 ⁸ → 二的一百二十八次方. Restore the exponent from the display/source before speaking it.

**False positives and limits**  
Matches the observed split pattern. Never infer missing exponent digits from the send alone.

**Observed examples**

- ` astronomy/big-bang ` · en · ` a07c0cd8 ` · ` …alloons by an enormous factor (at least 10 squared ⁶ times). Tiny quantum jitters get stretched into the seeds of every future galaxy. This is the least cer… `
- ` astronomy/big-bang ` · zh · ` e4cae1fa ` · ` 暴胀。在远远不到一万亿分之一的一万亿分之一秒里，一小块空间急剧膨胀了极其巨大的倍数（至少 10 的平方 ⁶ 倍）。微小的量子涨落被拉大，成了后来所有星系的“种子”。这是整个故事里最不确定的部分：有有力的线索，但还没被证实。 `
- ` cs/cs-data-crypto ` · en · ` 095aafc6 ` · ` …e long numbers — often 128 or 256 bits. 2¹ squared ⁸ possible keys is so many that trying them all would take longer than the age of the universe. The padlo… `
- ` cs/cs-data-crypto ` · zh · ` 6401a64e ` · ` 现代加密。今天，计算机用很长的数字作为密钥来打乱数据——通常是128位或256位。2¹ 的平方 ⁸种可能的密钥实在太多，全部试一遍所需的时间比宇宙的年龄还长。浏览器上的小锁和“https://”表示你和网站之间的连接是加密的。 `

<a id="lost_math_scope"></a>
### Ambiguous fraction or expression scope

**Hits** — 5/5 severity, 20 impact — 2 Mandarin clips in 1 lessons and 2 English clips in 1 lessons. 4 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[xy]2\s*(?:minus|减)\s*[xy]1\s*(?:over|分之)\s*[xy]2\s*(?:minus|减)\s*[xy]1)|(?:\b[0-9]+\s+over\s+[0-9]+\s+[xy]\b)|(?:[0-9]+\s*分之\s*[0-9]+\s*[xy](?![A-Za-z]))|Delta\s*x\s*分之\s*Delta\s*y|\bDelta\s+y\s+over\s+Delta\s+x\b
```

**Reading and handling (Context)**  
“y2 minus y1 over x2 minus x1” → subtract y sub one from y sub two. Divide that difference by x sub two minus x sub one. “3分之2 x” → 三分之二乘以 x.

**False positives and limits**  
Check grouping against the source. A letter can belong in the denominator, and Chinese fraction order differs from English.

**Observed examples**

- ` math/slope ` · en · ` 30c0d499 ` · ` …It crosses the y -axis at the y -intercept b equals 1 . From there every 3 steps right add 2, so y equals 2 over 3 x plus 1 . In general: y equals mx plus b `
- ` math/slope ` · en · ` d61950e9 ` · ` …itten m : m equals rise over run equals Delta y over Delta x equals y2 minus y1 over x2 minus x1 For our line m equals 2 over 3 : each 1 step right, it rise… `
- ` math/slope ` · zh · ` 718cec80 ` · ` 直线从哪里出发？它与 y 轴交于 b 等于 1 , b 叫作（在 y 轴上的）截距。从这里起，每向右 3 就增加 2，所以 y 等于 3分之2 x 加 1 。一般地： y 等于 mx 加 b （我国教材常写作 y 等于 kx 加 b ) `
- ` math/slope ` · zh · ` 9b4f639d ` · ` 这个不变的比值就是斜率，记作 m : m 等于 前进分之上升 等于 Delta x分之Delta y 等于 x2 减 x1分之y2 减 y1 我们这条直线 m 等于 3分之2 ：每向右走 1，就上升 3分之2 。 `

<a id="absolute_value"></a>
### Bars used as absolute value

**Hits** — 4/5 severity, 16 impact — 2 Mandarin clips in 1 lessons and 2 English clips in 1 lessons. 4 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[|｜]\s*[^|｜\r\n]{1,36}\s*[|｜]
```

**Reading and handling (Context)**  
“|负5| 等于 5” → 负五的绝对值等于五. “|a|” → the absolute value of a.

**False positives and limits**  
Paired bars may denote a determinant, cardinality, norm or divisibility elsewhere. Apply a fixed expansion only after the expression type is known.

**Observed examples**

- ` math/integers ` · en · ` 7cd8d085 ` · ` The absolute value |a| is a number’s distance from 0. negative5 is 5 steps from zero, so |negative5| equals 5 ; and |5| equals 5 too. A distance is never ne… `
- ` math/integers ` · en · ` d463eb2b ` · ` …are the same distance from 0. Absolute value: |a| is that distance, so |a| equals |negativea| . Order: a is less than b exactly when a is to the left of b . `
- ` math/integers ` · zh · ` 902046e9 ` · ` 把三条规律放在一起。相反数： a 与 负a 到 0 的距离相同。绝对值： |a| 就是这个距离，所以 |a| 等于 |负a| 。大小： a 在 b 的左边，就有 a 小于 b 。 `
- ` math/integers ` · zh · ` bc95f1ea ` · ` 绝对值 |a| 表示一个数到 0 的距离。 负5 离 0 有 5 格，所以 |负5| 等于 5 ； |5| 也等于 5。距离永远不会是负数。 `

<a id="angular_prime"></a>
### Angular minute and second primes

**Hits** — 4/5 severity, 16 impact — 1 Mandarin clips in 1 lessons and 3 English clips in 2 lessons. 4 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[′″]|[0-9]\s*°\s*[0-9]+\s*['"]
```

**Reading and handling (Fixed)**  
“33°42′” → thirty-three degrees, forty-two arcminutes. “0.768″” → zero point seven six eight arcseconds. “33 度 42′” → 三十三度四十二分.

**False positives and limits**  
Same primes can mean feet/inches, arc units or transformed points. Fixed only for known angular fields.

**Observed examples**

- ` astronomy/measuring-distance ` · en · ` ca9cd8b9 ` · ` …thout a telescope. Its parallax is 0.768″, so d equals 1 divided by 0.768 equals 1.30 parsecs equals 4.24 light-years. It belongs to the Alpha Centauri syst… `
- ` astronomy/measuring-distance ` · en · ` e58d422c ` · ` …, double the distance. Below about 0.001″ even Gaia’s measurements get too uncertain for single stars. Parsec equals the distance where p equals 1″ (about 3… `
- ` geography/latitude-longitude ` · en · ` f49b647d ` · ` … 84.4°W. Each degree splits into 60 minutes (′): 33.7° about 33°42′. Try it: drag the Latitude and Longitude sliders under the globe and watch the pin move. `
- ` geography/latitude-longitude ` · zh · ` 110f5c07 ` · ` 经纬度坐标。先写纬度，再写经度。一对坐标就是地球上一个准确的地址：先纬度，后经度。例如：亚特兰大约为北纬 33.7 度 ，西经 84.4 度 。1 度可以再分为 60 分（′）:33.7 度 约等于 33 度 42′。试一试：拖动地球下方的“纬度”和“经度”滑块，看图钉怎么移动。 `

<a id="fragment_end"></a>
### Clip ends at phrase punctuation

**Hits** — 2/5 severity, 16 impact — 8 Mandarin clips in 1 lessons and 0 English clips in 0 lessons. 8 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[,，:：;；—–]\s*$
```

**Reading and handling (Context)**  
“浮光跃金，静影沉璧，” → finish with the intended short pause, or join it to the next phrase when the interface allows uninterrupted playback.

**False positives and limits**  
Classical reading exercises can intentionally end mid-sentence. Do not rewrite a source quotation to replace its punctuation.

**Observed examples**

- ` yuwen/yw-wenyan-classics ` · zh · ` 37ece25f ` · ` 而或长烟一空，皓月千里， `
- ` yuwen/yw-wenyan-classics ` · zh · ` 5e67f08e ` · ` 日星隐曜，山岳潜形； `
- ` yuwen/yw-wenyan-classics ` · zh · ` 765e59f5 ` · ` 商旅不行，樯倾楫摧； `
- ` yuwen/yw-wenyan-classics ` · zh · ` 76741145 ` · ` 若夫淫雨霏霏，连月不开， `
- ` yuwen/yw-wenyan-classics ` · zh · ` c9ad914e ` · ` 浮光跃金，静影沉璧， `

<a id="isotope"></a>
### Isotope mass number

**Hits** — 3/5 severity, 15 impact — 3 Mandarin clips in 2 lessons and 2 English clips in 1 lessons. 5 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:碳|铀|氢|氦|氧|铯|钴)\s*[-–]\s*[0-9]{1,3}|(?i:\b(?:carbon|uranium|hydrogen|helium|oxygen|cesium|cobalt)[-–][0-9]{1,3}\b)|[⁰¹²³⁴⁵⁶⁷⁸⁹]+[A-Z][a-z]?(?![A-Za-z0-9])
```

**Reading and handling (Fixed)**  
“碳-14 测定” → 碳十四测定. “carbon-14” → carbon fourteen.

**False positives and limits**  
Fixed for confirmed isotope names. A superscript before a capital also occurs in labels, so validate the element and context.

**Observed examples**

- ` chemistry/atoms ` · en · ` 7ae1f88b ` · ` …als mass number minus atomic number. Example: carbon-14 has 14 minus 6 equals 8 neutrons. The number after an element’s name (carbon-12) is its mass number. `
- ` chemistry/atoms ` · en · ` c6e1f1ac ` · ` …tope. Same protons, different neutrons. Carbon-12, carbon-13 and carbon-14 are all carbon: each has 6 protons. Some isotopes are radioactive (unstable). Car… `
- ` chemistry/atoms ` · zh · ` 0bd92564 ` · ` 同位素。质子数相同、中子数不同。碳-12、碳-13 和碳-14 都是碳，都有 6 个质子。有些同位素具有放射性（不稳定）。碳-14 可以用来测定古代生物遗骸的年代（最多约 5 万年）。氢有三种同位素：氕（0 个中子）、氘（1 个中子）和氚（2 个中子）。 `
- ` chemistry/atoms ` · zh · ` 9500ed08 ` · ` 质量数。等于 质子数 + 中子数。电子太轻，不计入质量数。中子数 等于 质量数减原子序数。例如碳-14 有 14减6 等于 8 个中子。元素名称后面的数字（如碳-12）就是质量数。 `
- ` georgia/ga-native ` · zh · ` 45a67b5e ` · ` 奥克马尔吉土丘（梅肯）。这里发现的一枚克洛维斯尖状器表明，古印第安猎人 12,000 多年前就到过这里。 约公元 900 年，密西西比农人在这里建镇；大神庙土丘高 55 英尺。 “土屋”是一座圆形议事厅，原始地面经碳-14 测定约为公元 1015 年，里面约有 50 个座位。 `

<a id="numeric_sequence"></a>
### Hyphenated numeric sequence

**Hits** — 3/5 severity, 15 impact — 3 Mandarin clips in 3 lessons and 2 English clips in 2 lessons. 5 clips across 3 distinct lesson IDs.

**Detection** uses the following logic. Standalone chain of ≥3 ASCII integers joined by -, – or —. Exclude valid ISO dates.

**Reading and handling (Context)**  
“3-4-5 triangle” → a triangle with sides of lengths three, four and five. “2-8-8 规律” → 三层电子数的上限依次是二、八、八.

**False positives and limits**  
A three-part sequence could be a date outside ISO format, phone number, code or subtraction.

**Observed examples**

- ` chemistry/atoms ` · en · ` 9d89dd0d ` · ` …, shell 2 up to 8, shell 3 up to 8 (the 2-8-8 rule). Electrons fill the inner shells first, then move outward. Atoms with a full outer shell (like helium, n… `
- ` chemistry/atoms ` · zh · ` 76247cb6 ` · ` 电子层。电子所在的能级。对前 20 号元素：第 1 层最多 2 个电子，第 2 层最多 8 个，第 3 层最多 8 个（“2-8-8”规律）。电子先填满内层，再排到外层。最外层“排满”的原子（如氦、氖、氩）非常稳定，几乎不发生反应。 `
- ` math/pythagorean ` · en · ` 7fd8fbde ` · ` Try a 3-4-5 triangle and count unit squares: 3 squared equals 9 and 4 squared equals 16 . The big square holds 5 squared equals 25 , and 9 plus 16 equals 25… `
- ` math/pythagorean ` · zh · ` 1c9abb39 ` · ` 试试 3-4-5 三角形，数一数小方格： 3的平方 等于 9 , 4的平方 等于 16 。大正方形里有 5的平方 等于 25 个，而 9 加 16 等于 25 。是巧合吗？我们来看看为什么它总是成立。 `
- ` music/music-compose ` · zh · ` 02d356ce ` · ` 和弦与和弦进行。叠在一起的音，按顺序前进。三和弦由某一级音的 1-3-5 叠成。 和弦进行就是和弦的顺序——歌曲的“路线图”。 `

<a id="unbalanced"></a>
### Mismatched delimiter

**Hits** — 3/5 severity, 15 impact — 3 Mandarin clips in 3 lessons and 2 English clips in 2 lessons. 5 clips across 5 distinct lesson IDs.

**Detection** uses the following logic. Stack check for (), （）, [], ［］, {}, 【】, 《》, 〈〉, “”, 「」 and 『』. Flag first unmatched/crossed delimiter.

**Reading and handling (Context)**  
Verify the intended span, then close the correct quote/bracket or recast the sentence to make grouping explicit.

**False positives and limits**  
Outer delimiters can deliberately open in one clip and close in another. Halfwidth/fullwidth pairs can be visually equivalent.

**Observed examples**

- ` astronomy/solar-system ` · en · ` 9d525fe2 ` · ` …. Much farther out, the Oort Cloud may hold trillions of comets. A planet must 1) orbit the Sun, 2) be round, 3) clear its neighborhood. Pluto fails rule 3. `
- ` biology/cells-review ` · en · ` 450c3c36 ` · ` Cell theory and its timeline. 1) All living things are made of one or more cells. 2) The cell is the basic unit of structure and function. 3) All cells come… `
- ` math/slope ` · zh · ` 718cec80 ` · ` 直线从哪里出发？它与 y 轴交于 b 等于 1 , b 叫作（在 y 轴上的）截距。从这里起，每向右 3 就增加 2，所以 y 等于 3分之2 x 加 1 。一般地： y 等于 mx 加 b （我国教材常写作 y 等于 kx 加 b ) `
- ` math/systems ` · zh · ` 95288611 ` · ` 再只用第二个条件——总价：饼干 1 元一块、果汁 2 元一盒，得到 x 加 2y 等于 10 。满足它的（0, 5）、（2, 4）、（4, 3)……同样排成一条直线，但是另一条。 `
- ` yuwen/yw-wenyan-basics ` · zh · ` ec6628ed ` · ` 俄而雪骤，公欣然曰：“白雪纷纷何所似？ `

<a id="stars_and_marks"></a>
### Star or shorthand mark

**Hits** — 4/5 severity, 12 impact — 1 Mandarin clips in 1 lessons and 2 English clips in 2 lessons. 3 clips across 2 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?<![A-Za-z0-9])A\*|\*{1,3}|#[ \t]*[0-9]+|[✓✔✕✖✗✘]
```

**Reading and handling (Context)**  
Sagittarius A* → Sagittarius A star. 人马座 A* → 人马座 A 星. “#1 climate control” → the main factor controlling climate.

**False positives and limits**  
Asterisks can mark multiplication, footnotes or emphasis. Number sign can be rank, number or sharp.

**Observed examples**

- ` astronomy/galaxies ` · en · ` b96e2413 ` · ` Sagittarius A*. The supermassive black hole at the center. About 4 million times the mass of the Sun, packed into a space smaller than Mercury’s orbit. Astr… `
- ` astronomy/galaxies ` · zh · ` 9be7f5e6 ` · ` 人马座 A*。中心的超大质量黑洞。质量约为太阳的 400 万倍，却挤在比水星轨道还小的空间里。天文学家通过追踪绕着一个看不见的天体飞奔的恒星发现了它。2022 年，事件视界望远镜公布了它周围发光气体的第一张照片。它离我们约 2.6 万光年，远到根本不可能把地球吸进去。大多数大星系的中心都有一个超大质量黑洞。 `
- ` earth/climate ` · en · ` 2726e283 ` · ` …t vs. slanted sunlight. Latitude is the #1 climate control. Near the equator the noon Sun is high, so rays hit nearly straight on and their energy is packed… `

<a id="bar"></a>
### Bar separators outside confirmed absolute value

**Hits** — 3/5 severity, 12 impact — 2 Mandarin clips in 1 lessons and 2 English clips in 1 lessons. 4 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[|｜¦]
```

**Reading and handling (Context)**  
If used between UI fields, insert a short pause or connective phrase. If it marks absolute value, speak the full mathematical relation.

**False positives and limits**  
Includes the observed absolute-value bars. Boolean OR, divisibility and layout separators have different readings.

**Observed examples**

- ` math/integers ` · en · ` 7cd8d085 ` · ` The absolute value |a| is a number’s distance from 0. negative5 is 5 steps from zero, so |negative5| equals 5 ; and |5| equals 5 too. A distance is never ne… `
- ` math/integers ` · en · ` d463eb2b ` · ` …are the same distance from 0. Absolute value: |a| is that distance, so |a| equals |negativea| . Order: a is less than b exactly when a is to the left of b . `
- ` math/integers ` · zh · ` 902046e9 ` · ` 把三条规律放在一起。相反数： a 与 负a 到 0 的距离相同。绝对值： |a| 就是这个距离，所以 |a| 等于 |负a| 。大小： a 在 b 的左边，就有 a 小于 b 。 `
- ` math/integers ` · zh · ` bc95f1ea ` · ` 绝对值 |a| 表示一个数到 0 的距离。 负5 离 0 有 5 格，所以 |负5| 等于 5 ； |5| 也等于 5。距离永远不会是负数。 `

<a id="repeat_decimal"></a>
### Repeating-decimal notation flattened

**Hits** — 5/5 severity, 10 impact — 1 Mandarin clips in 1 lessons and 1 English clips in 1 lessons. 2 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:repeat(?:s|ing)?|循环小数)\s*[（(][^）)\r\n]{0,80}(?:equals|等于)\s*[0-9]+\.[0-9]{3,}
```

**Reading and handling (Context)**  
“1 over 7 equals 0.142857” in the repeating-decimal example → one seventh equals zero point one four two eight five seven, with those six digits repeating. Mandarin → 七分之一等于零点一四二八五七，这六位数字不断循环。

**False positives and limits**  
A rounded or finite decimal is different. Confirm which digits repeat against the source and preserve the distinction.

**Observed examples**

- ` math/roots-irrationals ` · en · ` 537131a4 ` · ` … either end ( 1 over 4 equals 0.25 ) or repeat ( 1 over 7 equals 0.142857 ). Those are rational numbers. Numbers like the square root of 2 and pi cannot be … `
- ` math/roots-irrationals ` · zh · ` c21b012f ` · ` 分数就不一样了：它们的小数要么是有限小数（ 4分之1 等于 0.25 ），要么是循环小数（ 7分之1 等于 0.142857 ），这些都是有理数。像 根号2 、 派 这样不能写成分数的数，叫作无理数。 `

<a id="binary_math"></a>
### Raw multiplication, division or subtraction

**Hits** — 4/5 severity, 8 impact — 2 Mandarin clips in 1 lessons and 0 English clips in 0 lessons. 2 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[×÷∙⋅]|(?<=[0-9\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF)）])\s*−\s*(?=[0-9A-Za-z\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U000323AF(（])|(?:[0-9]\s*度)\s+-\s*[0-9]|(?<=[0-9)])\s+-\s+(?=[0-9(])
```

**Reading and handling (Context)**  
“180 度 - 115 度” → 一百八十度减去一百一十五度. Say “multiplied by” or “divided by” with operand boundaries.

**False positives and limits**  
A dash can mark a range or prose aside. Preserve unary signs and mathematical scope.

**Observed examples**

- ` math/angles ` · zh · ` d7e805b9 ` · ` 用起来：一个三角形有两个角是 47 度 和 68 度 。第三个角 x 等于 180 度 - 47 度 - 68 度 等于 65 度 。 `
- ` math/angles ` · zh · ` f204dcbc ` · ` 一个角就够了！这里已知一个角是 115 度 。它的对顶角也是 115 度 ，与它组成平角的相邻角是 180 度 - 115 度 等于 65 度 ，下面的交叉点又是上面的“复制品”。一个角就能求出全部八个角！ `

<a id="blank"></a>
### Fill-in blank

**Hits** — 4/5 severity, 8 impact — 1 Mandarin clips in 1 lessons and 1 English clips in 1 lessons. 2 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
_{2,}|＿{2,}|□{2,}
```

**Reading and handling (Fixed)**  
“钠钾____消耗 ATP” → 钠钾，空格，消耗 A T P. In English say “blank” once for each answer slot.

**False positives and limits**  
Runs can be horizontal decoration or part of code. Restrict the expansion to exercise fields when metadata is available. A single underscore is handled separately.

**Observed examples**

- ` biology/cells-review ` · en · ` 4b747920 ` · ` The sodium-potassium ____ uses ATP to move ions against their gradients. `
- ` biology/cells-review ` · zh · ` 404470e3 ` · ` 钠钾____消耗 ATP，把离子逆浓度梯度运输。 `

<a id="url"></a>
### URL, protocol or email

**Hits** — 4/5 severity, 8 impact — 1 Mandarin clips in 1 lessons and 1 English clips in 1 lessons. 2 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:https?://[^\s”’\"）),，。]*|www\.[^\s”’\"）),，。]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})
```

**Reading and handling (Context)**  
“https://” → say “H T T P S” when teaching the secure protocol. If an address itself is required, speak the domain with “dot” / “点” and spell ambiguous parts.

**False positives and limits**  
Read verbatim structure only when students need to reproduce it. Keep URLs out of ordinary prose where the site can show them.

**Observed examples**

- ` cs/cs-data-crypto ` · en · ` 095aafc6 ` · ` …s is so many that trying them all would take longer than the age of the universe. The padlock and “https://” mean your connection to a website is encrypted. `
- ` cs/cs-data-crypto ` · zh · ` 6401a64e ` · ` 现代加密。今天，计算机用很长的数字作为密钥来打乱数据——通常是128位或256位。2¹ 的平方 ⁸种可能的密钥实在太多，全部试一遍所需的时间比宇宙的年龄还长。浏览器上的小锁和“https://”表示你和网站之间的连接是加密的。 `

<a id="relations"></a>
### Comparison, relation or signed operator glyph

**Hits** — 4/5 severity, 4 impact — 0 Mandarin clips in 0 lessons and 1 English clips in 1 lessons. 1 clips across 1 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
(?:[<>≤≥≠≈≃≡=＝＜＞±∓]|&(?:lt|gt|le|ge);)
```

**Reading and handling (Context)**  
“< 200 years” → less than two hundred years. Use 小于、约等于、正负 where the source distinguishes them. State open or closed bounds explicitly.

**False positives and limits**  
Angle brackets can be markup. An equals sign can be a bond or a label pairing.

**Observed examples**

- ` astronomy/small-bodies ` · en · ` 2eb6d154 ` · ` …ch a third of the way to the nearest star, Proxima Centauri (268,000 AU). Short trips (< 200 years), Kuiper Belt comets; very long trips, Oort Cloud comets. `

<a id="duplicate_marks"></a>
### Repeated or conflicting punctuation

**Hits** — 2/5 severity, 2 impact — 1 Mandarin clips in 1 lessons and 0 English clips in 0 lessons. 1 clips across 1 distinct lesson IDs.

**Detection** uses the following logic. Two or more marks from 。．.!！?？，,、：:；; (optional intermark spaces/tabs), after masking ABBR dotted abbreviations and titles.

**Reading and handling (Fixed)**  
“焦耳，J，,1 J” → “焦耳，字母 J。一个焦耳……” where the source has two statements. Collapse accidental duplicate sentence stops in prose.

**False positives and limits**  
Constructs such as “?!” and intentional ASCII ellipses need their own handling. Mixed separators can indicate a lost sentence boundary, so choose the surviving mark using the template.

**Observed examples**

- ` physics/simple-machines ` · zh · ` 0363552d ` · ` 机械效益与功。机械把力放大了几倍。机械效益 等于 输出力 除以 输入力。机械效益为 4，表示 100 N 的动力能提起 400 N 的重物。功 等于 力 乘 距离，单位是焦耳，J，,1 J 等于 1 N 乘 1 m。机械效益为 4 时，要拉动 4 m 的绳子才能把重物提高 1 m：功不变（理想机械）。 `

<a id="arrow"></a>
### Arrow, progression or reaction glyph

**Hits** — 4/5 severity, 0 impact — 0 Mandarin clips in 0 lessons and 0 English clips in 0 lessons. 0 clips across 0 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
[←→↔↑↓↗↘⇒⇌⇄⟶⟷➜]|(?:->|<-|=>|<=>)
```

**Reading and handling (Context)**  
In a reaction say “yields” / “生成”. In a derivation say “therefore” / “因此”. Read reversible arrows as two-way where the source makes that claim.

**False positives and limits**  
No observed arrows may mean the export strips them, as shown by the missing-relation class. Arrow direction and purpose cannot be guessed from the glyph alone.

No matching clips in this export.

<a id="no_spoken_text"></a>
### Empty or punctuation-only request

**Hits** — 4/5 severity, 0 impact — 0 Mandarin clips in 0 lessons and 0 English clips in 0 lessons. 0 clips across 0 distinct lesson IDs.

**Detection** uses the following Python regex against the exact ` send ` field.

```regex
\A[^\w]*\Z
```

**Reading and handling (Fixed)**  
Skip synthesis for an empty UI-only item. If a symbol or blank is the actual prompt, substitute the spoken label.

**False positives and limits**  
Punctuation-only prompts can represent meaningful signs. A symbol that will be voiced belongs in its specific class too.

No matching clips in this export.

<a id="wrong_script"></a>
### Clip entirely in the other script

**Hits** — 4/5 severity, 0 impact — 0 Mandarin clips in 0 lessons and 0 English clips in 0 lessons. 0 clips across 0 distinct lesson IDs.

**Detection** uses the following logic. zh has a LAT character and no HAN, or en has a HAN character and no LAT.

**Reading and handling (Context)**  
For a Mandarin-track English label, speak an approved Chinese name or deliberately voice its English pronunciation. For a Chinese-only quotation on the English track, use a Mandarin segment or the approved English gloss.

**False positives and limits**  
This is a script heuristic. “kiwi”, a formula, a unit and a name do not identify the language by themselves.

No matching clips in this export.

<a id="pictograph"></a>
### Emoji or other pictographic symbol

**Hits** — 3/5 severity, 0 impact — 0 Mandarin clips in 0 lessons and 0 English clips in 0 lessons. 0 clips across 0 distinct lesson IDs.

**Detection** uses the following logic. First character in U+1F000–1FAFF, U+2600–27BF, U+2300–23FF, U+2500–25FF, or U+FE0E/U+FE0F/U+200D, excluding listed mathematical and direction symbols.

**Reading and handling (Context)**  
Speak the meaning if it carries information, such as “warning” or “correct”. In “高音谱号 𝄞”, use the clef name and omit a redundant glyph.

**False positives and limits**  
Unicode range heuristic includes some UI ornamentation and misses some composite sequences. Music clefs are caught by the note class.

No matching clips in this export.

<a id="visible_control"></a>
### Invisible control or format character

**Hits** — 3/5 severity, 0 impact — 0 Mandarin clips in 0 lessons and 0 English clips in 0 lessons. 0 clips across 0 distinct lesson IDs.

**Detection** uses the following logic. Unicode category Cc, Cf or Cs, excluding tab, newline, CR and U+200D.

**Reading and handling (Fixed)**  
Normalize unexpected zero-width spaces or embedded markers at confirmed word boundaries before submission.

**False positives and limits**  
Some controls encode bidi, accessibility, spelling or grapheme structure. Preserve relevant content and avoid removing a meaningful separator blindly.

No matching clips in this export.

## Reproduce

Run ` python -B textscan.py ` with Python 3.10 or later. The scanner reads the adjacent transcript directory and regenerates this report and ` textscan_classes.json `. The JSON includes every matched ` (lesson, lang, key) ` along with the rules, counts, examples and handling guidance.
