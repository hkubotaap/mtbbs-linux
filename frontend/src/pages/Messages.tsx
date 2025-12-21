import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Chip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
} from '@mui/material'
import { Edit as EditIcon, Refresh as RefreshIcon } from '@mui/icons-material'
import { adminAPI } from '../api/client'

export default function Messages() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editingMessage, setEditingMessage] = useState<any>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  const queryClient = useQueryClient()

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages'],
    queryFn: async () => {
      const response = await adminAPI.getMessages()
      return response.data
    },
    refetchInterval: 10000, // Auto-refresh every 10 seconds
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => adminAPI.updateMessage(data.message_key, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      setOpenDialog(false)
      setEditingMessage(null)
    },
  })

  const initializeMutation = useMutation({
    mutationFn: () => adminAPI.initializeMessages(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  const handleEdit = (message: any) => {
    setEditingMessage({ ...message })
    setOpenDialog(true)
  }

  const handleUpdate = () => {
    if (editingMessage) {
      updateMutation.mutate(editingMessage)
    }
  }

  const handleInitialize = () => {
    if (window.confirm('Initialize default messages from messages_ja.py? Existing messages will not be overwritten.')) {
      initializeMutation.mutate()
    }
  }

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: 'primary' | 'success' | 'warning' | 'info' } = {
      menu: 'primary',
      greeting: 'success',
      info: 'info',
      help: 'warning',
    }
    return colors[category] || 'default'
  }

  const filteredMessages = messages?.filter((msg: any) =>
    categoryFilter === 'all' || msg.category === categoryFilter
  )

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">System Messages</Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              label="Category"
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="all">All Categories</MenuItem>
              <MenuItem value="menu">Menu</MenuItem>
              <MenuItem value="greeting">Greeting</MenuItem>
              <MenuItem value="info">Info</MenuItem>
              <MenuItem value="help">Help</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleInitialize}
            disabled={initializeMutation.isPending}
          >
            Initialize Defaults
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Key</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Variables</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredMessages?.map((message: any) => (
              <TableRow key={message.id}>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {message.message_key}
                  </Typography>
                </TableCell>
                <TableCell>{message.message_name}</TableCell>
                <TableCell>
                  <Chip
                    label={message.category}
                    color={getCategoryColor(message.category)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary">
                    {message.variables || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={message.is_active ? 'Active' : 'Inactive'}
                    color={message.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleEdit(message)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit Dialog */}
      <Dialog
        open={openDialog}
        onClose={() => {
          setOpenDialog(false)
          setEditingMessage(null)
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Message: {editingMessage?.message_name}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <TextField
              label="Message Name"
              fullWidth
              value={editingMessage?.message_name || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, message_name: e.target.value })
              }
            />
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={editingMessage?.category || 'menu'}
                label="Category"
                onChange={(e) =>
                  setEditingMessage({ ...editingMessage, category: e.target.value })
                }
              >
                <MenuItem value="menu">Menu</MenuItem>
                <MenuItem value="greeting">Greeting</MenuItem>
                <MenuItem value="info">Info</MenuItem>
                <MenuItem value="help">Help</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Description"
              fullWidth
              value={editingMessage?.description || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, description: e.target.value })
              }
            />
            <TextField
              label="Variables (comma-separated)"
              fullWidth
              placeholder="version,time,user_id,handle"
              value={editingMessage?.variables || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, variables: e.target.value })
              }
            />
            <TextField
              label="Content"
              fullWidth
              multiline
              rows={12}
              value={editingMessage?.content || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, content: e.target.value })
              }
              sx={{ fontFamily: 'monospace' }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={editingMessage?.is_active || false}
                  onChange={(e) =>
                    setEditingMessage({ ...editingMessage, is_active: e.target.checked })
                  }
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setOpenDialog(false)
            setEditingMessage(null)
          }}>
            Cancel
          </Button>
          <Button
            onClick={handleUpdate}
            variant="contained"
            disabled={updateMutation.isPending}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
