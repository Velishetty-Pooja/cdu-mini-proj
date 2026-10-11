import axios from 'axios';
import {
  HealthResponse,
  ImageAnalysisResponse,
  VideoJobStatus,
  AnalysisRecordSummary,
  SampleMedia,
  LaneDefinition,
  CountingLineDefinition,
} from '../types';

const apiClient = axios.create({
  baseURL: '', // Uses Vite proxy in development
  timeout: 300000, // 5 min timeout for video operations
});

export interface AnalysisConfigOptions {
  confidence?: number;
  sampleStride?: number;
  direction?: string;
  roadRoi?: number[];
  lanes?: LaneDefinition[];
  countingLines?: CountingLineDefinition[];
  restrictedZones?: number[][];
}

export const api = {
  getHealth: async (): Promise<HealthResponse> => {
    const res = await apiClient.get<HealthResponse>('/api/health');
    return res.data;
  },

  analyzeImage: async (
    file: File,
    options: AnalysisConfigOptions = {}
  ): Promise<ImageAnalysisResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options.confidence !== undefined) formData.append('confidence', options.confidence.toString());
    if (options.direction) formData.append('direction', options.direction);
    if (options.roadRoi) formData.append('road_roi', JSON.stringify(options.roadRoi));
    if (options.lanes && options.lanes.length > 0) formData.append('lane_config', JSON.stringify(options.lanes));
    if (options.countingLines && options.countingLines.length > 0) formData.append('counting_lines', JSON.stringify(options.countingLines));
    if (options.restrictedZones && options.restrictedZones.length > 0) formData.append('restricted_zones', JSON.stringify(options.restrictedZones));

    const res = await apiClient.post<ImageAnalysisResponse>('/api/analyze/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  analyzeVideo: async (
    file: File,
    options: AnalysisConfigOptions = {}
  ): Promise<{ job_id: string; status: string; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    if (options.confidence !== undefined) formData.append('confidence', options.confidence.toString());
    if (options.sampleStride !== undefined) formData.append('sample_stride', options.sampleStride.toString());
    if (options.direction) formData.append('direction', options.direction);
    if (options.roadRoi) formData.append('road_roi', JSON.stringify(options.roadRoi));
    if (options.lanes && options.lanes.length > 0) formData.append('lane_config', JSON.stringify(options.lanes));
    if (options.countingLines && options.countingLines.length > 0) formData.append('counting_lines', JSON.stringify(options.countingLines));
    if (options.restrictedZones && options.restrictedZones.length > 0) formData.append('restricted_zones', JSON.stringify(options.restrictedZones));

    const res = await apiClient.post<{ job_id: string; status: string; message: string }>('/api/analyze/video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  getJobStatus: async (jobId: string): Promise<VideoJobStatus> => {
    const res = await apiClient.get<VideoJobStatus>(`/api/jobs/${jobId}`);
    return res.data;
  },

  getAnalysisResult: async (analysisId: string): Promise<{ record: any; events: any[]; result: any }> => {
    const res = await apiClient.get(`/api/results/${analysisId}`);
    return res.data;
  },

  getHistory: async (limit: number = 50): Promise<{ history: AnalysisRecordSummary[] }> => {
    const res = await apiClient.get<{ history: AnalysisRecordSummary[] }>(`/api/history?limit=${limit}`);
    return res.data;
  },

  deleteHistoryItem: async (analysisId: string): Promise<{ success: boolean; message: string }> => {
    const res = await apiClient.delete<{ success: boolean; message: string }>(`/api/history/${analysisId}`);
    return res.data;
  },

  getSampleMedia: async (): Promise<{ samples: SampleMedia[] }> => {
    const res = await apiClient.get<{ samples: SampleMedia[] }>('/api/samples');
    return res.data;
  },

  analyzeSampleMedia: async (sampleName: string, options: AnalysisConfigOptions = {}): Promise<any> => {
    const formData = new FormData();
    formData.append('sample_name', sampleName);
    if (options.confidence !== undefined) formData.append('confidence', options.confidence.toString());
    if (options.sampleStride !== undefined) formData.append('sample_stride', options.sampleStride.toString());
    if (options.direction) formData.append('direction', options.direction);
    if (options.roadRoi) formData.append('road_roi', JSON.stringify(options.roadRoi));
    if (options.lanes && options.lanes.length > 0) formData.append('lane_config', JSON.stringify(options.lanes));
    if (options.countingLines && options.countingLines.length > 0) formData.append('counting_lines', JSON.stringify(options.countingLines));
    if (options.restrictedZones && options.restrictedZones.length > 0) formData.append('restricted_zones', JSON.stringify(options.restrictedZones));

    const res = await apiClient.post('/api/analyze/sample', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};
