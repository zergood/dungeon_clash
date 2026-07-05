#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║          DUNGEON CLASH  ⚔                    ║
║    ASCII D&D combat — run: python dungeon_clash.py
╚══════════════════════════════════════════════╝

Controls: type H / T / L and press ENTER each turn.
  H = Head  |  T = Torso  |  L = Legs

No external dependencies required.
"""

import os
import random
import sys
import time

# ── helpers ──────────────────────────────────────────────────────────────────


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def wait(t=0.8):
    time.sleep(t)


def pause(msg="  [ Press ENTER to continue ] "):
    input(msg)


def hpbar(hp, max_hp, width=22):
    hp = max(0, hp)
    filled = int((hp / max_hp) * width)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {hp:>3}/{max_hp}"


# ── zones ─────────────────────────────────────────────────────────────────────
#  key → (display name, base damage, hit probability)
ZONES = {
    "H": ("HEAD", 22, 0.55),
    "T": ("TORSO", 14, 0.75),
    "L": ("LEGS", 8, 0.92),
}


def zname(k):
    return ZONES[k][0]


def zdmg(k):
    return ZONES[k][1]


def zhit(k):
    return ZONES[k][2]


# ── ASCII art ─────────────────────────────────────────────────────────────────

TITLE = r"""
  ____  _   _ _   _  ____ _____ ___  _   _
 |  _ \| | | | \ | |/ ___| ____/ _ \| \ | |
 | | | | | | |  \| | |  _|  _|| | | |  \| |
 | |_| | |_| | |\  | |_| | |__| |_| | |\  |
 |____/ \___/|_| \_|\____|_____\___/|_| \_|

        ██████╗██╗      █████╗ ███████╗██╗  ██╗
       ██╔════╝██║     ██╔══██╗██╔════╝██║  ██║
       ██║     ██║     ███████║███████╗███████║
       ██║     ██║     ██╔══██║╚════██║██╔══██║
       ╚██████╗███████╗██║  ██║███████║██║  ██║
        ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""

ART = {
    # player classes
    "Warrior": [
        r"    \O/   ",
        r"     |    ",
        r"    /|\   ",
        r"   / | \  ",
    ],
    "Rogue": [
        r"    .O.   ",
        r"    /|    ",
        r"   d/ \   ",
        r"        ~ ",
    ],
    "Mage": [
        r"   ~*O*~  ",
        r"    /|\   ",
        r"   / | \  ",
        r"  *     * ",
    ],
    # enemies
    "Goblin": [
        r"    ,-.   ",
        r"   (o.o)  ",
        r"    )=(   ",
        r"   /| |\  ",
    ],
    "Skeleton": [
        r"    (*)   ",
        r"    \|/   ",
        r"     |    ",
        r"    / \   ",
    ],
    "Orc": [
        r"   _____  ",
        r"  (O   O) ",
        r"   \___/  ",
        r"   |||||  ",
        r"  /     \ ",
    ],
    "Dark Knight": [
        r"   /___\  ",
        r"  | X X | ",
        r"   \___/  ",
        r"   |||||  ",
        r"  /=====\ ",
    ],
    "Dragon": [
        r"  /\ _ /\ ",
        r" ( o   o )",
        r"  \  V  / ",
        r" <|=====|>",
        r"  |_____|  ",
    ],
}


def print_art(name, indent=6):
    lines = ART.get(name, ["  ???  "])
    for line in lines:
        print(" " * indent + line)


# ── classes ───────────────────────────────────────────────────────────────────

CLASSES = {
    "1": {
        "name": "Warrior",
        "hp": 100,
        "atk": 1.10,  # damage multiplier
        "blk": 0.65,  # fraction blocked when guarding correctly
        "dodge": 0.00,
        "desc": "100 HP  |  +10% dmg  |  65% block",
        "quote": '"Steel and shield!"',
    },
    "2": {
        "name": "Rogue",
        "hp": 75,
        "atk": 1.00,
        "blk": 0.45,
        "dodge": 0.22,  # 22% chance to dodge any hit entirely
        "desc": " 75 HP  |  22% dodge |  45% block",
        "quote": '"You\'ll never see me."',
    },
    "3": {
        "name": "Mage",
        "hp": 60,
        "atk": 1.45,
        "blk": 0.35,
        "dodge": 0.00,
        "desc": " 60 HP  |  +45% dmg  |  35% block",
        "quote": '"Arcane power flows through me."',
    },
}

# ── enemy templates ───────────────────────────────────────────────────────────

ENEMY_TEMPLATES = [
    {
        "name": "Goblin",
        "hp": 42,
        "atk": 0.75,
        "blk": 0.40,
        "bias": ["L", "L", "T"],  # prefers low sweeps
        "intro": "A sneaky Goblin drops from the ceiling!",
        "xp": 30,
        "loot": ["Gold Coins", "Rusty Dagger", "Stolen Bread"],
    },
    {
        "name": "Skeleton",
        "hp": 58,
        "atk": 0.90,
        "blk": 0.45,
        "bias": ["T", "T", "H"],
        "intro": "Bones rattle — a Skeleton rises from the floor!",
        "xp": 45,
        "loot": ["Bone Fragment", "Bronze Coin", "Old Scroll"],
    },
    {
        "name": "Orc",
        "hp": 85,
        "atk": 1.05,
        "blk": 0.55,
        "bias": ["H", "H", "T"],  # aggressive headhunter
        "intro": "An Orc warrior charges with a battle cry!",
        "xp": 70,
        "loot": ["Crude Axe", "Leather Strip", "Orc Fang"],
    },
    {
        "name": "Dark Knight",
        "hp": 110,
        "atk": 1.20,
        "blk": 0.65,
        "bias": ["H", "T", "H"],
        "intro": "A Dark Knight steps from the shadows. Eyes gleaming red.",
        "xp": 100,
        "loot": ["Dark Iron Shard", "Knight's Crest", "Cursed Coin"],
    },
    {
        "name": "Dragon",
        "hp": 180,
        "atk": 1.50,
        "blk": 0.70,
        "bias": ["H", "T", "L"],  # balanced, unpredictable
        "intro": "THE DRAGON AWAKENS.  Its roar shakes the dungeon walls!!!",
        "xp": 250,
        "loot": ["Dragon Scale", "Legendary Gem", "Ancient Gold"],
        "boss": True,
    },
]


def spawn_enemy(template, floor):
    """Return a fresh enemy dict scaled to current floor."""
    scale = 1.0 + (floor - 1) * 0.18
    e = dict(template)
    e["hp"] = int(template["hp"] * scale)
    e["max_hp"] = e["hp"]
    e["atk"] = round(template["atk"] * scale, 3)
    return e


# ── combat engine ─────────────────────────────────────────────────────────────


def resolve(atk_zone, def_zone, atk_mult, blk_mult, dodge=0.0):
    """
    Resolve one strike.
    Returns (damage_dealt, result_type)
    result_type: 'dodge' | 'miss' | 'blocked' | 'hit'
    """
    if dodge > 0 and random.random() < dodge:
        return 0, "dodge"

    _, base, hit_prob = ZONES[atk_zone]
    if random.random() > hit_prob:
        return 0, "miss"

    dmg = int(base * atk_mult)

    if atk_zone == def_zone:
        reduced = max(1, int(dmg * (1.0 - blk_mult)))
        return reduced, "blocked"

    return dmg, "hit"


def enemy_ai(enemy):
    """Simple AI: pick attack from bias pool, defense randomly."""
    atk = random.choice(enemy["bias"])
    dfn = random.choice(["H", "T", "L"])
    return atk, dfn


# ── display helpers ───────────────────────────────────────────────────────────

DIVIDER = "  " + "═" * 54
THIN_DIV = "  " + "─" * 54


def print_combat_header(gs, enemy):
    clear()
    print()
    print(DIVIDER)
    print(
        f"  ⚔  Floor {gs['floor']}  │  {gs['name']} the {gs['cls']['name']}"
        f"  │  Lvl {gs['level']}  │  XP {gs['xp']}/{xp_needed(gs['level'])}"
    )
    print(DIVIDER)
    print()

    col_w = 26
    # Hero side
    hero_lines = ART.get(gs["cls"]["name"], [])
    enemy_lines = ART.get(enemy["name"], [])

    max_art = max(len(hero_lines), len(enemy_lines))
    hero_lines = hero_lines + [""] * (max_art - len(hero_lines))
    enemy_lines = enemy_lines + [""] * (max_art - len(enemy_lines))

    for h, e in zip(hero_lines, enemy_lines):
        print(f"  {h:<{col_w}}  {e}")

    print()
    print(f"  {gs['name']:^{col_w}}   {enemy['name']}")
    print(f"  {hpbar(gs['hp'], gs['max_hp']):^{col_w}}   {hpbar(enemy['hp'], enemy['max_hp'])}")
    print()


def print_zone_help():
    print(THIN_DIV)
    print("  ZONE     DAMAGE   HIT CHANCE")
    print("  [H] Head    22      55%    ← high risk / high reward")
    print("  [T] Torso   14      75%    ← balanced")
    print("  [L] Legs     8      92%    ← safe chip damage")
    print(THIN_DIV)


def ask_zone(prompt):
    while True:
        v = input(prompt).strip().upper()[:1]
        if v in ZONES:
            return v
        print("  → Enter H, T, or L")


# ── main combat loop ──────────────────────────────────────────────────────────


def do_combat(gs, enemy):
    print()
    print("  " + "!" * 54)
    print(f"  {enemy['intro']}")
    print("  " + "!" * 54)
    wait(1.2)
    print_art(enemy["name"])
    pause()

    turn = 1
    while gs["hp"] > 0 and enemy["hp"] > 0:
        print_combat_header(gs, enemy)
        print(f"  ── Turn {turn} ──\n")
        print_zone_help()

        p_atk = ask_zone("  Your ATTACK zone  → ")
        p_def = ask_zone("  Your DEFEND zone  → ")

        e_atk, e_def = enemy_ai(enemy)

        print()
        print(DIVIDER)
        print("  RESOLUTION")
        print(THIN_DIV)

        # --- player strikes enemy ---
        dmg, rtype = resolve(p_atk, e_def, gs["cls"]["atk"], enemy["blk"])
        if rtype == "miss":
            print(f"  ✗  You swing at {zname(p_atk)}... MISS!")
        elif rtype == "blocked":
            print(f"  ⚔  You hit {zname(p_atk)} — {enemy['name']} BLOCKS! Only {dmg} damage.")
        else:
            print(f"  ⚔  UNGUARDED! You strike {zname(p_atk)} for {dmg} damage!")
        enemy["hp"] = max(0, enemy["hp"] - dmg)

        print()

        # --- enemy strikes player ---
        print(f"  {enemy['name']} attacks your {zname(e_atk)}  (you guard {zname(p_def)})")
        dmg2, rtype2 = resolve(e_atk, p_def, enemy["atk"], gs["cls"]["blk"], gs["cls"]["dodge"])
        if rtype2 == "dodge":
            print("  ✦  You DODGE the attack entirely!")
        elif rtype2 == "miss":
            print(f"  ✗  {enemy['name']} misses!")
        elif rtype2 == "blocked":
            print(f"  🛡  BLOCKED! Only {dmg2} damage gets through.")
        else:
            print(f"  💥  UNGUARDED! {enemy['name']} hits your {zname(e_atk)} for {dmg2} damage!")
        gs["hp"] = max(0, gs["hp"] - dmg2)

        print(DIVIDER)
        wait(0.4)
        pause()
        turn += 1

    if gs["hp"] <= 0:
        return "dead"

    # ── victory ──
    leveled = add_xp(gs, enemy["xp"])
    gs["kills"] += 1
    drop = random.choice(enemy["loot"])
    gs["loot"].append(drop)

    clear()
    print()
    print("  ★ ★ ★  VICTORY  ★ ★ ★")
    print(f"\n  You defeated the {enemy['name']}!")
    print(f"  +{enemy['xp']} XP  │  Loot: {drop}")

    if leveled:
        print(f"\n  *** LEVEL UP!  You are now level {gs['level']}! ***")
        print(f"  HP raised to {gs['max_hp']}.")

    heal = random.randint(6, 18)
    gs["hp"] = min(gs["max_hp"], gs["hp"] + heal)
    print(f"\n  You rest briefly.  Restored {heal} HP.  (HP: {gs['hp']}/{gs['max_hp']})")
    print()
    pause()
    return "win"


# ── progression ───────────────────────────────────────────────────────────────


def xp_needed(level):
    return level * 80


def add_xp(gs, amount):
    gs["xp"] += amount
    leveled = False
    while gs["xp"] >= xp_needed(gs["level"]):
        gs["xp"] -= xp_needed(gs["level"])
        gs["level"] += 1
        bonus = random.randint(8, 16)
        gs["max_hp"] += bonus
        gs["hp"] = min(gs["hp"] + bonus, gs["max_hp"])
        leveled = True
    return leveled


# floor → list of possible enemies to pick from
FLOORS = [
    [ENEMY_TEMPLATES[0]],  # 1 — Goblin
    [ENEMY_TEMPLATES[0], ENEMY_TEMPLATES[1]],  # 2 — Goblin / Skeleton
    [ENEMY_TEMPLATES[1], ENEMY_TEMPLATES[2]],  # 3 — Skeleton / Orc
    [ENEMY_TEMPLATES[2], ENEMY_TEMPLATES[3]],  # 4 — Orc / Dark Knight
    [ENEMY_TEMPLATES[4]],  # 5 — Dragon BOSS
]


def run_dungeon(gs):
    for floor_num, pool in enumerate(FLOORS, start=1):
        gs["floor"] = floor_num
        is_boss = floor_num == len(FLOORS)

        clear()
        print()
        if is_boss:
            print("  " + "█" * 54)
            print(f"  ██  FLOOR {floor_num}  ──  BOSS CHAMBER  ██")
            print("  " + "█" * 54)
        else:
            print("  " + "═" * 36)
            print(f"  ═══   FLOOR {floor_num}   ═══")
            print("  " + "═" * 36)

        wait(1.0)
        pause()

        template = random.choice(pool)
        enemy = spawn_enemy(template, floor_num)
        result = do_combat(gs, enemy)

        if result == "dead":
            screen_death(gs)
            return False

    screen_victory(gs)
    return True


# ── screens ───────────────────────────────────────────────────────────────────


def screen_title():
    clear()
    print(TITLE)
    print("  " + "═" * 54)
    print("  Each turn: choose WHERE to attack and WHERE to guard.")
    print("  Hit an unguarded zone for full damage.")
    print("  Block correctly to reduce incoming hits.")
    print("  " + "═" * 54)
    print()
    pause("  [ Press ENTER to begin ] ")


def screen_name():
    clear()
    print("\n  What is your name, adventurer?\n")
    name = input("  > ").strip()
    return name if name else "Stranger"


def screen_class():
    while True:
        clear()
        print("\n  Choose your class:\n")
        print("  " + "─" * 44)
        for key, c in CLASSES.items():
            print(f"  [{key}]  {c['name']:10s}  {c['desc']}")
            print(f"         {c['quote']}")
            print()
        print("  " + "─" * 44)
        ch = input("  > ").strip()
        if ch in CLASSES:
            cls = CLASSES[ch]
            clear()
            print(f"\n  You chose: {cls['name']}\n")
            print_art(cls["name"])
            print(f"\n  {cls['quote']}\n")
            wait(0.8)
            pause()
            return cls


def screen_death(gs):
    clear()
    print(r"""
  ██████╗ ███████╗ █████╗ ██████╗
  ██╔══██╗██╔════╝██╔══██╗██╔══██╗
  ██║  ██║█████╗  ███████║██║  ██║
  ██║  ██║██╔══╝  ██╔══██║██║  ██║
  ██████╔╝███████╗██║  ██║██████╔╝
  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝
    """)
    print(f"  {gs['name']} the {gs['cls']['name']} fell in the dungeon...")
    print(
        f"  Floor reached: {gs['floor']}  │  Enemies slain: {gs['kills']}  │  Level: {gs['level']}"
    )
    if gs["loot"]:
        print(f"  Loot collected: {', '.join(gs['loot'])}")
    print()
    print("  The dungeon claims another soul.")
    print()


def screen_victory(gs):
    clear()
    print(r"""
 __   _____ ___ _____ ___  _____   _
 \ \ / /_ _/ __|_   _/ _ \|  _ \ \ / |
  \ V / | | (__  | || (_) | |_) \ V /
   \_/ |___\___| |_| \___/|____/ |_|
    """)
    print(f"  {gs['name']} the {gs['cls']['name']} conquered the dungeon!")
    print(f"  Level {gs['level']}  │  {gs['kills']} kills")
    print(f"  Loot: {', '.join(gs['loot']) if gs['loot'] else 'nothing'}")
    print()
    print("  A legend is born.")
    print()


# ── entry point ───────────────────────────────────────────────────────────────


def new_game():
    screen_title()
    name = screen_name()
    cls = screen_class()
    gs = {
        "name": name,
        "cls": cls,
        "hp": cls["hp"],
        "max_hp": cls["hp"],
        "xp": 0,
        "level": 1,
        "floor": 1,
        "kills": 0,
        "loot": [],
    }
    return gs


def main():
    while True:
        gs = new_game()
        run_dungeon(gs)
        print()
        again = input("  Play again? [y/N]  ").strip().lower()
        if again != "y":
            print("\n  May your blade stay sharp. Farewell.\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  May your blade stay sharp. Farewell.\n")
        sys.exit(0)
