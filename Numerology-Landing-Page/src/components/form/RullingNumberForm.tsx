import { yupResolver } from '@hookform/resolvers/yup'
import SearchIcon from '@mui/icons-material/Search'
import { Autocomplete, Box, Button, InputLabel, TextField } from '@mui/material'
import { useRouter } from 'next/router'
import { Controller, useForm } from 'react-hook-form'

import { rullingNumberSchema } from '@/utils/schema'

import { IconDown } from '../icon'

interface FormValue {
  day: string
  month: string
  year: string
}
const DAY_LIST = [
  '01',
  '02',
  '03',
  '04',
  '05',
  '06',
  '07',
  '08',
  '09',
  '10',
  '11',
  '12',
  '13',
  '14',
  '15',
  '16',
  '17',
  '18',
  '19',
  '20',
  '21',
  '22',
  '23',
  '24',
  '25',
  '26',
  '27',
  '28',
  '29',
  '30',
  '31',
]

const MONTH_LIST = [
  '01',
  '02',
  '03',
  '04',
  '05',
  '06',
  '07',
  '08',
  '09',
  '10',
  '11',
  '12',
]
export default function RullingNumberForm() {
  const router = useRouter()
  const {
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValue>({
    resolver: yupResolver(rullingNumberSchema),
    defaultValues: {
      day: '',
      month: '',
      year: '',
    },
    mode: 'onChange',
  })
  const submitForm = (data: FormValue) => {
    // eslint-disable-next-line no-console
    console.log(data)
    router.push('/ket-qua')
  }
  return (
    <Box component={'form'} onSubmit={handleSubmit(submitForm)}>
      <Box display={'flex'} columnGap={2.5} rowGap={1.5} flexWrap={'wrap'}>
        <Controller
          name="day"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box
              display={'flex'}
              flexDirection={'column'}
              rowGap={0.5}
              flex={1}
            >
              <InputLabel htmlFor="day-id">Ngày sinh</InputLabel>
              <Autocomplete
                disablePortal
                id="day-id"
                options={DAY_LIST}
                value={value || null}
                clearIcon={false}
                popupIcon={<IconDown />}
                onChange={(_, v) => onChange(v)}
                sx={{
                  minWidth: '220px',
                  '& .MuiOutlinedInput-root': {
                    padding: 0,
                    '& .MuiOutlinedInput-input': {
                      padding: '12.5px 14px',
                    },
                  },
                }}
                renderInput={(params) => (
                  <TextField
                    placeholder="Ngày sinh"
                    {...params}
                    error={invalid}
                    helperText={
                      errors.day
                        ? (errors.day?.message as unknown as string)
                        : ''
                    }
                  />
                )}
              />
            </Box>
          )}
        />
        <Controller
          name="month"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box
              display={'flex'}
              flexDirection={'column'}
              rowGap={0.5}
              flex={1}
            >
              <InputLabel htmlFor="month-id">Tháng sinh</InputLabel>
              <Autocomplete
                disablePortal
                id="month-id"
                options={MONTH_LIST}
                value={value || null}
                clearIcon={false}
                popupIcon={<IconDown />}
                onChange={(_, v) => onChange(v)}
                sx={{
                  minWidth: '220px',
                  '& .MuiOutlinedInput-root': {
                    padding: 0,
                    '& .MuiOutlinedInput-input': {
                      padding: '12.5px 14px',
                    },
                  },
                }}
                renderInput={(params) => (
                  <TextField
                    placeholder="Tháng sinh"
                    {...params}
                    error={invalid}
                    helperText={
                      errors.month
                        ? (errors.month?.message as unknown as string)
                        : ''
                    }
                  />
                )}
              />
            </Box>
          )}
        />
        <Controller
          name="year"
          control={control}
          render={({ field: { onChange, value }, fieldState: { invalid } }) => (
            <Box
              display={'flex'}
              flexDirection={'column'}
              rowGap={0.5}
              flex={1}
            >
              <InputLabel htmlFor="year-id">Năm sinh</InputLabel>
              <Autocomplete
                disablePortal
                id="year-id"
                options={Array.from({ length: 151 }, (_, i) =>
                  (i + 1900).toString()
                )}
                value={value || null}
                clearIcon={false}
                popupIcon={<IconDown />}
                onChange={(_, v) => onChange(v)}
                sx={{
                  minWidth: '220px',
                  '& .MuiOutlinedInput-root': {
                    padding: 0,
                    '& .MuiOutlinedInput-input': {
                      padding: '12.5px 14px',
                    },
                  },
                }}
                renderInput={(params) => (
                  <TextField
                    placeholder="Năm sinh"
                    {...params}
                    error={invalid}
                    helperText={
                      errors.year
                        ? (errors.year?.message as unknown as string)
                        : ''
                    }
                  />
                )}
              />
            </Box>
          )}
        />
      </Box>
      <Button
        sx={{ mt: 2.5, minHeight: 48 }}
        type="submit"
        fullWidth
        size="medium"
        color="primary"
        variant="contained"
        startIcon={<SearchIcon />}
      >
        Tính số chủ đạo
      </Button>
    </Box>
  )
}
