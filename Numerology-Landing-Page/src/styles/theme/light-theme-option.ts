import type { ThemeOptions } from '@mui/material'

// Custom theme: Colors
const themeColors = {
  color: {
    main: '#F96A2D',
    bg: '#031D2E',
    textLight: '#fff',
    textDark: '#012233',
    error: '#EB5757',
    borderTextField: '#DDE4EE',
  },
} as const

const lightThemeOptions: ThemeOptions = {
  ...themeColors,
  typography: {
    fontFamily: ['Raleway', 'sans-serif'].join(','),
    h3: {
      fontSize: '1.375rem',
      fontWeight: 700,
    },
    h4: {
      fontSize: '1.125rem',
      fontWeight: 700,
    },
    h5: {
      fontSize: '1rem',
      fontWeight: 700,
    },
  },
  palette: {
    primary: {
      main: themeColors.color.main,
      contrastText: themeColors.color.textLight,
    },
    secondary: {
      main: '#6F49FD',
    },
    info: {
      main: '#3C75EF',
      light: '#5CB0F2',
    },
    error: {
      main: themeColors.color.error,
    },
    background: {
      default: themeColors.color.bg,
      paper: themeColors.color.textLight,
    },
    text: {
      // primary: themeColors.color.textLight,
      secondary: themeColors.color.textDark,
    },
    common: {
      white: themeColors.color.textLight,
      black: themeColors.color.textDark,
    },
    grey: {
      100: '#E1E6EA',
      200: '#DDE4EE',
      500: '#66768E',
      700: '#475866',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          padding: '8px 25px',
          borderRadius: '9999px;',
          color: themeColors.color.textLight,
          fontSize: '1rem',
          textTransform: 'capitalize',
          fontWeight: 600,
          lineHeight: 1.875,
        },
        sizeLarge: {
          padding: '15px 25px',
        },
        sizeSmall: {
          fontSize: '0.875rem',
          padding: '6px 18px',
        },
      },
    },
    MuiTypography: {
      styleOverrides: {
        root: {
          lineHeight: 1.25,
        },
        body2: {
          lineHeight: '20px',
        },
      },
    },
    MuiAutocomplete: {
      styleOverrides: {
        endAdornment: {
          right: '16px !important',
          top: 'calc(50% - 0.875rem)',
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: '9999px;',
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          color: themeColors.color.textLight,
          maxWidth: '458px',
          '& fieldset': {
            borderColor: themeColors.color.borderTextField,
          },
          '&:hover fieldset': {
            borderColor: `${themeColors.color.main} !important`,
          },
        },
        input: {
          padding: '12.5px 14px',
          fontWeight: 500,
          '&::placeholder': {
            color: '#66768E',
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        icon: {
          color: themeColors.color.textLight,
        },
      },
    },
    MuiContainer: {
      styleOverrides: {
        root: {
          maxWidth: '1288px',
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          color: themeColors.color.textLight,
          fontWeight: 500,
          cursor: 'pointer',
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: '#66768E',
        },
      },
    },
  },
}

export default lightThemeOptions
