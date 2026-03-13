import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProgramsPage from './pages/ProgramsPage'
import ProgramWorkspace from './pages/ProgramWorkspace'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/programs" element={<ProgramsPage />} />
        <Route path="/programs/:id" element={<ProgramWorkspace />} />
        <Route path="*" element={<Navigate to="/programs" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
