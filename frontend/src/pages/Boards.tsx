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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  IconButton,
  Chip,
} from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { adminAPI } from '../api/client'

export default function Boards() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [currentBoard, setCurrentBoard] = useState<any>(null)
  const [newBoard, setNewBoard] = useState({
    board_id: 0,
    name: '',
    description: '',
    read_level: 0,
    write_level: 1,
  })

  const queryClient = useQueryClient()

  const { data: boards, isLoading } = useQuery({
    queryKey: ['boards'],
    queryFn: async () => {
      const response = await adminAPI.getBoards()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => adminAPI.createBoard(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
      setOpenDialog(false)
      setNewBoard({ board_id: 0, name: '', description: '', read_level: 0, write_level: 1 })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (boardId: number) => adminAPI.deleteBoard(boardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
    },
  })

  const handleCreate = () => {
    createMutation.mutate(newBoard)
  }

  const handleEdit = (board: any) => {
    setEditMode(true)
    setCurrentBoard(board)
    setNewBoard({
      board_id: board.board_id,
      name: board.name,
      description: board.description || '',
      read_level: board.read_level,
      write_level: board.write_level,
    })
    setOpenDialog(true)
  }

  const handleDelete = (boardId: number) => {
    if (window.confirm('本当にこのボードを削除しますか？')) {
      deleteMutation.mutate(boardId)
    }
  }

  const handleClose = () => {
    setOpenDialog(false)
    setEditMode(false)
    setCurrentBoard(null)
    setNewBoard({ board_id: 0, name: '', description: '', read_level: 0, write_level: 1 })
  }

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
        <Typography variant="h4">Message Boards</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Add Board
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Board ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Read Level</TableCell>
              <TableCell>Write Level</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {boards?.map((board: any) => (
              <TableRow key={board.board_id}>
                <TableCell>{board.board_id}</TableCell>
                <TableCell><strong>{board.name}</strong></TableCell>
                <TableCell>{board.description || '-'}</TableCell>
                <TableCell>
                  <Chip label={`Level ${board.read_level}+`} size="small" color="primary" />
                </TableCell>
                <TableCell>
                  <Chip label={`Level ${board.write_level}+`} size="small" color="secondary" />
                </TableCell>
                <TableCell>
                  {board.is_active ? (
                    <Chip label="Active" color="success" size="small" />
                  ) : (
                    <Chip label="Inactive" color="default" size="small" />
                  )}
                </TableCell>
                <TableCell>
                  <IconButton color="primary" size="small" onClick={() => handleEdit(board)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton color="error" size="small" onClick={() => handleDelete(board.board_id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>{editMode ? 'Edit Board' : 'Create New Board'}</DialogTitle>
        <DialogContent>
          <TextField
            label="Board ID"
            type="number"
            fullWidth
            margin="normal"
            value={newBoard.board_id}
            onChange={(e) => setNewBoard({ ...newBoard, board_id: parseInt(e.target.value) })}
            disabled={editMode}
            helperText={editMode ? "Board ID cannot be changed" : "Unique identifier for this board"}
          />
          <TextField
            label="Board Name"
            fullWidth
            margin="normal"
            value={newBoard.name}
            onChange={(e) => setNewBoard({ ...newBoard, name: e.target.value })}
            helperText="Display name for this board"
            required
          />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={4}
            margin="normal"
            value={newBoard.description}
            onChange={(e) => setNewBoard({ ...newBoard, description: e.target.value })}
            helperText="Detailed description of the board's purpose"
          />
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Access Control
            </Typography>
            <TextField
              label="Read Level"
              type="number"
              fullWidth
              margin="normal"
              value={newBoard.read_level}
              onChange={(e) => setNewBoard({ ...newBoard, read_level: parseInt(e.target.value) })}
              helperText="Minimum user level required to read messages (0-9)"
              inputProps={{ min: 0, max: 9 }}
            />
            <TextField
              label="Write Level"
              type="number"
              fullWidth
              margin="normal"
              value={newBoard.write_level}
              onChange={(e) => setNewBoard({ ...newBoard, write_level: parseInt(e.target.value) })}
              helperText="Minimum user level required to post messages (0-9)"
              inputProps={{ min: 0, max: 9 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained" color="primary">
            {editMode ? 'Update Board' : 'Create Board'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
