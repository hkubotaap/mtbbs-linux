import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Users from './pages/Users'
import Boards from './pages/Boards'
import Messages from './pages/Messages'
import Connections from './pages/Connections'
import Settings from './pages/Settings'

function App() {
  return (
    <Layout>
      <Box sx={{ p: 3 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route path="/boards" element={<Boards />} />
          <Route path="/messages" element={<Messages />} />
          <Route path="/connections" element={<Connections />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Box>
    </Layout>
  )
}

export default App
