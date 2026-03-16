export type PageId = 'manager' | 'meetings' | 'tasks' | 'decisions' | 'speakers' | 'stale' | 'ingest' | 'employees';

export interface Employee {
  id: string;
  name: string;
  emp_id: string;
  department?: string | null;
  github_username?: string | null;
  created_at: string;
}

export interface Speaker {
  id: string;
  name: string;
  role: string;
  initials: string;
  color: string;
  tasks_owned: number;
  decisions_triggered: number;
  words_spoken: number;
  notable_quote: string;
}

export interface Meeting {
  id: string;
  title: string;
  host_name: string;
  description?: string;
  status: 'pending' | 'transcribing' | 'processing' | 'complete' | 'failed';
  input_type?: 'uploaded_audio' | 'text' | 'live_audio';
  raw_file_path?: string;
  raw_transcript?: string;
  cleaned_transcript?: string;
  tldr?: string;
  health_score?: number;
  created_at: string;
  processed_at?: string;
  task_count?: number;
  decision_count?: number;
  tasks?: Task[];
  decisions?: Decision[];
}

export interface Task {
  id: string;
  meeting_id: string;
  title: string;
  description?: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'approved' | 'in_progress' | 'completed' | 'failed' | 'pending_review' | 'discarded';
  confidence_score: number;
  assignee_name?: string;
  owner_emp_id?: string;
  owner_dept?: string;
  employee_id?: string;
  source_quote?: string;
  created_at: string;
  // Specific to StaleTasks
  days_overdue?: number;
  mentioned_in_meeting_id?: string;
  assignee_color?: string;
  assignee_initials?: string;
}

export interface Decision {
  id: string;
  meeting_id: string;
  title: string;
  description?: string;
  decided_by_name?: string;
  source_quote?: string;
  created_at: string;
}

