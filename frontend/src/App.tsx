import React, { useEffect, useState } from 'react';
import type {
  CompoundResponse,
  HealthResponse,
  ModelDetailResponse,
  PopulationRequest,
  PopulationResult,
  ScenarioRunResponse,
  StoredRunRecord,
} from './types/api';
import { Header, type ActiveTab } from './components/Header';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { CompoundCatalog } from './features/compounds/CompoundCatalog';
import { PopulationBuilder } from './features/population/PopulationBuilder';
import { PopulationResults } from './features/population/PopulationResults';
import { SessionRunHistory } from './features/runs/SessionRunHistory';
import { ModelInfoView } from './features/models/ModelInfoView';
import { getCompounds, getHealth, getModels, runPopulationScenario } from './api/client';
import { AlertBox } from './components/AlertBox';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('playground');

  // Backend state
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [compounds, setCompounds] = useState<CompoundResponse[]>([]);
  const [compoundsLoading, setCompoundsLoading] = useState<boolean>(true);
  const [compoundsError, setCompoundsError] = useState<string | null>(null);

  const [models, setModels] = useState<ModelDetailResponse[]>([]);
  const [modelsLoading, setModelsLoading] = useState<boolean>(true);
  const [modelsError, setModelsError] = useState<string | null>(null);

  // Cross-tab interaction state
  const [compoundToLoad, setCompoundToLoad] = useState<CompoundResponse | null>(null);
  const [activeLoadedRun, setActiveLoadedRun] = useState<ScenarioRunResponse | null>(null);

  // Population Cohort state
  const [populationRequest, setPopulationRequest] = useState<PopulationRequest | null>(null);
  const [populationResult, setPopulationResult] = useState<PopulationResult | null>(null);
  const [populationLoading, setPopulationLoading] = useState<boolean>(false);
  const [populationError, setPopulationError] = useState<string | null>(null);

  // Session Run History
  const [sessionRuns, setSessionRuns] = useState<StoredRunRecord[]>(() => {
    try {
      const stored = sessionStorage.getItem('vblood_session_runs');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Persist session runs
  useEffect(() => {
    try {
      sessionStorage.setItem('vblood_session_runs', JSON.stringify(sessionRuns));
    } catch {
      // Storage quota or disabled
    }
  }, [sessionRuns]);

  // Initial Data Fetch
  const fetchHealth = () => {
    setHealthLoading(true);
    setHealthError(null);
    getHealth()
      .then((h) => {
        setHealth(h);
        setHealthLoading(false);
      })
      .catch((err) => {
        setHealthError(err.detail || 'Backend unavailable');
        setHealthLoading(false);
      });
  };

  const fetchCompounds = () => {
    setCompoundsLoading(true);
    setCompoundsError(null);
    getCompounds()
      .then((data) => {
        setCompounds(data);
        setCompoundsLoading(false);
      })
      .catch((err) => {
        setCompoundsError(err.detail || 'Failed to fetch compound library');
        setCompoundsLoading(false);
      });
  };

  const fetchModels = () => {
    setModelsLoading(true);
    setModelsError(null);
    getModels()
      .then((data) => {
        setModels(data);
        setModelsLoading(false);
      })
      .catch((err) => {
        setModelsError(err.detail || 'Failed to fetch registered models');
        setModelsLoading(false);
      });
  };

  useEffect(() => {
    fetchHealth();
    fetchCompounds();
    fetchModels();
  }, []);

  const handleAddRunRecord = (rec: StoredRunRecord) => {
    setSessionRuns((prev) => [rec, ...prev]);
  };

  const handleSelectCompoundFromCatalog = (comp: CompoundResponse) => {
    setCompoundToLoad(comp);
    setActiveTab('playground');
  };

  const handleSelectHistoryRun = (record: StoredRunRecord) => {
    if (record.type === 'single' && record.result) {
      setActiveLoadedRun(record.result);
      setActiveTab('playground');
    } else if (record.type === 'population' && record.populationResult) {
      setPopulationResult(record.populationResult);
      setActiveTab('population');
    }
  };

  const handleRunPopulation = async (req: PopulationRequest) => {
    setPopulationRequest(req);
    setPopulationLoading(true);
    setPopulationError(null);

    try {
      const res = await runPopulationScenario(req);
      setPopulationResult(res);

      const compoundNames = req.scenario_request.compounds.map((c) => {
        const item = compounds.find((lib) => lib.compound_id === c.compound_id);
        return item ? item.name : c.compound_id;
      });

      handleAddRunRecord({
        id: `pop_${Date.now()}`,
        timestamp: new Date().toLocaleTimeString(),
        title: `Population (${req.n_cells} cells, ${compoundNames.join(' + ')})`,
        type: 'population',
        compoundNames,
        modelVersion: req.scenario_request.model_version,
        g6pdAlpha: req.scenario_request.g6pd_alpha,
        hasUnverified: req.scenario_request.compounds.some((c) => {
          const item = compounds.find((lib) => lib.compound_id === c.compound_id);
          return item?.is_unverified ?? false;
        }),
        populationResult: res,
      });
    } catch (err: any) {
      setPopulationError(err.detail || err.message || 'Cohort simulation failed.');
    } finally {
      setPopulationLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F2EB] text-[#181B18] flex flex-col lg:flex-row font-sans selection:bg-[#9B332B] selection:text-white">
      {/* Left Scientific Navigation Rail */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        healthError={healthError}
        onRetryHealth={fetchHealth}
      />

      {/* Main Workspace Stage */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Operational Status Bar */}
        <header className="border-b border-[#D8D1C2] bg-[#FCFAF6]/90 px-4 sm:px-6 lg:px-8 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] uppercase tracking-wider text-[#767D75]">
              Active Workspace:
            </span>
            <span className="font-editorial text-sm font-semibold text-[#181B18]">
              {activeTab === 'playground' && 'Single-Cell Kinetic Dynamics'}
              {activeTab === 'compounds' && 'Curated Chemical Compound Index'}
              {activeTab === 'population' && 'Heterogeneous Cohort Simulator'}
              {activeTab === 'history' && 'Workstation Simulation Ledger'}
              {activeTab === 'models' && 'Mechanistic Model Specifications'}
            </span>
          </div>

          <div className="flex items-center gap-4 text-[11px] font-mono text-[#666E65]">
            <span className="hidden sm:inline">
              COMPOUNDS: <strong className="text-[#181B18]">{compounds.length}</strong>
            </span>
            <span className="hidden sm:inline text-[#B5AC99]">|</span>
            <span className="hidden md:inline">
              MODELS: <strong className="text-[#181B18]">{models.length}</strong>
            </span>
            <span className="hidden md:inline text-[#B5AC99]">|</span>
            <span className="text-[#435E4B] flex items-center gap-1.5 font-medium">
              <span className="w-1.5 h-1.5 bg-[#435E4B]" />
              MASS CONSERVATION CERTIFIED
            </span>
          </div>
        </header>

        {/* Main Workspace Content */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 py-6 max-w-7xl w-full mx-auto space-y-6">
          {/* Connection Failure Banner */}
          {healthError && (
            <AlertBox type="error" title="FastAPI Core Engine Disconnected">
              {healthError}. Verify that the Python backend daemon is active via{' '}
              <code className="text-[#9B332B] font-mono bg-[#FFFFFF] px-1 py-0.5 border border-[#DCB0AC]">
                .\.venv\Scripts\python.exe -m uvicorn vblood.api.app:app --host 127.0.0.1 --port 8000
              </code>
              . Simulation submissions require an active numerical integration service.
            </AlertBox>
          )}

          {/* Module 1: Blood Playground */}
          {activeTab === 'playground' && (
            <PlaygroundPage
              compounds={compounds}
              onAddRunRecord={handleAddRunRecord}
              initialSelectedCompound={compoundToLoad}
              onClearInitialCompound={() => setCompoundToLoad(null)}
              activeLoadedRun={activeLoadedRun}
            />
          )}

          {/* Module 2: Compound Library */}
          {activeTab === 'compounds' && (
            <CompoundCatalog
              compounds={compounds}
              loading={compoundsLoading}
              error={compoundsError}
              onRefresh={fetchCompounds}
              onSelectForScenario={handleSelectCompoundFromCatalog}
            />
          )}

          {/* Module 3: Population Cohort */}
          {activeTab === 'population' && (
            <div className="space-y-6">
              {populationError && (
                <AlertBox type="error" title="Cohort Simulation Error">
                  {populationError}
                </AlertBox>
              )}

              <PopulationBuilder
                compounds={compounds}
                onRunPopulation={handleRunPopulation}
                loading={populationLoading}
              />

              <PopulationResults result={populationResult} request={populationRequest} />
            </div>
          )}

          {/* Module 4: Session Run History */}
          {activeTab === 'history' && (
            <SessionRunHistory
              records={sessionRuns}
              onSelectRun={handleSelectHistoryRun}
              onClearHistory={() => setSessionRuns([])}
            />
          )}

          {/* Module 5: Model & Evidence */}
          {activeTab === 'models' && (
            <ModelInfoView
              models={models}
              loading={modelsLoading}
              error={modelsError}
            />
          )}
        </main>

        {/* Archival Research Footer */}
        <footer className="border-t border-[#D8D1C2] bg-[#FAF7F2] py-4 text-xs text-[#767D75]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="font-editorial text-sm font-semibold text-[#181B18]">
                V-Blood Field Station
              </span>
              <span className="font-mono text-[10px] text-[#868E85]">
                // MILESTONE 5 PRODUCTION SPECIFICATION
              </span>
            </div>

            <div className="flex items-center gap-4 text-[11px] font-mono text-[#666E65]">
              <span>GSH / GSSG REDOX PAIR</span>
              <span>•</span>
              <span>PENTOSE PHOSPHATE DYNAMICS</span>
              <span>•</span>
              <span className="text-[#9B332B] font-semibold">NOT FOR CLINICAL DIAGNOSTICS</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
