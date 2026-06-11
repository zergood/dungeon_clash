# Dungeon Clash — Game Design Document
**Version:** 0.3 (Draft)
**Status:** Bestiary, Relics, Equipment filled. Player psychology section added. Awaiting unique content pass (10–20%).

---

## Table of Contents
1. [Vision & Concept](#1-vision--concept)
2. [Core Pillars](#2-core-pillars)
3. [Target Audience](#3-target-audience)
4. [Player Psychology & Design Constraints](#4-player-psychology--design-constraints)
5. [Game Modes](#5-game-modes)
6. [Strategy System](#6-strategy-system)
7. [World Structure & Map](#7-world-structure--map)
8. [Combat System](#8-combat-system)
9. [Stress System](#9-stress-system)
10. [Magic System](#10-magic-system)
11. [Resources](#11-resources)
12. [Equipment & Crafting](#12-equipment--crafting)
13. [Bestiary](#13-bestiary)
14. [Room Events](#14-room-events)
15. [Relics](#15-relics)
16. [Progression & Meta-progression](#16-progression--meta-progression)
17. [Roadmap](#17-roadmap)

---

## 1. Vision & Concept

**Dungeon Clash** is a console-native ASCII dungeon crawler built for developers. It lives in the terminal alongside your work — unobtrusive, asynchronous, always there when you want a break.

The core fantasy: your hero explores a dungeon while you write code. When you glance at your terminal pane, you see what happened. When you want to play properly, you take control. When you go back to work, your strategy script takes over.

The game is intentionally minimalist in presentation and deep in systems. It respects the player's attention.

> **Setting:** Classic D&D fantasy world. Dungeons, swords, magic, monsters. Occasional subtle developer easter eggs — rare enough to smile at, never the main theme.
>
> *Examples of the right tone:*
> - A cursed artifact called "The Legacy Scroll" — nobody knows how to remove it and everyone is afraid to touch it
> - A blacksmith NPC who says "works on my forge"
> - A monster called "Segfault Wraith" that appears without warning

---

## 2. Core Pillars

**1. Respects your attention**
The game never forces you to engage. No mandatory timers, no punishing interruptions. You check in when you want.

**2. Strategy as code**
Your character's passive behavior is defined by a Python function you write. Debugging why your hero died while you were in a meeting is part of the gameplay.

**3. Risk is a decision, not a punishment**
Deeper floors offer better rewards, but you choose when to push forward and when to extract. Death hurts but doesn't erase progress.

**4. Systems that talk to each other**
Stress affects combat, which affects resources, which affects your strategy options, which affects how you play the map. No mechanic exists in isolation.

---

## 3. Target Audience

**Primary:** Software developers, 20–40, who play games but don't have time for sessions. Comfortable with terminals, Python, and the idea of writing code as gameplay.

**Profile:**
- Has a terminal window open most of the day
- Appreciates mechanical depth over visual spectacle
- Will read patch notes and think about optimization
- Won't read a 40-page tutorial

**Key insight:** This audience will immediately spot forced "dev humor." The game earns their respect through clever systems, not by winking at them constantly.

---

## 4. Player Psychology & Design Constraints

This section documents what players consistently love and hate across the genres closest to Dungeon Clash — roguelikes, Darkest Dungeon-style games, and idle RPGs. Every design decision should be checked against this list.

Sources: player reviews, Steam discussions (Darkest Dungeon, Slay the Spire), game design analysis articles (2024–2025), research on randomness and player agency.

---

### 4.1 What Players Hate — and How We Respond

#### ❌ RNG that overrides decisions
**The complaint:** Losing a run because of a single unlucky dice roll — not a bad decision, just bad luck. Players consistently describe this as the #1 frustration in roguelikes. When randomness happens *after* the decision ("post-action luck"), the player's agency feels fake.

**Our response:**
- Zone hit chances are shown *before* the player chooses (55% HEAD, 75% TORSO, 92% LEGS). The player is betting on known odds, not discovering them after committing.
- Enemy zone bias is learnable across runs. Patterns are real and consistent, not re-randomized each fight.
- The Scholar's Lens relic reveals bias at fight start. This is a choice — players who want full information can build for it.

---

#### ❌ Progress erased in one unfair moment
**The complaint:** Darkest Dungeon is the canonical example. Players invest hours leveling heroes, then lose a full party in 5 minutes to a bad RNG cascade. The sunk-cost of the lost progress feels disproportionate to the "mistake" made.

**Our response:**
- No permadeath. Death means losing a portion of carried resources — never meta-progress or permanent character stats.
- Death penalties are asymmetric by design: Gold −50%, Ore/Materials −25%, permanent upgrades −0%.
- Push-your-luck decisions are *explicit*. The player actively chooses to stay on a floor. Death after that choice feels earned, not arbitrary.

---

#### ❌ Unbalanced punishment mechanics (Darkest Dungeon's stress)
**The complaint:** DD's stress system is universally cited as its most divisive mechanic. Enemies deal 20+ stress per attack; players can barely recover it. Afflictions stack in a single round with extreme costs to remove. Players feel the system punishes rather than creates tension.

**Our response:**
- Stress operates as **thresholds**, not a bleeding resource. You're either Calm, Rattled, Panicking, or Breaking — not sliding down a hidden damage-per-turn number.
- Thresholds are transparent and visible at all times in the UI.
- Each threshold has a *specific, readable* consequence. Players know exactly what changes at 70%.
- Recovery options are plentiful: rest rooms, relics, killing in one blow, specific spells.
- The breakdown at 100% (auto-flee) is *protective*, not terminal. You lose resources, not the run.

---

#### ❌ Repetitive early-game on every run
**The complaint:** Roguelikes force players to replay early content repeatedly to reach late-game builds. The first floors become a mindless blur. Slay the Spire partially solved this with persistent meta-upgrades (Neow's blessing, unlocked cards).

**Our response:**
- **Passive mode farms old floors automatically.** You never have to manually re-play mastered content.
- Once a floor is cleared in active mode, it's unlocked for passive farming forever.
- Meta-upgrades (Hall of Upgrades) provide permanent bonuses that make early floors faster on subsequent active runs.

---

#### ❌ Idle games becoming babysitters
**The complaint:** Idle games start passive then gradually add more and more systems until they require daily check-ins and constant micro-management. Players describe the shift from "idle" to "24/7 babysitter." The daily obligation loop ("log in or miss rewards") is deeply resented.

**Our response:**
- **No time-gated rewards.** Nothing expires if you don't check in. Passive resources accumulate indefinitely.
- The game never sends you a notification, pings you, or punishes absence. You open `dungeon status` when *you* want.
- There is no "daily quest" system. Ever.
- The passive strategy runs correctly even if you don't look at the game for three days.

---

#### ❌ Decisions made on incomplete information
**The complaint:** Being punished for a reasonable decision made with the information available at the time. The Mimic is a canonical example — if there's no tell, discovering one feels purely unfair.

**Our response:**
- The Mimic has a *discoverable* tell: it appears in rooms logged as "CHEST" but its encounter probability on deeper floors is known to the player (documented in the journal). Experienced players will hedge in their strategy (`event_choice` can account for Mimic risk).
- Every enemy's special mechanic is shown in the combat log on first encounter. It's always logged even in passive mode, so the player can learn after the fact.
- Push-your-luck extraction shows exact current HP, stress, and floor enemy pool before the player decides.

---

### 4.2 What Players Love — and How We Amplify It

#### ✅ Losses that feel traceable to a decision
**Why it works:** Slay the Spire is praised specifically for this. Players say: *"I can usually trace my death back to a decision or risk that didn't pan out."* This transforms frustration into motivation.

**How we ensure it:**
- The combat log in passive mode records every turn with full context: zone chosen, enemy zone, hit result, damage. The player can read exactly why HP dropped.
- Strategy exceptions are logged with stack traces. `[STRATEGY ERROR on turn 4: KeyError 'arcane_crystals']` is a clue, not a mystery.
- Death screen shows the last 10 log entries, the stress level at death, and the floor.

---

#### ✅ Pre-action luck (randomness before the decision)
**Why it works:** Carnegie Mellon research confirms random rewards increase engagement — but *only when players feel in control*. Pre-action luck (you're given a random hand, then you decide how to play it) enhances satisfaction. Post-action luck (you commit, then roll) reduces it.

**How we use it:**
- Random shop inventory, random chest loot, random relic drops → player chooses how to respond.
- Hit chance variance (a HEAD attack has a 55% base chance) is declared before the swing. The player is making a probabilistic bet with stated odds, not discovering the result of a hidden roll after the fact.
- Floor map routes are randomly generated but *fully visible before the player chooses their path*.

---

#### ✅ Synergies between mechanics
**Why it works:** The "a-ha" moment when two mechanics combine unexpectedly is the most-cited reason players keep returning to Slay the Spire and Binding of Isaac. It creates emergent complexity from simple parts.

**Examples in our game:**
- `Odd Mushroom` relic + `Mage` class + low HP build → enters Panicking, gets ATK +20%, hits extremely hard with +45% class bonus
- `Regen Troll` + `Staff` weapon → you're slower but generate arcane crystals; use Fireball (ignores armor) to race his regeneration
- `Greatsword` + `Scholar's Lens` → you know exactly which zone to hit (HEAD/TORSO only), zero wasted swings
- High stress + `Odd Mushroom` + `Blood Cultist` fight → deliberately letting stress rise to trigger the bonus before the Cultist's Blood Frenzy one-shots you

---

#### ✅ Permanent meta-progression
**Why it works:** Players tolerate — and enjoy — restarting when each run builds toward something persistent. Hades built an entire narrative around this. Slay the Spire uses it for card unlocks. The feeling of "this run contributed something even though I lost" is crucial.

**How we use it:**
- Hall of Upgrades: permanent HP, stress thresholds, action unlocks.
- Enemy Materials drop on death too (just less) — no run is ever truly wasted.
- Floor unlocks are permanent. The first time you reach floor 5, it's unlocked for passive farming forever.

---

#### ✅ Meaningful optimization
**Why it works:** The developer audience specifically enjoys finding the optimal solution. Unlike casual players, they will read logs, benchmark strategies, and iterate. This is not a bug — it's the core engagement loop for this audience.

**How we enable it:**
- Strategy-as-code: the optimization *is* the gameplay.
- Detailed combat logs with damage numbers, hit rolls, and stress values.
- `dungeon log --stats` command shows: avg damage dealt/taken, stress accumulated, gold/floor, death causes (v2).
- Strategy sharing system allows comparison of different approaches on the same floor.

---

### 4.3 Design Rules Derived from Research

These rules apply to every future design decision.

| Rule | Rationale |
|------|-----------|
| Never punish absence | Idle game babysitting is the top complaint in the genre |
| Always show odds before the bet | Pre-action luck is loved; post-action luck is resented |
| Every death must be logged in detail | Traceable losses feel fair; mystery deaths feel unfair |
| No permanent progress on death | Losing hours of work to one unlucky moment is the top roguelike complaint |
| Stress must be readable and recoverable | DD's stress is the most-criticized mechanic in the genre |
| Every mechanic must interact with at least one other | Synergies are the primary source of player delight |
| Early game must never require replaying manually | Passive mode exists specifically to eliminate this friction |

---

## 5. Game Modes

### 4.1 Passive Mode (default)
The hero acts autonomously according to the player's strategy script. The game logs every event to a persistent log. No interruptions.

The player can check in at any time:
```
$ dungeon status       → current floor, HP, stress, last events
$ dungeon log          → full session log
$ dungeon log --last 5 → last 5 events
```

### 4.2 Active Mode
Full player control. Event-driven — nothing happens until you make a decision. Launched with:
```
$ dungeon play
```

Switching between modes is seamless. Exiting active mode hands control back to the strategy script at the exact game state where you left off.

### 4.3 Mode Switching Logic
```
passive (strategy runs) ←→ dungeon play ←→ active (you decide)
                                ↑
                         exit anytime,
                    strategy resumes from here
```

In passive mode, the strategy function receives the full game state and returns actions. If the strategy raises an exception or returns an invalid action, the character skips the turn and the error is logged — this is intentional. Debugging your strategy is part of the game.

---

## 5. Strategy System

The player defines their character's passive behavior as a Python function. This is the primary progression mechanic in the mid-to-late game.

### 5.1 Basic Example
```python
def strategy(state):
    if state.hp_pct < 0.35:
        return flee()

    if state.stress_pct > 0.80:
        return flee()

    if state.enemy.hp < 15:
        return attack("HEAD"), defend("TORSO")

    return attack("TORSO"), defend("HEAD")
```

### 5.2 State Object
The `state` object passed to the strategy contains:

```python
state.hp            # current HP
state.max_hp        # max HP
state.hp_pct        # HP as 0.0–1.0

state.stress        # current stress (0–100)
state.stress_pct    # stress as 0.0–1.0

state.floor         # current dungeon floor
state.room          # current room type

state.enemy.name    # enemy name
state.enemy.hp      # enemy current HP
state.enemy.max_hp
state.enemy.stress_attacker  # True if enemy causes stress

state.gold          # current gold
state.arcane        # arcane crystals (magic resource)

state.relics        # list of active relic names
state.spells        # list of available spells
```

### 5.3 Available Actions

**Early game (always available):**
```python
attack("HEAD" | "TORSO" | "LEGS")
defend("HEAD" | "TORSO" | "LEGS")
flee()           # leave dungeon, keep resources
extract()        # safely exit current floor (push-your-luck trigger)
rest()           # use a rest room (reduces stress, costs gold)
```

**Unlocked through progression:**
```python
cast("spell_name")     # magic spells (deep floors)
use_item("item_name")  # consumables from inventory
```

### 5.4 Strategy as Progression
Unlocking new actions and conditions is tied to resources and meta-upgrades. A fresh character has access to only `attack`, `defend`, and `flee`. Richer strategic options are earned.

---

## 6. World Structure & Map

### 6.1 Dungeon Structure
The dungeon consists of **floors**, each floor consists of a **branching map of rooms**. The player (or strategy) navigates from the entrance to the exit.

```
FLOOR 7
                    [REST]
                   /
[ENTRANCE] → [?] → [ELITE] → [CHEST] → [EXIT]
                   \
                    [SHOP] → [NORMAL]
```

### 6.2 Room Types

| Icon | Type | Description |
|------|------|-------------|
| ⚔ | Normal combat | Standard enemy encounter |
| 💀 | Elite combat | Stronger enemy, better loot |
| 🏪 | Shop | Buy/sell items, relics, potions |
| 🔥 | Event | Random event with a choice |
| 🛌 | Rest | Spend gold to reduce stress / recover HP |
| 📦 | Chest | Loot room, may contain trap |
| ? | Mystery | Unknown until entered |
| 👑 | Boss | Floor boss, required to progress |

### 6.3 Floor Depth & Themes

| Floors | Theme | Ore | New Feature |
|--------|-------|-----|-------------|
| 1–2 | Stone Tunnels | Stone | Basic combat |
| 3–4 | Catacombs | Copper | Stress introduced |
| 5–6 | Dark Halls | Iron | Relics introduced |
| 7–8 | Cursed Vaults | Silver | Magic unlocked |
| 9–10 | Abyss | Steel | Arcane enemies |
| 11+ | TBD | TBD | TBD |

Each theme has unique enemy types, event flavor, and environmental effects.

### 6.4 Map Navigation in Strategy
In passive mode, the strategy can express path preference:
```python
def map_choice(options):
    if state.stress_pct > 0.6:
        return prefer(options, "REST", "NORMAL")
    if state.gold > 80:
        return prefer(options, "SHOP")
    return prefer(options, "ELITE", "NORMAL")
```

---

## 7. Combat System

### 7.1 Zone Targeting
Each combat turn consists of two simultaneous decisions: **where to attack** and **where to defend**.

| Zone | Base Damage | Hit Chance | Notes |
|------|-------------|------------|-------|
| HEAD | 22 | 55% | High risk / high reward |
| TORSO | 14 | 75% | Balanced |
| LEGS | 8 | 92% | Safe chip damage |

**Resolution:**
- If the attacker hits a zone the defender is NOT guarding → full damage
- If the attacker hits the guarded zone → damage reduced by defender's block stat
- If attack roll fails hit chance → miss

Both sides resolve simultaneously. Each round: player acts, enemy acts, results shown.

### 7.2 Damage Formula
```
final_dmg = base_dmg × attacker_str_mult
if zone == defended_zone:
    final_dmg = max(1, final_dmg × (1 - block_pct))
```

### 7.3 Enemy AI
Enemies have **zone biases** — weighted tendencies for where they attack. This is intentional and discoverable: learning an enemy's patterns is how you tune your strategy for that floor.

Enemies do NOT defend perfectly. Their defense zone is chosen each turn from their own bias pool, creating exploitable patterns.

### 7.4 Combat Modifiers from Stress
See Section 8.

### 7.5 Special Enemy Mechanics
Beyond HP/damage/zone differences, some enemies have unique mechanics that require strategy adaptation:

| Enemy Type | Mechanic |
|------------|----------|
| Mirror Knight | Copies your defense zone; always attacks your open zone |
| Regen Troll | Regenerates 5 HP per turn; must kill within N turns |
| Tactician | Learns your pattern; if you attack the same zone twice in a row, it starts defending it |
| Swarm | Three weak enemies; each kill makes the remaining ones stronger |
| Lich | Casts spells; partially ignores armor |

---

## 8. Stress System

Stress is a secondary resource (0–100) that represents the hero's psychological state. It accumulates from frightening enemies, dark events, and prolonged combat.

### 8.1 Stress Thresholds

| Range | State | Combat Effect |
|-------|-------|---------------|
| 0–40 | Calm | No penalties |
| 40–70 | Rattled | −10% hit chance on HEAD attacks |
| 70–90 | Panicking | Defense zone randomly shifts once per fight |
| 90–100 | Breaking | Strategy is ignored; character acts randomly |
| 100 | Breakdown | Character flees automatically; loses 30% of carried gold |

### 8.2 Stress Sources

**In combat:**
- Taking a critical hit: +8 stress
- Enemy with "terrifying" trait attacks: +5–15 stress per turn
- Banshee scream (ignores armor, hits stress directly)
- Discovering a Mimic: +30 stress

**On the map:**
- Entering a "dark" room (mystery): +5 stress
- A party member dying (MMO, v2): +20 stress
- Failed trap disarm: +10 stress

### 8.3 Stress Recovery
- Rest room: −25 stress (costs 30 gold)
- Killing an enemy in one blow: −5 stress
- Certain relics: passive stress reduction
- "Sanctuary" event room: −40 stress (rare)

### 8.4 Strategy Implications
```python
def strategy(state):
    # exit before breakdown, not during
    if state.stress_pct > 0.82:
        return flee()
    ...
```

---

## 9. Magic System

Magic is unlocked at floor 7+. It adds a **third action slot** to each combat turn: in addition to attack zone and defense zone, the player can optionally cast a spell.

Spells cost **Arcane Crystals** (see Resources). Running out of crystals means no magic that turn.

### 9.1 Spell List (v1)

| Spell | Cost | Effect |
|-------|------|--------|
| Fireball | 2 crystals | Deals 30 damage, ignores defense zone |
| Shield | 1 crystal | Fully blocks next incoming hit regardless of zone |
| Curse | 2 crystals | Enemy loses 20% block for 3 turns |
| Lightning | 3 crystals | Hits random zone for 45 damage |
| Drain | 2 crystals | Deals 15 damage, restores 10 HP |
| Calm | 1 crystal | Reduces stress by 15 |

### 9.2 Magic Resources
- **Arcane Crystals** — found in rooms on floors 7+, drop from magical enemies
- **Arcane Essence** — rare drop from liches and dark mages; used to craft advanced spells

### 9.3 Magic Enemies (Floors 7+)

| Enemy | Mechanic |
|-------|----------|
| Dark Mage | Casts debuffs that alter your strategy's output for 2 turns |
| Lich | High HP, immune to LEGS attacks, spells deal double |
| Void Elemental | Immune to physical; must use magic or flee |
| Banshee | Attacks stress directly, ignores armor |

---

## 10. Resources

### 10.1 Overview

| Resource | Source | Used For |
|----------|--------|----------|
| Gold | All enemies, chests, events | Shop, rest rooms, crafting consumables |
| Ore (tiered) | Rooms, breakable walls | Equipment crafting |
| Enemy Materials | Specific enemy drops | Equipment crafting, meta-upgrades |
| Arcane Crystals | Floors 7+, magical enemies | Casting spells |
| Arcane Essence | Liches, dark mages (rare) | Crafting advanced spells |

### 10.2 Ore Tiers by Floor Depth

| Ore | Floors | Crafts |
|-----|--------|--------|
| Stone | 1–2 | Basic weapons & armor |
| Copper | 3–4 | Standard gear |
| Iron | 5–6 | Enhanced gear |
| Silver | 7–8 | Magical gear |
| Steel | 9–10 | Endgame gear |
| *(more TBD)* | 11+ | TBD |

### 10.3 Death Penalties
- Gold: lose **50%** of carried gold on death
- Ore & Materials: lose **25%** on death
- Arcane Crystals: lose **25%** on death
- Meta-upgrades (permanent): **never lost**

The asymmetry is intentional. Temporary resources punish recklessness; permanent progress is protected.

---

## 11. Equipment & Crafting

### 11.1 Equipment Slots
Four slots per character. Each slot has a gear tier determined by ore used.

| Slot | Effect | Notes |
|------|--------|-------|
| Weapon | ATK multiplier; weapon type adds a passive | 5 weapon types |
| Armor | Block % | 2 armor subtypes (light/heavy) |
| Helmet | Stress resistance; reduces stress thresholds | — |
| Accessory | Unique passive effect | Relic-like, non-droppable |

---

### 11.2 Crafting Formula
```
Item = Ore (type × qty) + Enemy Material (type × qty)
```
All crafting is done at the **Forge** (main menu, between runs). You cannot craft mid-run.

---

### 11.3 Weapons

Four weapon types — choose one per run, locked in at run start.

#### Type: Sword *(Balanced)*
Standard ATK multiplier. No special passive. Reliable baseline.
Inspiration: *D&D (Longsword), Diablo II (Normal sword tree)*

| Tier | Name | Recipe | ATK mult | Passive |
|------|------|--------|----------|---------|
| 1 | Stone Blade | Stone ×4 | 1.00× | — |
| 2 | Copper Sword | Copper ×5 + Goblin Fang ×2 | 1.10× | — |
| 3 | Iron Sword | Iron ×6 + Orc Fang ×2 | 1.20× | — |
| 4 | Silver Sword | Silver ×6 + Knight's Crest ×1 | 1.30× | Hits on TORSO deal +5 bonus damage |
| 5 | Steel Blade | Steel ×8 + Dragon Scale ×2 | 1.42× | +8 bonus dmg on TORSO; critical hits stun enemy 1 turn |

---

#### Type: Axe *(High damage, low accuracy)*
Higher ATK multiplier but −12% hit chance on all attacks.
Inspiration: *D&D (Battleaxe), Darkest Dungeon (Man-at-Arms axe attacks have high damage/low accuracy pattern)*

| Tier | Name | Recipe | ATK mult | Hit penalty |
|------|------|--------|----------|------------|
| 1 | Stone Hatchet | Stone ×5 | 1.10× | −12% |
| 2 | Copper Axe | Copper ×6 + Rat Pelt ×3 | 1.22× | −12% |
| 3 | Iron Axe | Iron ×7 + Troll Hide ×2 | 1.35× | −12% |
| 4 | Silver Axe | Silver ×7 + Orc Fang ×3 | 1.48× | −10% |
| 5 | Steel Greataxe | Steel ×9 + Dragon Scale ×3 | 1.62× | −8% (partially trained out) |

---

#### Type: Dagger *(Fast, crits)*
Lower ATK multiplier. Each hit has +18% chance to deal double damage (critical).
Inspiration: *D&D (Rogue dagger), Nethack (dagger critical hit system)*

| Tier | Name | Recipe | ATK mult | Crit chance |
|------|------|--------|----------|------------|
| 1 | Bone Shiv | Stone ×2 + Rat Pelt ×2 | 0.85× | +18% |
| 2 | Copper Dagger | Copper ×4 + Spider Silk ×3 | 0.92× | +18% |
| 3 | Iron Stiletto | Iron ×5 + Ghoul Claw ×2 | 1.00× | +18% |
| 4 | Silver Fang | Silver ×5 + Mimic Eye ×1 | 1.08× | +22% |
| 5 | Shadow Blade | Steel ×6 + Void Shard ×3 | 1.15× | +25%; crits also apply Poison (3 dmg/turn for 2 turns) |

---

#### Type: Staff *(Magic synergy)*
Low physical ATK. Passively generates +1 Arcane Crystal per floor while equipped.
Only meaningful on deep floors (7+) where magic matters. Weak choice early.
Inspiration: *D&D (Wizard's Staff), Nethack (magic staff), Final Fantasy (staff/rod for mages)*

| Tier | Name | Recipe | ATK mult | Arcane per floor |
|------|------|--------|----------|-----------------|
| 1 | Gnarled Branch | Stone ×3 + Grave Dust ×2 | 0.70× | +1 |
| 2 | Copper-Tipped Staff | Copper ×4 + Cult Relic Fragment ×2 | 0.78× | +1 |
| 3 | Iron Staff | Iron ×5 + Arcane Crystal ×2 | 0.85× | +2 |
| 4 | Silver Rod | Silver ×5 + Dark Rune ×2 | 0.90× | +2; spells deal +15% dmg |
| 5 | Void Staff | Steel ×6 + Void Essence ×2 + Arcane Essence ×1 | 0.95× | +3; spells deal +25% dmg |

---

#### Type: Greatsword *(Devastating, limited targeting)*
Very high ATK, but can **only target HEAD or TORSO** — no LEGS attacks.
Inspiration: *Dark Souls (Greatsword, Ultra Greatsword — slow and powerful, limited moveset)*

| Tier | Name | Recipe | ATK mult | Restriction |
|------|------|--------|----------|------------|
| 1 | Heavy Stone Sword | Stone ×6 | 1.20× | No LEGS |
| 2 | Copper Greatsword | Copper ×8 + Orc Fang ×2 | 1.35× | No LEGS |
| 3 | Iron Claymore | Iron ×9 + Troll Hide ×3 | 1.50× | No LEGS |
| 4 | Silver Executioner | Silver ×9 + Knight's Crest ×2 | 1.65× | No LEGS; HEAD hits stun 1 turn |
| 5 | Steel Colossus | Steel ×12 + Dragon Scale ×4 | 1.82× | No LEGS; HEAD stun + +20 stress to enemy |

---

### 11.4 Armor

Two subtypes: **Light** and **Heavy**. Choose at crafting time.

**Light Armor** — lower block, but stress threshold penalties are reduced by 10 points (you function better under stress).
**Heavy Armor** — higher block, but +5 stress per floor from the weight.
Inspiration: *Darkest Dungeon (light vs. heavy equipment affecting stress/scouting), Dark Souls (fat-roll vs fast-roll tradeoff)*

| Tier | Light Name | Heavy Name | Recipe | Light Block | Heavy Block |
|------|-----------|-----------|--------|------------|------------|
| 1 | Cloth Wrap | Stone Plate | Stone ×3 | 30% | 42% |
| 2 | Copper Chainmail | Copper Plate | Copper ×5 + Spider Silk ×2 | 38% | 52% |
| 3 | Iron Scale | Iron Plate | Iron ×6 + Troll Hide ×2 | 46% | 60% |
| 4 | Silver Sentinel | Silver Fortress | Silver ×7 + Shadow Cloth ×2 | 53% | 67% |
| 5 | Shadowweave | Steel Fortress | Steel ×9 + Dragon Scale ×2 | 58% | 73% |

---

### 11.5 Helmets

Helmets reduce **stress threshold breakpoints** — shifting when penalties kick in.

*Base thresholds: Rattled @40, Panicking @70, Breaking @90*
*With Tier 5 helmet: Rattled @50, Panicking @78, Breaking @94*

| Tier | Name | Recipe | Stress threshold shift |
|------|------|--------|----------------------|
| 1 | Hood | Stone ×2 | — (no shift) |
| 2 | Copper Cap | Copper ×4 + Grave Dust ×2 | +3 to all thresholds |
| 3 | Iron Helm | Iron ×5 + Ghoul Claw ×2 | +5 to all thresholds |
| 4 | Silver Visor | Silver ×6 + Banshee Veil ×1 | +7 to all thresholds |
| 5 | Steel Crown | Steel ×8 + Dragon Eye ×1 | +10 to all thresholds; immunity to Mimic stress spike |

---

### 11.6 Accessories

Crafted or found. One slot. More relic-like in effect.

| Name | Recipe | Effect | Inspiration |
|------|--------|--------|-------------|
| Ring of Thorns | Iron ×3 + Spider Silk ×3 | Attacker takes 5 dmg on every hit (stacks with Bronze Scales relic) | *D&D (Armor of Thorns), Slay the Spire (Thorns)* |
| Amulet of Fortune | Silver ×2 + Mimic Eye ×1 | Gold drops +20%; 5% chance any enemy drops a relic | *Binding of Isaac (Lucky Foot / treasure room luck)* |
| Boots of Haste | Copper ×3 + Rat Pelt ×3 | Hit chance on LEGS attacks +15% (from 92% to 107% — effectively always hit) | *D&D (Boots of Speed), classic RPG accessory* |
| Iron Will Band | Iron ×4 + Cult Relic Fragment ×2 | Stress breakdown threshold shifted to 105 (slightly above max — prevents auto-flee) | *Darkest Dungeon (virtue/affliction system — controlling the breaking point)* |
| Arcane Focus | Silver ×3 + Dark Rune ×2 | Spell hit chance +20%; spells can now target LEGS (normally spells hit all zones) | *D&D (Arcane Focus), Pathfinder* |
| Scholar's Band | Stone ×2 + Mage Scroll ×2 | Reveals enemy zone bias after turn 1 (one turn slower than Scholar's Lens relic) | *Slay the Spire (Frozen Eye, lesser version)* |

---

## 12. Bestiary

### 12.1 Enemy Design Principles
- Every enemy has a **zone bias** — a weighted tendency for where they attack. Discoverable through play, exploitable through strategy.
- Every enemy from floor 3+ has **one unique mechanic** that forces strategy adaptation.
- Stress-attacking enemies appear from floor 3+.
- Physical-immune / magic-required enemies appear from floor 7+.
- Each floor range has a **boss** with multiple phases.

---

### 12.2 Regular Enemies

#### Floor 1–2: Stone Tunnels

**Goblin Scout**
> *"Faster than it looks. Watch your pockets."*

| Stat | Value |
|------|-------|
| HP | 38–55 |
| ATK | 0.75× |
| Block | 40% |
| Bias | LEGS, LEGS, TORSO |
| Special | **Pickpocket:** On any hit, steals 4–8 gold from the player |
| Drops | Goblin Fang, Gold |
| Inspiration | *D&D (Goblin), classic fantasy archetype* |

---

**Giant Rat**
> *"Teeth like iron. Moves in the walls."*

| Stat | Value |
|------|-------|
| HP | 30–45 |
| ATK | 0.65× |
| Block | 30% |
| Bias | TORSO, LEGS, TORSO |
| Special | **Gnaw:** On crit, inflicts Weakness (-10% ATK) on player for 2 turns |
| Drops | Rat Pelt, Gold |
| Inspiration | *Nethack (giant rat), Darkest Dungeon (Rabid Gnasher)* |

---

**Cave Spider**
> *"You don't feel it until the venom does."*

| Stat | Value |
|------|-------|
| HP | 25–38 |
| ATK | 0.60× |
| Block | 25% |
| Bias | LEGS, TORSO, LEGS |
| Special | **Venom:** On hit, applies Poison (3 dmg/turn for 3 turns) |
| Drops | Spider Silk, Venom Gland |
| Inspiration | *D&D (Giant Spider), Nethack* |

---

#### Floor 3–4: Catacombs

**Skeleton Warrior**
> *"It rose once before. Keep hitting."*

| Stat | Value |
|------|-------|
| HP | 55–80 |
| ATK | 0.90× |
| Block | 45% |
| Bias | TORSO, TORSO, HEAD |
| Special | **Reassemble:** Revives once at 12 HP when first killed. Log entry: `[SKELETON RISES]` |
| Drops | Bone Fragment, Bronze Coin |
| Inspiration | *D&D (Skeleton), Darkest Dungeon (Bone Rabble)* |

---

**Skeleton Archer**
> *"It doesn't need to be close to hurt you."*

| Stat | Value |
|------|-------|
| HP | 42–60 |
| ATK | 0.85× |
| Block | 35% |
| Bias | HEAD, TORSO, HEAD |
| Special | **Ranged:** Attacks always hit; defense zone is ignored. Standard block % still applies if zone matches. |
| Drops | Bone Fragment, Arrow Tip |
| Inspiration | *D&D (Skeleton Archer), Nethack* |

---

**Ghoul**
> *"It took something. You feel it."*

| Stat | Value |
|------|-------|
| HP | 60–85 |
| ATK | 0.95× |
| Block | 50% |
| Bias | TORSO, HEAD, TORSO |
| Special | **Rotting Touch:** On hit, permanently reduces player max HP by 4 for the remainder of the run |
| Drops | Ghoul Claw, Grave Dust |
| Inspiration | *D&D (Ghoul), Nethack (Ghoul)* |

---

**Cultist**
> *"It's been waiting here. It's been preparing."*

| Stat | Value |
|------|-------|
| HP | 50–70 |
| ATK | 0.80× |
| Block | 40% |
| Bias | HEAD, TORSO, HEAD |
| Special | **Summon:** If alive after 3 turns, summons a Skeleton Warrior with +20% HP |
| Drops | Cult Relic Fragment, Dark Cloth |
| Inspiration | *Darkest Dungeon (Cultist Acolyte, Fanatic)* |

---

#### Floor 5–6: Dark Halls

**Orc Warrior**
> *"It wants to hurt you. That's all it wants."*

| Stat | Value |
|------|-------|
| HP | 85–120 |
| ATK | 1.05× |
| Block | 55% |
| Bias | HEAD, HEAD, TORSO |
| Special | **Blood Rage:** When HP drops below 30%, ATK becomes 1.55× for remaining turns |
| Drops | Orc Fang, Crude Iron Chunk |
| Inspiration | *D&D (Orc Berserker), Tolkien, Darkest Dungeon (Brigand Bloodletter)* |

---

**Orc Shaman**
> *"Kill it first. Always kill it first."*

| Stat | Value |
|------|-------|
| HP | 65–90 |
| ATK | 0.80× |
| Block | 45% |
| Bias | TORSO, HEAD, TORSO |
| Special | **War Chant:** If another enemy is present, heals it for 12 HP per turn. Stops if Shaman is the only enemy remaining. |
| Drops | Shaman Totem, Crude Iron Chunk |
| Inspiration | *D&D (Orc Shaman), Hades (Hexed Mage supporting mechanic)* |

---

**Dark Knight**
> *"It's fought a hundred heroes. It remembers them all."*

| Stat | Value |
|------|-------|
| HP | 110–155 |
| ATK | 1.20× |
| Block | 65% |
| Bias | HEAD, HEAD, TORSO |
| Special | **Mirror Block:** Each turn, copies the player's defense zone. Attacking the zone you're also defending deals half damage. Forces you to vary attacks. |
| Drops | Dark Iron Shard, Knight's Crest |
| Inspiration | *Dark Souls (Pursuer, Mirror Knight boss)* |

---

**Mimic**
> *"The chest looked fine. It wasn't fine."*

| Stat | Value |
|------|-------|
| HP | 75–100 |
| ATK | 1.10× |
| Block | 50% |
| Bias | Random |
| Special | **Disguised:** Appears as a Chest room. Reveal triggers +30 stress. Stats are significantly higher than expected for the floor. In passive mode, strategy's `event_choice` for "CHEST" must account for Mimic probability. |
| Drops | Rare loot (1.5× normal chest), Mimic Eye |
| Inspiration | *D&D (Mimic), Dark Souls (Mimic chest)* |

---

#### Floor 7–8: Cursed Vaults

**Banshee**
> *"You can't wound it. You can only endure it."*

| Stat | Value |
|------|-------|
| HP | 60–80 |
| ATK | — |
| Block | 20% |
| Bias | — (stress-only) |
| Special | **Wail:** Each turn deals 18–25 stress damage directly. Completely ignores HP, armor, and defense zones. Physical attacks deal half damage to it; magic deals full. |
| Drops | Silver Dust, Banshee Veil |
| Inspiration | *Darkest Dungeon (Banshee, Crone), D&D (Banshee)* |

---

**Regen Troll**
> *"If you don't kill it fast, you won't kill it at all."*

| Stat | Value |
|------|-------|
| HP | 130–175 |
| ATK | 1.00× |
| Block | 55% |
| Bias | TORSO, TORSO, LEGS |
| Special | **Regeneration:** Recovers 8 HP per turn. If fight lasts longer than 7 turns, HP recovery increases to 15/turn. Strategy must account for DPS race. |
| Drops | Troll Hide, Troll Blood Vial |
| Inspiration | *D&D (Troll), Darkest Dungeon (Collected, Rabid Gnasher mechanic)* |

---

**Blood Cultist**
> *"It hurts itself. To hurt you more."*

| Stat | Value |
|------|-------|
| HP | 90–120 |
| ATK | 1.05× |
| Block | 50% |
| Bias | HEAD, TORSO, HEAD |
| Special | **Blood Frenzy:** Every 3 turns, sacrifices 20 of its own HP to deal an unblockable 35 damage strike next turn. Visible in log one turn ahead: `[CULTIST PREPARES BLOOD FRENZY]` |
| Drops | Blood Vial, Dark Essence |
| Inspiration | *Darkest Dungeon (Flagellant class, Wilbur + Shambler dynamic)* |

---

**Void Shade**
> *"Each hit chips away at something."*

| Stat | Value |
|------|-------|
| HP | 95–130 |
| ATK | 1.10× |
| Block | 55% |
| Bias | TORSO, HEAD, TORSO |
| Special | **Armor Crush:** Each successful hit reduces the player's block % by 5 for the rest of the fight (cumulative, min 0%). Forces early aggression. |
| Drops | Void Shard, Shadow Cloth |
| Inspiration | *Dark Souls (curse/armor degradation mechanic), Dead Cells (Shieldbearer)* |

---

#### Floor 9–10: Abyss

**Lich**
> *"It died once. It didn't like it."*

| Stat | Value |
|------|-------|
| HP | 140–185 |
| ATK | 1.20× |
| Block | 60% |
| Bias | HEAD, TORSO, HEAD |
| Special | **Spellcast:** Every 2 turns, casts a random spell (Fireball / Drain / Curse) that bypasses zone defense entirely. Also immune to LEGS attacks — skeletal structure offers no vulnerability there. |
| Drops | Arcane Essence ×2, Bone Staff, Lich Crown Fragment |
| Inspiration | *D&D (Lich), classic fantasy archetype, WoW (Lich King)* |

---

**Dark Mage**
> *"It reaches into your tactics and scrambles them."*

| Stat | Value |
|------|-------|
| HP | 80–110 |
| ATK | 0.95× |
| Block | 45% |
| Bias | TORSO, TORSO, HEAD |
| Special | **Curse of Confusion:** Once per fight, applies a curse that randomly shuffles the player's strategy output for 1 turn. In log: `[YOUR STRATEGY IS SCRAMBLED THIS TURN]`. Not applied if player has "Clarity Rune" relic. |
| Drops | Arcane Crystal ×2, Dark Rune, Mage Scroll |
| Inspiration | *D&D (Dark Mage / Enchanter), Hades (Megaera whip attack that inverts controls)* |

---

**Void Elemental**
> *"Steel passes through it like smoke."*

| Stat | Value |
|------|-------|
| HP | 100–135 |
| ATK | 1.05× |
| Block | 30% |
| Bias | Random |
| Special | **Physical Immunity:** All physical attacks deal 1 damage (regardless of zone/damage/stats). Must use spells to deal real damage. Forces magic-dependent strategy on this fight. |
| Drops | Arcane Crystal ×3, Void Essence |
| Inspiration | *Nethack (elemental immunities), D&D (Elemental), Final Fantasy (elemental weakness system)* |

---

**Abyssal Swarm**
> *"Three at once. And they're angrier when you kill one."*

| Stat | Value |
|------|-------|
| HP | 40–55 each (×3) |
| ATK | 0.70× each |
| Block | 35% each |
| Bias | Random each |
| Special | **Pack Fury:** When one Swarm member dies, remaining members gain +20% ATK and +10% block. Each kill also adds +8 stress (the carnage is unsettling). |
| Drops | Void Shard ×2, Abyss Fragment |
| Inspiration | *Binding of Isaac (Hush-phase flies), Darkest Dungeon (Rabble group encounters)* |

---

### 12.3 Bosses

**Cave Troll** *(Floor 2 Boss)*
> *"It owns this level. Has for years."*

HP: 150 | ATK: 1.10× | Bias: TORSO, LEGS, TORSO

- **Phase 1:** Standard attacks + Regeneration (+5 HP/turn)
- **Phase 2** (below 50% HP): **Rock Throw** — unblockable hit to all zones simultaneously (deals 12 damage, +10 stress). Regeneration increases to +10 HP/turn.
- Drops: Troll Hide ×3, Iron Ore ×4, Troll Boss Crest
- Inspiration: *D&D (Troll), Tolkien, Darkest Dungeon (boss phase transitions)*

---

**Lich King** *(Floor 4 Boss)*
> *"It has served this dungeon since before you were born."*

HP: 180 | ATK: 1.15× | Bias: HEAD, TORSO, HEAD

- **Phase 1:** Standard attacks
- **Phase 2** (below 60% HP): **Raise Dead** — resurrects the last enemy killed this fight at 50% HP, once per phase. Max 2 raises.
- **Phase 3** (below 30% HP): **Death Mark** — next player attack that misses deals damage to the player instead.
- Drops: Bone Staff, Arcane Crystal ×2, Lich Crown Fragment ×2
- Inspiration: *D&D (Lich), WoW Lich King (raise dead mechanic)*

---

**Black Knight** *(Floor 6 Boss)*
> *"Every hit you land might come back to you."*

HP: 220 | ATK: 1.30× | Bias: HEAD, HEAD, TORSO

- **Phase 1:** Standard attacks + **Mirror Block** (copies defense zone, as Dark Knight)
- **Phase 2** (below 50% HP): **Parry** — 25% chance per player attack to reflect full damage back to player. Reflected attacks still trigger zone resolution.
- Drops: Dark Iron ×5, Knight's Crest ×2, Black Blade Fragment
- Inspiration: *Dark Souls (Black Knight, Dragonslayer Ornstein parry timing)*

---

**Shadow Drake** *(Floor 8 Boss)*
> *"The fear comes before the fire."*

HP: 260 | ATK: 1.35× | Bias: HEAD, TORSO, LEGS

- **Passive Aura:** +6 stress per turn regardless of actions (fear aura).
- **Phase 1:** Standard attacks
- **Phase 2** (below 50% HP): **Breath Weapon** — every 3 turns, unblockable attack to all three zones simultaneously (15 dmg each). +15 stress on hit.
- Drops: Dragon Scale ×2, Shadow Fang, Arcane Essence ×2
- Inspiration: *D&D (Shadow Dragon, fear aura mechanic), Darkest Dungeon (stress-aura bosses)*

---

**Ancient Dragon** *(Floor 10 Boss — Final Boss v1)*
> *"This is what the dungeon was built around."*

HP: 320 | ATK: 1.55× | Bias: HEAD, TORSO, LEGS (balanced)

- **Phase 1:** Standard attacks + Breath Weapon every 4 turns (as Shadow Drake)
- **Phase 2** (below 60% HP): **Wing Buffet** — 40% chance each turn to randomly shift player's defense zone by one (HEAD→TORSO, TORSO→LEGS, LEGS→HEAD). Logged as `[WIND DISRUPTS YOUR GUARD]`.
- **Phase 3** (below 30% HP): **Frenzy** — attacks twice per turn. ATK becomes 1.80×.
- Drops: Dragon Scale ×5, Legendary Gem, Ancient Gold ×50, Dragon Eye
- Inspiration: *D&D (Ancient Dragon, multi-phase), Dark Souls (Seath the Scaleless, Gaping Dragon phase transitions)*

---

## 13. Room Events

Events are choice-based encounters with no guaranteed outcome. They are the primary source of narrative flavor and risk/reward decisions outside of combat.

### 13.1 Event Categories

**Gamble events** — risk something for potential gain:
- *The Altar* — sacrifice HP for a random buff
- *The Mysterious Chest* — may contain loot, a trap, or an enemy
- *The Auctioneer* — rare relic available; price rises every second you wait
- *The Crossroads* — two paths: one labeled "dangerous but rich," one unmarked

**Puzzle events** — answer correctly for reward, wrong for penalty:
- *The Riddle Door* — answer correctly: bonus loot. Wrong: fight a buffed guardian
- *The Trapped Corridor* — disarm successfully: pass safely. Fail: damage + stress

**Neutral events** — information or minor effects:
- *The Wandering Merchant* — better prices than the shop, one item only
- *The Old Knight's Ghost* — tells you the bias of the next enemy on the floor
- *The Campfire* — free minor stress reduction (once per floor)

**Rare events:**
- *The Sanctuary* — −40 stress, no cost (very rare)
- *The Devil's Bargain* — permanently increase ATK by 15% but lose 20 max HP

### 13.2 Events in Passive Mode
Each event type has a **default action** used by the strategy when no explicit handling is defined. Players can override:
```python
def event_choice(event, options):
    if event.type == "altar":
        if state.hp_pct > 0.80:
            return "sacrifice"  # worth it when healthy
        return "ignore"
    return default_safe_choice(options)
```

---

## 14. Relics

Relics are passive items that modify rules for the entire run. Found in elite rooms, chests, boss rewards, and shops. Maximum **3 active relics** per run.

### 14.1 Design Rules
- Every relic changes *something fundamental*, not just a flat stat
- Relics can have explicit drawbacks (tradeoff relics are the most interesting)
- Rarity: Common (drop from normal/elite) → Uncommon (elite/boss) → Rare (boss/shop only)

---

### 14.2 Full Relic List

#### Common

**Old Amulet**
Effect: −5 stress after every combat victory.
Flavor: *Warm to the touch. Someone wore this for a long time.*
Inspiration: *Darkest Dungeon (stress relief trinkets)*

---

**Burning Blood**
Effect: Heal 6 HP after every combat (including losses that don't kill you).
Flavor: *The wound closes before you notice it.*
Inspiration: *Slay the Spire (Burning Blood — Ironclad starter relic)*

---

**Bag of Marbles**
Effect: First attack each combat has −15% enemy hit chance.
Flavor: *Something scatters across the floor. The enemy hesitates.*
Inspiration: *Slay the Spire (Bag of Marbles)*

---

**Bronze Scales**
Effect: When hit in an unguarded zone, attacker takes 3 reflected damage.
Flavor: *It bites back a little.*
Inspiration: *Slay the Spire (Bronze Scales)*

---

**Rat's Foot**
Effect: 12% chance any room contains a small bonus gold pile.
Flavor: *Lucky for you. Less so for the rat.*
Inspiration: *Binding of Isaac (Lucky Foot), Slay the Spire (Gremlin Horn)*

---

**Canary Feather**
Effect: Traps are always detected before triggering. Trap rooms show a warning icon.
Flavor: *It twitches when danger is near.*
Inspiration: *Darkest Dungeon (Detect Traps camping skill, translated to passive item)*

---

#### Uncommon

**Bird-Faced Urn**
Effect: Attacking HEAD and landing the hit heals 2 HP.
Flavor: *The beak points forward. Always forward.*
Inspiration: *Slay the Spire (Bird-Faced Urn)*

---

**Medicinal Herbs**
Effect: Rest rooms heal an additional 20 stress (on top of normal stress recovery).
Flavor: *Bitter. But it works.*
Inspiration: *Darkest Dungeon (Medicinal Herbs curio item)*

---

**Holy Water**
Effect: Undead enemies (Skeleton Warrior, Skeleton Archer, Ghoul, Lich) take +25% damage from all sources.
Flavor: *Blessed at the surface. Potent down here.*
Inspiration: *Darkest Dungeon (Holy Water consumable and undead enemy type weaknesses)*

---

**Philosopher's Stone**
Effect: Gold drops +40%. Cannot buy from shops (merchants refuse you).
Flavor: *It smells like wealth. Merchants hate it.*
Inspiration: *Nethack (Philosopher's Stone), tradeoff relic pattern from Slay the Spire*

---

**Odd Mushroom**
Effect: When entering the Panicking stress threshold (70%), gain +20% ATK for the remainder of that fight.
Flavor: *Fear makes you reckless. Recklessness sometimes works.*
Inspiration: *Slay the Spire (Odd Mushroom — size increase at low health)*

---

**Whetstone**
Effect: At run start, one weapon stat (ATK mult) is upgraded by +0.10×.
Flavor: *Someone sharpened this before leaving it.*
Inspiration: *Slay the Spire (Whetstone — upgrades cards at run start)*

---

**Cursed Tome**
Effect: Spells cost 1 fewer Arcane Crystal (min 1). On each cast, +5 stress.
Flavor: *Power has a price. It always does.*
Inspiration: *D&D (cursed items with tradeoffs), Slay the Spire (double-edged relics like Ectoplasm)*

---

**Dead Branch**
Effect: When you miss an attack, your next attack this combat is guaranteed to hit.
Flavor: *Still has thorns. Still useful.*
Inspiration: *Slay the Spire (Dead Branch — triggers on exhausted cards, adapted here to miss)*

---

**The Small Rock**
Effect: −10 max HP. +10 base damage on all attacks.
Flavor: *Heavy. Surprisingly heavy.*
Inspiration: *Binding of Isaac (The Small Rock — exact same tradeoff)*

---

**Berserker's Brand**
Effect: ATK +25%. Block −20%.
Flavor: *Burned into the skin. Cannot be removed.*
Inspiration: *Darkest Dungeon (Berserker's buckle trinket), Slay the Spire (Lantern-type risk relics)*

---

#### Rare

**Shard of Chaos**
Effect: All damage dealt and received has ±40% random variance. High risk, high reward.
Flavor: *It vibrates with something unstable. Feels like a bad idea.*
Inspiration: *Slay the Spire (Tingsha — damage on card exhaust, unpredictable outcomes); Binding of Isaac (D6 randomness philosophy)*

---

**Dragon Heart**
Effect: Max HP +30. Regenerate 2 HP per turn during combat.
Flavor: *Still beating. Faintly.*
Inspiration: *Dark Souls (Dragon Heart item, Dragon covenant mechanic), D&D (Dragon constitution)*

---

**Scholar's Lens**
Effect: At the start of each fight, enemy's zone bias is revealed.
Flavor: *You see the pattern before the first swing.*
Inspiration: *Slay the Spire (Frozen Eye — see draw pile), Darkest Dungeon (Scouting reveals room contents)*

---

**Soul Lantern**
Effect: All room types on the current floor are revealed before you choose your path.
Flavor: *The flame bends toward danger.*
Inspiration: *Darkest Dungeon (Scouting mechanic), Slay the Spire (map information relics)*

---

**Runic Pyramid**
Effect: After each floor, stress does NOT increase from "resting" or extraction delays. You can stay on a cleared floor indefinitely in passive mode without stress penalty.
Flavor: *Time moves differently around it.*
Inspiration: *Slay the Spire (Runic Pyramid — keeps hand at end of turn, removes forced decision pressure)*

---

**Philosopher's Idol**
Effect: First kill of each enemy type per run drops double materials.
Flavor: *The first time is always the richest.*
Inspiration: *Monster Hunter (research bonus on first investigation), Dead Cells (first kill blueprint system)*

---

**Knight's Crest**
Effect: Block +15%. When successfully blocking an attack (guarding correct zone), heal 5 HP.
Flavor: *Earned. Not bought.*
Inspiration: *Dark Souls (Lothric Knight armor set, blocking rewards)*

---

**Merchant's Favor**
Effect: Shop prices permanently −20%.
Flavor: *The merchant remembers you. Fondly.*
Inspiration: *Slay the Spire (Membership Card — shop 50% off), toned down*

---

**Void Fragment**
Effect: Spells cost 1 fewer Arcane Crystal (min 1). No drawback.
Flavor: *It absorbs arcane energy from the air around it.*
Inspiration: *Slay the Spire (Snecko Skull — reduces cost of specific cards)*

---

## 15. Progression & Meta-progression

### 15.1 Within a Run
- XP → level up → HP increase
- Equipment improves combat stats
- Relics modify run rules
- Spells unlock at floor 7

### 15.2 Between Runs (Permanent)
Spent via **Enemy Materials** at the "Hall of Upgrades" (accessible from main menu):

| Upgrade | Material Cost | Effect |
|---------|--------------|--------|
| Iron Will | Skeleton Bone ×10 | Max stress cap +10 |
| Tough Hide | Troll Hide ×5 | Max HP +10 (all runs) |
| Scholar | Dragon Scale ×1 | Start each run with Scholar's Lens relic |
| Tactician | Dark Crystal ×3 | Unlock `assess()` action in strategy |
| *(more TBD)* | | |

### 15.3 Floor Unlock
New floors are permanently unlocked by reaching them in active mode. Once a floor is unlocked, passive mode can farm it.

```
Active mode: explore new floor → die or extract
                ↓ (floor reached = unlocked)
Passive mode: farm that floor on autopilot
```

### 15.4 Push Your Luck
At the exit of each floor, the player (or strategy) chooses:

| Choice | Effect |
|--------|--------|
| **Extract** | Leave dungeon, keep all resources |
| **Continue** | Stay, get +25% bonus to all resources on current floor |

Each floor cleared after the first "continue" increases the bonus by an additional +15%, but also increases encounter difficulty by 10%.

If the hero dies after choosing to continue, the run-session multiplier is lost.

---

## 16. Roadmap

### v1 — Single Player Foundation
- Active & passive modes
- Strategy system (Python function)
- 10 floors, 5 themes
- Full bestiary (see Section 12)
- Equipment & crafting
- Stress system
- Relics
- Room events
- Magic system (floors 7+)
- Meta-progression (permanent upgrades)

### v2 — Character Depth
- Quirks system (Darkest Dungeon-inspired)
- Additional character classes
- Strategy sharing (`dungeon strategy share`)
- Expanded bestiary (20+ enemies)
- More relics, spells, events

### v3 — MMO Layer
- Shared persistent world
- Async co-op: see other players' heroes in your dungeon log
- Guild system
- Collective world events ("all players defeat the Dragon → floor 11 unlocks for everyone")
- Leaderboards by strategy efficiency

### v4 — Living World
- Real market data integration: market volatility → dungeon difficulty modifier
- Community-contributed content (enemies, events, relics) via PR + vote
- Strategy tournaments

---

*Document maintained by: Ilia*
*Last updated: 2026-06-09*
