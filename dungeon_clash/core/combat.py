"""The combat engine: a pure, deterministic turn resolver.

``step`` is the single source of truth for combat rules. Given a state, the
hero's action, and a seeded RNG, it returns the next state plus the events that
happened. No I/O, no printing, no hidden randomness — everything flows through
the passed-in :class:`Rng`.

Determinism contract: for a fixed seed, the RNG is consumed in a fixed order
every turn:

    0. stress action mutation  (only when Panicking → 1 draw, or Breaking → 2)
    1. enemy attack-zone choice
    2. enemy defend-zone choice
    3. hero's strike hit-roll  (only if the hero attacks this turn)
    4. enemy's strike hit-roll

At Calm stress (the default) step 0 draws nothing, so stress-free replays are
unchanged. Changing this order changes replay hashes, so it is part of the
public contract (and is pinned by the determinism tests).

Damage (GDD §7.2), all integer / basis points::

    final = base_damage(zone) * atk_bp // 10_000
    if zone == guarded_zone:
        final = max(1, final * (10_000 - block_bp) // 10_000)

Both sides resolve **simultaneously** from the start-of-turn state (GDD §7.1):
an enemy still lands its retaliation on the turn it dies, so a mutual knockout
is possible — and counts as a hero loss.
"""

from __future__ import annotations

from dungeon_clash.core.events import (
    AttackResolved,
    AttackResult,
    CombatDefeated,
    Event,
    StressChanged,
)
from dungeon_clash.core.models import ONE_X_BP, CombatAction, Combatant, CombatState, Enemy
from dungeon_clash.core.rng import Rng
from dungeon_clash.core.stress import (
    ONE_BLOW_RELIEF,
    RATTLED_HEAD_PENALTY_BP,
    StressState,
    clamp_stress,
    stress_state,
)
from dungeon_clash.core.zones import Zone, base_damage, hit_chance_bp

_ALL_ZONES = tuple(Zone)


def _stressed_action(action: CombatAction, state: StressState, rng: Rng) -> CombatAction:
    """Apply the stress state's effect on the hero's chosen action (GDD §8.1).

    Panicking randomly shifts the guard; Breaking ignores the strategy entirely
    and acts at random. Calm/Rattled leave the action untouched (Rattled's
    penalty is applied to the hit roll instead).
    """
    if state is StressState.BREAKING:
        return CombatAction(attack=rng.choice(_ALL_ZONES), defend=rng.choice(_ALL_ZONES))
    if state is StressState.PANICKING:
        return action.model_copy(update={"defend": rng.choice(_ALL_ZONES)})
    return action


def resolve_strike(
    attack_zone: Zone,
    defend_zone: Zone | None,
    atk_bp: int,
    block_bp: int,
    rng: Rng,
    hit_mod_bp: int = 0,
) -> tuple[int, AttackResult]:
    """Resolve a single strike into ``(damage, result)``.

    Pure integer math; the only randomness is the hit-chance roll. A
    ``defend_zone`` of ``None`` means the target guards nothing, so the hit can
    never be blocked. ``hit_mod_bp`` adjusts the hit chance (e.g. the Rattled
    stress penalty on HEAD attacks).
    """
    if not rng.chance(hit_chance_bp(attack_zone) + hit_mod_bp):
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
    sstate = stress_state(state.stress)

    # 0: stress may override the hero's action before anything is committed.
    action = _stressed_action(action, sstate, rng)

    # 1–2: enemy commits its action for the turn.
    enemy_attack, enemy_defend = choose_enemy_action(enemy, rng)

    # 3: hero strikes enemy's guard (only if the hero attacks this turn).
    hero_damage = 0
    hero_result: AttackResult | None = None
    if action.attack is not None:
        # Rattled costs 10% hit chance on HEAD (GDD §8.1).
        hit_mod = (
            -RATTLED_HEAD_PENALTY_BP
            if sstate is StressState.RATTLED and action.attack is Zone.HEAD
            else 0
        )
        hero_damage, hero_result = resolve_strike(
            action.attack, enemy_defend, hero.atk_bp, enemy.block_bp, rng, hit_mod
        )
    # 4: enemy strikes hero's guard.
    enemy_damage, enemy_result = resolve_strike(
        enemy_attack, action.defend, enemy.atk_bp, hero.block_bp, rng
    )

    # Both hits land against start-of-turn HP (simultaneous resolution).
    new_enemy = enemy.with_damage(hero_damage)
    new_hero = hero.with_damage(enemy_damage)

    # Stress: a terrifying enemy's landed hit raises it; a one-blow kill relieves it.
    new_stress = state.stress
    if enemy.stress_attack and enemy_result in (AttackResult.HIT, AttackResult.BLOCKED):
        new_stress += enemy.stress_attack
    if new_enemy.hp == 0 and enemy.hp == enemy.max_hp:
        new_stress -= ONE_BLOW_RELIEF
    new_stress = clamp_stress(new_stress)

    events: list[Event] = []
    if action.attack is not None and hero_result is not None:
        events.append(
            AttackResolved(
                attacker=hero.name,
                defender=enemy.name,
                attack_zone=action.attack,
                defend_zone=enemy_defend,
                result=hero_result,
                damage=hero_damage,
                defender_hp=new_enemy.hp,
            )
        )
    events.append(
        AttackResolved(
            attacker=enemy.name,
            defender=hero.name,
            attack_zone=enemy_attack,
            defend_zone=action.defend,
            result=enemy_result,
            damage=enemy_damage,
            defender_hp=new_hero.hp,
        )
    )

    if new_stress != state.stress:
        events.append(
            StressChanged(
                stress=new_stress,
                delta=new_stress - state.stress,
                state=stress_state(new_stress).value,
            )
        )

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
            "stress": new_stress,
            "over": over,
            "winner": winner,
        }
    )
    return new_state, events
