import { yupResolver } from '@hookform/resolvers/yup'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import SearchIcon from '@mui/icons-material/Search'
import {
  Autocomplete,
  Box,
  Button,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import dayjs from 'dayjs'
import { useRouter } from 'next/router'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'

import type { CountryType, Customer } from '@/models'
import { useStore } from '@/store/useStore'
import { countries, SEX_LABEL } from '@/utils/constant'
import { searchSchema } from '@/utils/schema'

import { IconCalendar, IconDown, IconTwoRhombus } from '../icon'

type FormValue = Customer
export interface SearchNumerologyFormProps {
  title: string
  subTitle?: string
}

export default function SearchNumerologyForm({
  title,
  subTitle,
}: SearchNumerologyFormProps) {
  const router = useRouter()
  const setCustomerInfo = useStore((state) => state.setCustomerInfo)

  const {
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValue>({
    resolver: yupResolver(searchSchema),
    defaultValues: {
      name: '',
      sex: 'M',
      birthDay: '',
      phoneNumber: '',
    },
    mode: 'onChange',
  })
  const [countryCode, setCountryCode] = useState<CountryType>(
    countries[238] as CountryType
  )
  const submitForm = (data: FormValue) => {
    setCustomerInfo(data)
    router.push('/ket-qua')
  }
  return (
    <Box component={'form'} onSubmit={handleSubmit(submitForm)}>
      <IconTwoRhombus />
      <Box>
        <Typography className="text-heading">{title}</Typography>
        {subTitle && (
          <Typography className="text-heading">{subTitle}</Typography>
        )}

        <Box mt={2}>
          <Typography fontSize={14}>
            - Tính toán hàng chục nghìn phép tính thần số phức tạp cực nhanh chỉ
            sau 1 giây để cho ra các tổ hợp chỉ số mà không hề sai sót như tính
            tay.
          </Typography>
          <Typography fontSize={14} mt={0.5}>
            - Luận giải kết quả tra cứu được cá nhân hóa dựa vào nghiên cứu
            chuyên sâu của các chuyên gia Thần số học.
          </Typography>
        </Box>
      </Box>
      <Box mt={3.75} display={'flex'} flexDirection={'column'} rowGap={2}>
        <Controller
          name="name"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box display={'flex'} flexDirection={'column'} rowGap={0.5}>
              <InputLabel htmlFor="name-id">
                Họ tên khai sinh (nên nhập không dấu)
              </InputLabel>
              <TextField
                placeholder="Nhập họ tên"
                onChange={onChange}
                value={value}
                id="name-id"
                error={invalid}
                helperText={
                  errors.name ? (errors.name?.message as unknown as string) : ''
                }
              />
            </Box>
          )}
        />
        <Controller
          name="sex"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box display={'flex'} flexDirection={'column'} rowGap={0.5}>
              <InputLabel htmlFor="sex-id">Giới tính</InputLabel>
              <Select
                id="sex-id"
                placeholder="Giới tính"
                value={value}
                fullWidth
                error={invalid}
                onChange={onChange}
                MenuProps={{
                  disableScrollLock: true,
                }}
                IconComponent={() => (
                  <IconButton sx={{ right: 7 }}>
                    <IconDown />
                  </IconButton>
                )}
              >
                {SEX_LABEL.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </Box>
          )}
        />
        <Controller
          name="birthDay"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box display={'flex'} flexDirection={'column'} rowGap={0.5}>
              <InputLabel htmlFor="date-birthday-id">
                Ngày/tháng/năm sinh dương lịch
              </InputLabel>
              <DatePicker
                format="DD/MM/YYYY"
                slots={{
                  openPickerIcon: IconCalendar,
                }}
                maxDate={dayjs(new Date('2050-01-01'))}
                minDate={dayjs(new Date('1900-01-01'))}
                onChange={onChange}
                value={value || null}
                componentsProps={{
                  openPickerIcon: IconCalendar,
                  textField: {
                    id: 'date-birthday-id',
                    error: invalid,
                    helperText: errors.birthDay
                      ? (errors.birthDay?.message as unknown as string)
                      : '',
                  },
                }}
              />
            </Box>
          )}
        />

        <Controller
          name="phoneNumber"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box display={'flex'} flexDirection={'column'} rowGap={0.5}>
              <InputLabel htmlFor="phone-id">Nhập số điện thoại</InputLabel>
              <TextField
                id="phone-id"
                inputMode="numeric"
                type="number"
                value={value}
                onChange={onChange}
                placeholder="Nhập số điện thoại"
                error={invalid}
                helperText={
                  errors.phoneNumber
                    ? (errors.phoneNumber?.message as unknown as string)
                    : ''
                }
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Autocomplete
                        id="country-select"
                        sx={{
                          minWidth: 150,
                        }}
                        options={countries}
                        value={countryCode}
                        onChange={(_: any, newValue: CountryType) => {
                          setCountryCode(newValue)
                        }}
                        autoHighlight
                        disableClearable
                        getOptionLabel={(option) => option.label}
                        popupIcon={
                          <KeyboardArrowDownIcon sx={{ color: '#fff' }} />
                        }
                        renderOption={(props, option) => (
                          <Box
                            component="li"
                            sx={{ '& > img': { mr: 2, flexShrink: 0 } }}
                            {...props}
                          >
                            <img
                              loading="lazy"
                              width="20"
                              src={`https://flagcdn.com/w20/${option.code.toLowerCase()}.png`}
                              srcSet={`https://flagcdn.com/w40/${option.code.toLowerCase()}.png 2x`}
                              alt=""
                            />
                            {option.label} ({option.code}) +{option.phone}
                          </Box>
                        )}
                        renderInput={(params) => (
                          <TextField
                            {...params}
                            className="select-code-phone"
                            inputProps={{
                              ...params.inputProps,
                              autoComplete: 'new-password', // disable autocomplete and autofill
                            }}
                          />
                        )}
                      />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
          )}
        />

        <Button
          sx={{ mt: 2, maxWidth: 458 }}
          type="submit"
          size="large"
          color="primary"
          variant="contained"
          startIcon={<SearchIcon />}
        >
          Tra Cứu Ngay
        </Button>
      </Box>
    </Box>
  )
}
