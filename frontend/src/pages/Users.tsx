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
  FormControlLabel,
  Checkbox,
} from '@mui/material'
import { Delete as DeleteIcon, Add as AddIcon, Edit as EditIcon } from '@mui/icons-material'
import { adminAPI } from '../api/client'

export default function Users() {
  const [openDialog, setOpenDialog] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const [newUser, setNewUser] = useState({
    user_id: '',
    password: '',
    handle_name: '',
    email: '',
    level: 1,
    is_active: true,
    must_change_password_on_next_login: false,
  })

  const queryClient = useQueryClient()

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await adminAPI.getUsers()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => adminAPI.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setOpenDialog(false)
      setNewUser({ user_id: '', password: '', handle_name: '', email: '', level: 1, is_active: true, must_change_password_on_next_login: false })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) =>
      adminAPI.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setOpenDialog(false)
      setEditMode(false)
      setCurrentUser(null)
      setNewUser({ user_id: '', password: '', handle_name: '', email: '', level: 1, is_active: true, must_change_password_on_next_login: false })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: string) => adminAPI.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const handleCreate = () => {
    createMutation.mutate(newUser)
  }

  const handleUpdate = () => {
    const updateData: any = {
      handle_name: newUser.handle_name,
      email: newUser.email,
      level: newUser.level,
      is_active: newUser.is_active,
      must_change_password_on_next_login: newUser.must_change_password_on_next_login,
    }
    if (newUser.password) {
      updateData.password = newUser.password
    }
    updateMutation.mutate({
      userId: currentUser.user_id,
      data: updateData,
    })
  }

  const handleEdit = (user: any) => {
    setEditMode(true)
    setCurrentUser(user)
    setNewUser({
      user_id: user.user_id,
      password: '',
      handle_name: user.handle_name,
      email: user.email || '',
      level: user.level,
      is_active: user.is_active ?? true,
      must_change_password_on_next_login: user.must_change_password_on_next_login ?? false,
    })
    setOpenDialog(true)
  }

  const handleClose = () => {
    setOpenDialog(false)
    setEditMode(false)
    setCurrentUser(null)
    setNewUser({ user_id: '', password: '', handle_name: '', email: '', level: 1, is_active: true, must_change_password_on_next_login: false })
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
        <Typography variant="h4">Users</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Add User
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User ID</TableCell>
              <TableCell>Handle Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users?.map((user: any) => (
              <TableRow key={user.user_id}>
                <TableCell>{user.user_id}</TableCell>
                <TableCell>{user.handle_name}</TableCell>
                <TableCell>{user.email || '-'}</TableCell>
                <TableCell>{user.level}</TableCell>
                <TableCell>
                  {user.last_login
                    ? new Date(user.last_login).toLocaleString()
                    : 'Never'}
                </TableCell>
                <TableCell>
                  <IconButton color="primary" size="small" onClick={() => handleEdit(user)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    color="error"
                    size="small"
                    onClick={() => deleteMutation.mutate(user.user_id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{editMode ? 'Edit User' : 'Create New User'}</DialogTitle>
        <DialogContent>
          <TextField
            label="User ID"
            fullWidth
            margin="normal"
            value={newUser.user_id}
            onChange={(e) => setNewUser({ ...newUser, user_id: e.target.value })}
            disabled={editMode}
            helperText={editMode ? "User ID cannot be changed" : "Unique identifier for this user"}
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            helperText={editMode ? "Leave empty to keep current password" : "User password"}
            required={!editMode}
          />
          <TextField
            label="Handle Name"
            fullWidth
            margin="normal"
            value={newUser.handle_name}
            onChange={(e) => setNewUser({ ...newUser, handle_name: e.target.value })}
            required
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            margin="normal"
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
          />
          <TextField
            label="Level"
            type="number"
            fullWidth
            margin="normal"
            value={newUser.level}
            onChange={(e) => setNewUser({ ...newUser, level: parseInt(e.target.value) })}
            inputProps={{ min: 0, max: 9 }}
            helperText="User level (0-9)"
          />
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={newUser.is_active}
                  onChange={(e) => setNewUser({ ...newUser, is_active: e.target.checked })}
                />
              }
              label="Active (uncheck to temporarily disable user)"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={newUser.must_change_password_on_next_login}
                  onChange={(e) => setNewUser({ ...newUser, must_change_password_on_next_login: e.target.checked })}
                />
              }
              label="Require password change on next login"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            onClick={editMode ? handleUpdate : handleCreate}
            variant="contained"
            color="primary"
          >
            {editMode ? 'Update User' : 'Create User'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
