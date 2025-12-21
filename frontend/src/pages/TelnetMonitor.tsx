import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  Grid,
  Card,
  CardContent,
} from '@mui/material'
import { People as PeopleIcon, Person as PersonIcon, VerifiedUser as VerifiedUserIcon } from '@mui/icons-material'
import axios from 'axios'

const monitorAPI = axios.create({
  baseURL: 'http://localhost:8001/api',
})

export default function TelnetMonitor() {
  const { data: connections, isLoading: loadingConnections } = useQuery({
    queryKey: ['telnet-connections'],
    queryFn: async () => {
      const response = await monitorAPI.get('/telnet/connections')
      return response.data
    },
    refetchInterval: 3000, // 3秒ごとに更新
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['telnet-stats'],
    queryFn: async () => {
      const response = await monitorAPI.get('/telnet/stats')
      return response.data
    },
    refetchInterval: 3000,
  })

  if (loadingConnections || loadingStats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" mb={3}>
        Telnet接続モニター
      </Typography>

      {/* 統計カード */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <PeopleIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">総接続数</Typography>
              </Box>
              <Typography variant="h3">{stats?.total_connections || 0}</Typography>
              <Typography variant="caption" color="text.secondary">
                現在アクティブな接続
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <VerifiedUserIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">認証済みユーザー</Typography>
              </Box>
              <Typography variant="h3">{stats?.authenticated_users || 0}</Typography>
              <Typography variant="caption" color="text.secondary">
                ログイン完了
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <PersonIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">ゲストユーザー</Typography>
              </Box>
              <Typography variant="h3">{stats?.guest_users || 0}</Typography>
              <Typography variant="caption" color="text.secondary">
                ゲストログイン
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 接続一覧テーブル */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>クライアントID</TableCell>
              <TableCell>ユーザーID</TableCell>
              <TableCell>ハンドル名</TableCell>
              <TableCell>レベル</TableCell>
              <TableCell>認証状態</TableCell>
              <TableCell>接続時刻</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {connections?.connections?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary">現在接続中のユーザーはいません</Typography>
                </TableCell>
              </TableRow>
            ) : (
              connections?.connections?.map((conn: any, index: number) => (
                <TableRow key={index}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {conn.client_id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <strong>{conn.user_id}</strong>
                  </TableCell>
                  <TableCell>{conn.handle_name}</TableCell>
                  <TableCell>
                    <Chip label={`Level ${conn.level}`} size="small" color="primary" />
                  </TableCell>
                  <TableCell>
                    {conn.authenticated ? (
                      <Chip label="認証済み" color="success" size="small" />
                    ) : (
                      <Chip label="未認証" color="default" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(conn.connected_at).toLocaleString('ja-JP')}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 最終更新時刻 */}
      {connections?.last_updated && (
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            最終更新: {new Date(connections.last_updated).toLocaleString('ja-JP')} (自動更新: 3秒ごと)
          </Typography>
        </Box>
      )}
    </Box>
  )
}
