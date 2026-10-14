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
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Chemical Compound Catalog</h1>
          <p className="text-xs text-slate-400 mt-1">
            Curated biochemical oxidants, electrophilic conjugators, and redox modulators with explicit provenance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
            {filteredCompounds.length} / {compounds.length} compounds
          </span>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-50 transition-colors"
            title="Refresh compound library"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Unverified compounds warning note */}
      <AlertBox type="disclaimer" title="Scientific Evidence Standards">
        Compounds marked <strong className="text-rose-400">UNVERIFIED</strong> (such as synthetic lead Xenobiotic X-101)
        contain hypothetical parameters not derived from human red blood cell literature. They are surfaced exclusively
        for platform stress testing and are automatically flagged in all simulation outputs.
      </AlertBox>

      {/* Filter & Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 bg-slate-900/80 p-4 rounded-lg border border-slate-800">
        {/* Search */}
        <div className="sm:col-span-5 relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by compound name, ID, SMILES..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-600 font-sans"
          />
        </div>

        {/* Mechanism Filter */}
        <div className="sm:col-span-4 relative">
          <select
            value={selectedMechanism}
            onChange={(e) => setSelectedMechanism(e.target.value as any)}
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-600 cursor-pointer"
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
            className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-slate-600 cursor-pointer"
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
        <div className="flex items-center justify-center h-48 text-slate-400 text-xs gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-slate-500" />
          <span>Loading verified chemical compound catalog...</span>
        </div>
      )}

      {/* Compound Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCompounds.map((c) => {
          return (
            <div
              key={c.compound_id}
              className={`bg-slate-900/90 rounded-lg border p-4 flex flex-col justify-between transition-all hover:border-slate-700 shadow-sm ${
                c.is_unverified ? 'border-rose-900/50 bg-rose-950/10' : 'border-slate-800'
              }`}
            >
              <div>
                {/* Header: Name & Evidence */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
                      {c.name}
                      {c.is_unverified && (
                        <span title="Unverified compound entry">
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                        </span>
                      )}
                    </h3>
                    <span className="text-[11px] font-mono text-slate-400">{c.compound_id}</span>
                  </div>
                  <EvidenceBadge level={c.evidence_level} />
                </div>

                {/* Mechanism & Units */}
                <div className="text-xs space-y-1.5 my-3">
                  <div className="flex items-center justify-between text-slate-400 border-b border-slate-800/80 pb-1">
                    <span>Mechanism:</span>
                    <span className="font-medium text-slate-200">
                      {c.mechanism_type.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400 border-b border-slate-800/80 pb-1">
                    <span>Exposure Units:</span>
                    <span className="font-mono text-slate-300">{c.exposure_units}</span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400">
                    <span>Confidence Score:</span>
                    <span className="font-mono text-emerald-400">{(c.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {/* Provenance Snippet */}
                <p className="text-[11px] text-slate-400 italic line-clamp-2 mt-2 leading-relaxed bg-slate-950/40 p-2 rounded border border-slate-800/60">
                  "{c.provenance}"
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between gap-2 mt-4 pt-3 border-t border-slate-800">
                <button
                  onClick={() => setActiveModalCompound(c)}
                  className="px-2.5 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded border border-slate-700 flex items-center gap-1 transition-colors"
                >
                  <Eye className="w-3.5 h-3.5 text-slate-400" />
                  <span>Inspect Details</span>
                </button>

                <button
                  onClick={() => onSelectForScenario(c)}
                  className="px-3 py-1.5 text-xs font-semibold text-rose-300 hover:text-white bg-rose-950/70 hover:bg-rose-900 border border-rose-800/70 rounded flex items-center gap-1 transition-colors"
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
        <div className="text-center py-12 border border-slate-800 rounded-lg text-slate-400">
          <Filter className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm">No chemical compounds match your search and filter criteria.</p>
        </div>
      )}

      {/* Details Modal */}
      <CompoundModal
        compound={activeModalCompound}
        onClose={() => setActiveModalCompound(null)}
        onSelectForScenario={onSelectForScenario}
      />
    </div>
  );
};
