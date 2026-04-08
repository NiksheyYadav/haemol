import { ReviewTable } from "@/components/review-table";

export default function ReviewPage({ params }: { params: { reportId: string } }): JSX.Element {
  return <ReviewTable reportId={params.reportId} />;
}
