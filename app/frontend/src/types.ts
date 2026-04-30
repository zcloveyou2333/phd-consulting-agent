export type StudentCase = {
  id: string;
  student_name: string;
  summary: string;
  target_regions: string[];
  notes: string;
  output_ids: string[];
};

export type GeneratedOutput = {
  id: string;
  case_id: string;
  kind: string;
  title: string;
  content: string;
};
