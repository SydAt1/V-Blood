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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-rose-900 selection:text-white">
      {/* Platform Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        healthError={healthError}
        onRetryHealth={fetchHealth}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Connection Failure Banner */}
        {healthError && (
          <div className="mb-6">
            <AlertBox type="error" title="API Backend Not Reachable">
              {healthError}. Verify that the FastAPI backend server is running via{' '}
              <code className="text-rose-300 font-mono">
                .\.venv\Scripts\python.exe -m uvicorn vblood.api.app:app --host 127.0.0.1 --port 8000
              </code>
              .
            </AlertBox>
          </div>
        )}

        {/* Tab 1: Blood Playground */}
        {activeTab === 'playground' && (
          <PlaygroundPage
            compounds={compounds}
            onAddRunRecord={handleAddRunRecord}
            initialSelectedCompound={compoundToLoad}
            onClearInitialCompound={() => setCompoundToLoad(null)}
            activeLoadedRun={activeLoadedRun}
          />
        )}

        {/* Tab 2: Compound Library */}
        {activeTab === 'compounds' && (
          <CompoundCatalog
            compounds={compounds}
            loading={compoundsLoading}
            error={compoundsError}
            onRefresh={fetchCompounds}
            onSelectForScenario={handleSelectCompoundFromCatalog}
          />
        )}

        {/* Tab 3: Population Cohort */}
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

            <PopulationResults result={populationResult} />
          </div>
        )}

        {/* Tab 4: Session Run History */}
        {activeTab === 'history' && (
          <SessionRunHistory
            records={sessionRuns}
            onSelectRun={handleSelectHistoryRun}
            onClearHistory={() => setSessionRuns([])}
          />
        )}

        {/* Tab 5: Model & Evidence */}
        {activeTab === 'models' && (
          <ModelInfoView
            models={models}
            loading={modelsLoading}
            error={modelsError}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>V-Blood Mechanistic Simulation Platform • Milestone 5</span>
          <span className="font-mono text-[11px]">Source code strictly preserves biological mass conservation</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
