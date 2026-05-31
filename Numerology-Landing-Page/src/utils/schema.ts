import dayjs from 'dayjs'
import * as yup from 'yup'

export const searchSchema = yup.object().shape({
  name: yup.string().required('Vui lòng nhập tên'),
  sex: yup.string(),
  phoneNumber: yup
    .string()
    .required('Vui lòng nhập số điện thoại')
    .min(8, 'Vui lòng nhập đúng số điện thoại')
    .max(13, 'Vui lòng nhập đúng số điện thoại'),
  birthDay: yup
    .date()
    .required('Vui lòng chọn ngày sinh')
    .nullable()
    .typeError('Sai định dạng ngày sinh')
    .min(
      dayjs(new Date('1900-01-01')),
      'Ngày sinh lớn hơn 1900 và nhỏ hơn 2050'
    )
    .max(
      dayjs(new Date('2050-01-01')),
      'Ngày sinh lớn hơn 1900 và nhỏ hơn 2050'
    ),
})

export const rullingNumberSchema = yup.object().shape({
  day: yup.string().required('Vui lòng chọn ngày sinh'),
  month: yup.string().required('Vui lòng chọn tháng sinh'),
  year: yup.string().required('Vui lòng chọn năm sinh'),
})
