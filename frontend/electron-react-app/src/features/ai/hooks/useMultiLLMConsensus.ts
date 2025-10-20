import { useQuery } from "@tanstack/react-query";
import { useAppStore } from "../../../store/useAppStore";
import { fetchMultiLLMAnalysis, fetchConsensusMetrics } from "../api";

export interface ConsensusResult {
  consensus_score: number;
  model_agreements: Record<string, number>;
  final_findings: Array<{
    id: string;
    issue_title: string;
    reasoning: string;
    suggestion: string;
    confidence: number;
    consensus_confidence: number;
    model_votes: Record<string, boolean>;
    disagreement_flag: boolean;
  }>;
  model_outputs: Record<
    string,
    {
      findings: any[];
      confidence: number;
      processing_time: number;
    }
  >;
  ensemble_metadata: {
    total_models: number;
    agreement_threshold: number;
    weighted_voting: boolean;
    processing_time_ms: number;
  };
}

export const useMultiLLMConsensus = (documentId?: string) => {
  const token = useAppStore((state) => state.auth.token);

  const consensusQuery = useQuery({
    queryKey: ["multi-llm-consensus", documentId],
    queryFn: () => fetchMultiLLMAnalysis(documentId!),
    enabled: Boolean(token && documentId),
    staleTime: 300000, // 5 minutes
  });

  const metricsQuery = useQuery({
    queryKey: ["consensus-metrics"],
    queryFn: fetchConsensusMetrics,
    enabled: Boolean(token),
    staleTime: 60000, // 1 minute
  });

  return {
    consensus: consensusQuery.data,
    metrics: metricsQuery.data,
    isLoading: consensusQuery.isLoading || metricsQuery.isLoading,
    isError: consensusQuery.isError || metricsQuery.isError,
    refetch: () => {
      consensusQuery.refetch();
      metricsQuery.refetch();
    },
  };
};
