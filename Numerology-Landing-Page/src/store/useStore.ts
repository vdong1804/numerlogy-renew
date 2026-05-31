import { create } from 'zustand'

import type { ICounterSlice } from './creatCounterSlice'
import { createCounterSlice } from './creatCounterSlice'
import type { ICommonSlice } from './createCommonSlice'
import { createCommonSlice } from './createCommonSlice'

export type MyState = ICommonSlice & ICounterSlice

export const useStore = create<MyState>()((...a) => ({
  ...createCommonSlice(...a),
  ...createCounterSlice(...a),
}))
