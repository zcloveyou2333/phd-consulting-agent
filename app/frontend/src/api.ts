import type { GeneratedOutput, StudentCase } from "./types";

const API_BASE = "http://127.0.0.1:8765";

export async function createCase(input: {
  student_name: string;
  summary: string;
  target_regions: string[];
  notes: string;
}): Promise<StudentCase> {
  const response = await fetch(`${API_BASE}/cases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error(`Create case failed: ${response.status}`);
  return response.json();
}

export async function runSkill(caseId: string, skillName: string, userInstruction: string): Promise<GeneratedOutput> {
  const response = await fetch(`${API_BASE}/cases/${caseId}/run/${skillName}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_instruction: userInstruction }),
  });
  if (!response.ok) throw new Error(`Run skill failed: ${response.status}`);
  return response.json();
}

export async function listOutputs(caseId: string): Promise<GeneratedOutput[]> {
  const response = await fetch(`${API_BASE}/cases/${caseId}/outputs`);
  if (!response.ok) throw new Error(`List outputs failed: ${response.status}`);
  return response.json();
}
