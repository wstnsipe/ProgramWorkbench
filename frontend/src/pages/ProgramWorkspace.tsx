import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import '../App.css'
import UploadTab from './UploadTab'
import BriefTab from './BriefTab'
import ModulesTab from './ModulesTab'
import DocumentsTab from './DocumentsTab'
import ExemplarsTab from './ExemplarsTab'
import KnowledgeTab from './KnowledgeTab'
import SufficiencyBanner from '../components/ui/SufficiencyBanner'
import EvidencePanel from '../components/ui/EvidencePanel'
import { useSufficiency } from '../hooks/useSufficiency'
import { useEvidence } from '../hooks/useEvidence'

const API = import.meta.env.VITE_API_BASE_URL

interface Program {
  id: number
  name: string
}

const TABS = ['Upload', 'Brief', 'Modules', 'Documents', 'Exemplars', 'Knowledge'] as const
type Tab = typeof TABS[number]

export default function ProgramWorkspace() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [program, setProgram] = useState<Program | null>(null)
  const [fetchError, setFetchError] = useState('')
  const [activeTab, setActiveTab] = useState<Tab>('Upload')
  const [panelOpen, setPanelOpen] = useState(false)
  const { result: sufficiency, loading: sufficiencyLoading, refresh: refreshSufficiency } = useSufficiency(id!)
  const { data: evidenceData, loading: evidenceLoading } = useEvidence(id!, activeTab.toLowerCase(), panelOpen)

  useEffect(() => {
    async function fetchProgram() {
      const res = await fetch(`${API}/programs/${id}`)
      if (res.status === 404) { setFetchError('Program not found'); return }
      if (!res.ok) { setFetchError('Failed to load program'); return }
      setProgram(await res.json())
    }
    fetchProgram()
  }, [id])

  if (fetchError) {
    return (
      <div className="ws">
        <div className="ws-error">
          <p className="error">{fetchError}</p>
          <button className="btn btn--secondary" onClick={() => navigate('/programs')}>
            ← Back to Programs
          </button>
        </div>
      </div>
    )
  }

  if (!program) {
    return (
      <div className="ws">
        <div className="ws-loading">Loading…</div>
      </div>
    )
  }

  return (
    <div className="ws">
      {/* Header */}
      <div className="ws-header">
        <div className="ws-header-inner">
          <button className="ws-back" onClick={() => navigate('/programs')}>
            ← Programs
          </button>
          <div className="ws-title-row">
            <h1 className="ws-name">{program.name}</h1>
            <span className="ws-id">ID #{program.id}</span>
          </div>
        </div>

        {/* Tab bar — sits at the bottom of the header box */}
        <nav className="ws-tabs" aria-label="Program sections">
          {TABS.map(tab => (
            <button
              key={tab}
              className={`ws-tab${activeTab === tab ? ' ws-tab--active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
          <button
            className={`ws-tab ws-tab--panel${panelOpen ? ' ws-tab--active' : ''}`}
            onClick={() => setPanelOpen(o => !o)}
            title="Toggle evidence panel"
          >
            Evidence
          </button>
        </nav>
      </div>

      {/* Sufficiency banner */}
      <div className="ws-suf-strip">
        <SufficiencyBanner
          result={sufficiency}
          loading={sufficiencyLoading}
          onRefresh={refreshSufficiency}
        />
      </div>

      {/* Content */}
      <div className={`ws-body${panelOpen ? ' ws-body--with-panel' : ''}`}>
        <div className="ws-content">
          {activeTab === 'Upload'    && <UploadTab    programId={id!} />}
          {activeTab === 'Brief'     && <BriefTab     programId={id!} />}
          {activeTab === 'Modules'   && <ModulesTab   programId={id!} />}
          {activeTab === 'Documents' && <DocumentsTab programId={id!} />}
          {activeTab === 'Exemplars' && <ExemplarsTab programId={id!} />}
          {activeTab === 'Knowledge' && <KnowledgeTab programId={id!} />}
        </div>
        {panelOpen && (
          <EvidencePanel
            onClose={() => setPanelOpen(false)}
            loading={evidenceLoading}
            hasDocs={evidenceData?.has_docs ?? false}
            chunks={evidenceData?.chunks ?? []}
            warnings={sufficiency?.rule_violations ?? []}
            context={activeTab}
          />
        )}
      </div>
    </div>
  )
}
