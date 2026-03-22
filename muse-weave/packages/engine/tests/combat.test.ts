import { describe, it, expect, vi } from "vitest";
import { StateMachine, type IState } from "../src/combat/state-machine";
import {
  CommandInvoker,
  DealDamageCommand,
  GainBlockCommand,
  HealCommand,
  ApplyStatusCommand,
  type ICombatEntity,
} from "../src/combat/commands";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeMockState(name: string): IState & {
  enterCalls: number;
  exitCalls: number;
  updateCalls: number;
} {
  return {
    enterCalls: 0,
    exitCalls: 0,
    updateCalls: 0,
    enter() {
      this.enterCalls++;
    },
    exit() {
      this.exitCalls++;
    },
    update() {
      this.updateCalls++;
    },
  };
}

function makeCombatEntity(hp: number, maxHp: number, block = 0): ICombatEntity {
  const statuses = new Map<string, number>();
  return {
    hp,
    maxHp,
    block,
    addStatusEffect(effectId: string, stacks: number) {
      statuses.set(effectId, (statuses.get(effectId) ?? 0) + stacks);
    },
    removeStatusEffect(effectId: string, stacks: number) {
      const current = statuses.get(effectId) ?? 0;
      const newVal = current - stacks;
      if (newVal <= 0) {
        statuses.delete(effectId);
      } else {
        statuses.set(effectId, newVal);
      }
    },
    // Expose for assertions
    _statuses: statuses,
  } as ICombatEntity & { _statuses: Map<string, number> };
}

// ---------------------------------------------------------------------------
// StateMachine
// ---------------------------------------------------------------------------

describe("StateMachine", () => {
  it("starts with no current state", () => {
    const sm = new StateMachine();
    expect(sm.currentState).toBeNull();
  });

  it("changeState calls enter on the new state", () => {
    const sm = new StateMachine();
    const state = makeMockState("idle");
    sm.changeState(state);
    expect(state.enterCalls).toBe(1);
  });

  it("changeState calls exit on old state and enter on new state", () => {
    const sm = new StateMachine();
    const oldState = makeMockState("old");
    const newState = makeMockState("new");

    sm.changeState(oldState);
    sm.changeState(newState);

    expect(oldState.exitCalls).toBe(1);
    expect(newState.enterCalls).toBe(1);
    expect(sm.currentState).toBe(newState);
  });

  it("update calls current state's update", () => {
    const sm = new StateMachine();
    const state = makeMockState("active");
    sm.changeState(state);
    sm.update();
    sm.update();
    expect(state.updateCalls).toBe(2);
  });

  it("update is safe with no current state", () => {
    const sm = new StateMachine();
    expect(() => sm.update()).not.toThrow();
  });

  it("pushState exits current, pushes new, enters new", () => {
    const sm = new StateMachine();
    const base = makeMockState("base");
    const sub = makeMockState("sub");

    sm.changeState(base);
    sm.pushState(sub);

    expect(base.exitCalls).toBe(1);
    expect(sub.enterCalls).toBe(1);
    expect(sm.currentState).toBe(sub);
  });

  it("popState exits current sub-state and re-enters the one beneath", () => {
    const sm = new StateMachine();
    const base = makeMockState("base");
    const sub = makeMockState("sub");

    sm.changeState(base);
    sm.pushState(sub);
    sm.popState();

    expect(sub.exitCalls).toBe(1);
    // base was re-entered after pop
    expect(base.enterCalls).toBe(2); // initial + re-enter after pop
    expect(sm.currentState).toBe(base);
  });

  it("popState on empty stack does nothing", () => {
    const sm = new StateMachine();
    expect(() => sm.popState()).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// CommandInvoker
// ---------------------------------------------------------------------------

describe("CommandInvoker", () => {
  it("execute runs the command", () => {
    const invoker = new CommandInvoker();
    const entity = makeCombatEntity(50, 100);
    const cmd = new DealDamageCommand(entity, 10);

    invoker.executeCommand(cmd);
    expect(entity.hp).toBe(40);
  });

  it("undo reverses the last command", () => {
    const invoker = new CommandInvoker();
    const entity = makeCombatEntity(50, 100);

    invoker.executeCommand(new DealDamageCommand(entity, 10));
    expect(entity.hp).toBe(40);

    invoker.undoLastCommand();
    expect(entity.hp).toBe(50);
  });

  it("multiple commands build history; undo peels them off", () => {
    const invoker = new CommandInvoker();
    const entity = makeCombatEntity(100, 100);

    invoker.executeCommand(new DealDamageCommand(entity, 20));
    invoker.executeCommand(new DealDamageCommand(entity, 15));
    expect(entity.hp).toBe(65);

    invoker.undoLastCommand();
    expect(entity.hp).toBe(80);

    invoker.undoLastCommand();
    expect(entity.hp).toBe(100);
  });

  it("undo on empty history does nothing", () => {
    const invoker = new CommandInvoker();
    expect(() => invoker.undoLastCommand()).not.toThrow();
  });

  it("notifies listeners on execute", () => {
    const invoker = new CommandInvoker();
    const listener = vi.fn();
    invoker.onCommandExecuted(listener);

    const entity = makeCombatEntity(50, 100);
    const cmd = new DealDamageCommand(entity, 5);
    invoker.executeCommand(cmd);

    expect(listener).toHaveBeenCalledWith(cmd);
  });

  it("unsubscribes listeners correctly", () => {
    const invoker = new CommandInvoker();
    const listener = vi.fn();
    const unsub = invoker.onCommandExecuted(listener);

    unsub();

    const entity = makeCombatEntity(50, 100);
    invoker.executeCommand(new DealDamageCommand(entity, 5));

    expect(listener).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// DealDamageCommand
// ---------------------------------------------------------------------------

describe("DealDamageCommand", () => {
  it("reduces HP by the damage amount", () => {
    const entity = makeCombatEntity(50, 100);
    const cmd = new DealDamageCommand(entity, 15);
    cmd.execute();
    expect(entity.hp).toBe(35);
  });

  it("respects block — damage is reduced by block first", () => {
    const entity = makeCombatEntity(50, 100, 10);
    const cmd = new DealDamageCommand(entity, 15);
    cmd.execute();
    expect(entity.block).toBe(0);
    expect(entity.hp).toBe(45); // 15 - 10 block = 5 actual damage
  });

  it("block absorbs all damage if block >= damage", () => {
    const entity = makeCombatEntity(50, 100, 20);
    const cmd = new DealDamageCommand(entity, 10);
    cmd.execute();
    expect(entity.block).toBe(10);
    expect(entity.hp).toBe(50);
  });

  it("undo restores HP and block", () => {
    const entity = makeCombatEntity(50, 100, 5);
    const cmd = new DealDamageCommand(entity, 10);
    cmd.execute();
    expect(entity.hp).toBe(45);
    expect(entity.block).toBe(0);

    cmd.undo();
    expect(entity.hp).toBe(50);
    expect(entity.block).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// GainBlockCommand
// ---------------------------------------------------------------------------

describe("GainBlockCommand", () => {
  it("adds block to entity", () => {
    const entity = makeCombatEntity(50, 100, 0);
    const cmd = new GainBlockCommand(entity, 8);
    cmd.execute();
    expect(entity.block).toBe(8);
  });

  it("stacks with existing block", () => {
    const entity = makeCombatEntity(50, 100, 5);
    const cmd = new GainBlockCommand(entity, 8);
    cmd.execute();
    expect(entity.block).toBe(13);
  });

  it("undo removes the block gained", () => {
    const entity = makeCombatEntity(50, 100, 5);
    const cmd = new GainBlockCommand(entity, 8);
    cmd.execute();
    cmd.undo();
    expect(entity.block).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// HealCommand
// ---------------------------------------------------------------------------

describe("HealCommand", () => {
  it("heals the entity", () => {
    const entity = makeCombatEntity(50, 100);
    const cmd = new HealCommand(entity, 20);
    cmd.execute();
    expect(entity.hp).toBe(70);
  });

  it("does not exceed maxHp", () => {
    const entity = makeCombatEntity(90, 100);
    const cmd = new HealCommand(entity, 20);
    cmd.execute();
    expect(entity.hp).toBe(100);
  });

  it("undo removes the actual amount healed", () => {
    const entity = makeCombatEntity(90, 100);
    const cmd = new HealCommand(entity, 20);
    cmd.execute();
    expect(entity.hp).toBe(100);

    cmd.undo();
    expect(entity.hp).toBe(90); // only 10 was actually healed
  });
});

// ---------------------------------------------------------------------------
// ApplyStatusCommand
// ---------------------------------------------------------------------------

describe("ApplyStatusCommand", () => {
  it("adds a status effect", () => {
    const entity = makeCombatEntity(50, 100) as ICombatEntity & {
      _statuses: Map<string, number>;
    };
    const cmd = new ApplyStatusCommand(entity, "poison", 3);
    cmd.execute();
    expect(entity._statuses.get("poison")).toBe(3);
  });

  it("stacks status effects", () => {
    const entity = makeCombatEntity(50, 100) as ICombatEntity & {
      _statuses: Map<string, number>;
    };
    new ApplyStatusCommand(entity, "poison", 3).execute();
    new ApplyStatusCommand(entity, "poison", 2).execute();
    expect(entity._statuses.get("poison")).toBe(5);
  });

  it("undo removes status stacks", () => {
    const entity = makeCombatEntity(50, 100) as ICombatEntity & {
      _statuses: Map<string, number>;
    };
    new ApplyStatusCommand(entity, "poison", 3).execute();
    const cmd = new ApplyStatusCommand(entity, "poison", 2);
    cmd.execute();
    expect(entity._statuses.get("poison")).toBe(5);

    cmd.undo();
    expect(entity._statuses.get("poison")).toBe(3);
  });
});
