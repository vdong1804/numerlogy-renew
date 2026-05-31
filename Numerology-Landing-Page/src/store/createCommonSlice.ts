import dayjs from 'dayjs'
import type { StateCreator } from 'zustand'

import type { Customer } from '@/models'

import type { MyState } from './useStore'

export interface ICommonSlice {
  customerInfo: Customer
  setCustomerInfo: (value: Customer) => void
  mainNumber: number
  setMainNumber: (value: number) => void
}
export const createCommonSlice: StateCreator<MyState, [], [], ICommonSlice> = (
  set
) => ({
  customerInfo: {
    name: '',
    phoneNumber: '',
    sex: 'M',
    birthDay: dayjs(),
  },
  setCustomerInfo: (value) =>
    set((state) => ({ ...state, customerInfo: value })),
  mainNumber: 9,
  setMainNumber: (value: number) =>
    set((state) => ({ ...state, mainNumber: value })),
})
