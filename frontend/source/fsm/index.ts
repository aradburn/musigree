/**
 * @fileoverview Entry point for FSM that maintains backward compatibility
 */

import { MusigreeFSM } from "./MusigreeFSM";
import type { FSMInstance } from "./types";

export type {
    FSMInstance,
    FSMStateType,
    FSMState,
    FSMStates,
    FSMConfig,
} from "./types";

/**
 * The singleton FSM instance
 */
export let fsm: FSMInstance;

/**
 * Initialize the FSM with the new implementation
 */
export const initFSM = (): void => {
    // Create the new FSM implementation
    const newFsm = new MusigreeFSM();

    // Cast to the expected interface to maintain compatibility
    fsm = newFsm as unknown as FSMInstance;
};
