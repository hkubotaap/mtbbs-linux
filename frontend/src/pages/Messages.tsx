import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
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
  Tooltip,
  Alert,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material'
import { adminAPI } from '../api/client'

export default function Messages() {
  const { t } = useTranslation()
  const [openDialog, setOpenDialog] = useState(false)
  const [openPreview, setOpenPreview] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editingMessage, setEditingMessage] = useState<any>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [previewVariables, setPreviewVariables] = useState<{ [key: string]: string }>({})

  const queryClient = useQueryClient()

  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages'],
    queryFn: async () => {
      const response = await adminAPI.getMessages()
      return response.data
    },
    refetchInterval: 10000,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => adminAPI.createMessage(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      handleClose()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: any) => adminAPI.updateMessage(data.message_key, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      handleClose()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (messageKey: string) => adminAPI.deleteMessage(messageKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  const initializeMutation = useMutation({
    mutationFn: () => adminAPI.initializeMessages(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  const handleCreate = () => {
    setEditMode(false)
    setEditingMessage({
      message_key: '',
      message_name: '',
      category: 'menu',
      content: '',
      description: '',
      variables: '',
      is_active: true,
    })
    setOpenDialog(true)
  }

  const handleEdit = (message: any) => {
    setEditMode(true)
    setEditingMessage({ ...message })
    setOpenDialog(true)
  }

  const handleSave = () => {
    if (editMode) {
      updateMutation.mutate(editingMessage)
    } else {
      createMutation.mutate(editingMessage)
    }
  }

  const handleDelete = (messageKey: string) => {
    if (window.confirm(t('messages.deleteConfirm'))) {
      deleteMutation.mutate(messageKey)
    }
  }

  const handleInitialize = () => {
    if (window.confirm(t('messages.initializeConfirm'))) {
      initializeMutation.mutate()
    }
  }

  const handleClose = () => {
    setOpenDialog(false)
    setEditMode(false)
    setEditingMessage(null)
  }

  const handlePreview = (message: any) => {
    setEditingMessage(message)
    // Initialize preview variables with example values
    const vars = message.variables ? message.variables.split(',').map((v: string) => v.trim()) : []
    const previewVars: { [key: string]: string } = {}
    vars.forEach((v: string) => {
      switch (v) {
        case 'version':
          previewVars[v] = '4.0.0'
          break
        case 'time':
          previewVars[v] = new Date().toLocaleString()
          break
        case 'user_id':
          previewVars[v] = 'sysop'
          break
        case 'handle':
          previewVars[v] = 'System Operator'
          break
        case 'board_name':
          previewVars[v] = 'Info Board'
          break
        default:
          previewVars[v] = `{${v}}`
      }
    })
    setPreviewVariables(previewVars)
    setOpenPreview(true)
  }

  const renderPreview = () => {
    if (!editingMessage) return ''
    let preview = editingMessage.content
    Object.keys(previewVariables).forEach((key) => {
      const regex = new RegExp(`\\{${key}\\}`, 'g')
      preview = preview.replace(regex, previewVariables[key])
    })
    return preview
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
        <Typography variant="h4">{t('messages.title')}</Typography>
        <Box display="flex" gap={2}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t('messages.category')}</InputLabel>
            <Select
              value={categoryFilter}
              label={t('messages.category')}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="all">{t('messages.allCategories')}</MenuItem>
              <MenuItem value="menu">{t('messages.categoryMenu')}</MenuItem>
              <MenuItem value="greeting">{t('messages.categoryGreeting')}</MenuItem>
              <MenuItem value="info">{t('messages.categoryInfo')}</MenuItem>
              <MenuItem value="help">{t('messages.categoryHelp')}</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleInitialize}
            disabled={initializeMutation.isPending}
          >
            {t('messages.initializeDefaults')}
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            {t('messages.addMessage')}
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('messages.messageKey')}</TableCell>
              <TableCell>{t('messages.messageName')}</TableCell>
              <TableCell>{t('messages.category')}</TableCell>
              <TableCell>{t('messages.variables')}</TableCell>
              <TableCell>{t('messages.status')}</TableCell>
              <TableCell>{t('common.actions')}</TableCell>
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
                    label={message.is_active ? t('messages.active') : 'Inactive'}
                    color={message.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title={t('messages.preview')}>
                    <IconButton
                      size="small"
                      onClick={() => handlePreview(message)}
                      color="info"
                    >
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('common.edit')}>
                    <IconButton
                      size="small"
                      onClick={() => handleEdit(message)}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('common.delete')}>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(message.message_key)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog
        open={openDialog}
        onClose={handleClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editMode ? t('messages.editMessage') : t('messages.createMessage')}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <TextField
              label={t('messages.messageKey')}
              fullWidth
              required
              disabled={editMode}
              value={editingMessage?.message_key || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, message_key: e.target.value })
              }
              helperText={editMode ? t('messages.messageKeyCannotChange') : t('messages.messageKeyHelper')}
            />
            <TextField
              label={t('messages.messageName')}
              fullWidth
              required
              value={editingMessage?.message_name || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, message_name: e.target.value })
              }
            />
            <FormControl fullWidth>
              <InputLabel>{t('messages.category')}</InputLabel>
              <Select
                value={editingMessage?.category || 'menu'}
                label={t('messages.category')}
                onChange={(e) =>
                  setEditingMessage({ ...editingMessage, category: e.target.value })
                }
              >
                <MenuItem value="menu">{t('messages.categoryMenu')}</MenuItem>
                <MenuItem value="greeting">{t('messages.categoryGreeting')}</MenuItem>
                <MenuItem value="info">{t('messages.categoryInfo')}</MenuItem>
                <MenuItem value="help">{t('messages.categoryHelp')}</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label={t('messages.description')}
              fullWidth
              value={editingMessage?.description || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, description: e.target.value })
              }
            />
            <TextField
              label={t('messages.variables')}
              fullWidth
              placeholder="version,time,user_id,handle"
              value={editingMessage?.variables || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, variables: e.target.value })
              }
              helperText={t('messages.variablesHelper')}
            />
            <TextField
              label={t('messages.content')}
              fullWidth
              required
              multiline
              rows={12}
              value={editingMessage?.content || ''}
              onChange={(e) =>
                setEditingMessage({ ...editingMessage, content: e.target.value })
              }
              sx={{ fontFamily: 'monospace' }}
              helperText={t('messages.contentHelper')}
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
              label={t('messages.active')}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>{t('common.cancel')}</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        open={openPreview}
        onClose={() => setOpenPreview(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t('messages.preview')}: {editingMessage?.message_name}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            <Alert severity="info">
              {t('messages.variables')}: {editingMessage?.variables || 'なし'}
            </Alert>
            {editingMessage?.variables && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  変数値（プレビュー用）:
                </Typography>
                {editingMessage.variables.split(',').map((v: string) => {
                  const varName = v.trim()
                  return (
                    <TextField
                      key={varName}
                      label={varName}
                      size="small"
                      fullWidth
                      margin="dense"
                      value={previewVariables[varName] || ''}
                      onChange={(e) =>
                        setPreviewVariables({
                          ...previewVariables,
                          [varName]: e.target.value,
                        })
                      }
                    />
                  )
                })}
              </Box>
            )}
            <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
              <Typography variant="subtitle2" gutterBottom>
                プレビュー:
              </Typography>
              <Box
                component="pre"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  m: 0,
                }}
              >
                {renderPreview()}
              </Box>
            </Paper>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPreview(false)}>{t('common.cancel')}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
