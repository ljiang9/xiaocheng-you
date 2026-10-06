#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小城游 · 文旅局模拟器
你是某十八线小城的文旅局长。国庆 7 天，把有限的"情绪价值点数"
投到美食 / NPC互动 / 夜游 / 限流 / 修厕所，应对一波波热搜级随机事件。
7 天后按 接待量 / 口碑 / 局长发量 结算。祝局长头发安好。
纯标准库：argparse / random / sys / copy。
灵感来源：2026 国庆"小城游/县城游"爆火热搜（"景区热度前十被小城包揽""情绪价值拉满"）。
"""
from __future__ import annotations

import argparse
import random
import sys

PROJECTS = ["美食", "NPC互动", "夜游", "限流", "修厕所"]
DAILY_POINTS = 10
TOTAL_DAYS = 7


class IllegalMove(Exception):
    """非法分配 / 非法输入。"""


class Bureau:
    """一局游戏的状态机。"""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.day = 1
        self.visitors = 0.0      # 累计接待量（万人次）
        self.rep = 60.0          # 口碑 0-100
        self.hair = 100.0        # 局长发量 0-100
        self.log: list[str] = []

    def allocate(self, alloc: dict[str, int]) -> None:
        """校验并记录当日分配。键必须是 5 个项目，值非负整数，总和=DAILY_POINTS。"""
        if set(alloc.keys()) != set(PROJECTS):
            raise IllegalMove(f"项目必须是 {PROJECTS}，收到 {sorted(alloc.keys())}")
        for k, v in alloc.items():
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                raise IllegalMove(f"「{k}」的点数必须是非负整数，收到 {v!r}")
        if sum(alloc.values()) != DAILY_POINTS:
            raise IllegalMove(f"每天恰好 {DAILY_POINTS} 点，收到 {sum(alloc.values())} 点")
        self._alloc = dict(alloc)

    def _pick_event(self) -> str:
        pool: list[tuple[str, int]] = [
            ("游客爆单", 3),
            ("特种兵旅游团杀到", 2),
            ("网红探店", 2),
            ("厕所告急", 2),
            ("本地人上班被堵", 2),
            ("风平浪静", 3),
        ]
        if self.day >= 3:
            pool.append(("万岁山式22倍热度", 1))
        if self.visitors > 40:
            pool.append(("景区被迫限流劝退", 2))
        names = [n for n, _ in pool]
        weights = [w for _, w in pool]
        return self.rng.choices(names, weights=weights, k=1)[0]

    def _apply_event(self, event: str, a: dict[str, int]) -> list[str]:
        msgs: list[str] = [f"【突发】{event}"]
        v, r, h = self.visitors, self.rep, self.hair

        if event == "游客爆单":
            v += 8
            if a["限流"] < 3:
                r -= 8; h -= 5
                msgs.append("人太多被骂上热搜 #小城人挤人#，口碑-8，局长愁掉一把头发")
            else:
                r += 3
                msgs.append("限流得当，游客虽多但有序，口碑+3")
        elif event == "万岁山式22倍热度":
            v += 30; r += 5; h -= 15
            msgs.append("一夜爆火！全网都在问这是哪座小城，接待+30万，局长一夜白头")
        elif event == "景区被迫限流劝退":
            r -= 5; h += 5
            v = min(v, 70)
            msgs.append("景区官宣限流劝退：\"人实在太多了，求放过\"，口碑-5，局长松了口气")
        elif event == "本地人上班被堵":
            if a["限流"] < 2:
                r -= 10; h -= 8
                msgs.append("本地人：这班没法上了！口碑-10")
            else:
                r -= 2
                msgs.append("提前疏导，本地人勉强能上班，口碑-2")
        elif event == "特种兵旅游团杀到":
            if a["NPC互动"] >= 3:
                r += 12; v += 5
                msgs.append("特种兵：NPC 情绪价值拉满，五星好评！口碑+12")
            else:
                r -= 5
                msgs.append("特种兵：就这？差评！口碑-5")
        elif event == "网红探店":
            if a["美食"] >= 3:
                r += 10
                msgs.append("探店博主：这家店我吹爆！口碑+10")
            else:
                v += 2
                msgs.append("博主：味道一般，但人是真多，顺手涨了点客流")
        elif event == "厕所告急":
            if a["修厕所"] < 2:
                r -= 12; h -= 5
                msgs.append("全网热搜 #小城厕所#：游客排队两小时，口碑-12")
            else:
                r += 3
                msgs.append("游客：这厕所比景区还干净，好评+3")
        elif event == "风平浪静":
            h += 3
            msgs.append("难得清闲，局长多长了两根头发")

        self.visitors = max(0.0, v)
        self.rep = min(100.0, max(0.0, r))
        self.hair = min(100.0, max(0.0, h))
        return msgs

    def resolve_day(self, alloc: dict[str, int]) -> list[str]:
        """执行一天：先算项目基础收益，再掷事件。返回当日战报。"""
        self.allocate(alloc)
        a = self._alloc
        msgs = [f"—— 第 {self.day} 天 ——",
                f"分配：{' / '.join(f'{k}{v}' for k, v in a.items())}"]

        dv = 5.0 + a["美食"] * 0.8 + a["NPC互动"] * 0.3 + a["夜游"] * 1.0
        dr = a["美食"] * 1.0 + a["NPC互动"] * 3.0
        self.visitors += dv
        self.rep = min(100.0, self.rep + dr)
        msgs.append(f"基础客流 +{dv:.1f} 万人次，口碑 +{dr:.0f}")

        msgs.extend(self._apply_event(self._pick_event(), a))
        msgs.append(f"当日小结：累计接待 {self.visitors:.1f} 万人次，"
                    f"口碑 {self.rep:.0f}，发量 {self.hair:.0f}")
        self.day += 1
        self.log.extend(msgs)
        return msgs

    def ending(self) -> tuple[str, str]:
        """返回 (结局名, 结局文案)。"""
        v, r, h = self.visitors, self.rep, self.hair
        if r < 35 or h < 25:
            return ("局长连夜跑路",
                    f"口碑 {r:.0f}、发量 {h:.0f} 双双见底。热搜：#某文旅局长已提桶#")
        if v >= 80 and r >= 75:
            return ("下一个淄博",
                    f"7 天接待 {v:.0f} 万人次，口碑 {r:.0f}！全国小城都在学你！")
        if v < 25 and r >= 50:
            return ("劝退成功",
                    f"接待仅 {v:.0f} 万人次但口碑 {r:.0f}。人少景美，本地人狂喜。")
        if r >= 60 and v >= 40:
            return ("细水长流小城",
                    f"接待 {v:.0f} 万人次，口碑 {r:.0f}，稳扎稳打，明年再战。")
        return ("平平无奇小城",
                f"接待 {v:.0f} 万人次，口碑 {r:.0f}。热搜查无此城。")


def ai_allocate(g: Bureau) -> dict[str, int]:
    """贪心 AI：保厕所、看口碑补 NPC、看客流补限流，剩下的冲夜游/美食。"""
    a = {k: 0 for k in PROJECTS}
    a["修厕所"] = 2
    left = DAILY_POINTS - 2
    if g.rep < 55:
        n = min(3, left); a["NPC互动"] += n; left -= n
    if g.visitors > 45:
        n = min(3, left); a["限流"] += n; left -= n
    elif g.rep < 70:
        n = min(2, left); a["美食"] += n; left -= n
    for k in ("夜游", "美食"):
        while left > 0:
            a[k] += 1; left -= 1
            if k == "夜游" and left == 0:
                break
        if left == 0:
            break
    a["夜游"] += left  # 兜底：理论上 left 已为 0
    return a


def play_auto(seed: int, verbose: bool = False) -> tuple[str, Bureau]:
    g = Bureau(seed=seed)
    for _ in range(TOTAL_DAYS):
        msgs = g.resolve_day(ai_allocate(g))
        if verbose:
            print("\n".join(msgs) + "\n")
    name, _ = g.ending()
    return name, g


def play_interactive() -> None:
    if not sys.stdin.isatty():
        print("交互模式需要终端。请用 --auto 看 AI 局长表演。", file=sys.stderr)
        sys.exit(2)
    g = Bureau()
    print("欢迎来到小城文旅局！国庆 7 天，每天 10 点情绪价值点数，祝好运。")
    print(f"项目：{'、'.join(PROJECTS)}（输入 5 个数字，空格分隔，总和须为 {DAILY_POINTS}）")
    while g.day <= TOTAL_DAYS:
        try:
            raw = input(f"\n第 {g.day} 天分配> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n局长提前跑路了。")
            return
        if raw.lower() in ("q", "quit", "退出"):
            print("局长连夜跑路了。")
            return
        try:
            nums = [int(x) for x in raw.split()]
            if len(nums) != len(PROJECTS):
                raise IllegalMove(f"要输入 {len(PROJECTS)} 个数字")
            alloc = dict(zip(PROJECTS, nums))
            msgs = g.resolve_day(alloc)
        except (ValueError, IllegalMove) as e:
            print(f"分配无效：{e}，请重输（或 q 退出）。")
            continue
        print("\n".join(msgs))
    name, text = g.ending()
    print(f"\n★ 结局：{name}\n{text}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="小城游 · 文旅局模拟器：国庆 7 天，小城文旅局长的情绪价值攻防战")
    ap.add_argument("--auto", action="store_true", help="AI 局长自动游玩")
    ap.add_argument("--games", type=int, default=10, help="--auto 时的局数（默认 10）")
    ap.add_argument("--seed", type=int, default=None, help="随机种子，可复现")
    ap.add_argument("--verbose", action="store_true", help="--auto 时打印每局战报")
    args = ap.parse_args(argv)

    if args.auto:
        if args.games < 1:
            print("--games 至少为 1", file=sys.stderr)
            sys.exit(2)
        rng = random.Random(args.seed)
        endings: dict[str, int] = {}
        for i in range(args.games):
            name, g = play_auto(seed=rng.randrange(1 << 30), verbose=args.verbose)
            endings[name] = endings.get(name, 0) + 1
            if args.verbose:
                print(f"第 {i+1} 局结局：{name}"
                      f"（接待 {g.visitors:.0f} 万 / 口碑 {g.rep:.0f} / 发量 {g.hair:.0f}）\n")
        print(f"共 {args.games} 局，结局分布：")
        for name, cnt in sorted(endings.items(), key=lambda kv: -kv[1]):
            print(f"  {name}：{cnt} 局")
    else:
        play_interactive()


if __name__ == "__main__":
    main()
