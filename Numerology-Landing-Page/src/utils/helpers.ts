import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'

export default function CustomDateAdapter(options: any) {
  const adapter = new AdapterDayjs(options)

  const constructUpperObject = (text: string) => ({ toUpperCase: () => text })
  const constructDayObject = (day: string) => ({
    charAt: () => constructUpperObject(day),
  })

  return {
    ...adapter,
    getWeekdays() {
      // Feel free to replace this with your custom value
      const customWeekdays = ['CN', 'Hai', 'Ba', 'Bốn', 'Năm', 'Sáu', 'Bảy']
      // const customWeekdays = adapter.getWeekdays()

      return customWeekdays.map((day) => constructDayObject(day))
    },
  }
}

export const formatNumberDE = (n: number) => {
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 }).format(n)
}
export const getImageByMainNumber = (mainNumber: number) =>
  `/assets/images/numbers/${mainNumber}.png`
export const convertToVND = (value: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(
    value
  )
