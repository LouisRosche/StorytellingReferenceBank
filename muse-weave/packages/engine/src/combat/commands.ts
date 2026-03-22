/**
 * Command pattern for combat mutations.
 * Ported from CombatCommands.cs, CommandInvoker.cs, ICombatEntity.cs.
 *
 * Commands are the sole mechanism for mutating combat state, giving us
 * a full undo stack and an event stream for UI / replay.
 */

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

export interface ICommand {
  execute(): void;
  undo(): void;
}

export interface ICombatEntity {
  hp: number;
  readonly maxHp: number;
  block: number;
  addStatusEffect(effectId: string, stacks: number): void;
  removeStatusEffect(effectId: string, stacks: number): void;
}

export interface IDeckManager {
  draw(count: number): void;
  discard(cardId: string): void;
  exhaust(cardId: string): void;
}

// ---------------------------------------------------------------------------
// CommandInvoker — central dispatcher with undo history & cascade queue.
// ---------------------------------------------------------------------------

export type CommandListener = (command: ICommand) => void;

export class CommandInvoker {
  private readonly history: ICommand[] = [];
  private readonly resolutionQueue: ICommand[] = [];
  private readonly listeners: CommandListener[] = [];

  /** Subscribe to every command execution (including triggered cascades). */
  onCommandExecuted(listener: CommandListener): () => void {
    this.listeners.push(listener);
    return () => {
      const idx = this.listeners.indexOf(listener);
      if (idx !== -1) this.listeners.splice(idx, 1);
    };
  }

  executeCommand(command: ICommand): void {
    command.execute();
    this.history.push(command);
    this.notify(command);

    // Process cascading commands enqueued during execution.
    while (this.resolutionQueue.length > 0) {
      const triggered = this.resolutionQueue.shift()!;
      triggered.execute();
      this.history.push(triggered);
      this.notify(triggered);
    }
  }

  /**
   * Enqueue a triggered command to resolve after the current command completes.
   * Used for "whenever X happens, do Y" effects.
   */
  enqueueTriggered(command: ICommand): void {
    this.resolutionQueue.push(command);
  }

  undoLastCommand(): void {
    if (this.history.length === 0) return;
    const command = this.history.pop()!;
    command.undo();
  }

  clearHistory(): void {
    this.history.length = 0;
  }

  private notify(command: ICommand): void {
    for (const listener of this.listeners) {
      listener(command);
    }
  }
}

// ---------------------------------------------------------------------------
// Concrete commands
// ---------------------------------------------------------------------------

export class DealDamageCommand implements ICommand {
  private actualDamage = 0;
  private blockedAmount = 0;

  constructor(
    private readonly target: ICombatEntity,
    private readonly amount: number,
  ) {}

  execute(): void {
    this.blockedAmount = Math.min(this.target.block, this.amount);
    this.actualDamage = this.amount - this.blockedAmount;
    this.target.block -= this.blockedAmount;
    this.target.hp -= this.actualDamage;
  }

  undo(): void {
    this.target.hp += this.actualDamage;
    this.target.block += this.blockedAmount;
  }
}

export class GainBlockCommand implements ICommand {
  constructor(
    private readonly target: ICombatEntity,
    private readonly amount: number,
  ) {}

  execute(): void {
    this.target.block += this.amount;
  }

  undo(): void {
    this.target.block -= this.amount;
  }
}

export class ApplyStatusCommand implements ICommand {
  constructor(
    private readonly target: ICombatEntity,
    private readonly effectId: string,
    private readonly stacks: number,
  ) {}

  execute(): void {
    this.target.addStatusEffect(this.effectId, this.stacks);
  }

  undo(): void {
    this.target.removeStatusEffect(this.effectId, this.stacks);
  }
}

export class HealCommand implements ICommand {
  private actualHeal = 0;

  constructor(
    private readonly target: ICombatEntity,
    private readonly amount: number,
  ) {}

  execute(): void {
    const before = this.target.hp;
    this.target.hp = Math.min(this.target.hp + this.amount, this.target.maxHp);
    this.actualHeal = this.target.hp - before;
  }

  undo(): void {
    this.target.hp -= this.actualHeal;
  }
}

export class DrawCardCommand implements ICommand {
  constructor(
    private readonly deck: IDeckManager,
    private readonly count: number,
  ) {}

  execute(): void {
    this.deck.draw(this.count);
  }

  undo(): void {
    /* Draw is not trivially reversible — intentionally left empty. */
  }
}
