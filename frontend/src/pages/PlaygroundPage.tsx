import React, { useState } from 'react';
import type { CompoundResponse, ScenarioRequest, ScenarioRunResponse, StoredRunRecord } from '../types/api';
import { ScenarioBuilder } from '../features/scenarios/ScenarioBuilder';
import { ScenarioResults } from '../features/scenarios/ScenarioResults';
import { ErythrocyteViewer } from '../features/visualization/ErythrocyteViewer';
import { runScenario } from '../api/client';
import { AlertBox } from '../components/AlertBox';

interface Props {
  compounds: CompoundResponse[];
  onAddRunRecord: (record: StoredRunRecord) => void;
  initialSelectedCompound?: CompoundResponse | null;
  onClearInitialCompound?: () => void;
  activeLoadedRun?: ScenarioRunResponse | null;
}

export const PlaygroundPage: React.FC<Props> = ({
  compounds,
  onAddRunRecord,
  initialSelectedCompound,
  onClearInitialCompound,
  activeLoadedRun,
}) => {
  const [treatmentResult, setTreatmentResult] = useState<ScenarioRunResponse | null>(activeLoadedRun || null);
  const [controlResult, setControlResult] = useState<ScenarioRunResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showViewer, setShowViewer] = useState<boolean>(false);

  // If a run is passed from history, load it
  React.useEffect(() => {
    if (activeLoadedRun) {
      setTreatmentResult(activeLoadedRun);
      setControlResult(null);
    }
  }, [activeLoadedRun]);

  const handleExecuteScenario = async (req: ScenarioRequest, compareWithControl: boolean) => {
    setLoading(true);
    setError(null);

    try {
      // 1. Run Treatment Scenario
      const trtRes = await runScenario(req);
      setTreatmentResult(trtRes);

      // Log to session history
      const compoundNames = req.compounds.map((c) => {
        const item = compounds.find((lib) => lib.compound_id === c.compound_id);
        return item ? item.name : c.compound_id;
      });

      onAddRunRecord({
        id: trtRes.run_id,
        timestamp: new Date().toLocaleTimeString(),
        title: `Single-Cell (${compoundNames.join(' + ')})`,
        type: 'single',
        compoundNames,
        modelVersion: req.model_version,
        g6pdAlpha: req.g6pd_alpha,
        hasUnverified: trtRes.has_unverified_compounds,
        result: trtRes,
      });

      // 2. Optionally run Control (dose=0 or no compounds)
      if (compareWithControl) {
        try {
          const ctrlReq: ScenarioRequest = {
            ...req,
            compounds: req.compounds.map((c) => ({ ...c, dose_mM: 0.0 })),
          };
          const ctrlRes = await runScenario(ctrlReq);
          setControlResult(ctrlRes);
        } catch {
          // If control run fails, continue with treatment
          setControlResult(null);
        }
      } else {
        setControlResult(null);
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && <AlertBox type="error" title="Simulation Error">{error}</AlertBox>}

      {/* Scenario Configuration Form */}
      <ScenarioBuilder
        compounds={compounds}
        onRunScenario={handleExecuteScenario}
        loading={loading}
        selectedCompoundForAdd={initialSelectedCompound}
        onClearSelectedCompound={onClearInitialCompound}
      />

      {/* Results Section */}
      {treatmentResult && (
        <div className="space-y-6 pt-2">
          {/* Erythrocyte Visualizer (Collapsible / Toggleable) */}
          {showViewer && (
            <div className="animate-fade-in">
              <ErythrocyteViewer
                runId={treatmentResult.run_id}
                onClose={() => setShowViewer(false)}
              />
            </div>
          )}

          {/* Time Series & Derived Metrics */}
          <ScenarioResults
            treatmentResult={treatmentResult}
            controlResult={controlResult}
            onOpenPlayback={() => setShowViewer((prev) => !prev)}
          />
        </div>
      )}
    </div>
  );
};
