import { StatusView } from "@/components/status-view";

export default function ReportStatusPage({ params }: { params: { reportId: string } }): JSX.Element {
  return <StatusView reportId={params.reportId} />;
}
