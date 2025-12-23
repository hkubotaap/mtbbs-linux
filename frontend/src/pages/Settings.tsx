import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Alert,
  Snackbar,
} from '@mui/material'
import { adminAPI } from '../api/client'

export default function Settings() {
  const { t } = useTranslation()
  const [openConfirm, setOpenConfirm] = useState(false)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' })

  const initializeMutation = useMutation({
    mutationFn: () => adminAPI.initializeDatabase(),
    onSuccess: (data) => {
      setOpenConfirm(false)
      setSnackbar({
        open: true,
        message: t('settings.initializeSuccess', {
          users: data.data.users_created,
          boards: data.data.boards_created,
          messages: data.data.system_messages_created
        }),
        severity: 'success'
      })
    },
    onError: (error: any) => {
      setOpenConfirm(false)
      setSnackbar({
        open: true,
        message: t('settings.initializeError', { error: error.response?.data?.detail || error.message }),
        severity: 'error'
      })
    },
  })

  const handleInitializeDatabase = () => {
    setOpenConfirm(true)
  }

  const handleConfirmInitialize = () => {
    initializeMutation.mutate()
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {t('settings.title')}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('settings.telnetServer')}
            </Typography>
            <TextField
              label={t('settings.host')}
              defaultValue="0.0.0.0"
              fullWidth
              margin="normal"
              disabled
            />
            <TextField
              label={t('settings.port')}
              defaultValue="23"
              type="number"
              fullWidth
              margin="normal"
              disabled
            />
            <TextField
              label={t('settings.maxConnections')}
              defaultValue="100"
              type="number"
              fullWidth
              margin="normal"
            />
            <TextField
              label={t('settings.idleTimeout')}
              defaultValue="1800"
              type="number"
              fullWidth
              margin="normal"
            />
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('settings.userSettings')}
            </Typography>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label={t('settings.autoRegistration')}
            />
            <TextField
              label={t('settings.guestUserId')}
              defaultValue="guest"
              fullWidth
              margin="normal"
            />
            <TextField
              label={t('settings.defaultUserLevel')}
              defaultValue="1"
              type="number"
              fullWidth
              margin="normal"
            />
            <TextField
              label={t('settings.sysopLevel')}
              defaultValue="9"
              type="number"
              fullWidth
              margin="normal"
            />
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {t('settings.database')}
            </Typography>
            <TextField
              label={t('settings.databaseUrl')}
              defaultValue="postgresql+asyncpg://mtbbs:****@localhost:5432/mtbbs"
              fullWidth
              margin="normal"
              type="password"
            />
            <TextField
              label={t('settings.redisUrl')}
              defaultValue="redis://localhost:6379"
              fullWidth
              margin="normal"
            />
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                color="error"
                onClick={handleInitializeDatabase}
                disabled={initializeMutation.isPending}
              >
                {initializeMutation.isPending ? t('settings.initializing') : t('settings.initializeDatabase')}
              </Button>
              <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
                {t('settings.initializeWarning')}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Box display="flex" justifyContent="flex-end" gap={2}>
            <Button variant="outlined">{t('common.reset')}</Button>
            <Button variant="contained">{t('settings.saveChanges')}</Button>
          </Box>
        </Grid>
      </Grid>

      {/* Confirmation Dialog */}
      <Dialog open={openConfirm} onClose={() => setOpenConfirm(false)}>
        <DialogTitle>{t('settings.initializeConfirmTitle')}</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {t('settings.initializeConfirmMessage')}
            <ul>
              <li>{t('settings.initializeConfirm1')}</li>
              <li>{t('settings.initializeConfirm2')}</li>
              <li>{t('settings.initializeConfirm3')}</li>
            </ul>
            <strong>{t('settings.initializeConfirmWarning')}</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenConfirm(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleConfirmInitialize} color="error" variant="contained">
            {t('settings.yesInitialize')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
