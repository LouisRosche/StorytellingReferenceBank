/**
 * Turn phase states ported from TurnStates.cs.
 * Each state implements IState and operates on CombatState from shared types.
 */

import type { CombatState } from "@deckbuilder/shared";
import type { IState } from "./state-machine";

// ---------------------------------------------------------------------------
// Callback signatures used by the turn states.
// The combat manager wires these up so states stay decoupled from systems.
// ---------------------------------------------------------------------------

export interface TurnCallbacks {
  drawCards(state: CombatState, count: number): CombatState;
  enablePlayerInput(): void;
  disablePlayerInput(): void;
  resolveEnemyIntents(state: CombatState): CombatState;
  resolveEndOfTurn(state: CombatState): CombatState;
}

// ---------------------------------------------------------------------------
// Shared context that every turn state reads / writes.
// ---------------------------------------------------------------------------

export interface TurnContext {
  state: CombatState;
  callbacks: TurnCallbacks;
  /** Called by a state when it is finished and the FSM should advance. */
  onPhaseComplete: () => void;
}

// ---------------------------------------------------------------------------
// Draw Phase — draw N cards, then immediately signal completion.
// ---------------------------------------------------------------------------

export class DrawState implements IState {
  constructor(
    private readonly ctx: TurnContext,
    private readonly drawCount: number,
  ) {}

  enter(): void {
    this.ctx.state = this.ctx.callbacks.drawCards(this.ctx.state, this.drawCount);
    this.ctx.state = { ...this.ctx.state, turnPhase: "draw" };
  }

  update(): void {
    this.ctx.onPhaseComplete();
  }

  exit(): void {}
}

// ---------------------------------------------------------------------------
// Player Action — waits for the player to play cards / end turn.
// ---------------------------------------------------------------------------

export class PlayerActionState implements IState {
  constructor(private readonly ctx: TurnContext) {}

  enter(): void {
    this.ctx.state = { ...this.ctx.state, turnPhase: "player_action" };
    this.ctx.callbacks.enablePlayerInput();
  }

  update(): void {
    /* Waits for external command (card play / end turn button). */
  }

  exit(): void {
    this.ctx.callbacks.disablePlayerInput();
  }
}

// ---------------------------------------------------------------------------
// Enemy Intent — resolve all enemy actions, then signal completion.
// ---------------------------------------------------------------------------

export class EnemyIntentState implements IState {
  constructor(private readonly ctx: TurnContext) {}

  enter(): void {
    this.ctx.state = { ...this.ctx.state, turnPhase: "enemy_intent" };
    this.ctx.state = this.ctx.callbacks.resolveEnemyIntents(this.ctx.state);
  }

  update(): void {
    this.ctx.onPhaseComplete();
  }

  exit(): void {}
}

// ---------------------------------------------------------------------------
// Resolution — tick status effects, clean up, then signal completion.
// ---------------------------------------------------------------------------

export class ResolutionState implements IState {
  constructor(private readonly ctx: TurnContext) {}

  enter(): void {
    this.ctx.state = { ...this.ctx.state, turnPhase: "resolution" };
    this.ctx.state = this.ctx.callbacks.resolveEndOfTurn(this.ctx.state);
  }

  update(): void {
    this.ctx.onPhaseComplete();
  }

  exit(): void {}
}

// ---------------------------------------------------------------------------
// End Turn — bump the turn counter and signal completion so the loop restarts.
// ---------------------------------------------------------------------------

export class EndTurnState implements IState {
  constructor(private readonly ctx: TurnContext) {}

  enter(): void {
    this.ctx.state = {
      ...this.ctx.state,
      turnPhase: "end_turn",
      turnNumber: this.ctx.state.turnNumber + 1,
    };
  }

  update(): void {
    this.ctx.onPhaseComplete();
  }

  exit(): void {}
}
