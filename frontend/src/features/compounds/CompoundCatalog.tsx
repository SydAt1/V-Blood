import React, { useMemo, useState } from 'react';
import type { CompoundResponse, EvidenceLevel, MechanismType } from '../../types/api';
import { EvidenceBadge } from '../../components/EvidenceBadge';
import { AlertBox } from '../../components/AlertBox';
import { CompoundModal } from './CompoundModal';
import { Eye, Filter, Plus, RefreshCw, Search, ShieldAlert } from 'lucide-react';

interface Props {
  compounds: CompoundResponse[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onSelectForScenario: (compound: CompoundResponse) => void;
  onNavigateToResearch?: () => void;
}

const MECHANISM_OPTIONS: Array<{ value: MechanismType | 'ALL'; label: string }> = [
  { value: 'ALL', label: 'All Mechanisms' },
  { value: 'DIRECT_OXIDANT', label: 'Direct Oxidant' },
  { value: 'GSH_CONJUGATOR', label: 'GSH Conjugator' },
  { value: 'REDOX_CYCLER', label: 'Redox Cycler' },
  { value: 'ENZYME_INHIBITOR', label: 'Enzyme Inhibitor' },
  { value: 'NADPH_DRAIN', label: 'NADPH Pool Drain' },
];

const EVIDENCE_OPTIONS: Array<{ value: EvidenceLevel | 'ALL'; label: string }> = [
  { value: 'ALL', label: 'All Evidence Levels' },
  { value: 'CURATED', label: 'Curated' },
  { value: 'ESTIMATED', label: 'Estimated' },
  { value: 'UNVERIFIED', label: 'Unverified Only' },
];

export const CompoundCatalog: React.FC<Props> = ({
  compounds,
  loading,
  error,
  onRefresh,
  onSelectForScenario,
  onNavigateToResearch,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMechanism, setSelectedMechanism] = useState<MechanismType | 'ALL'>('ALL');
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceLevel | 'ALL'>('ALL');
  const [activeModalCompound, setActiveModalCompound] = useState<CompoundResponse | null>(null);

  // Filtered compounds
  const filteredCompounds = useMemo(() => {
    return compounds.filter((c) => {
      // Mechanism filter
      if (selectedMechanism !== 'ALL' && c.mechanism_type !== selectedMechanism) {
        return false;
      }
      // Evidence filter
      if (selectedEvidence !== 'ALL' && c.evidence_level !== selectedEvidence) {
        return false;
      }
      // Text search
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesName = c.name.toLowerCase().includes(query);
        const matchesId = c.compound_id.toLowerCase().includes(query);
        const matchesSmiles = (c.smiles || '').toLowerCase().includes(query);
        const matchesInchi = (c.inchikey || '').toLowerCase().includes(query);
        if (!matchesName && !matchesId && !matchesSmiles && !matchesInchi) {
          return false;
        }
      }
      return true;
    });
  }, [compounds, selectedMechanism, selectedEvidence, searchTerm]);

  return (
    <div className="space-y-6">
      {/* Title & Index Telemetry */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#D8D1C2] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-[#767D75] uppercase tracking-wider">
              CATALOGUE //
            </span>
            <h1 className="font-editorial text-2xl font-bold text-[#181B18] tracking-tight">
              Chemical Compound Catalog
            </h1>
          </div>
          <p className="text-xs text-[#666E65] mt-1 font-sans">
            Curated biochemical oxidants, electrophilic conjugators, and redox modulators with explicit provenance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {onNavigateToResearch && (
            <button
              onClick={onNavigateToResearch}
              className="px-2.5 py-1.5 bg-[#9B332B] text-white text-xs font-mono font-semibold hover:bg-[#802820] transition-colors flex items-center gap-1.5 shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Research Substance</span>
            </button>
          )}
          <span className="text-xs font-mono text-[#181B18] bg-[#FAF7F2] px-2.5 py-1 border border-[#B5AC99]">
            {filteredCompounds.length} / {compounds.length} compounds indexed
          </span>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-1.5 border border-[#B5AC99] bg-[#FFFFFF] text-[#484E48] hover:text-[#181B18] hover:bg-[#FAF7F2] disabled:opacity-50 transition-colors shadow-[1px_1px_0px_0px_rgba(24,27,24,0.08)]"
            title="Refresh compound library"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Unverified compounds warning note */}
      <AlertBox type="disclaimer" title="Scientific Evidence Standards">
        Compounds marked <strong className="text-[#9B332B] font-mono">UNVERIFIED</strong> (such as synthetic lead Xenobiotic X-101)
        contain hypothetical parameters not derived from human red blood cell literature. They are surfaced exclusively
        for platform stress testing and are automatically flagged in all simulation outputs.
      </AlertBox>

      {/* Filter & Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 bg-[#FFFFFF] p-3.5 border border-[#D8D1C2] shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]">
        {/* Search */}
        <div className="sm:col-span-5 relative">
          <Search className="w-3.5 h-3.5 text-[#868E85] absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by compound name, ID, SMILES..."
            className="w-full bg-[#FAF7F2] border border-[#B5AC99] pl-9 pr-3 py-1.5 text-xs text-[#181B18] placeholder-[#868E85] focus:outline-none focus:border-[#181B18] font-sans"
          />
        </div>

        {/* Mechanism Filter */}
        <div className="sm:col-span-4 relative">
          <select
            value={selectedMechanism}
            onChange={(e) => setSelectedMechanism(e.target.value as any)}
            className="w-full bg-[#FAF7F2] border border-[#B5AC99] px-3 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer font-sans"
          >
            {MECHANISM_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Evidence Filter */}
        <div className="sm:col-span-3 relative">
          <select
            value={selectedEvidence}
            onChange={(e) => setSelectedEvidence(e.target.value as any)}
            className="w-full bg-[#FAF7F2] border border-[#B5AC99] px-3 py-1.5 text-xs text-[#181B18] focus:outline-none focus:border-[#181B18] cursor-pointer font-sans"
          >
            {EVIDENCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <AlertBox type="error" title="Failed to Load Compound Catalog">
          {error}
        </AlertBox>
      )}

      {/* Loading state */}
      {loading && compounds.length === 0 && (
        <div className="flex items-center justify-center h-48 text-[#767D75] text-xs gap-2 font-mono border border-dashed border-[#D8D1C2] bg-[#FAF7F2]">
          <RefreshCw className="w-4 h-4 animate-spin text-[#868E85]" />
          <span>Loading verified chemical compound catalog...</span>
        </div>
      )}

      {/* Archival Specimen Catalogue Table / Ledger */}
      <div className="border border-[#D8D1C2] bg-[#FFFFFF] shadow-[2px_2px_0px_0px_rgba(24,27,24,0.06)] divide-y divide-[#EDE8DE]">
        {filteredCompounds.map((c) => {
          return (
            <div
              key={c.compound_id}
              className={`p-4 transition-all hover:bg-[#FAF8F3] flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                c.is_unverified ? 'bg-[#FAF5F4]/70 border-l-4 border-l-[#9B332B]' : ''
              }`}
            >
              {/* Left Column: Specimen Identity & Mechanism */}
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-editorial text-base font-bold text-[#181B18] flex items-center gap-2">
                    <span>{c.name}</span>
                    {c.is_unverified && (
                      <span title="Unverified compound entry">
                        <ShieldAlert className="w-3.5 h-3.5 text-[#9B332B]" />
                      </span>
                    )}
                  </h3>
                  <EvidenceBadge level={c.evidence_level} />
                </div>

                <div className="flex flex-wrap items-center gap-3 text-xs text-[#666E65] font-mono">
                  <span>ID: <code className="text-[#181B18]">{c.compound_id}</code></span>
                  <span>•</span>
                  <span>Mechanism: <strong className="text-[#383E38]">{c.mechanism_type.replace(/_/g, ' ')}</strong></span>
                  <span>•</span>
                  <span>Units: {c.exposure_units}</span>
                  <span>•</span>
                  <span>Confidence: <strong className="text-[#286345]">{(c.confidence_score * 100).toFixed(0)}%</strong></span>
                </div>

                <p className="text-[11px] text-[#555C54] italic font-serif leading-relaxed line-clamp-1 pt-0.5">
                  "{c.provenance}"
                </p>
              </div>

              {/* Right Column: Actions */}
              <div className="flex items-center gap-2 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-[#EDE8DE]">
                <button
                  onClick={() => setActiveModalCompound(c)}
                  className="px-3 py-1.5 text-xs font-mono font-medium text-[#181B18] bg-[#FFFFFF] hover:bg-[#FAF7F2] border border-[#B5AC99] flex items-center gap-1.5 transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.06)]"
                >
                  <Eye className="w-3.5 h-3.5 text-[#767D75]" />
                  <span>Inspect Details</span>
                </button>

                <button
                  onClick={() => onSelectForScenario(c)}
                  className="px-3 py-1.5 text-xs font-mono font-semibold text-white bg-[#9B332B] hover:bg-[#802821] border border-[#9B332B] flex items-center gap-1.5 transition-all shadow-[1px_1px_0px_0px_rgba(24,27,24,0.12)]"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add to Scenario</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {filteredCompounds.length === 0 && !loading && (
        <div className="text-center py-12 border border-dashed border-[#D8D1C2] bg-[#FAF7F2] text-[#767D75]">
          <Filter className="w-8 h-8 text-[#B5AC99] mx-auto mb-2" />
          <p className="text-sm font-editorial">No chemical compounds match your search and filter criteria.</p>
        </div>
      )}

      {/* Details Inspection Monograph Modal */}
      <CompoundModal
        compound={activeModalCompound}
        onClose={() => setActiveModalCompound(null)}
        onSelectForScenario={onSelectForScenario}
      />
    </div>
  );
};
