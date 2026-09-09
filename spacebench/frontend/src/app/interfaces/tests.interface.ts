export interface TestResult {
  name: string;
  file: string;
  status: 'pending' | 'running' | 'PASSED' | 'FAILED' | 'ERROR';
  log?: string;
  expanded: boolean;
}

export interface TestEvent {
  type: 'result' | 'failure' | 'done';
  file?: string;
  name?: string;
  status?: string;
  passed?: number;
  failed?: number;
  log?: string;
}
