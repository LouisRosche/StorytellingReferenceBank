/**
 * Generic finite state machine (pushdown automaton).
 * Ported from Unity C# StateMachine.cs — zero framework dependencies.
 *
 * States are stacked so sub-states (e.g. target selection) can be pushed
 * on top of the current state and popped when complete.
 */

export interface IState {
  enter(): void;
  exit(): void;
  update(): void;
}

export class StateMachine {
  private readonly stateStack: IState[] = [];

  get currentState(): IState | null {
    return this.stateStack.length > 0
      ? this.stateStack[this.stateStack.length - 1]
      : null;
  }

  /** Push a sub-state onto the stack. The previous state's exit() is called. */
  pushState(state: IState): void {
    this.currentState?.exit();
    this.stateStack.push(state);
    state.enter();
  }

  /** Pop the current sub-state and re-enter the one beneath it. */
  popState(): void {
    if (this.stateStack.length === 0) return;

    const exiting = this.stateStack.pop()!;
    exiting.exit();
    this.currentState?.enter();
  }

  /** Clear the entire stack and transition to a single new state. */
  changeState(state: IState): void {
    while (this.stateStack.length > 0) {
      this.stateStack.pop()!.exit();
    }
    this.stateStack.push(state);
    state.enter();
  }

  /** Tick the current state. */
  update(): void {
    this.currentState?.update();
  }

  getCurrentState(): IState | null {
    return this.currentState;
  }
}
