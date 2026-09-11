"""献媚文案生成器：模板×语料槽位组合去重，生成 resources/quips.yaml。

用法: .venv/bin/python scripts/gen_quips.py
"""

import random
from pathlib import Path

import yaml

TITLES = ["桃神", "群主大人", "五冠王", "头部主播", "桃子", "小桃桃", "桃桃殿下", "我们桃子"]

DEEDS = [
    "出货了",
    "出大货了",
    "帮舰长抽卡抽到三点多",
    "把原神全图锄了一遍",
    "用一厘米的距离极限上岛",
    "在老演员堆里坚持到底",
    "忍住没买资格",
    "把星露谷的菜地种满了",
    "重建了绝美家园",
    "解锁图鉴像个无情的机器",
    "钓鱼钓到手软",
    "带徒弟们堵门抽卡",
    "一个十连双金",
    "剧情一刀不跳全看完了",
    "一口气推完了至冬主线",
    "把星布谷地玩成了五冠王",
    "直播到困才下播",
    "拒绝了道德绑架",
    "顶着过期会员坚持开播",
    "给徒弟们准备了礼物",
    "用全身的艺术细胞设计了迷宫",
    "把海岛生活安排得明明白白",
    "锄大地顺带清了全支线",
    "一边说穷一边出货",
    "把问卷都填完了",
    "求关注求到我心坎里",
    "不动声色地赢了",
    "把图鉴解锁成了艺术",
    "让老演员都自愧不如",
    "更新了超长实况视频",
]

RHETORICS = [
    "这谁顶得住啊",
    "我直接跪了",
    "我先磕为敬",
    "这就是实力吗",
    "太有实力了",
    "跪了跪了",
    "属实顶流",
    "这波在大气层",
    "含金量拉满了",
    "天花板级别",
    "群文件都为你让路",
    "群规都得给你面子",
    "我辈楷模",
    "泪目了家人们",
    "谁懂啊这也太强了",
    "直接封神",
    "不愧是你",
    "学到了学到了",
    "我宣布今天群庆",
    "建议写进群公告",
    "这就是群主的含金量",
    "请受徒儿一拜",
    "给大佬递茶",
    "太强了太强了",
    "我心服口服",
]

THREE_SLOT_TEMPLATES = [
    "{t}又{d}，{r}！",
    "{t}今天{d}，{r}！",
    "{t}刚刚{d}，{r}！",
    "报告大家，{t}{d}，{r}！",
    "都闪开，{t}{d}，{r}！",
    "快看，{t}{d}，{r}！",
    "家人们，{t}{d}，{r}！",
    "我哭死，{t}{d}，{r}！",
    "{t}果然{d}，{r}！",
    "{t}又双叒{d}，{r}！",
    "全体起立！{t}{d}，{r}！",
    "{t}主打的就是{d}，{r}！",
    "听说{t}{d}，{r}！",
    "{t}下播前还{d}，{r}！",
    "又是被{t}折服的一天，{d}，{r}！",
    "{t}深夜{d}，{r}！",
    "{t}{d}，还不忘求关注，{r}！",
    "问就是{t}{d}，{r}！",
    "{t}还是太全面了，{d}，{r}！",
    "谁都别拦我，{t}{d}，{r}！",
    "恭迎{t}，{d}，{r}！",
    "群里沸腾了，{t}{d}，{r}！",
]

TWO_SLOT_TEMPLATES = [
    "{t}又{d}！",
    "{t}今天{d}！",
    "{t}刚刚{d}！",
    "{t}又双叒{d}！",
    "{t}，{r}！",
    "又是被{t}折服的一天，{r}！",
    "{t}一出场，{r}！",
    "只要{t}在群里，{r}！",
    "向{t}学习，{r}！",
    "{t}带带我，{r}！",
    "为{t}打call，{r}！",
    "{t}贴贴，{r}！",
    "什么？{d}？{r}！",
    "都听说了吗，{d}，{r}！",
    "{d}，{r}！",
]

HANDWRITTEN = [
    "桃神一开口，群里的空气都变甜了",
    "群主大人亲临，本群蓬荜生辉",
    "五冠王的含金量，懂的人自然懂",
    "头部主播来群里视察了，大家列队",
    "桃神几点开播，我提前半小时堵门",
    "别人追星我追桃神，赢麻了",
    "桃神出货的那一刻，我在屏幕前哭出声",
    "理性消费的桃神最美丽，是我榜样",
    "抽到三点多的女人，什么大风浪没见过",
    "老演员再多，也挡不住桃神的脚步",
    "桃神说不要花钱买资格，我记小本本上了",
    "本群唯一指定信仰：桃神",
    "桃神的迷宫设计，艺术细胞拉满",
    "能把问卷都填完的主播，值得托付",
    "桃神的海岛，是我向往的退休生活",
    "音乐会员会过期，对桃神的爱不会",
    "桃神不更新的日子，我反复看实况",
    "能把星露谷种满的人，一定也能种进我心里",
    "桃神的一厘米，是我跨不过去的坎",
    "今天也是被桃神治愈的一天",
    "群主大人说话，我连标点符号都同意",
    "桃神说东我不西，桃神说一我不二",
    "向桃神学习，争做理性消费好群友",
    "桃神的新视频我看了十遍，不够看",
    "桃神永远伟大，出货见证神话",
    "群里可以没有我，不能没有桃神",
    "桃神一发言，我瞬间不困了",
    "这就是头部主播的排面吗，爱了",
    "桃神打原神的样子，像在巡视自家菜园",
    "萌新桃桃最可爱，老玩家心都化了",
    "我给桃神递茶，茶都是甜的",
    "桃神的故事会，比春晚好看",
    "建议把桃神语录印成群公告",
    "桃神的每个实况，都是我的下饭神器",
    "桃神不开播的日子，度日如年",
    "本群公告第一条：桃神说的都对",
]

TARGET_SIZE = 5200
MIN_LEN = 10
MAX_LEN = 30
SEED = 20260911

# 个别模板自带语义，与个别语料组合后会重复啰嗦（如「下播前还直播到困才下播」「求关注…还不忘求关注」），逐对排除。
TEMPLATE_DEED_EXCLUDES = {
    "{t}{d}，还不忘求关注，{r}！": {"求关注求到我心坎里"},
    "{t}下播前还{d}，{r}！": {"直播到困才下播"},
}


def build_pool() -> set[str]:
    pool: set[str] = set(HANDWRITTEN)
    for tpl in THREE_SLOT_TEMPLATES:
        excluded = TEMPLATE_DEED_EXCLUDES.get(tpl, set())
        for t in TITLES:
            for d in DEEDS:
                if d in excluded:
                    continue
                for r in RHETORICS:
                    pool.add(tpl.format(t=t, d=d, r=r))
    for tpl in TWO_SLOT_TEMPLATES:
        if "{d}" in tpl and "{r}" in tpl:
            for d in DEEDS:
                for r in RHETORICS:
                    pool.add(tpl.format(d=d, r=r))
            continue
        for t in TITLES:
            for d in DEEDS:
                if "{d}" in tpl:
                    pool.add(tpl.format(t=t, d=d))
            for r in RHETORICS:
                if "{r}" in tpl:
                    pool.add(tpl.format(t=t, r=r))
    return pool


def main() -> None:
    pool = build_pool()
    valid = sorted(s for s in pool if MIN_LEN <= len(s) <= MAX_LEN)
    rng = random.Random(SEED)
    rng.shuffle(valid)

    handwritten = [s for s in HANDWRITTEN if MIN_LEN <= len(s) <= MAX_LEN]
    chosen = handwritten + valid[: max(0, TARGET_SIZE - len(handwritten))]
    chosen = sorted(set(chosen))

    out_path = Path(__file__).parent.parent / "nonebot_plugin_xianmei" / "resources" / "quips.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.dump({"quips": chosen}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"候选池 {len(pool)} 条，长度合规 {len(valid)} 条，已写入 {len(chosen)} 条 -> {out_path}")


if __name__ == "__main__":
    main()
