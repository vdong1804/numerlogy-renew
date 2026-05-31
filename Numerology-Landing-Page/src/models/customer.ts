import type { Dayjs } from 'dayjs'

export interface Customer {
  name: string
  sex: 'M' | 'F'
  birthDay: Dayjs | null | undefined
  phoneNumber: string
}
