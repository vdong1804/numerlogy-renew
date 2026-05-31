/**
 * TextField wrapper used by auth pages.
 *
 * The global MUI theme overrides `MuiOutlinedInput` and `MuiInputLabel` with
 * white text (assumes dark backgrounds). On these pages we sit on a dark
 * gradient already — but we still need to explicitly:
 *   - lock label color (avoid invisible-on-focus states)
 *   - give the input a readable filled background
 *   - keep helper / error text legible
 */
import type { TextFieldProps } from '@mui/material'
import { TextField } from '@mui/material'
import { forwardRef } from 'react'

const AuthTextField = forwardRef<HTMLDivElement, TextFieldProps>(
  function AuthTextField(props, ref) {
    return (
      <TextField
        ref={ref}
        fullWidth
        variant="outlined"
        {...props}
        sx={{
          '& .MuiInputLabel-root': {
            color: 'rgba(255,255,255,0.75)',
          },
          '& .MuiInputLabel-root.Mui-focused': {
            color: '#F96A2D',
          },
          '& .MuiInputLabel-root.Mui-error': {
            color: '#EB5757',
          },
          '& .MuiOutlinedInput-root': {
            borderRadius: 2,
            backgroundColor: 'rgba(255,255,255,0.08)',
            color: '#fff',
            maxWidth: '100%',
            '& fieldset': {
              borderColor: 'rgba(255,255,255,0.25)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255,255,255,0.5) !important',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#F96A2D !important',
            },
          },
          '& .MuiOutlinedInput-input::placeholder': {
            color: 'rgba(255,255,255,0.5)',
            opacity: 1,
          },
          '& .MuiFormHelperText-root': {
            color: 'rgba(255,255,255,0.6)',
            marginLeft: 0.5,
          },
          '& .MuiFormHelperText-root.Mui-error': {
            color: '#FF8A8A',
          },
          '& .MuiSvgIcon-root': {
            color: 'rgba(255,255,255,0.7)',
          },
          ...props.sx,
        }}
      />
    )
  }
)

export default AuthTextField
