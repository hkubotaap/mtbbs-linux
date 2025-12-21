import { useQuery } from '@tanstack/react-query'
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material'
import {
  People as PeopleIcon,
  Forum as ForumIcon,
  Message as MessageIcon,
  Cable as CableIcon,
} from '@mui/icons-material'
import { adminAPI } from '../api/client'

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string
  value: number
  icon: React.ReactNode
  color: string
}) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" gap={2}>
          <Box
            sx={{
              backgroundColor: color,
              borderRadius: 2,
              p: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box sx={{ color: 'white' }}>{icon}</Box>
          </Box>
          <Box>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            <Typography color="text.secondary">{title}</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await adminAPI.getStats()
      return response.data
    },
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Users"
            value={stats?.total_users || 0}
            icon={<PeopleIcon fontSize="large" />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Boards"
            value={stats?.total_boards || 0}
            icon={<ForumIcon fontSize="large" />}
            color="#2e7d32"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Messages"
            value={stats?.total_messages || 0}
            icon={<MessageIcon fontSize="large" />}
            color="#ed6c02"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Connections"
            value={stats?.telnet_connections || 0}
            icon={<CableIcon fontSize="large" />}
            color="#9c27b0"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            <Typography variant="body2" color="text.secondary">
              MTBBS Linux Version 4.0.0
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Server Status: Running
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Telnet Server: Active (Port 23)
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • View active Telnet connections
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • Manage users and boards
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • Monitor system performance
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
