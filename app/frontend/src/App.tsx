import { useState } from "react";
import { Brain, FileText, MessagesSquare, School, Sparkles } from "lucide-react";
import { createCase, listOutputs, runSkill } from "./api";
import type { GeneratedOutput, StudentCase } from "./types";
import "./styles.css";

const actions = [
  ["student_profile_analysis", "背景分析", Brain],
  ["research_direction_design", "研究方向", Sparkles],
  ["school_supervisor_matching", "学校/导师", School],
  ["comparable_case_generator", "可比案例", FileText],
  ["consultant_delivery_rewriter", "顾问话术", MessagesSquare],
  ["consultation_call_prep", "电话准备", MessagesSquare],
] as const;

export default function App() {
  const [summary, setSummary] = useState("");
  const [regions, setRegions] = useState("香港,澳洲");
  const [studentCase, setStudentCase] = useState<StudentCase | null>(null);
  const [outputs, setOutputs] = useState<GeneratedOutput[]>([]);
  const [busy, setBusy] = useState(false);

  async function handleCreateCase() {
    setBusy(true);
    try {
      const created = await createCase({
        student_name: "匿名学生",
        summary,
        target_regions: regions.split(",").map((item) => item.trim()).filter(Boolean),
        notes: "",
      });
      setStudentCase(created);
      setOutputs([]);
    } finally {
      setBusy(false);
    }
  }

  async function handleRun(skillName: string, label: string) {
    if (!studentCase) return;
    setBusy(true);
    try {
      await runSkill(studentCase.id, skillName, `请生成${label}`);
      setOutputs(await listOutputs(studentCase.id));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="workspace">
      <section className="case-panel">
        <h1>PhD 咨询 Case 工作台</h1>
        <label>
          学生背景
          <textarea value={summary} onChange={(event) => setSummary(event.target.value)} />
        </label>
        <label>
          目标地区
          <input value={regions} onChange={(event) => setRegions(event.target.value)} />
        </label>
        <button disabled={!summary || busy} onClick={handleCreateCase}>创建 Case</button>
        {studentCase && <p className="case-id">当前 Case: {studentCase.id}</p>}
      </section>

      <section className="action-panel">
        {actions.map(([skillName, label, Icon]) => (
          <button key={skillName} disabled={!studentCase || busy} onClick={() => handleRun(skillName, label)}>
            <Icon size={16} />
            {label}
          </button>
        ))}
      </section>

      <section className="outputs">
        {outputs.map((output) => (
          <article key={output.id} className="output">
            <h2>{output.title}</h2>
            <pre>{output.content}</pre>
          </article>
        ))}
      </section>
    </main>
  );
}
