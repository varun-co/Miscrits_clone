---
Status: Draft
Owner: Varun
Last updated: 2026-05-08
---

# Vision — Miscrits Clone

## What are we building?

A faithful reconstruction of the core mechanics of **Miscrits**, a turn-based creature-battling game. The project serves two purposes:

1. **A playable battle simulation** that captures the strategic depth of the original — natures, stat interplay, switching, status effects, and team composition.
2. **A training ground for Reinforcement Learning agents** that discover, evaluate, and evolve competitive strategies as the miscrit roster and attack catalog grow.

## Why are we building it?

| Goal | What success looks like |
|---|---|
| **Learn structured software development** | A well-documented, extensible codebase built spec-first — PRDs before code, TDDs before implementation, ADRs for every significant choice. |
| **Learn to build meaningful RL agents** | Agents that surface non-obvious strategies (team composition, speed control, switch timing) and whose findings shift as the meta changes with new miscrits or attacks. |

## Game at a glance

Miscrits is a turn-based creature-battling game with the following pillars:

### Creatures (Miscrits)

- Each miscrit belongs to a **species** (template) and exists as an **instance** owned by a player.
- Species define base stat ratings, nature, and a movelist.
- Instances carry a **grade** (F through S+) that governs how fast stats grow per level. Grade is determined by per-stat quality (Red / White / Green).
- Miscrits evolve at levels 10, 20, and 30 — gaining a new name, new appearance, and buffed stats.
- Level cap is 35.

### Nature system

Six natures organized into two rock-paper-scissors triangles:

- **Triangle 1:** Nature > Water > Fire > Nature
- **Triangle 2:** Wind > Earth > Lightning > Wind

Elemental attacks deal **2x damage** against a weak nature and **0.5x damage** against a strong one. Neutral matchups deal 1x.

Some miscrits are **dual-natured** (one nature from each triangle), making them strong against two natures and weak against two.

### Stats

| Stat | Role |
|---|---|
| HP | Health pool — survivability |
| SPD | Turn order, and the key to advanced "speed control" tactics (see below) |
| PA | Physical Attack power |
| EA | Elemental Attack power |
| PD | Physical Defence |
| ED | Elemental Defence |

**Speed control** is the mechanic that makes PvP strategically deep. Having the faster miscrit is not always advantageous — sometimes acting second lets you react to the opponent's switch or setup move. The full rules around speed control are TBD and will be specified in the battle system PRD.

### Attacks and effects

- **Physical attacks** — neutral type, damage scales with PA vs PD.
- **Elemental attacks** — carry the attacker's nature, damage scales with EA vs ED, affected by nature matchup.
- **Buffs / Debuffs** — modify stats (PA, PD, EA, ED, SPD) for a duration. Stacking rules TBD.
- **DOT / HOT** — damage or healing over multiple turns, stat-based.
- **Poison / Venom** — fixed damage per turn, not affected by stats.
- **Switch Curse** — fixed damage that escalates each turn the afflicted miscrit stays in.
- **Negate** — removes elemental weakness for the current battle (until switched out).
- **Other effects** — Bleeding, Water Bomb, Ethereal, Buff-over-time, Debuff-over-time, Antiheal. Details TBD.

Attacks can be **enchanted** (costs gold) to increase power, accuracy, or add secondary effects.

### Battle structure

- Each player fields a **team of 4 miscrits** in ordered slots.
- One miscrit is **active** at a time per side.
- On your turn you either **attack** or **switch** (switching costs your turn).
- The faster miscrit acts first each round (SPD-based).
- A side loses when all 4 miscrits are fainted.

### Progression

- **Capture** — miscrits are found in the wild; capturing adds them to your inventory. The captured instance receives a random grade.
- **First capture / first evolution** of a species grants +1 Rank and +1 Platinum.
- **Ranks** unlock **Virtues** — passive modifiers that improve quality of life.
- **Leveling** — after battle, miscrits earn XP. Stat growth per level depends on template base stats and instance grade. Players may spend 1 Platinum per level to add a bonus stat point (community term for a fully bonus-trained miscrit is TBD).
- **XP spreading** mechanic is TBD.
- **Currencies:** Gold (common) and Platinum (rare).

### World

- Multiple areas, each with unique miscrits to encounter.
- **Magicites** — mini-bosses guarding each area.
- **Elementum** — major bosses, one per nature type (6 total).
- Two regions: **Sunfall Kingdom** (3 Elementum) and **Volcano Island** (3 Elementum).
- **Apollo Nox** — final boss.
- Side-quest rare bosses scattered across the map.

### PvE and PvP

- **PvE:** Player vs game AI (the "Boss" abstraction). Encounters are triggered by clicking areas on the world map. Can be a battle or a gift (potions / items).
- **PvP:** Player vs player — the competitive endgame where speed control and team composition matter most.

## Phasing

| Phase | Scope | Outcome |
|---|---|---|
| **v1 — Core battle simulation** | Miscrit/attack domain model, nature system, damage calculation, turn order, effect lifecycle, storage adapter. No switching, no leveling, no capture. | A runnable battle simulation where two teams of miscrits fight to completion. |
| **v2 — Tactical depth** | Switching in battle, enchantments, leveling/stat growth, grade system affecting growth, buff/debuff stacking rules. | Battles that reflect the full tactical depth of the original game. |
| **v3 — World and progression** | Capture, inventory, areas, magicites, elementum, ranks, virtues, currencies. | A playable PvE loop. |
| **v4 — RL agent platform** | Action/observation space definition, reward signals, training harness, strategy analysis tooling. | RL agents training against the sim and surfacing strategy insights. |
| **v5 — PvP and meta-analysis** | PvP matchmaking, rating system, meta tracking as roster changes. | The full loop: add miscrits/attacks, RL discovers new strategies, meta evolves. |

## Open questions

- What is the community term for a miscrit fully bonus-trained across all 35 levels?
- Exact speed control rules — when and why is acting second advantageous?
- Dual-nature details — does a dual-natured miscrit have two explicit natures, or a single combined nature?
- Buff/debuff stacking — is there a cap? Do same-type buffs refresh or stack?
- XP spreading rules across the team.
- Full details on: Bleeding, Water Bomb, Ethereal, Buff-over-time, Debuff-over-time, Antiheal.
