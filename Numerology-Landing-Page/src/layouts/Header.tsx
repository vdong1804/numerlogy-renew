import ClearIcon from '@mui/icons-material/Clear'
import MenuIcon from '@mui/icons-material/Menu'
import SearchIcon from '@mui/icons-material/Search'
import { Divider, Drawer, MenuList, Stack } from '@mui/material'
import AppBar from '@mui/material/AppBar'
import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import IconButton from '@mui/material/IconButton'
import MenuItem from '@mui/material/MenuItem'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Link from 'next/link'
import { useRouter } from 'next/router'
import * as React from 'react'

import { ModalSearch } from '@/components/modal'
import { useUserAuth } from '@/lib/user-auth'

const PAGES = [
  {
    name: 'Trang chủ',
    to: '#',
  },
  {
    name: 'Tra cứu',
    to: '#tra-cuu',
  },
  {
    name: 'Liên hệ',
    to: '/contact',
  }
]

function ResponsiveAppBar() {
  const router = useRouter()
  const { user, logout } = useUserAuth()
  const [anchorElNav, setAnchorElNav] = React.useState(false)
  const [openSearch, setOpenSearch] = React.useState(false)

  const toggleDrawer =
    (isOpen: boolean) => (event: React.KeyboardEvent | React.MouseEvent) => {
      if (
        event.type === 'keydown' &&
        ((event as React.KeyboardEvent).key === 'Tab' ||
          (event as React.KeyboardEvent).key === 'Shift')
      ) {
        return
      }
      setAnchorElNav(isOpen)
    }

  const handleCloseModalSearch = () => setOpenSearch(false)

  return (
    <AppBar
      position="static"
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(3, 29, 46, 0.9)',
        zIndex: 100,
        backdropFilter: 'blur(4px)',
      }}
    >
      <Container maxWidth={false}>
        <Toolbar disableGutters>
          <Link passHref href={'/'} legacyBehavior>
            <Typography
              variant="h6"
              noWrap
              component="a"
              sx={{
                my: 2,
                '&:hover': {
                  filter: 'brightness(0.75)',
                  transition: 'all ease 0.2s',
                },
              }}
            >
              <img
                src={`${router.basePath}/numerology_logo.svg`}
                alt="Logo Numerology"
              />
            </Typography>
          </Link>
          <Box
            sx={{
              flexGrow: 1,
              display: { xs: 'none', md: 'flex', justifyContent: 'center' },
            }}
          >
            {PAGES.map(({ name, to }) => (
              <Button
                key={name}
                size="small"
                sx={{ textTransform: 'uppercase' }}
                onClick={() => router.push(to, undefined, { scroll: false })}
              >
                {name}
              </Button>
            ))}
          </Box>
          <Box
            sx={{
              display: {
                xs: 'none',
                md: 'flex',
              },
              flexShrink: 0,
              justifyContent: {
                xs: 'center',
                md: 'right',
              },
              alignItems: 'center',
            }}
          >
            <IconButton color="primary" onClick={() => setOpenSearch(true)}>
              <SearchIcon fontSize="large" sx={{ color: '#fff' }} />
            </IconButton>
            <ModalSearch
              open={openSearch}
              handleClose={handleCloseModalSearch}
            />
            <Divider
              orientation="vertical"
              variant="middle"
              sx={{ borderColor: '#fff', marginLeft: 1 }}
              flexItem
            />
            <Box ml={2}>
              {!user && (
                <Stack direction="row" spacing={1.5}>
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={() => router.push('/register')}
                  >
                    Đăng Ký
                  </Button>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => router.push('/login')}
                  >
                    Đăng Nhập
                  </Button>
                </Stack>
              )}

              {user && (
                <Box
                  sx={{
                    flexGrow: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  {/* Chat link — visible only when authenticated */}
                  <Button
                    size="small"
                    variant="outlined"
                    sx={{
                      textTransform: 'none',
                      fontWeight: 600,
                      borderColor: 'rgba(249,106,45,0.6)',
                      color: '#F96A2D',
                      '&:hover': {
                        borderColor: '#F96A2D',
                        backgroundColor: 'rgba(249,106,45,0.08)',
                      },
                    }}
                    onClick={() => router.push('/chat')}
                    aria-label="Mở Chat AI"
                  >
                    Chat AI
                  </Button>
                  <Link
                    href="/my-account/profile"
                    passHref
                    legacyBehavior
                    aria-label={
                      `${user.first_name} ${user.last_name}`.trim() ||
                      user.email
                    }
                  >
                    <IconButton sx={{ p: 0 }} size="large" component="a">
                      <Avatar
                        alt="User"
                        sx={{
                          width: 46,
                          height: 46,
                          mr: 1,
                        }}
                      >
                        {user.email[0]?.toUpperCase()}
                      </Avatar>
                    </IconButton>
                  </Link>
                </Box>
              )}
            </Box>
          </Box>

          <Box
            sx={{
              display: { xs: 'flex', md: 'none' },
              marginLeft: 'auto',
            }}
          >
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={toggleDrawer(true)}
              color="inherit"
            >
              <MenuIcon fontSize="large" color="primary" />
            </IconButton>
            <Drawer
              anchor="right"
              open={anchorElNav}
              onClose={toggleDrawer(false)}
            >
              <Box
                sx={{
                  width: 250,
                  p: 1,
                  height: '100%',
                }}
                role="presentation"
                onClick={toggleDrawer(false)}
                onKeyDown={toggleDrawer(false)}
                className="menu-mobile-navbar"
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 1,
                  }}
                >
                  <img
                    src={`${router.basePath}/numerology_favicon.svg`}
                    alt="Logo Numerology"
                  />

                  <IconButton color="primary">
                    <ClearIcon fontSize="large" color="primary" />
                  </IconButton>
                </Box>
                <MenuList>
                  {PAGES.map(({ name, to }) => (
                    <MenuItem key={name} sx={{ borderRadius: '5px', py: 1 }}>
                      <Typography
                        textAlign="center"
                        variant="body1"
                        sx={{
                          color: '#fff',
                          fontWeight: 600,
                          '&:active': { color: '#F96A2D' },
                        }}
                        component={'a'}
                        href={to}
                      >
                        {name}
                      </Typography>
                    </MenuItem>
                  ))}
                  {!user && (
                    <>
                      <MenuItem
                        sx={{ borderRadius: '5px', py: 1 }}
                        onClick={() => router.push('/login')}
                      >
                        <Typography
                          variant="body1"
                          sx={{ color: '#fff', fontWeight: 600 }}
                        >
                          Đăng Nhập
                        </Typography>
                      </MenuItem>
                      <MenuItem
                        sx={{ borderRadius: '5px', py: 1 }}
                        onClick={() => router.push('/register')}
                      >
                        <Typography
                          variant="body1"
                          sx={{ color: '#fff', fontWeight: 600 }}
                        >
                          Đăng Ký
                        </Typography>
                      </MenuItem>
                    </>
                  )}
                  {user && (
                    <MenuItem
                      sx={{ borderRadius: '5px', py: 1 }}
                      onClick={() => router.push('/chat')}
                    >
                      <Typography
                        variant="body1"
                        sx={{ color: '#F96A2D', fontWeight: 600 }}
                      >
                        Chat AI
                      </Typography>
                    </MenuItem>
                  )}
                  {user && (
                    <MenuItem
                      sx={{ borderRadius: '5px', py: 1 }}
                      onClick={() => logout()}
                    >
                      <Typography
                        variant="body1"
                        sx={{ color: '#fff', fontWeight: 600 }}
                      >
                        Đăng Xuất
                      </Typography>
                    </MenuItem>
                  )}
                </MenuList>
              </Box>
            </Drawer>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  )
}
export default ResponsiveAppBar
