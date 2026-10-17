import React, { useEffect, useState } from 'react';
import type {
  CompoundResponse,
  ResearchDossier,
  ResearchJobStatus,
  ResearchLifecycleStatus,
} from '../../types/api';
import {
  approveResearchCandidate,
  getResearchCandidates,
  getResearchJob,
  refreshResearchCandidate,
  rejectResearchCandidate,
  submitResearchJob,
  validateResearchCandidate,
} from '../../api/client';
import { AlertBox } from '../../components/AlertBox';
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  ExternalLink,
  FlaskConical,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  XCircle,
} from 'lucide-react';

interface Props {
  onLoadIntoScenario: (compound: CompoundResponse) => void;
  onRefreshLibrary: () => void;
}

const SAMPLE_SUBSTANCES = [
  'Primaquine',
  'Menadione',
  'Hydrogen peroxide',
  'Ferrous iron',
  'Ferric chloride',
  'Doxorubicin',
  'Ascorbic acid',
];

export const CompoundResearchWorkspace: React.FC<Props> = ({
  onLoadIntoScenario,
  onRefreshLibrary,
}) => {
  const [substanceInput, setSubstanceInput] = useState('');
  const [objectiveInput, setObjectiveInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active Job & Polling
  const [activeJob, setActiveJob] = useState<ResearchJobStatus | null>(null);

  // Dossiers State
  const [dossiers, setDossiers] = useState<ResearchDossier[]>([]);
  const [selectedDossier, setSelectedDossier] = useState<ResearchDossier | null>(null);
  const [dossiersLoading, setDossiersLoading] = useState(false);

  // Section Accordion State
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    identity: true,
    sources: true,
    findings: true,
    mechanism: true,
    validation: true,
    audit: false,
  });

  const toggleSection = (key: string) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Fetch all existing dossiers on mount
  const fetchDossiers = async () => {
    setDossiersLoading(true);
    try {
      const list = await getResearchCandidates();
      setDossiers(list);
      if (list.length > 0 && !selectedDossier) {
        setSelectedDossier(list[0]);
      }
    } catch {
      // Ignored if empty or backend restarting
    } finally {
      setDossiersLoading(false);
    }
  };

  useEffect(() => {
    fetchDossiers();
  }, []);

  // Poll for background research job completion
  useEffect(() => {
    if (!activeJob || activeJob.stage === 'COMPLETED' || activeJob.stage === 'FAILED') {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const job = await getResearchJob(activeJob.job_id);
        setActiveJob(job);

        if (job.stage === 'COMPLETED') {
          setLoading(false);
          await fetchDossiers();
          if (job.candidate_id) {
            const list = await getResearchCandidates();
            const found = list.find((d) => d.candidate_id === job.candidate_id);
            if (found) {
              setSelectedDossier(found);
            }
          }
        } else if (job.stage === 'FAILED') {
          setLoading(false);
          setError(job.error || 'Research pipeline failed.');
        }
      } catch (err: any) {
        // Polling error
      }
    }, 1200);

    return () => clearInterval(timer);
  }, [activeJob]);

  // Submit new substance research
  const handleStartResearch = async (substanceName?: string) => {
    const target = (substanceName || substanceInput).trim();
    if (!target) {
      setError('Please enter a chemical compound or element name.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const job = await submitResearchJob({
        substance_name: target,
        research_objective: objectiveInput.trim() || undefined,
        force_refresh: true,
      });
      setActiveJob(job);
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to submit substance research.');
      setLoading(false);
    }
  };

  // Lifecycle actions
  const handleApprove = async () => {
    if (!selectedDossier) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await approveResearchCandidate(
        selectedDossier.candidate_id,
        'researcher',
        'Approved candidate from research workstation interface.'
      );
      setSelectedDossier(updated);
      await fetchDossiers();
      onRefreshLibrary();
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to approve candidate.');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!selectedDossier) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await validateResearchCandidate(selectedDossier.candidate_id);
      setSelectedDossier(updated);
      await fetchDossiers();
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to revalidate candidate.');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedDossier) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await rejectResearchCandidate(
        selectedDossier.candidate_id,
        'researcher',
        'Marked as rejected by researcher.'
      );
      setSelectedDossier(updated);
      await fetchDossiers();
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to reject candidate.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!selectedDossier) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await refreshResearchCandidate(selectedDossier.candidate_id);
      setSelectedDossier(updated);
      await fetchDossiers();
      onRefreshLibrary();
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to refresh candidate research.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadInPlayground = () => {
    if (!selectedDossier || selectedDossier.status !== 'SIMULATION_READY') return;
    const compatibleMapping = selectedDossier.mechanism_mappings.find((m) => m.is_compatible);
    if (!compatibleMapping) return;

    const defaults: Record<string, any> = {};
    const ranges: Record<string, [number, number]> = {};
    for (const p of compatibleMapping.parameters) {
      defaults[p.name] = p.value;
      ranges[p.name] = [p.min_bound, p.max_bound];
    }
    if (compatibleMapping.target_enzyme) defaults.target_enzyme = compatibleMapping.target_enzyme;
    if (compatibleMapping.inhibition_type) defaults.inhibition_type = compatibleMapping.inhibition_type;

    const pseudoCompound: CompoundResponse = {
      compound_id: selectedDossier.candidate_id,
      name: selectedDossier.chemical_identity.preferred_name,
      smiles: selectedDossier.chemical_identity.smiles,
      inchikey: selectedDossier.chemical_identity.inchikey,
      mechanism_type: compatibleMapping.mechanism_type,
      default_parameters: defaults,
      parameter_ranges: ranges,
      exposure_units: 'mM',
      evidence_level: 'ESTIMATED',
      is_unverified: false,
      provenance: `Milestone 7 LLM Candidate: ${selectedDossier.candidate_id}`,
      confidence_score: compatibleMapping.confidence,
    };

    onLoadIntoScenario(pseudoCompound);
  };

  const getStatusBadge = (status: ResearchLifecycleStatus) => {
    switch (status) {
      case 'SIMULATION_READY':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-bold bg-[#EDF3EE] text-[#284431] border border-[#BCD0C1]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#3E5C46]" />
            SIMULATION_READY
          </span>
        );
      case 'CANDIDATE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-bold bg-[#FDF4E7] text-[#8E5A1E] border border-[#ECD1A4]">
            <Clock className="w-3.5 h-3.5 text-[#B3541E]" />
            CANDIDATE (PENDING APPROVAL)
          </span>
        );
      case 'RESEARCHED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-bold bg-[#EBF1F9] text-[#1E3A5F] border border-[#B0C5E5]">
            <BookOpen className="w-3.5 h-3.5 text-[#2B4C7E]" />
            RESEARCHED
          </span>
        );
      case 'NEEDS_RESEARCH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-bold bg-[#F5F2EB] text-[#555C54] border border-[#D8D1C2]">
            <AlertTriangle className="w-3.5 h-3.5 text-[#767D75]" />
            NEEDS_RESEARCH
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-bold bg-[#F9ECEB] text-[#7D221C] border border-[#DCB0AC]">
            <XCircle className="w-3.5 h-3.5 text-[#9B332B]" />
            REJECTED
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Masthead & Telemetry */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#D8D1C2] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
              PIPELINE // MODULE 06
            </span>
            <h1 className="font-editorial text-2xl font-bold text-[#181B18] tracking-tight flex items-center gap-2">
              <span>LLM Compound Intelligence & Research</span>
              <Sparkles className="w-4 h-4 text-[#9B332B]" />
            </h1>
          </div>
          <p className="text-xs text-[#666E65] mt-1 font-sans">
            Authoritative identity resolution, literature retrieval, evidence grading, and 10-gate candidate registration into V-Blood.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-[#181B18] bg-[#FAF7F2] px-2.5 py-1 border border-[#B5AC99]">
            {dossiers.length} Research Dossiers
          </span>
          <button
            onClick={fetchDossiers}
            disabled={dossiersLoading}
            className="p-1.5 border border-[#B5AC99] bg-[#FFFFFF] text-[#484E48] hover:text-[#181B18] hover:bg-[#FAF7F2] disabled:opacity-50 transition-colors shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]"
            title="Refresh candidate library"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${dossiersLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <AlertBox type="error" title="Research Pipeline Notice">
          {error}
        </AlertBox>
      )}

      {/* Section 1: Chemical Investigation Bench */}
      <div className="border border-[#D8D1C2] bg-[#FFFFFF] shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)] p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-[#9B332B]" />
            <h2 className="font-editorial text-base font-bold text-[#181B18]">
              Substance Research Submission
            </h2>
          </div>
          <span className="font-mono text-[10px] uppercase text-[#767D75] tracking-wider">
            HUMAN ERYTHROCYTE SCOPE
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 space-y-1.5">
            <label className="block text-xs font-mono font-semibold text-[#181B18]">
              CHEMICAL SUBSTANCE OR COMMON NAME *
            </label>
            <div className="relative">
              <input
                type="text"
                value={substanceInput}
                onChange={(e) => setSubstanceInput(e.target.value)}
                placeholder="e.g. Primaquine, Menadione, Hydrogen peroxide, Ferrous iron..."
                disabled={loading}
                className="w-full px-3 py-2 text-xs font-mono bg-[#FCFAF6] border border-[#B5AC99] text-[#181B18] focus:outline-none focus:border-[#9B332B] focus:ring-1 focus:ring-[#9B332B]"
              />
              <Search className="w-3.5 h-3.5 text-[#767D75] absolute right-3 top-2.5" />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-semibold text-[#181B18]">
              RESEARCH OBJECTIVE (OPTIONAL)
            </label>
            <input
              type="text"
              value={objectiveInput}
              onChange={(e) => setObjectiveInput(e.target.value)}
              placeholder="e.g. Investigate G6PD oxidative sensitivity"
              disabled={loading}
              className="w-full px-3 py-2 text-xs bg-[#FCFAF6] border border-[#B5AC99] text-[#181B18] focus:outline-none focus:border-[#9B332B]"
            />
          </div>
        </div>

        {/* Suggestion pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs">
          <span className="font-mono text-[10px] text-[#767D75] mr-1">EXAMPLES:</span>
          {SAMPLE_SUBSTANCES.map((sub) => (
            <button
              key={sub}
              type="button"
              disabled={loading}
              onClick={() => {
                setSubstanceInput(sub);
                handleStartResearch(sub);
              }}
              className="px-2 py-0.5 font-mono text-[11px] bg-[#FAF7F2] border border-[#D8D1C2] hover:border-[#9B332B] hover:text-[#9B332B] text-[#484E48] transition-colors"
            >
              {sub}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-[#EDE8DE]">
          <div className="text-[11px] text-[#666E65] flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[#2D5A4C]" />
            <span>Strict 10-gate scientific barrier: unvalidated claims are never registered as simulation-ready.</span>
          </div>

          <button
            type="button"
            onClick={() => handleStartResearch()}
            disabled={loading || !substanceInput.trim()}
            className="px-4 py-2 bg-[#9B332B] text-white text-xs font-mono font-semibold hover:bg-[#802820] disabled:opacity-50 transition-colors shadow-[2px_2px_0px_0px_rgba(24,27,24,0.15)] flex items-center gap-2"
          >
            {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>{loading ? 'Executing Research Pipeline...' : 'Investigate Substance'}</span>
          </button>
        </div>
      </div>

      {/* Real-time Job Progress Indicator */}
      {activeJob && activeJob.stage !== 'COMPLETED' && (
        <div className="border border-[#B5AC99] bg-[#FAF7F2] p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-none bg-[#9B332B] animate-pulse" />
              <span className="font-mono text-xs font-semibold text-[#181B18]">
                JOB {activeJob.job_id} // STAGE: {activeJob.stage}
              </span>
            </div>
            <span className="font-mono text-xs font-bold text-[#9B332B]">
              {activeJob.progress_pct}%
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-[#E8E2D5] h-2 border border-[#D8D1C2]">
            <div
              className="bg-[#9B332B] h-full transition-all duration-300"
              style={{ width: `${activeJob.progress_pct}%` }}
            />
          </div>

          <p className="text-xs font-mono text-[#484E48]">
            {activeJob.message}
          </p>
        </div>
      )}

      {/* Main Workspace Layout: Dossier Explorer & Deep Plate */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left: Saved Dossiers Ledger */}
        <div className="lg:col-span-1 space-y-3">
          <div className="flex items-center justify-between pb-1 border-b border-[#D8D1C2]">
            <span className="font-mono text-[10px] uppercase tracking-wider text-[#767D75]">
              RESEARCH REGISTRY ({dossiers.length})
            </span>
          </div>

          {dossiers.length === 0 ? (
            <div className="border border-dashed border-[#D8D1C2] p-4 text-center text-xs text-[#767D75]">
              No compounds researched yet. Submit a substance above to begin.
            </div>
          ) : (
            <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
              {dossiers.map((d) => {
                const isSelected = selectedDossier?.candidate_id === d.candidate_id;
                return (
                  <button
                    key={d.candidate_id}
                    onClick={() => setSelectedDossier(d)}
                    className={`w-full text-left p-2.5 border transition-all ${
                      isSelected
                        ? 'bg-[#FFFFFF] border-[#9B332B] shadow-[2px_2px_0px_0px_rgba(155,51,43,0.15)] relative before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-[#9B332B]'
                        : 'bg-[#FCFAF6] border-[#D8D1C2] hover:bg-[#FFFFFF] hover:border-[#B5AC99]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#181B18] truncate">
                        {d.chemical_identity.preferred_name}
                      </span>
                      <span className="font-mono text-[9px] uppercase px-1 py-0.5 border border-[#D8D1C2] bg-[#FAF7F2] text-[#484E48]">
                        REV {d.revision}
                      </span>
                    </div>

                    <div className="mt-1 flex items-center justify-between text-[10px] font-mono text-[#767D75]">
                      <span>{d.candidate_id}</span>
                      <span
                        className={`font-semibold ${
                          d.status === 'SIMULATION_READY'
                            ? 'text-[#284431]'
                            : d.status === 'CANDIDATE'
                            ? 'text-[#8E5A1E]'
                            : d.status === 'REJECTED'
                            ? 'text-[#7D221C]'
                            : 'text-[#484E48]'
                        }`}
                      >
                        {d.status}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Selected Research Dossier Plate */}
        <div className="lg:col-span-3 space-y-6">
          {!selectedDossier ? (
            <div className="border border-[#D8D1C2] bg-[#FFFFFF] p-12 text-center text-[#767D75] space-y-2">
              <BookOpen className="w-8 h-8 mx-auto text-[#B5AC99]" />
              <p className="font-editorial text-lg font-bold text-[#181B18]">No Dossier Selected</p>
              <p className="text-xs max-w-md mx-auto">
                Submit an unsupported chemical substance to execute automated identity resolution, literature retrieval, and 10-gate validation.
              </p>
            </div>
          ) : (
            <div className="border border-[#D8D1C2] bg-[#FFFFFF] shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)] p-6 space-y-6">
              {/* Dossier Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-[#EDE8DE] pb-5">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="font-editorial text-2xl font-bold text-[#181B18]">
                      {selectedDossier.chemical_identity.preferred_name}
                    </h2>
                    <span className="px-2 py-0.5 text-[10px] font-mono border border-[#B5AC99] bg-[#FAF7F2] text-[#484E48] font-bold">
                      {selectedDossier.chemical_identity.entity_type}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-[#767D75] mt-1 flex flex-wrap items-center gap-3">
                    <span>ID: <strong>{selectedDossier.candidate_id}</strong></span>
                    <span>•</span>
                    <span>Formula: <strong>{selectedDossier.chemical_identity.molecular_formula || 'N/A'}</strong></span>
                    <span>•</span>
                    <span>MW: <strong>{selectedDossier.chemical_identity.molecular_weight || 'N/A'} g/mol</strong></span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2">
                  {getStatusBadge(selectedDossier.status)}
                  <span className="text-[10px] font-mono text-[#767D75]">
                    Updated: {new Date(selectedDossier.updated_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>

              {/* Action Controls Bar */}
              <div className="bg-[#FAF7F2] border border-[#D8D1C2] p-3 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  {selectedDossier.status === 'SIMULATION_READY' ? (
                    <button
                      onClick={handleLoadInPlayground}
                      className="px-3.5 py-1.5 bg-[#2D5A4C] text-white text-xs font-mono font-semibold hover:bg-[#23473C] transition-colors flex items-center gap-1.5 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.1)]"
                    >
                      <ArrowRight className="w-3.5 h-3.5" />
                      <span>Load in Scenario Builder</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleApprove}
                      disabled={!selectedDossier.validation_summary.simulation_eligible || loading}
                      className="px-3.5 py-1.5 bg-[#9B332B] text-white text-xs font-mono font-semibold hover:bg-[#802820] disabled:opacity-50 transition-colors flex items-center gap-1.5 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.1)]"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve for Simulation</span>
                    </button>
                  )}

                  <button
                    onClick={handleValidate}
                    disabled={loading}
                    className="px-3 py-1.5 bg-[#FFFFFF] border border-[#B5AC99] text-[#181B18] text-xs font-mono hover:bg-[#FAF7F2] transition-colors"
                  >
                    Re-Validate Gates
                  </button>

                  {selectedDossier.status !== 'REJECTED' && (
                    <button
                      onClick={handleReject}
                      disabled={loading}
                      className="px-3 py-1.5 bg-[#FFFFFF] border border-[#DCB0AC] text-[#7D221C] text-xs font-mono hover:bg-[#F9ECEB] transition-colors"
                    >
                      Reject Candidate
                    </button>
                  )}
                </div>

                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="px-2.5 py-1.5 text-xs font-mono text-[#484E48] hover:text-[#181B18] flex items-center gap-1 hover:bg-[#EDE8DE] transition-colors"
                  title="Re-query literature and re-extract evidence"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  <span>Refresh Research</span>
                </button>
              </div>

              {/* Panel 1: Chemical Identity & External Structure */}
              <div className="border border-[#D8D1C2]">
                <button
                  onClick={() => toggleSection('identity')}
                  className="w-full px-4 py-2.5 bg-[#FAF7F2] text-left flex items-center justify-between font-mono text-xs font-bold text-[#181B18] border-b border-[#D8D1C2]"
                >
                  <span>1. CHEMICAL IDENTITY & IDENTIFIERS</span>
                  {openSections.identity ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {openSections.identity && (
                  <div className="p-4 bg-[#FFFFFF] space-y-3 text-xs">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono">
                      <div className="p-2 border border-[#EDE8DE] bg-[#FCFAF6]">
                        <span className="text-[10px] text-[#767D75] block uppercase">SMILES STRUCTURE:</span>
                        <code className="text-[11px] text-[#181B18] break-all select-all font-bold">
                          {selectedDossier.chemical_identity.smiles}
                        </code>
                      </div>
                      <div className="p-2 border border-[#EDE8DE] bg-[#FCFAF6]">
                        <span className="text-[10px] text-[#767D75] block uppercase">IUPAC INCHIKEY:</span>
                        <code className="text-[11px] text-[#181B18] break-all select-all font-bold">
                          {selectedDossier.chemical_identity.inchikey}
                        </code>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs font-mono pt-1 text-[#484E48]">
                      <span>Source: <strong>{selectedDossier.chemical_identity.source}</strong></span>
                      {selectedDossier.chemical_identity.pubchem_cid && (
                        <span>PubChem CID: <strong>{selectedDossier.chemical_identity.pubchem_cid}</strong></span>
                      )}
                      <span>Charge: <strong>{selectedDossier.chemical_identity.charge}</strong></span>
                    </div>

                    {selectedDossier.chemical_identity.common_names.length > 0 && (
                      <div className="text-[11px] text-[#666E65]">
                        <span className="font-mono text-[10px] text-[#767D75] uppercase mr-1">SYNONYMS:</span>
                        {selectedDossier.chemical_identity.common_names.slice(0, 6).join('; ')}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Panel 2: Scientific Literature Registry */}
              <div className="border border-[#D8D1C2]">
                <button
                  onClick={() => toggleSection('sources')}
                  className="w-full px-4 py-2.5 bg-[#FAF7F2] text-left flex items-center justify-between font-mono text-xs font-bold text-[#181B18] border-b border-[#D8D1C2]"
                >
                  <span>2. RETRIEVED SCIENTIFIC LITERATURE ({selectedDossier.sources.length})</span>
                  {openSections.sources ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {openSections.sources && (
                  <div className="p-4 bg-[#FFFFFF] space-y-3">
                    {selectedDossier.sources.length === 0 ? (
                      <div className="text-xs text-[#767D75] italic">
                        No literature records found in PubMed / Europe PMC for this query.
                      </div>
                    ) : (
                      selectedDossier.sources.map((src, idx) => (
                        <div key={src.source_id} className="border border-[#EDE8DE] bg-[#FCFAF6] p-3 space-y-1.5 text-xs">
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-editorial text-sm font-bold text-[#181B18]">
                              {idx + 1}. {src.title}
                            </span>
                            <span
                              className={`px-1.5 py-0.5 text-[9px] font-mono uppercase whitespace-nowrap border ${
                                src.erythrocyte_relevant
                                  ? 'bg-[#EDF3EE] text-[#284431] border-[#BCD0C1]'
                                  : 'bg-[#FAF7F2] text-[#767D75] border-[#D8D1C2]'
                              }`}
                            >
                              {src.erythrocyte_relevant ? 'HUMAN RBC' : 'INDIRECT'}
                            </span>
                          </div>

                          <div className="text-[11px] text-[#666E65] font-mono">
                            {src.authors.slice(0, 3).join(', ')} {src.authors.length > 3 ? 'et al.' : ''} •{' '}
                            <em>{src.journal || src.source_type}</em> ({src.year || 'n.d.'})
                          </div>

                          {src.abstract && (
                            <p className="text-[11.5px] text-[#484E48] leading-relaxed line-clamp-3">
                              "{src.abstract}"
                            </p>
                          )}

                          <div className="pt-1 flex items-center gap-3 font-mono text-[10px]">
                            {src.doi && (
                              <a
                                href={`https://doi.org/${src.doi}`}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[#9B332B] hover:underline flex items-center gap-0.5"
                              >
                                <span>DOI: {src.doi}</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                            {src.pmid && (
                              <a
                                href={`https://pubmed.ncbi.nlm.nih.gov/${src.pmid}/`}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[#9B332B] hover:underline flex items-center gap-0.5"
                              >
                                <span>PMID: {src.pmid}</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Panel 3: Structured Evidence Findings */}
              <div className="border border-[#D8D1C2]">
                <button
                  onClick={() => toggleSection('findings')}
                  className="w-full px-4 py-2.5 bg-[#FAF7F2] text-left flex items-center justify-between font-mono text-xs font-bold text-[#181B18] border-b border-[#D8D1C2]"
                >
                  <span>3. STRUCTURED EVIDENCE FINDINGS ({selectedDossier.findings.length})</span>
                  {openSections.findings ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {openSections.findings && (
                  <div className="p-4 bg-[#FFFFFF] space-y-3">
                    {selectedDossier.findings.length === 0 ? (
                      <div className="text-xs text-[#767D75] italic">No structured findings extracted.</div>
                    ) : (
                      selectedDossier.findings.map((fnd) => (
                        <div key={fnd.finding_id} className="border border-[#EDE8DE] p-3 space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-[11px] font-bold text-[#181B18]">
                              FINDING {fnd.finding_id} // {fnd.biological_system}
                            </span>
                            <span
                              className={`px-2 py-0.5 text-[9px] font-mono font-bold uppercase border ${
                                fnd.finding_evidence_level === 'CURATED'
                                  ? 'bg-[#EDF3EE] text-[#284431] border-[#BCD0C1]'
                                  : fnd.finding_evidence_level === 'ESTIMATED'
                                  ? 'bg-[#FDF4E7] text-[#8E5A1E] border-[#ECD1A4]'
                                  : 'bg-[#F9ECEB] text-[#7D221C] border-[#DCB0AC]'
                              }`}
                            >
                              {fnd.finding_evidence_level}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11.5px] text-[#484E48]">
                            <div>
                              <strong className="text-[#181B18]">Proposed Mechanism:</strong> {fnd.proposed_mechanism}
                            </div>
                            <div>
                              <strong className="text-[#181B18]">Observed Redox Effect:</strong> {fnd.observed_outcomes}
                            </div>
                          </div>

                          {fnd.exact_quote && (
                            <div className="bg-[#FAF7F2] border-l-2 border-[#9B332B] p-2 text-[11px] font-sans italic text-[#484E48]">
                              "{fnd.exact_quote}"
                            </div>
                          )}

                          <div className="text-[10.5px] font-mono text-[#767D75]">
                            RATIONALE: {fnd.grade_rationale}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Panel 4: Mechanism Mapping & Parameters */}
              <div className="border border-[#D8D1C2]">
                <button
                  onClick={() => toggleSection('mechanism')}
                  className="w-full px-4 py-2.5 bg-[#FAF7F2] text-left flex items-center justify-between font-mono text-xs font-bold text-[#181B18] border-b border-[#D8D1C2]"
                >
                  <span>4. ODE MECHANISM MAPPING & KINETIC PARAMETERS</span>
                  {openSections.mechanism ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {openSections.mechanism && (
                  <div className="p-4 bg-[#FFFFFF] space-y-4 text-xs">
                    {selectedDossier.mechanism_mappings.map((m, mIdx) => (
                      <div key={mIdx} className="space-y-3">
                        <div className="flex items-center justify-between p-2.5 bg-[#FAF7F2] border border-[#D8D1C2]">
                          <div>
                            <span className="font-mono text-[10px] text-[#767D75] uppercase block">
                              MAPPED KINETIC CLASS:
                            </span>
                            <span className="font-mono text-sm font-bold text-[#181B18]">
                              {m.mechanism_type}
                            </span>
                          </div>
                          <span
                            className={`px-2 py-0.5 text-xs font-mono font-bold uppercase border ${
                              m.is_compatible
                                ? 'bg-[#EDF3EE] text-[#284431] border-[#BCD0C1]'
                                : 'bg-[#F9ECEB] text-[#7D221C] border-[#DCB0AC]'
                            }`}
                          >
                            {m.is_compatible ? 'ODE COMPATIBLE' : 'INCOMPATIBLE'}
                          </span>
                        </div>

                        {/* Parameter Table */}
                        {m.parameters.length > 0 && (
                          <div className="overflow-x-auto">
                            <table className="w-full border border-[#D8D1C2] text-left font-mono text-[11px]">
                              <thead className="bg-[#FAF7F2] border-b border-[#D8D1C2] text-[#484E48]">
                                <tr>
                                  <th className="p-2">PARAMETER</th>
                                  <th className="p-2">PROPOSED VALUE</th>
                                  <th className="p-2">UNITS</th>
                                  <th className="p-2">BOUNDS</th>
                                  <th className="p-2">PROVENANCE</th>
                                  <th className="p-2">STATUS</th>
                                </tr>
                              </thead>
                              <tbody>
                                {m.parameters.map((p) => (
                                  <tr key={p.name} className="border-b border-[#EDE8DE] hover:bg-[#FCFAF6]">
                                    <td className="p-2 font-bold text-[#181B18]">{p.name}</td>
                                    <td className="p-2 text-[#9B332B] font-bold">{p.value}</td>
                                    <td className="p-2 text-[#484E48]">{p.units}</td>
                                    <td className="p-2 text-[#767D75]">[{p.min_bound}, {p.max_bound}]</td>
                                    <td className="p-2">
                                      <span
                                        className={`px-1.5 py-0.5 text-[9px] uppercase border font-bold ${
                                          p.provenance === 'MEASURED'
                                            ? 'bg-[#EDF3EE] text-[#284431] border-[#BCD0C1]'
                                            : p.provenance === 'DERIVED'
                                            ? 'bg-[#EBF1F9] text-[#1E3A5F] border-[#B0C5E5]'
                                            : p.provenance === 'INFERRED'
                                            ? 'bg-[#FDF4E7] text-[#8E5A1E] border-[#ECD1A4]'
                                            : 'bg-[#F9ECEB] text-[#7D221C] border-[#DCB0AC]'
                                        }`}
                                      >
                                        {p.provenance}
                                      </span>
                                    </td>
                                    <td className="p-2 text-[#284431] font-bold">{p.validation_status}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}

                        {/* Unmodeled Physics & Assumptions */}
                        <div className="p-3 border border-[#EDE8DE] bg-[#FCFAF6] space-y-1 text-[11px] text-[#484E48]">
                          <strong className="text-[#181B18] block font-mono text-[10px] uppercase">
                            UNMODELED BIOLOGY & ASSUMPTIONS:
                          </strong>
                          <ul className="list-disc pl-4 space-y-0.5">
                            {m.assumptions.map((a, i) => (
                              <li key={i}>{a}</li>
                            ))}
                            {m.unmodeled_aspects.map((u, i) => (
                              <li key={`u_${i}`} className="text-[#7D221C]">{u}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Panel 5: 10-Gate Scientific Validation Checklist */}
              <div className="border border-[#D8D1C2]">
                <button
                  onClick={() => toggleSection('validation')}
                  className="w-full px-4 py-2.5 bg-[#FAF7F2] text-left flex items-center justify-between font-mono text-xs font-bold text-[#181B18] border-b border-[#D8D1C2]"
                >
                  <div className="flex items-center gap-2">
                    <span>5. 10-GATE SCIENTIFIC VALIDATION CHECKLIST</span>
                    {selectedDossier.validation_summary.simulation_eligible ? (
                      <span className="text-[10px] text-[#284431] font-bold">(10/10 PASS)</span>
                    ) : (
                      <span className="text-[10px] text-[#7D221C] font-bold">
                        ({selectedDossier.validation_summary.blocking_reasons.length} BLOCKERS)
                      </span>
                    )}
                  </div>
                  {openSections.validation ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {openSections.validation && (
                  <div className="p-4 bg-[#FFFFFF] space-y-2">
                    {selectedDossier.validation_summary.gates.map((g, idx) => (
                      <div
                        key={idx}
                        className={`p-2.5 border flex items-start gap-2.5 text-xs ${
                          g.passed
                            ? 'bg-[#FFFFFF] border-[#EDE8DE]'
                            : 'bg-[#F9ECEB] border-[#DCB0AC] text-[#7D221C]'
                        }`}
                      >
                        {g.passed ? (
                          <CheckCircle2 className="w-4 h-4 text-[#2D5A4C] mt-0.5 shrink-0" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[#9B332B] mt-0.5 shrink-0" />
                        )}
                        <div className="flex-1">
                          <div className="font-mono text-[11px] font-bold text-[#181B18]">
                            {g.gate_name}
                          </div>
                          <div className="text-[11px] text-[#484E48] mt-0.5">
                            {g.message}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
