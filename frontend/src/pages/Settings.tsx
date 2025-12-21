import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
} from '@mui/material'

export default function Settings() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Telnet Server
            </Typography>
            <TextField
              label="Host"
              defaultValue="0.0.0.0"
              fullWidth
              margin="normal"
              disabled
            />
            <TextField
              label="Port"
              defaultValue="23"
              type="number"
              fullWidth
              margin="normal"
              disabled
            />
            <TextField
              label="Max Connections"
              defaultValue="100"
              type="number"
              fullWidth
              margin="normal"
            />
            <TextField
              label="Idle Timeout (seconds)"
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
              User Settings
            </Typography>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Auto Registration Enabled"
            />
            <TextField
              label="Guest User ID"
              defaultValue="guest"
              fullWidth
              margin="normal"
            />
            <TextField
              label="Default User Level"
              defaultValue="1"
              type="number"
              fullWidth
              margin="normal"
            />
            <TextField
              label="Sysop Level"
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
              Database
            </Typography>
            <TextField
              label="Database URL"
              defaultValue="postgresql+asyncpg://mtbbs:****@localhost:5432/mtbbs"
              fullWidth
              margin="normal"
              type="password"
            />
            <TextField
              label="Redis URL"
              defaultValue="redis://localhost:6379"
              fullWidth
              margin="normal"
            />
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Box display="flex" justifyContent="flex-end" gap={2}>
            <Button variant="outlined">Reset</Button>
            <Button variant="contained">Save Changes</Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}
