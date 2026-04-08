import { ResultsView } from "@/components/results-view";

export default function AnalysisPage({ params }: { params: { analysisId: string } }): JSX.Element {
  return <ResultsView analysisId={params.analysisId} />;
}
