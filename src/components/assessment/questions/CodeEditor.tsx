import { useState, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Question } from "@/data/assessmentData";
import { Play, CheckCircle, XCircle } from "lucide-react";

interface CodeEditorProps {
  question: Question;
  answer: any;
  onAnswer: (answer: any) => void;
  language: "en" | "ar";
}

const CodeEditor = ({ question, answer, onAnswer, language }: CodeEditorProps) => {
  const [code, setCode] = useState(answer || "# Write your code here\n");
  const [testResults, setTestResults] = useState<{ passed: boolean; message: string }[]>([]);
  const [hasRun, setHasRun] = useState(false);

  useEffect(() => {
    if (answer) {
      setCode(answer);
    }
  }, [answer]);

  const handleCodeChange = (value: string | undefined) => {
    if (value !== undefined) {
      setCode(value);
      onAnswer(value);
    }
  };

  const runCode = () => {
    // Simulate code execution and test case validation
    const results = question.testCases?.map((testCase) => {
      // This is a simple mock - in a real app, you'd run the code in a sandbox
      const passed = Math.random() > 0.3; // 70% pass rate for demo
      return {
        passed,
        message: `Input: ${testCase.input} | Expected: ${testCase.expected} | ${
          passed ? "✓ Passed" : "✗ Failed"
        }`,
      };
    }) || [];

    setTestResults(results);
    setHasRun(true);
  };

  return (
    <div className="space-y-4">
      <div className="border border-border rounded-lg overflow-hidden">
        <Editor
          height="300px"
          defaultLanguage={question.codeLanguage || "python"}
          value={code}
          onChange={handleCodeChange}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      <Button onClick={runCode} className="gap-2">
        <Play size={16} />
        {language === "en" ? "Run Code" : "تشغيل الكود"}
      </Button>

      {hasRun && (
        <Card className="p-4">
          <h4 className="font-semibold mb-3">
            {language === "en" ? "Test Results" : "نتائج الاختبار"}
          </h4>
          <div className="space-y-2">
            {testResults.map((result, index) => (
              <div
                key={index}
                className={`flex items-start gap-2 p-3 rounded-lg ${
                  result.passed ? "bg-secondary/10" : "bg-destructive/10"
                }`}
              >
                {result.passed ? (
                  <CheckCircle size={18} className="text-secondary flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle size={18} className="text-destructive flex-shrink-0 mt-0.5" />
                )}
                <span className="text-sm font-mono">{result.message}</span>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-primary/5 rounded-lg">
            <p className="text-sm">
              <span className="font-semibold">
                {testResults.filter((r) => r.passed).length}/{testResults.length}
              </span>{" "}
              {language === "en" ? "test cases passed" : "حالات اختبار نجحت"}
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default CodeEditor;
