import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { DocumentViewer } from './pages/DocumentViewer'
import { SummaryPage } from './pages/SummaryPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/document/:id" element={<DocumentViewer />} />
        <Route path="/summary/:id" element={<SummaryPage />} />
      </Routes>
    </Layout>
  )
}

export default App
