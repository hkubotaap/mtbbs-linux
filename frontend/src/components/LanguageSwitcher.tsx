import { IconButton, Menu, MenuItem } from '@mui/material'
import { Language as LanguageIcon } from '@mui/icons-material'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng)
    handleClose()
  }

  return (
    <>
      <IconButton color="inherit" onClick={handleClick}>
        <LanguageIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
      >
        <MenuItem onClick={() => changeLanguage('ja')} selected={i18n.language === 'ja'}>
          日本語
        </MenuItem>
        <MenuItem onClick={() => changeLanguage('en')} selected={i18n.language === 'en'}>
          English
        </MenuItem>
      </Menu>
    </>
  )
}
