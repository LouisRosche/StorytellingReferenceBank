/**
 * Card effect resolution, ported from the Unity Effects/ directory.
 * Each effect type is a pure function. The EffectResolver dispatches
 * CardEffect data to the appropriate handler via the command system.
 */

import type { CardEffect } from "@deckbuilder/shared";
import type { ICombatEntity, IDeckManager } from "../combat/commands";
import {
  CommandInvoker,
  DealDamageCommand,
  GainBlockCommand,
  ApplyStatusCommand,
  DrawCardCommand,
} from "../combat/commands";

// ---------------------------------------------------------------------------
// Context carried into every effect resolution.
// ---------------------------------------------------------------------------

export interface EffectContext {
  invoker: CommandInvoker;
  source: ICombatEntity;
  target: ICombatEntity;
  deck: IDeckManager;
}

// ---------------------------------------------------------------------------
// Individual effect functions.
// ---------------------------------------------------------------------------

export function dealDamage(ctx: EffectContext, effect: CardEffect): void {
  const command = new DealDamageCommand(ctx.target, effect.value);
  ctx.invoker.executeCommand(command);
}

export function gainBlock(ctx: EffectContext, effect: CardEffect): void {
  const command = new GainBlockCommand(ctx.source, effect.value);
  ctx.invoker.executeCommand(command);
}

export function drawCards(ctx: EffectContext, effect: CardEffect): void {
  const command = new DrawCardCommand(ctx.deck, effect.value);
  ctx.invoker.executeCommand(command);
}

export function applyStatus(ctx: EffectContext, effect: CardEffect): void {
  const command = new ApplyStatusCommand(
    ctx.target,
    effect.type, // e.g. "poison", "weak", "vulnerable"
    effect.value,
  );
  ctx.invoker.executeCommand(command);
}

// ---------------------------------------------------------------------------
// Registry & resolver.
// ---------------------------------------------------------------------------

type EffectHandler = (ctx: EffectContext, effect: CardEffect) => void;

const defaultHandlers: Record<string, EffectHandler> = {
  deal_damage: dealDamage,
  gain_block: gainBlock,
  draw_cards: drawCards,
  apply_status: applyStatus,
};

export class EffectResolver {
  private readonly handlers: Record<string, EffectHandler>;

  constructor(extraHandlers?: Record<string, EffectHandler>) {
    this.handlers = { ...defaultHandlers, ...extraHandlers };
  }

  /** Resolve a single CardEffect against the provided context. */
  resolve(effect: CardEffect, ctx: EffectContext): void {
    const handler = this.handlers[effect.type];
    if (!handler) {
      throw new Error(`Unknown card effect type: "${effect.type}"`);
    }
    handler(ctx, effect);
  }

  /** Resolve all effects on a card in order. */
  resolveAll(effects: CardEffect[], ctx: EffectContext): void {
    for (const effect of effects) {
      this.resolve(effect, ctx);
    }
  }

  /** Register or override an effect handler at runtime (e.g. modded effects). */
  register(type: string, handler: EffectHandler): void {
    this.handlers[type] = handler;
  }
}
