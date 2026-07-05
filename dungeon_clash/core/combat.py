"""The combat engine: a pure, deterministic turn resolver.

``step`` is the single source of truth for combat rules. Given a state, the
hero's action, and a seeded RNG, it returns the next state plus the events that
happened. No I/O, no printing, no hidden randomness — everything flows through
the passed-in :class:`Rng`.

Determinism contract: for a fixed seed, the RNG is consumed in a fixed order
every turn:

    1. enemy attack-zone choice
    2. enemy defend-zone choice
    3. hero's strike hit-roll
    4. enemy's strike hit-roll

Changing this order changes replay hashes, so it is part of the public contract
(and is pinned by the determinism tests).

Damage (GDD §7.2), all integer / basis points::

    final = base_damage(zone) * atk_bp // 10_000
    if zone == guarded_zone:
        final = max(1, final * (10_000 - block_bp) // 10_000)

Both sides resolve **simultaneously** from the start-of-turn state (GDD §7.1):
an enemy still lands its retaliation on the turn it dies, so a mutual knockout
is possible — and counts as a hero loss.
"""

from __future__ import annotations

from dungeon_clash.core.events import AttackResolved, AttackResult, CombatDefeated, Event
from dungeon_clash.core.models import ONE_X_BP, CombatAction, Combatant, CombatState, Enemy
from dungeon_clash.core.rng import Rng
from dungeon_clash.core.zones import Zone, base_damage, hit_chance_bp


def resolve_strike(
    attack_zone: Zone,
    defend_zone: Zone,
    atk_bp: int,
    block_bp: int,
    rng: Rng,
) -> tuple[int, AttackResult]:
    """Resolve a single strike into ``(damage, result)``.

    Pure integer math; the only randomness is the hit-chance roll.
    """
    if not rng.chance(hit_chance_bp(attack_zone)):
        return 0, AttackResult.MISS

    damage = base_damage(attack_zone) * atk_bp // ONE_X_BP

    if attack_zone == defend_zone:
        damage = max(1, damage * (ONE_X_BP - block_bp) // ONE_X_BP)
        return damage, AttackResult.BLOCKED

    return damage, AttackResult.HIT


def choose_enemy_action(enemy: Enemy, rng: Rng) -> tuple[Zone, Zone]:
    """Enemy AI (GDD §7.3): attack drawn from the bias pool, defense drawn from
    the same pool — imperfect, so patterns stay exploitable."""
    attack = rng.choice(enemy.bias)
    defend = rng.choice(enemy.bias)
    return attack, defend


def step(state: CombatState, action: CombatAction, rng: Rng) -> tuple[CombatState, list[Event]]:
    """Advance one combat turn.

    Returns the next :class:`CombatState` and the ordered list of events for
    this turn. Never mutates ``state`` or ``action``.
    """
    if state.over:
        raise ValueError("combat is already over")

    hero: Combatant = state.hero
    enemy: Enemy = state.enemy

    # 1–2: enemy commits its action for the turn.
    enemy_attack, enemy_defend = choose_enemy_action(enemy, rng)

    # 3: hero strikes enemy's guard.
    hero_damage, hero_result = resolve_strike(
        action.attack, enemy_defend, hero.atk_bp, enemy.block_bp, rng
    )
    # 4: enemy strikes hero's guard.
    enemy_damage, enemy_result = resolve_strike(
        enemy_attack, action.defend, enemy.atk_bp, hero.block_bp, rng
    )

    # Both hits land against start-of-turn HP (simultaneous resolution).
    new_enemy = enemy.with_damage(hero_damage)
    new_hero = hero.with_damage(enemy_damage)

    events: list[Event] = [
        AttackResolved(
            attacker=hero.name,
            defender=enemy.name,
            attack_zone=action.attack,
            defend_zone=enemy_defend,
            result=hero_result,
            damage=hero_damage,
            defender_hp=new_enemy.hp,
        ),
        AttackResolved(
            attacker=enemy.name,
            defender=hero.name,
            attack_zone=enemy_attack,
            defend_zone=action.defend,
            result=enemy_result,
            damage=enemy_damage,
            defender_hp=new_hero.hp,
        ),
    ]

    hero_dead = not new_hero.alive
    enemy_dead = not new_enemy.alive
    over = hero_dead or enemy_dead
    winner: str | None = None
    if over:
        # Mutual knockout counts as a hero loss (you don't win by dying).
        winner = enemy.name if hero_dead else hero.name
        loser = hero.name if hero_dead else enemy.name
        events.append(CombatDefeated(loser=loser, winner=winner, turns=state.turn))

    new_state = state.model_copy(
        update={
            "hero": new_hero,
            "enemy": new_enemy,
            "turn": state.turn + 1,
            "over": over,
            "winner": winner,
        }
    )
    return new_state, events
